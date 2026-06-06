import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# ================= CONFIG =================
st.set_page_config(layout="wide")
st.title("📱 QuantEdge AI - Ultimate Trading App")

# ================= STATE =================
if "balance" not in st.session_state:
    st.session_state.balance = 100000
    st.session_state.position = 0
    st.session_state.history = []
    st.session_state.mode = "AUTO"

# ================= INPUT =================
stock_input = st.text_input("🔍 Stock Symbol (e.g. RELIANCE, TCS, INFY)", "RELIANCE")

# ================= DATA FUNCTION (FIXED) =================
def get_data(symbol):
    try:
        symbol = symbol.strip().upper()

        # Auto add .NS for Indian stocks
        if not symbol.endswith(".NS"):
            symbol = symbol + ".NS"

        df = yf.Ticker(symbol).history(period="3mo")

        # Retry if empty
        if df is None or df.empty:
            df = yf.download(symbol, period="3mo", progress=False)

        if df is None or df.empty:
            return None, symbol

        return df, symbol

    except:
        return None, symbol

data, stock = get_data(stock_input)

# ================= DEFAULT VALUES =================
status = "LIVE"
signal = "HOLD"
trend = "SIDEWAYS"
confidence = 0

# ================= LOGIC =================
if data is None:
    status = "FALLBACK"
    price = 2500 + np.random.uniform(-50, 50)

else:
    data = data.dropna()

    if len(data) < 20:
        status = "LOW DATA"

    price = float(data["Close"].iloc[-1])

    # Indicators
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()

    delta = data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))

    # Trend
    if len(data) > 50:
        if data["MA20"].iloc[-1] > data["MA50"].iloc[-1]:
            trend = "UPTREND"
        else:
            trend = "DOWNTREND"

    # Signal + Confidence
    if len(data) > 20:
        if price > data["MA20"].iloc[-1]:
            signal = "BUY"
            confidence = min(100, abs(price - data["MA20"].iloc[-1]) / price * 200)
        elif price < data["MA20"].iloc[-1]:
            signal = "SELL"
            confidence = min(100, abs(price - data["MA20"].iloc[-1]) / price * 200)

# ================= TRADING =================
def trade(sig, price):
    if sig == "BUY" and st.session_state.balance >= price:
        st.session_state.position += 1
        st.session_state.balance -= price

    elif sig == "SELL" and st.session_state.position > 0:
        st.session_state.position -= 1
        st.session_state.balance += price

    st.session_state.history.append({
        "time": pd.Timestamp.now(),
        "signal": sig,
        "price": price
    })

# AUTO MODE
if st.session_state.mode == "AUTO":
    if signal != "HOLD" and confidence > 60:
        trade(signal, price)

# ================= UI =================
col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Price", f"₹{round(price,2)}")
col2.metric("🤖 Signal", signal)
col3.metric("📊 Trend", trend)
col4.metric("🧠 Confidence", f"{round(confidence,2)}%")

# ================= STATUS =================
st.caption(f"Status: {status} | Symbol: {stock}")

if data is None:
    st.error(f"❌ '{stock}' ka data nahi mila (symbol check karo)")

# ================= CONTROLS =================
st.subheader("🎮 Control Panel")

c1, c2, c3, c4 = st.columns(4)

if c1.button("AUTO"):
    st.session_state.mode = "AUTO"

if c2.button("MANUAL"):
    st.session_state.mode = "MANUAL"

if c3.button("BUY"):
    trade("BUY", price)

if c4.button("SELL"):
    trade("SELL", price)

st.write("Mode:", st.session_state.mode)

# ================= CHART =================
st.subheader("📈 Chart")

if data is not None and not data.empty:
    st.line_chart(data["Close"])
else:
    fake = np.random.randn(50).cumsum() + price
    st.line_chart(fake)

# ================= PORTFOLIO =================
st.subheader("💼 Portfolio")

st.write("Balance:", round(st.session_state.balance,2))
st.write("Position:", st.session_state.position)

# ================= HISTORY =================
st.subheader("📜 Trade History")

if len(st.session_state.history) > 0:
    df_hist = pd.DataFrame(st.session_state.history)
    st.dataframe(df_hist.tail(10))
else:
    st.write("No trades yet")

# ================= REFRESH =================
st.caption("🔄 Auto refresh every 5 sec")

time.sleep(5)
st.rerun()
