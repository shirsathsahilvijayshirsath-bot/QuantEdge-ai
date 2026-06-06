import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# ================= CONFIG =================
st.set_page_config(layout="wide")
st.title("📈 QuantEdge AI - Pro Dashboard")

# ================= INPUT =================
stock = st.text_input("Enter Stock Symbol (Example: RELIANCE.NS)", "RELIANCE.NS")

# ================= FETCH DATA =================
def get_data(symbol):
    try:
        df = yf.Ticker(symbol).history(period="3mo")
        if df is None or df.empty:
            return None
        return df
    except:
        return None

data = get_data(stock)

# ================= UI =================
if data is None:
    st.error("❌ Stock data load nahi hua (symbol ya internet issue)")

    # fallback price
    price = 2500 + np.random.uniform(-50, 50)

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Price (Fallback)", f"₹{round(price,2)}")
    col2.metric("📊 Signal", "HOLD")
    col3.metric("⚠️ Status", "No Data")

else:
    data = data.dropna()

    if len(data) < 5:
        st.warning("⚠️ Data bahut kam hai")

    price = float(data["Close"].iloc[-1])

    # ================= SIGNAL LOGIC =================
    data["MA20"] = data["Close"].rolling(20).mean()

    signal = "HOLD"
    if len(data) > 20:
        if data["Close"].iloc[-1] > data["MA20"].iloc[-1]:
            signal = "BUY"
        elif data["Close"].iloc[-1] < data["MA20"].iloc[-1]:
            signal = "SELL"

    # ================= METRICS =================
    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Price", f"₹{round(price,2)}")
    col2.metric("🤖 Signal", signal)
    col3.metric("📊 Data Points", len(data))

    # ================= CHART =================
    st.subheader("📊 Price Chart")
    st.line_chart(data["Close"])

# ================= AUTO REFRESH =================
st.caption("🔄 Auto refresh every 5 seconds")

time.sleep(5)
st.rerun()
