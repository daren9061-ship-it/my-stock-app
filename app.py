import streamlit as st
import yfinance as yf
import pandas as pd
import talib
from FinMind.data import DataLoader
import time

# 網頁設定
st.set_page_config(page_title="AI 選股儀表板", layout="wide")
st.title("🎯 AI 盤後選股儀表板")
st.markdown("策略條件：**20/60月線多頭** + **日均線糾結** + **收黑K** + **主力買超**")

# 側邊欄：股票清單設定
st.sidebar.header("設定")
stock_input = st.sidebar.text_area("輸入股票代號 (逗號隔開)", "2330, 2317, 2454, 2382, 2301, 3037, 2603, 2609, 2303, 3231, 2376")
stock_list = [s.strip() for s in stock_input.split(",")]

if st.sidebar.button("開始掃描今日標的"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, stock_id in enumerate(stock_list):
        try:
            status_text.text(f"正在分析: {stock_id}...")
            # 1. 抓取股價
            df = yf.download(f"{stock_id}.TW", period="3y", interval="1d", progress=False)
            if len(df) < 400: continue
            
            # 2. 計算技術指標
            df['ma400'] = talib.SMA(df['Close'], timeperiod=400) # 模擬20月線
            df['ma1200'] = talib.SMA(df['Close'], timeperiod=1200) # 模擬60月線
            df['ema2'] = talib.EMA(df['Close'], timeperiod=2)
            df['ema10'] = talib.EMA(df['Close'], timeperiod=10)
            df['ema20'] = talib.EMA(df['Close'], timeperiod=20)
            
            # 3. 判定條件
            cond_long = df['ma400'].iloc[-1] > df['ma1200'].iloc[-1]
            ema_vals = [df['ema2'].iloc[-1], df['ema10'].iloc[-1], df['ema20'].iloc[-1]]
            std_ratio = pd.Series(ema_vals).std() / df['Close'].iloc[-1]
            cond_cluster = std_ratio < 0.006
            cond_black_k = df['Close'].iloc[-1] < df['Open'].iloc[-1]
            
            if cond_long and cond_cluster and cond_black_k:
                # 4. 抓取籌碼 (FinMind)
                dl = DataLoader()
                today_str = df.index[-1].strftime('%Y-%m-%d')
                chip = dl.taiwan_stock_main_purchase(stock_id=stock_id, date=today_str)
                main_buy = chip['buy'].sum() - chip['sell'].sum()
                
                if main_buy > 0:
                    results.append({
                        "股票代號": stock_id,
                        "收盤價": f"{df['Close'].iloc[-1]:.1f}",
                        "主力買超(張)": int(main_buy),
                        "均線糾結度": f"{std_ratio:.2%}",
                        "診斷": "符合洗盤噴發條件"
                    })
        except: pass
        progress_bar.progress((i + 1) / len(stock_list))
    
    status_text.text("掃描完成！")
    if results:
        st.success(f"找到 {len(results)} 檔符合策略的標的")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.info("今日無符合標的。")
