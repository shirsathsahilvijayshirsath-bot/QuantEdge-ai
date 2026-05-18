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

# Multi-select
stocks = st.sidebar.multiselect(
    "Select Stocks to Compare", 
    nifty50, 
    default=["RELIANCE.NS"]
)

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

# =========================
# 🕯️ Candlestick Chart
# =========================

st.subheader("🕯️ Candlestick Chart")

stock = stocks[0]

ohlc = yf.download(stock, start=start_date, end=end_date)

fig = go.Figure(data=[go.Candlestick(
    x=ohlc.index,
    open=ohlc['Open'],
    high=ohlc['High'],
    low=ohlc['Low'],
    close=ohlc['Close']
)])

fig.update_layout(
    title=f"{stock} Candlestick Chart",
    xaxis_title="Date",
    yaxis_title="Price"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# 🤖 Buy / Sell Signal
# =========================

st.subheader("🤖 Buy / Sell Signal")

signal_data = data[stock]

ma50 = signal_data.rolling(window=50).mean()
ma200 = signal_data.rolling(window=200).mean()

latest_ma50 = ma50.iloc[-1]
latest_ma200 = ma200.iloc[-1]
latest_price = signal_data.iloc[-1]

if latest_ma50 > latest_ma200:
    st.success(f"🟢 BUY Signal for {stock}")
elif latest_ma50 < latest_ma200:
    st.error(f"🔴 SELL Signal for {stock}")
else:
    st.warning("⚖️ HOLD")

# =========================
# 📉 RSI Indicator
# =========================

st.subheader("📉 RSI Indicator")

delta = signal_data.diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))

latest_rsi = rsi.iloc[-1]

st.write(f"RSI: {round(latest_rsi,2)}")

if latest_rsi > 70:
    st.error("🔴 Overbought (Sell Zone)")
elif latest_rsi < 30:
    st.success("🟢 Oversold (Buy Zone)")
else:
    st.warning("⚖️ Neutral")

st.line_chart(rsi, use_container_width=True)

# =========================
# 🎯 Stop Loss / Target
# =========================

st.subheader("🎯 Stop Loss & Target Calculator")

buy_price = st.number_input("Enter Buy Price", value=float(latest_price))

stop_loss = buy_price * 0.95
target = buy_price * 1.10

st.write(f"🛑 Stop Loss: ₹ {round(stop_loss,2)}")
st.write(f"🎯 Target: ₹ {round(target,2)}")

# =========================
# 🔔 Price Alert
# =========================

st.subheader("🔔 Price Alert")

alert_price = st.number_input("Set Alert Price", value=float(latest_price))

if latest_price >= alert_price:
    st.success(f"🚨 Alert! Price reached ₹ {alert_price}")
else:
    st.info(f"Current Price: ₹ {round(latest_price,2)}")

# =========================
# 📊 Normalized Comparison
# =========================

normalized = data.copy()

for col in normalized.columns:
    normalized[col] = (normalized[col] / normalized[col].iloc[0]) * 100

st.subheader("📊 Stock Comparison (Normalized)")
st.line_chart(normalized, use_container_width=True)

# =========================
# 🤖 AI Prediction
# =========================

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

st.line_chart(combined, use_container_width=True)

# =========================
# 💰 Latest Prices
# =========================

st.subheader("💰 Latest Prices")

for stock in stocks:
    price = data[stock].iloc[-1]
    st.write(f"{stock}: ₹ {round(price, 2)}")

# =========================
# 📋 Recent Data
# =========================

st.subheader("📋 Recent Data")
st.dataframe(data.tail())
