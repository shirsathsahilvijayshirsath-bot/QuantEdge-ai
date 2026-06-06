# ================= IMPORT =================
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="QuantEdge ELITE+", layout="wide")

st.title("📊 QuantEdge AI - Live Alert System")

# ================= TELEGRAM =================
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ================= SESSION =================
if "last_alert" not in st.session_state:
    st.session_state.last_alert = {}

# ================= STOCK LIST =================
stocks = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"]

# ================= DATA =================
@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        df = yf.download(symbol, period="3mo", progress=False)
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
        return "BUY", price, pred
    elif all(sell):
        return "SELL", price, pred
    else:
        return "HOLD", price, pred

# ================= UI =================
st.subheader("📡 Live Alert Scanner")

for stock in stocks:

    df = get_data(stock)
    signal, price, pred = get_signal(df)

    if signal in ["BUY","SELL"]:

        # Avoid spam alerts
        last = st.session_state.last_alert.get(stock)

        if last != signal:
            msg = f"{stock} | {signal} | Price: ₹{round(price,2)}"
            send_alert(msg)
            st.session_state.last_alert[stock] = signal

    st.write(f"{stock} → {signal} @ ₹{round(price,2)}")

# ================= REFRESH =================
time.sleep(10)
st.rerun()
