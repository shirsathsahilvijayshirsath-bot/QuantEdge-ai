import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import date
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

# --- CONFIGURATION ---
stocks_list = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'SBIN', 'LT']
mode = "Intraday"

# --- 1. INITIALIZATION & CACHE ---
if "ml_models" not in st.session_state: st.session_state.ml_models = {}
if "last_trained" not in st.session_state: st.session_state.last_trained = {}
if "trade_count" not in st.session_state: st.session_state.trade_count = 0
if "last_day" not in st.session_state: st.session_state.last_day = date.today()
if "positions" not in st.session_state: st.session_state.positions = {}
if "entry_price" not in st.session_state: st.session_state.entry_price = {}
if "trail_price" not in st.session_state: st.session_state.trail_price = {}
if "balance" not in st.session_state: st.session_state.balance = 100000.0

if st.session_state.last_day != date.today():
    st.session_state.trade_count = 0
    st.session_state.last_day = date.today()

MAX_TRADES = 7

# --- 2. CORE FUNCTIONS (Data & AI) ---
def get_data(stock, mode):
    # Yahan apna API/Yahoo Finance logic lagayein
    return pd.DataFrame(np.random.randn(100, 4), columns=['Open', 'High', 'Low', 'Close']) 

def prepare_ml_data(df):
    # Dummy features (SMA/RSI logic yahan aayega)
    X = pd.DataFrame(np.random.randn(100, 3), columns=['SMA20', 'RSI', 'VOL'])
    y = np.random.randint(0, 2, 100)
    return X, y

def train_rf(df):
    X, y = prepare_ml_data(df)
    model = RandomForestClassifier().fit(X, y)
    return model, 0.65 # Acc

def train_xgb(df):
    X, y = prepare_ml_data(df)
    model = XGBClassifier().fit(X, y)
    return model, 0.68 # Acc

def get_best_model(stock, df):
    now = time.time()
    if stock not in st.session_state.last_trained or now - st.session_state.last_trained[stock] > 300:
        rf, rf_acc = train_rf(df)
        xgb, xgb_acc = train_xgb(df)
        if xgb_acc > rf_acc:
            st.session_state.ml_models[stock] = (xgb, "XGBoost", xgb_acc)
        else:
            st.session_state.ml_models[stock] = (rf, "RandomForest", rf_acc)
        st.session_state.last_trained[stock] = now
    return st.session_state.ml_models[stock]

def fast_ai_signal(stock, df):
    model, name, acc = get_best_model(stock, df)
    X, _ = prepare_ml_data(df)
    latest = X.iloc[-1:]
    pred = model.predict(latest)[0]
    confidence = np.random.uniform(60, 95) # Replace with model.predict_proba
    signal = "BUY" if pred == 1 else "SELL"
    return signal, confidence, name, acc

def risk_reward_ok(price, sl, target):
    risk = price * sl
    reward = price * target
    return (reward / risk) >= 2

# --- 3. MAIN DASHBOARD ---
st.write("🤖 **AI Engine Active (RF + XGB)**")
leaderboard = []

for stock in stocks_list:
    df = get_data(stock, mode)
    if df is not None:
        signal, confidence, name, acc = fast_ai_signal(stock, df)
        price = 1000.0 # Mock price
        leaderboard.append((stock, signal, confidence, price, name, acc))

leaderboard = [s for s in leaderboard if s[2] > 65 and s[5] > 0.55]
leaderboard.sort(key=lambda x: x[2], reverse=True)

st.subheader("🤖 AI Leaderboard")
for s in leaderboard[:10]:
    st.write(f"**{s[0]}** | {s[1]} | 🔥 {s[2]:.1f}% | ₹{s[3]:.2f} | 🧠 {s[4]} | Acc: {s[5]*100:.1f}%")

# Execution
if len(leaderboard) > 0 and leaderboard[0][2] > 70:
    best = leaderboard[0]
    if risk_reward_ok(best[3], 0.02, 0.04) and st.session_state.trade_count < MAX_TRADES:
        st.session_state.trade_count += 1
        st.success(f"🚀 EXECUTING: {best[0]}")
        st.session_state.positions[best[0]] = 1
