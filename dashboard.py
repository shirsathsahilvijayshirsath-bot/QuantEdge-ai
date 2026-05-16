import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="QuantEdge AI PRO", layout="wide")

st.title("🚀 QuantEdge AI - Pro Trading Dashboard")

# Sidebar
st.sidebar.header("Settings")

# ✅ Nifty 50 Dropdown
nifty50 = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
    "HDFCBANK.NS", "ICICIBANK.NS",
    "LT.NS", "SBIN.NS", "ITC.NS"
]

stock = st.sidebar.selectbox("Select Stock", nifty50)

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Fetch data
data = yf.download(stock, start=start_date, end=end_date)

if data.empty:
    st.error("Invalid stock symbol")
    st.stop()

# Indicators
data["50_MA"] = data["Close"].rolling(50).mean()
data["200_MA"] = data["Close"].rolling(200).mean()

# BUY/SELL SIGNAL
latest_price = data["Close"].iloc[-1]
ma50 = data["50_MA"].iloc[-1]
ma200 = data["200_MA"].iloc[-1]

signal = ""

if ma50 > ma200:
    signal = "🟢 BUY"
elif ma50 < ma200:
    signal = "🔴 SELL"
else:
    signal = "⚪ HOLD"

st.subheader(f"Signal: {signal}")

# Candlestick chart
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name="Candles"
))

fig.add_trace(go.Scatter(x=data.index, y=data["50_MA"], name="50 MA"))
fig.add_trace(go.Scatter(x=data.index, y=data["200_MA"], name="200 MA"))

st.plotly_chart(fig, use_container_width=True)

# Stats
st.subheader("📊 Stats")
st.write("Latest Price:", round(latest_price, 2))
st.write("High:", round(data["High"].max(), 2))
st.write("Low:", round(data["Low"].min(), 2))

# Data
st.subheader("📋 Recent Data")
st.dataframe(data.tail())
