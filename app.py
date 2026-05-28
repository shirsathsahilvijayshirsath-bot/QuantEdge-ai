import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from collections import deque
from sklearn.linear_model import SGDClassifier
from datetime import datetime
import time

# ================= CONFIG =================
st.set_page_config(layout="wide")
st.title("🚀 QuantEdge AI - Trading Dashboard")

# ================= ML MODEL =================
prices = deque(maxlen=50)
model = SGDClassifier(loss="log_loss")
trained = False

def update_model():
    global trained

    if len(prices) < 20:
        return

    X, y = [], []
    arr = np.array(prices)

    for i in range(5, len(arr)-1):
        ret = (arr[i] - arr[i-1]) / arr[i-1]
        target = 1 if arr[i+1] > arr[i] else 0

        X.append([ret, arr[:i].mean(), np.std(arr[:i])])
        y.append(target)

    model.fit(X, y)
    trained = True

def predict():
    if not trained or len(prices) < 20:
        return "HOLD", 0

    arr = np.array(prices)

    ret = (arr[-1] - arr[-2]) / arr[-2]
    ma = arr.mean()
    vol = np.std(arr)

    prob = model.predict_proba([[ret, ma, vol]])[0]
    conf = max(prob)

    if prob[1] > 0.6:
        return "BUY", conf
    elif prob[0] > 0.6:
        return "SELL", conf

    return "HOLD", conf

# ================= SESSION =================
if "history" not in st.session_state:
    st.session_state.history = []

if "balance" not in st.session_state:
    st.session_state.balance = 100000

if "position" not in st.session_state:
    st.session_state.position = 0

# ================= SIMULATED PRICE =================
price = round(2500 + np.random.uniform(-10, 10), 2)

# ================= ML FLOW =================
prices.append(price)
update_model()
signal, confidence = predict()

# ================= TOP METRICS =================
col1, col2, col3 = st.columns(3)

col1.metric("💰 Price", f"₹{price}")

if signal == "BUY":
    col2.metric("🤖 Signal", "BUY 🟢")
elif signal == "SELL":
    col2.metric("🤖 Signal", "SELL 🔴")
else:
    col2.metric("🤖 Signal", "HOLD ⚪")

col3.metric("🧠 Confidence", f"{round(confidence*100,2)}%")

# ================= STORE HISTORY =================
st.session_state.history.append({
    "time": datetime.now(),
    "price": price
})

df = pd.DataFrame(st.session_state.history)

# ================= CHART =================
st.subheader("📈 Live Chart")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['time'],
    y=df['price'],
    mode='lines',
    name='Price'
))

st.plotly_chart(fig, use_container_width=True)

# ================= PAPER TRADING =================
st.subheader("💰 Paper Trading")

col1, col2 = st.columns(2)
qty = st.number_input("Quantity", min_value=1, value=1)

if col1.button("🟢 Buy"):
    if st.session_state.balance >= price * qty:
        st.session_state.position += qty
        st.session_state.balance -= price * qty

if col2.button("🔴 Sell"):
    if st.session_state.position >= qty:
        st.session_state.position -= qty
        st.session_state.balance += price * qty

# ================= PORTFOLIO =================
st.subheader("📊 Portfolio")

st.write(f"💵 Balance: ₹{round(st.session_state.balance,2)}")
st.write(f"📦 Position: {st.session_state.position}")

# ================= AUTO REFRESH =================
st.caption("🔄 Auto refresh every 2 sec")

time.sleep(2)
st.rerun()
