import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import time

st.set_page_config(layout="wide")

# ================= STATE =================
if "balance" not in st.session_state:
    st.session_state.balance = 100000

if "position" not in st.session_state:
    st.session_state.position = 0

if "history" not in st.session_state:
    st.session_state.history = []

if "mode" not in st.session_state:
    st.session_state.mode = "AUTO"

# ================= LIVE DATA (SAFE) =================
ticker = "RELIANCE.NS"

data = yf.download(ticker, period="1d", interval="1m")

if data.empty or "Close" not in data:
    st.warning("⚠️ Live data load nahi hua, fallback use ho raha hai")
    price = 2500 + np.random.uniform(-5, 5)
    df = pd.DataFrame()
else:
    price = float(data["Close"].dropna().iloc[-1])
    df = data.reset_index()

# ================= AI STRATEGY =================
signal = "HOLD"

if not df.empty and len(df) > 20:
    df["MA20"] = df["Close"].rolling(20).mean()

    if df["Close"].iloc[-1] > df["MA20"].iloc[-1]:
        signal = "BUY"
    elif df["Close"].iloc[-1] < df["MA20"].iloc[-1]:
        signal = "SELL"

# ================= AUTO TRADING =================
def execute_trade(signal, price):
    if signal == "BUY" and st.session_state.balance >= price:
        st.session_state.position += 1
        st.session_state.balance -= price

    elif signal == "SELL" and st.session_state.position > 0:
        st.session_state.position -= 1
        st.session_state.balance += price

if st.session_state.mode == "AUTO":
    execute_trade(signal, price)

# ================= UI =================
st.title("🤖 QuantEdge AUTO TRADING")

col1, col2, col3 = st.columns(3)

col1.metric("💰 Price", f"₹{round(price,2)}")
col2.metric("📊 Signal", signal)
col3.metric("⚙️ Mode", st.session_state.mode)

# ================= CONTROL =================
c1, c2 = st.columns(2)

if c1.button("AUTO"):
    st.session_state.mode = "AUTO"

if c2.button("STOP"):
    st.session_state.mode = "STOP"

# ================= CHART =================
if not df.empty:
    fig = go.Figure(data=[go.Candlestick(
        x=df['Datetime'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    )])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Chart data available nahi hai")

# ================= PORTFOLIO =================
st.subheader("💰 Portfolio")

pnl = (st.session_state.position * price) + st.session_state.balance - 100000

st.write("Balance:", round(st.session_state.balance,2))
st.write("Position:", st.session_state.position)
st.write("PnL:", round(pnl,2))

# ================= AUTO REFRESH =================
time.sleep(5)
st.rerun()
