import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="QuantEdge AI PRO", layout="wide")

st.title("🚀 QuantEdge AI - Pro Trading Dashboard")

# Sidebar
st.sidebar.header("Settings")

# Stock list
nifty50 = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
    "HDFCBANK.NS", "ICICIBANK.NS",
    "LT.NS", "SBIN.NS", "ITC.NS"
]

# ✅ Multi-select for comparison
stocks = st.sidebar.multiselect("Select Stocks to Compare", nifty50, default=["RELIANCE.NS"])

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

if len(stocks) == 0:
    st.warning("Select at least one stock")
    st.stop()

# Fetch data
data = yf.download(stocks, start=start_date, end=end_date)["Close"]

if data.empty:
    st.error("No data found")
    st.stop()
if len(data) < 2:
    st.warning("Not enough data")
    st.stop()
# Normalize for comparison
normalized = data.copy()

for col in normalized.columns:
    normalized[col] = (normalized[col] / normalized[col].iloc[0]) * 100

st.subheader("📊 Stock Comparison (Normalized)")
st.line_chart(combined, use_container_width=True)

# 👇👇👇 YAHAN ADD KARNA HAI

# 🤖 AI Prediction (Simple Trend)

st.subheader("🤖 AI Prediction (Next 7 Days)")

last_price = data.iloc[-1]

predictions = []

returns = data.pct_change().mean()

for i in range(7):
    next_price = last_price * (1 + returns)
    predictions.append(next_price)
    last_price = next_price

future_dates = pd.date_range(start=data.index[-1], periods=7)
pred_df = pd.DataFrame(predictions, index=future_dates, columns=data.columns)

combined = pd.concat([data.tail(30), pred_df])

st.line_chart(combined)
# Show latest prices
st.subheader("💰 Latest Prices")

for stock in stocks:
    price = data[stock].iloc[-1]
    st.write(f"{stock}: ₹ {round(price,2)}")

# Optional: show raw data
st.subheader("📋 Recent Data")
st.dataframe(data.tail())
