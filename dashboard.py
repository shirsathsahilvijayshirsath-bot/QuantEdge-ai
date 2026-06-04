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

# ================= LIVE DATA =================
ticker = "RELIANCE.NS"
data = yf.download(ticker, period="1d", interval="1m")

price = float(data["Close"].iloc[-1])
df = data.reset_index()

# ================= SIMPLE AI STRATEGY =================
df["MA20"] = df["Close"].rolling(20).mean()

signal = "HOLD"

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
st.title("🤖 AUTO TRADING BOT")

col1, col2, col3 = st.columns(3)

col1.metric("💰 Price", f"₹{round(price,2)}")
col2.metric("📊 Signal", signal)
col3.metric("⚙️ Mode", st.session_state.mode)

# ================= CONTROL =================
if st.button("AUTO"):
    st.session_state.mode = "AUTO"

if st.button("STOP"):
    st.session_state.mode = "STOP"

# ================= CHART =================
fig = go.Figure(data=[go.Candlestick(
    x=df['Datetime'],
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close']
)])

st.plotly_chart(fig, use_container_width=True)

# ================= PORTFOLIO =================
st.subheader("💰 Portfolio")

pnl = (st.session_state.position * price) + st.session_state.balance - 100000

st.write("Balance:", round(st.session_state.balance,2))
st.write("Position:", st.session_state.position)
st.write("PnL:", round(pnl,2))

# ================= REFRESH =================
time.sleep(5)
st.rerun()
