import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from FinMind.data import DataLoader

st.set_page_config(page_title="AI 自動選股儀表板", layout="wide")
st.title("🎯 AI 全自動盤後掃描")

# --- 自動導入股票池 (0050 + 0051 成份股示例) ---
default_list = [
    '2330','2317','2454','2382','2301','3037','2603','2609','2303','3231','2376',
    '2357','2881','2882','2002','2412','2308','2886','2884','2885','2891','1301',
    '1303','3711','2408','2327','2892','2880','2883','2887','1216','2912','5871'
    # 您可以繼續在此增加更多代號，建議控制在 100-150 檔內效果最好
]

st.sidebar.header("掃描設定")
mode = st.sidebar.radio("選擇掃描模式", ["自動掃描預設清單", "手動輸入代號"])

if mode == "手動輸入代號":
    stock_input = st.sidebar.text_area("輸入代號 (逗號隔開)", "2330, 2317")
    active_list = [s.strip() for s in stock_input.split(",")]
else:
    active_list = default_list
    st.sidebar.info(f"當前預設清單共 {len(active_list)} 檔熱門股")

if st.sidebar.button("🚀 開始全自動掃描"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, stock_id in enumerate(active_list):
        try:
            status_text.text(f"正在掃描 ({i+1}/{len(active_list)}): {stock_id}")
            df = yf.download(f"{stock_id}.TW", period="3y", interval="1d", progress=False)
            if len(df) < 240: continue
            
            # 技術面計算
            df['ma400'] = ta.sma(df['Close'], length=400)
            df['ma1200'] = ta.sma(df['Close'], length=1200)
            df['ema2'] = ta.ema(df['Close'], length=2)
            df['ema10'] = ta.ema(df['Close'], length=10)
            df['ema20'] = ta.ema(df['Close'], length=20)
            
            # 判斷邏輯
            cond_long = df['ma400'].iloc[-1] > df['ma1200'].iloc[-1]
            ema_vals = [df['ema2'].iloc[-1], df['ema10'].iloc[-1], df['ema20'].iloc[-1]]
            std_ratio = pd.Series(ema_vals).std() / df['Close'].iloc[-1]
            cond_cluster = std_ratio < 0.007 
            cond_black_k = df['Close'].iloc[-1] < df['Open'].iloc[-1]
            
            if cond_long and cond_cluster and cond_black_k:
                # 籌碼面計算
                dl = DataLoader()
                today_str = df.index[-1].strftime('%Y-%m-%d')
                chip = dl.taiwan_stock_main_purchase(stock_id=stock_id, date=today_str)
                main_buy = chip['buy'].sum() - chip['sell'].sum()
                
                if main_buy > 0:
                    results.append({
                        "代號": stock_id,
                        "收盤價": f"{df['Close'].iloc[-1]:.1f}",
                        "主力買超(張)": int(main_buy),
                        "均線糾結度": f"{std_ratio:.2%}"
                    })
        except: pass
        progress_bar.progress((i + 1) / len(active_list))
    
    status_text.empty()
    if results:
        st.success(f"✅ 掃描完成！符合「洗盤噴發」條件的股票如下：")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("今日預設清單中無符合標的。")
