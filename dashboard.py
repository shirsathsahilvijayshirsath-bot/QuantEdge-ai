# ================= IMPORT =================
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz
import os
import joblib

st.set_page_config(page_title="QuantEdge AI", layout="wide", page_icon="📊")

# ================= SECURITY LOGIN =================
MY_PASSWORD = "QuantEdge2026"

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]: 
        st.title("🔒 Security Gateway") 
        st.text_input("Apna Password Darj Karein:", type="password", key="password_input") 
        
        if st.session_state.get("password_input") == MY_PASSWORD: 
            st.session_state["password_correct"] = True 
            st.rerun() 
        elif st.session_state.get("password_input"): 
            st.error("❌ Galat Password! Kripya dobara try karein.") 
        return False 
    return True 

if not check_password():
    st.stop()

# ================= CONFIG =================
st.title("📊 QuantEdge AI - Ultimate Apex Engine")
mode = st.radio("Select Trading Mode", ["Swing", "Intraday"], horizontal=True)

if mode == "Intraday":
    STOP_LOSS_PCT = 0.01   # 1%
    TARGET_PCT = 0.025     # 2.5%
else:
    STOP_LOSS_PCT = 0.03   # 3%
    TARGET_PCT = 0.08      # 8%

ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)

# ================= TELEGRAM =================
TOKEN = "8629163881:AAHrO4n9KpDNT0tMR1DoRvXeJeZ5VEIWCCA" 
CHAT_ID = "7602586865"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass  # Silent fail in production

# ================= SESSION STATE =================
if "balance" not in st.session_state:
    st.session_state.balance = 100000.0
    st.session_state.positions = {}
    st.session_state.entry_price = {}
    st.session_state.highest_price = {}

# ================= STOCK LIST =================
stocks = [
    "TATAMOTORS.NS", "M&M.NS", "DLF.NS", "BRITANNIA.NS", "BHARTIARTL.NS", "SBIN.NS",
    "KOTAKBANK.NS", "ZOMATO.NS", "TITAN.NS", "MAXHEALTH.NS", "HAL.NS", "LTIM.NS",
    "TORNTPHARM.NS", "SUZLON.NS", "ABB.NS", "GODREJPROP.NS", "HAPPSTMNDS.NS",
    "TATAELXSI.NS", "PERSISTENT.NS", "HCLTECH.NS", "INFY.NS", "MARUTI.NS", "HYUNDAI.NS",
    "HINDALCO.NS", "ASIANPAINT.NS", "BAJAJ-AUTO.NS", "TRENT.NS", "EICHERMOT.NS",
    "TVSMOTOR.NS", "NTPC.NS", "MOTHERSON.NS", "ZYDUSLIFE.NS", "MAZDOCK.NS", "AXISBANK.NS",
    "HINDUNILVR.NS", "PIDILITIND.NS", "SRF.NS", "VBL.NS", "NETWEB.NS"
]

# ================= CACHED MODEL =================
@st.cache_resource
def get_model():
    MODEL_PATH = "rf_model.pkl"
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    joblib.dump(model, MODEL_PATH)
    return model

# ================= MARKET REGIME =================
@st.cache_data(ttl=300)
def get_market_regime(current_mode):
    try:
        nifty = yf.Ticker("^NSEI")
        if current_mode == "Intraday":
            df = nifty.history(period="5d", interval="5m")
        else:
            df = nifty.history(period="6mo")
        
        if df.empty:
            return True, "Unknown"
            
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        latest_close = df['Close'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        
        is_bullish = latest_close > sma_50
        status = "Bullish (Safe to Buy)" if is_bullish else "Bearish (Defensive Mode)"
        return is_bullish, status
    except:
        return True, "Data Error (Allowing Trades)"

# ================= DATA FETCH =================
@st.cache_data(ttl=90, show_spinner=False)
def get_data(symbol, current_mode):
    try:
        stock = yf.Ticker(symbol)
        if current_mode == "Intraday":
            df = stock.history(period="5d", interval="5m")
        else:
            df = stock.history(period="1y")
        return df.dropna() if not df.empty else None
    except:
        return None

# ================= CORE ENGINE =================
def advanced_engine(symbol, df, current_mode):
    if df is None or len(df) < 100:
        return "HOLD", 0, 0, "Insufficient Data"

    try:
        df = df.copy()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['Volume_SMA_20'] = df['Volume'].rolling(window=20).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger
        df['BB_Mid'] = df['Close'].rolling(window=20).mean()
        df['BB_Std'] = df['Close'].rolling(window=20).std()
        df['BB_Low'] = df['BB_Mid'] - (df['BB_Std'] * 2)
        
        if current_mode == "Intraday":
            df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['VP'] = df['Typical_Price'] * df['Volume']
            df['Date'] = df.index.date
            df['Cum_Vol'] = df.groupby('Date')['Volume'].cumsum()
            df['Cum_VP'] = df.groupby('Date')['VP'].cumsum()
            df['VWAP'] = df['Cum_VP'] / df['Cum_Vol']
        
        df = df.dropna()
        if len(df) < 50:
            return "HOLD", 0, 0, "Data Error"

        price = float(df["Close"].iloc[-1])
        rsi = float(df["RSI"].iloc[-1])
        sma50 = float(df["SMA_50"].iloc[-1])
        macd = float(df["MACD"].iloc[-1])
        signal_line = float(df["Signal_Line"].iloc[-1])
        vwap_price = float(df["VWAP"].iloc[-1]) if current_mode == "Intraday" else 0
        current_vol = float(df["Volume"].iloc[-1])
        avg_vol = float(df["Volume_SMA_20"].iloc[-1])

        model = get_model()
        features = ['Close', 'Volume', 'SMA_50', 'RSI', 'MACD']
        latest_data = df[features].iloc[-1:].copy()
        prediction = model.predict(latest_data)[0]

        score = 0
        reasons = []

        if prediction == 1:
            score += 25
            reasons.append("Model Bullish")
        if rsi < 45:
            score += 12
            reasons.append("Oversold")
        if price > sma50:
            score += 12
            reasons.append("Above SMA50")
        if macd > signal_line:
            score += 12
            reasons.append("MACD Bullish")
        if current_vol > (avg_vol * 1.5):
            score += 10
            reasons.append("Volume Surge")

        if current_mode == "Intraday":
            if price > vwap_price:
                score += 35
                reasons.append("✅ Above VWAP")
            else:
                score -= 35
                reasons.append("❌ Below VWAP")

        status_msg = " | ".join(reasons[:3])

        if score >= 80:
            return "BUY", price, score, status_msg
        elif prediction == 0 and rsi > 72:
            return "SELL", price, score, status_msg
        else:
            return "HOLD", price, score, status_msg

    except Exception as e:
        return "HOLD", 0, 0, "Error"

# ================= UI =================
if st.button("🔄 Refresh All Data"):
    st.cache_data.clear()

is_bullish, regime_status = get_market_regime(mode)

if is_bullish:
    st.success(f"🌐 **Nifty 50 Trend:** {regime_status}")
else:
    st.error(f"🌐 **Nifty 50 Trend:** {regime_status} - Defensive Mode Active")

can_take_new_trades = not (mode == "Intraday" and (now.hour > 14 or (now.hour == 14 and now.minute >= 30)))

st.caption(f"🕒 IST: {now.strftime('%H:%M:%S')} | Mode: **{mode}**")

st.divider()

# ================= MAIN RADAR =================
leaderboard = []
cols = st.columns(2)

for stock in stocks:
    df = get_data(stock, mode)
    signal, price, score, status_msg = advanced_engine(stock, df, mode)
    
    leaderboard.append((stock, signal, score, price, status_msg))

    with cols[stocks.index(stock) % 2]:
        st.metric(
            label=f"{stock} (Score: {score})", 
            value=signal,
            delta=f"₹{price:.2f}" if price > 0 else ""
        )
        if df is not None and not df.empty:
            st.line_chart(df['Close'].tail(30), height=120, use_container_width=True)

# ================= TOP OPPORTUNITIES =================
st.divider()
st.subheader("🏆 Top Signals")

leaderboard = sorted(leaderboard, key=lambda x: x[2], reverse=True)

col_buy, col_sell = st.columns(2)

with col_buy:
    st.subheader("🟢 Top BUY Opportunities")
    buy_list = [s for s in leaderboard if s[1] == "BUY"]
    if buy_list:
        for s in buy_list[:8]:
            st.success(f"**{s[0]}** — Score: **{s[2]}** | ₹{s[3]:.2f} | {s[4]}")
    else:
        st.info("No strong BUY signals right now.")

with col_sell:
    st.subheader("🔴 Top SELL Opportunities")
    sell_list = [s for s in leaderboard if s[1] == "SELL"]
    if sell_list:
        for s in sell_list[:6]:
            st.error(f"**{s[0]}** — Score: **{s[2]}** | ₹{s[3]:.2f}")
    else:
        st.info("No strong SELL signals right now.")

# ================= AUTO TRADE EXECUTION & RISK MANAGEMENT =================
for stock, signal, _, price, _ in leaderboard:
    qty = st.session_state.positions.get(stock, 0)
    
    if signal == "BUY" and qty == 0 and price > 0 and can_take_new_trades:
        alloc_pct = 0.15 if score >= 85 and is_bullish else 0.10 if is_bullish else 0.05
        invest = st.session_state.balance * alloc_pct
        q = int(invest / price)
        
        if q > 0:
            st.session_state.positions[stock] = q
            st.session_state.balance -= q * price
            st.session_state.entry_price[stock] = price
            st.session_state.highest_price[stock] = price
            
            calc_tg = price * (1 + TARGET_PCT)
            calc_sl = price * (1 - STOP_LOSS_PCT)
            
            emoji = "🟢 [AGGRESSIVE]" if alloc_pct == 0.15 else "🔵 [STANDARD]" if is_bullish else "🛡️ [DEFENSIVE]"
            
            msg = f"{emoji} {mode} BUY: {stock}\nScore: {score}\nEntry: ₹{price:.2f}\nTarget: ₹{calc_tg:.2f}\nSL: ₹{calc_sl:.2f}"
            send_telegram(msg)

    elif signal == "SELL" and qty > 0 and price > 0:
        st.session_state.balance += qty * price
        st.session_state.positions[stock] = 0
        st.session_state.entry_price.pop(stock, None)
        st.session_state.highest_price.pop(stock, None)
        send_telegram(f"🔴 [{mode}] SELL: {stock} @ ₹{price:.2f}")

# ================= TRAILING STOP & TARGET =================
for s, q in list(st.session_state.positions.items()):
    if q > 0:
        df2 = get_data(s, mode)
        if df2 is None or len(df2) == 0:
            continue
        current_price = float(df2["Close"].iloc[-1])
        
        if s not in st.session_state.highest_price:
            st.session_state.highest_price[s] = st.session_state.entry_price.get(s, current_price)
        
        if current_price > st.session_state.highest_price[s]:
            st.session_state.highest_price[s] = current_price
            
        trailing_sl = st.session_state.highest_price[s] * (1 - STOP_LOSS_PCT)
        entry = st.session_state.entry_price.get(s)
        
        if mode == "Intraday" and now.hour == 15 and now.minute >= 20:
            st.session_state.balance += q * current_price
            st.session_state.positions[s] = 0
            send_telegram(f"⏳ EOD EXIT: {s} @ ₹{current_price:.2f}")
            
        elif current_price <= trailing_sl:
            st.session_state.balance += q * current_price
            st.session_state.positions[s] = 0
            send_telegram(f"🛑 Trailing SL Hit: {s} @ ₹{current_price:.2f}")
            
        elif current_price >= entry * (1 + TARGET_PCT):
            st.session_state.balance += q * current_price
            st.session_state.positions[s] = 0
            send_telegram(f"🎯 Target Hit: {s} @ ₹{current_price:.2f}")

# ================= PORTFOLIO =================
st.divider()
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("💼 Portfolio")
    st.write(f"**Cash Balance:** ₹{st.session_state.balance:,.2f}")
    
    if st.session_state.positions:
        for s, q in st.session_state.positions.items():
            if q > 0:
                entry = st.session_state.entry_price.get(s)
                high = st.session_state.highest_price.get(s, entry)
                current_sl = high * (1 - STOP_LOSS_P
