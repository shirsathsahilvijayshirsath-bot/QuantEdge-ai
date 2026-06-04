import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(layout="wide")

# ================= CSS (PRO UI) =================
st.markdown("""
<style>
body {background-color: #0e1117; color: white;}
.block-container {padding: 1rem;}

.card {
    background: #1c1f26;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 10px;
}

.buy button {
    background: #00c853;
    color: white;
    height: 55px;
    width: 100%;
    font-size: 18px;
    border-radius: 12px;
}

.sell button {
    background: #ff1744;
    color: white;
    height: 55px;
    width: 100%;
    font-size: 18px;
    border-radius: 12px;
}

.nav {
    position: fixed;
    bottom: 0;
    width: 100%;
    background: #1c1f26;
    padding: 10px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ================= STATE =================
if "balance" not in st.session_state:
    st.session_state.balance = 100000

if "position" not in st.session_state:
    st.session_state.position = 0

if "history" not in st.session_state:
    st.session_state.history = []

if "page" not in st.session_state:
    st.session_state.page = "Trade"

# ================= PRICE SIM =================
price = 2500 + np.random.uniform(-10, 10)

st.session_state.history.append({
    "time": datetime.now(),
    "price": price
})

df = pd.DataFrame(st.session_state.history)

# ================= NAVIGATION =================
col1, col2, col3 = st.columns(3)

if col1.button("📊 Trade"):
    st.session_state.page = "Trade"
if col2.button("📈 Portfolio"):
    st.session_state.page = "Portfolio"
if col3.button("⚙️ Settings"):
    st.session_state.page = "Settings"

# ================= TRADE PAGE =================
if st.session_state.page == "Trade":

    st.title("📱 QuantEdge PRO")

    # PRICE CARD
    st.markdown(f"""
    <div class="card">
        <h2>₹{round(price,2)}</h2>
        <p>Live Market Price</p>
    </div>
    """, unsafe_allow_html=True)

    # AI SIGNAL
    signal = np.random.choice(["BUY", "SELL", "HOLD"])
    confidence = np.random.uniform(0.6, 0.95)

    st.markdown(f"""
    <div class="card">
        <h3>🤖 AI Signal: {signal}</h3>
        <p>Confidence: {round(confidence*100,1)}%</p>
    </div>
    """, unsafe_allow_html=True)

    # CANDLE CHART
    if len(df) > 5:
        df['open'] = df['price'].shift(1)
        df['high'] = df[['price','open']].max(axis=1)
        df['low'] = df[['price','open']].min(axis=1)
        df['close'] = df['price']

        fig = go.Figure(data=[go.Candlestick(
            x=df['time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])

        st.plotly_chart(fig, use_container_width=True)

    # BUY SELL
    col1, col2 = st.columns(2)

    def buy():
        if st.session_state.balance >= price:
            st.session_state.position += 1
            st.session_state.balance -= price

    def sell():
        if st.session_state.position > 0:
            st.session_state.position -= 1
            st.session_state.balance += price

    with col1:
        st.markdown('<div class="buy">', unsafe_allow_html=True)
        st.button("BUY", on_click=buy)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="sell">', unsafe_allow_html=True)
        st.button("SELL", on_click=sell)
        st.markdown('</div>', unsafe_allow_html=True)

# ================= PORTFOLIO =================
elif st.session_state.page == "Portfolio":

    st.title("📈 Portfolio")

    pnl = (st.session_state.position * price) + st.session_state.balance - 100000

    st.markdown(f"""
    <div class="card">
        <h3>Balance: ₹{round(st.session_state.balance,2)}</h3>
        <h3>Position: {st.session_state.position}</h3>
        <h2>PnL: ₹{round(pnl,2)}</h2>
    </div>
    """, unsafe_allow_html=True)

# ================= SETTINGS =================
elif st.session_state.page == "Settings":

    st.title("⚙️ Settings")

    st.write("Mode: Manual / Auto coming soon 😎")
    st.write("AI Level: Advanced")

# ================= AUTO REFRESH =================
time.sleep(2)
st.rerun()
