# ================= IMPORT =================
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="QuantEdge ELITE", layout="wide")

st.title("📊 QuantEdge AI - Elite Trading System")

# ================= SESSION =================
if "balance" not in st.session_state:
    st.session_state.balance = 100000
    st.session_state.positions = {}
    st.session_state.history = []
    st.session_state.mode = "AUTO"
    st.session_state.last_trade_time = {}

# ================= STOCK LIST =================
stocks = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"]

# ================= DATA =================
@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        df = yf.download(symbol, period="3mo", progress=False)
        if df is None or df.empty:
            return None
        return df.dropna()
    except:
        return None

# ================= INDICATORS =================
def indicators(df):

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100/(1+rs))

    ema12 = df["Close"].ewm(span=12).mean()
    ema26 = df["Close"].ewm(span=26).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9).mean()

    df["MA10"] = df["Close"].rolling(10).mean()
    df["MA20"] = df["Close"].rolling(20).mean()

    return df.dropna()

# ================= SIGNAL =================
def get_signal(df):

    if df is None or len(df) < 30:
        return "HOLD", 0, 0, 0

    df = indicators(df)

    price = df["Close"].iloc[-1]

    X = df[["MA10","MA20"]]
    y = df["Close"]

    model = LinearRegression()
    model.fit(X, y)

    pred = model.predict([X.iloc[-1]])[0]

    rsi = df["RSI"].iloc[-1]
    macd = df["MACD"].iloc[-1]
    sig = df["Signal"].iloc[-1]

    buy = [pred > price, rsi < 35, macd > sig]
    sell = [pred < price, rsi > 65, macd < sig]

    if all(buy):
        signal = "BUY"
        conf = sum(buy)/3 * 100
    elif all(sell):
        signal = "SELL"
        conf = sum(sell)/3 * 100
    else:
        signal = "HOLD"
        conf = 0

    return signal, price, pred, conf

# ================= TRADE =================
def trade(stock, signal, price):

    now = time.time()

    # Overtrading protection (10 sec gap)
    if stock in st.session_state.last_trade_time:
        if now - st.session_state.last_trade_time[stock] < 10:
            return

    if stock not in st.session_state.positions:
        st.session_state.positions[stock] = 0

    qty = st.session_state.positions[stock]

    if signal == "BUY" and qty == 0:
        invest = st.session_state.balance * 0.1
        q = int(invest / price)
        if q > 0:
            st.session_state.positions[stock] = q
            st.session_state.balance -= q * price

    elif signal == "SELL" and qty > 0:
        st.session_state.balance += qty * price
        st.session_state.positions[stock] = 0

    st.session_state.last_trade_time[stock] = now

    st.session_state.history.append({
        "stock": stock,
        "signal": signal,
        "price": price,
        "time": pd.Timestamp.now()
    })

# ================= UI =================
st.subheader("📡 Live Smart Scanner")

cols = st.columns(len(stocks))

for i,stock in enumerate(stocks):

    df = get_data(stock)
    signal, price, pred, conf = get_signal(df)

    # ALERT STYLE
    if signal == "BUY" and conf >= 70:
        label = "⭐ STRONG BUY"
    elif signal == "SELL" and conf >= 70:
        label = "⭐ STRONG SELL"
    elif signal in ["BUY","SELL"]:
        label = "⚠️ WEAK"
    else:
        label = "⛔ HOLD"

    with cols[i]:
        st.metric(stock, label)

    # AUTO trading only strong signals
    if st.session_state.mode == "AUTO":
        if signal in ["BUY","SELL"] and conf >= 70:
            trade(stock, signal, price)

# ================= CONTROLS =================
st.subheader("⚙️ Controls")

c1,c2 = st.columns(2)

if c1.button("AUTO MODE"):
    st.session_state.mode = "AUTO"

if c2.button("MANUAL MODE"):
    st.session_state.mode = "MANUAL"

st.write("Mode:", st.session_state.mode)

# ================= PORTFOLIO =================
st.subheader("💼 Portfolio")

st.write("Balance:", round(st.session_state.balance,2))

for s,q in st.session_state.positions.items():
    st.write(f"{s}: {q}")

# ================= HISTORY =================
st.subheader("📜 Trade History")

if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history).tail(10))

# ================= REFRESH =================
time.sleep(5)
st.rerun()
