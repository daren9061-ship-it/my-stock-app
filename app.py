import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from FinMind.data import DataLoader
from datetime import datetime, timedelta

# 1. 網頁基本設定
st.set_page_config(page_title="AI 選股儀表板", layout="wide")
st.title("🎯 AI 全方位選股系統")

# 初始化資料庫
dl = DataLoader()

def get_top_turnover(market_types, count=100):
    """獲取成交值排行榜標的"""
    try:
        target_date = datetime.now().strftime('%Y-%m-%d')
        df_price = dl.taiwan_stock_price_all(date=target_date)
        df_info = dl.taiwan_stock_info()
        df = pd.merge(df_price, df_info[['stock_id', 'type']], on='stock_id')
        market_map = {"上市": "twse", "上櫃": "tpex"}
        selected = [market_map[m] for m in market_types]
        top_df = df[df['type'].isin(selected)].sort_values(by='Trading_money', ascending=False).head(count)
        return top_df['stock_id'].tolist()
    except:
        return []

# 2. 側邊欄設定
st.sidebar.header("🔧 功能切換")
mode = st.sidebar.selectbox("模式選擇", ["成交值排行掃描", "自定義代號輸入"])

if mode == "成交值排行掃描":
    market_choice = st.sidebar.multiselect("市場選擇", ["上市", "上櫃"], default=["上市"])
    scan_limit = st.sidebar.slider("掃描名數", 50, 200, 100)
else:
    stock_input = st.sidebar.text_area("請輸入代號 (用空格或逗號隔開)", "2330, 2317, 2454")
    scan_limit = 0

# 3. 執行按鈕
if st.sidebar.button("🚀 開始掃描"):
    if mode == "成交值排行掃描":
        if not market_choice:
            st.error("請選擇市場！")
            st.stop()
        with st.spinner("獲取排行資料中..."):
            all_targets = get_top_turnover(market_choice, scan_limit)
    else:
        all_targets = [s.strip() for s in stock_input.replace(',', ' ').split() if s.strip()]

    if not all_targets:
        st.warning("無有效代號。")
    else:
        results = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        for i, stock_id in enumerate(all_targets):
            try:
                status.text(f"正在掃描 ({i+1}/{len(all_targets)}): {stock_id}")
                df = yf.download(f"{stock_id}.TW", period="3y", interval="1d", progress=False)
                if len(df) < 240: continue
                
                # 指標計算 (使用 pandas_ta)
                df['ma400'] = ta.sma(df['Close'], length=400)
                df['ma1200'] = ta.sma(df['Close'], length=1200)
                df['ema2'] = ta.ema(df['Close'], length=2)
                df['ema10'] = ta.ema(df['Close'], length=10)
                df['ema20'] = ta.ema(df['Close'], length=20)
                
                # 判定邏輯
                c_long = df['ma400'].iloc[-1] > df['ma1200'].iloc[-1]
                ema_v = [df['ema2'].iloc[-1], df['ema10'].iloc[-1], df['ema20'].iloc[-1]]
                std_r = pd.Series(ema_v).std() / df['Close'].iloc[-1]
                c_cluster = std_r < 0.007
                c_black = df['Close'].iloc[-1] < df['Open'].iloc[-1]
                
                if c_long and c_cluster and c_black:
                    # 籌碼判斷
                    t_str = df.index[-1].strftime('%Y-%m-%d')
                    chip = dl.taiwan_stock_main_purchase(stock_id=stock_id, date=t_str)
                    main_b = chip['buy'].sum() - chip['sell'].sum()
                    
                    if main_b > 0:
                        results.append({
                            "代號": stock_id,
                            "價格": f"{df['Close'].iloc[-1]:.1f}",
                            "主力買超": f"{int(main_b)}張",
                            "糾結度": f"{std_ratio:.2%}"
                        })
            except: pass
            progress_bar.progress((i + 1) / len(all_targets))
            
        status.empty()
        if results:
            st.success("✅ 篩選完成！符合標的如下：")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.info("掃描結束，今日清單中無符合條件標的。")
