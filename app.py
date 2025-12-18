import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from FinMind.data import DataLoader
from datetime import datetime, timedelta

# 網頁基本設定
st.set_page_config(page_title="AI 綜合選股系統", layout="wide")
st.title("🎯 AI 全方位選股：排行掃描 + 手動輸入")

# 初始化 FinMind 資料庫
dl = DataLoader()

def get_top_turnover_stocks(market_types, count=200):
    """取得選定市場成交值前 N 名的股票代號"""
    target_date = datetime.now().strftime('%Y-%m-%d')
    try:
        df_price = dl.taiwan_stock_price_all(date=target_date)
        df_info = dl.taiwan_stock_info()
        df = pd.merge(df_price, df_info[['stock_id', 'type']], on='stock_id')
        
        market_map = {"上市": "twse", "上櫃": "tpex"}
        selected_types = [market_map[m] for m in market_types]
        
        top_stocks = df[df['type'].isin(selected_types)].sort_values(by='Trading_money', ascending=False).head(count)
        return top_stocks['stock_id'].tolist()
    except:
        return []

# --- 側邊欄：功能切換 ---
st.sidebar.header("🔧 選股模式")
mode = st.sidebar.selectbox("請選擇模式", ["成交值排行掃描", "自定義代號輸入"])

if mode == "成交值排行掃描":
    market_choice = st.sidebar.multiselect("選擇市場", ["上市", "上櫃"], default=["上市"])
    scan_limit = st.sidebar.slider("掃描總名數", 50, 400, 100)
    st.sidebar.info("💡 系統將自動抓取當日成交額最大的標的進行過濾。")
else:
    stock_input = st.sidebar.text_area("請輸入股票代號 (用逗號或空格隔開)", "2330, 2317, 2454, 2382, 3037")
    scan_limit = 0 # 手動模式不限制數量
    st.sidebar.info("💡 針對您指定的名單進行精準分析。")

# --- 執行按鈕 ---
if st.sidebar.button("🚀 開始掃描"):
    # 決定目標清單
    if mode == "成交值排行掃描":
        if not market_choice:
            st.error("請至少選擇一個市場！")
            st.stop()
        with st.
