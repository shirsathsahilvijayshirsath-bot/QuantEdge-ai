# ================= IMPORT =================
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="QuantEdge AI", layout="wide")

st.title("📊 QuantEdge AI - Telegram Enabled")

# ================= TELEGRAM =================
TOKEN = 8629163881:AAHrO4n9KpDNT0tMR1DoRvXeJeZ5VEIWCCA
CHAT_ID = "7602586865"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    try:
        requests.post(url, data=data)
    except:
        pass

# ================= SESSION =================
if "balance" not in st.session_state:
    st.session_state.balance = 100000
    st.session_state.positions = {}
    st.session_state.history = []

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
        return "HOLD", 0, 0

    df = indicators(df)

    try:
        price = float(df["Close"].iloc[-1])
        rsi = float(df["RSI"].iloc[-1])
        macd = float(df["MACD"].iloc[-1])
        sig = float(df["Signal"].iloc[-1])

        X = df[["MA10","MA20"]]
        y = df["Close"]

        model = LinearRegression()
        model.fit(X, y)

        pred = float(model.predict([X.iloc[-1]])[0])

    except:
        return "HOLD", 0, 0

    buy = (pred > price) and (rsi < 35) and (macd > sig)
    sell = (pred < price) and (rsi > 65) and (macd < sig)

    if buy:
        return "BUY", price, pred
    elif sell:
        return "SELL", price, pred
    else:
        return "HOLD", price, pred

# ================= TRADE =================
def trade(stock, signal, price):

    if stock not in st.session_state.positions:
        st.session_state.positions[stock] = 0

    qty = st.session_state.positions[stock]

    if signal == "BUY" and qty == 0:
        invest = st.session_state.balance * 0.1
        q = int(invest / price)

        if q > 0:
            st.session_state.positions[stock] = q
            st.session_state.balance -= q * price

            send_telegram(f"📈 BUY {stock} at ₹{price}")

    elif signal == "SELL" and qty > 0:
        st.session_state.balance += qty * price
        st.session_state.positions[stock] = 0

        send_telegram(f"📉 SELL {stock} at ₹{price}")

    st.session_state.history.append({
        "stock": stock,
        "signal": signal,
        "price": price,
        "time": pd.Timestamp.now()
    })

# ================= UI =================
st.subheader("📡 Live Scanner")

cols = st.columns(len(stocks))

for i, stock in enumerate(stocks):

    df = get_data(stock)
    signal, price, pred = get_signal(df)

    with cols[i]:
        st.metric(stock, signal)

    if signal in ["BUY","SELL"] and price > 0:
        trade(stock, signal, price)

# ================= PORTFOLIO =================
st.subheader("💼 Portfolio")

st.write("Balance:", round(st.session_state.balance,2))

for s,q in st.session_state.positions.items():
    st.write(f"{s}: {q}")

# ================= HISTORY =================
st.subheader("📜 Trade History")

if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history).tail(10))

# ================= TEST =================
if st.button("Test Telegram"):
    send_telegram("🔥 Bot Connected Successfully!")

# ================= AUTO REFRESH =================
time.sleep(5)
st.rerun()
