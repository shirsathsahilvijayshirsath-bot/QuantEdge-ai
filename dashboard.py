import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import numpy as np
from collections import deque
from sklearn.linear_model import SGDClassifier
from datetime import datetime

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

# ================= STATE =================
if "balance" not in st.session_state:
    st.session_state.balance = 100000

if "position" not in st.session_state:
    st.session_state.position = 0

if "mode" not in st.session_state:
    st.session_state.mode = "AUTO"

if "manual_signal" not in st.session_state:
    st.session_state.manual_signal = "HOLD"

# ================= TRADING =================
def execute_trade(signal, price):
    if signal == "BUY" and st.session_state.balance >= price:
        st.session_state.position += 1
        st.session_state.balance -= price

    elif signal == "SELL" and st.session_state.position > 0:
        st.session_state.position -= 1
        st.session_state.balance += price

# ================= STREAMLIT =================
st.set_page_config(layout="wide")
st.title("🚀 QuantEdge AI - FINAL PRO SYSTEM")

# ================= PRICE (SIMULATED) =================
price = 2500 + np.random.uniform(-5, 5)

# ================= ML FLOW =================
prices.append(price)
update_model()
signal, confidence = predict()

# ================= EXECUTION =================
if st.session_state.mode == "AUTO":
    if signal != "HOLD" and confidence > 0.65:
        execute_trade(signal, price)

elif st.session_state.mode == "MANUAL":
    if st.session_state.manual_signal in ["BUY", "SELL"]:
        execute_trade(st.session_state.manual_signal, price)
        st.session_state.manual_signal = "HOLD"

# ================= UI =================
col1, col2, col3 = st.columns(3)

col1.metric("💰 Price", f"₹{round(price,2)}")
col2.metric("🤖 Signal", signal)
col3.metric("🧠 Confidence", f"{round(confidence*100,2)}%")

# ================= CONTROL PANEL =================
st.subheader("🎮 Control Panel")

c1, c2, c3, c4 = st.columns(4)

if c1.button("AUTO"):
    st.session_state.mode = "AUTO"

if c2.button("MANUAL"):
    st.session_state.mode = "MANUAL"

if c3.button("BUY"):
    st.session_state.manual_signal = "BUY"

if c4.button("SELL"):
    st.session_state.manual_signal = "SELL"

if st.button("🚨 STOP"):
    st.session_state.mode = "STOP"

st.write("Mode:", st.session_state.mode)

# ================= CHART =================
if "history" not in st.session_state:
    st.session_state.history = []

st.session_state.history.append({
    "time": datetime.now(),
    "price": price
})

df = pd.DataFrame(st.session_state.history)

fig = go.Figure()
fig.add_trace(go.Scatter(x=df['time'], y=df['price'], mode='lines'))

st.plotly_chart(fig, use_container_width=True)

# ================= PORTFOLIO =================
st.subheader("💰 Portfolio")

st.write("Balance:", round(st.session_state.balance,2))
st.write("Position:", st.session_state.position)

# ================= REFRESH =================
time.sleep(2)
st.rerun()
