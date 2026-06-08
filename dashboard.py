# ================= IMPORT =================
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="QuantEdge AI", layout="wide")

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

st.title("📊 QuantEdge AI - Master Version")

# ================= TELEGRAM =================
TOKEN ="8629163881:AAHrO4n9KpDNT0tMR1DoRvXeJeZ5VEIWCCA"
CHAT_ID ="7602586865"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# ================= SESSION =================
if "balance" not in st.session_state:
    st.session_state.balance = 100000.0
    st.session_state.positions = {}
    st.session_state.history = []

# ================= STOCK LIST =================
stocks = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"]

# ================= DATA & ENGINE =================
@st.cache_data(ttl=300) 
def get_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="1y")
        if df is None or df.empty:
            return None
        return df.dropna()
    except:
        return None

def advanced_engine(df):
    if df is None or len(df) < 50:
        return "HOLD", 0

    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['Tomorrow_Close'] = df['Close'].shift(-1)
    df['Target'] = (df['Tomorrow_Close'] > df['Close']).astype(int)
    df = df.dropna()
    
    try:
        price = float(df["Close"].iloc[-1])
        rsi = float(df["RSI"].iloc[-1])
        sma50 = float(df["SMA_50"].iloc[-1])
        
        features = ['Close', 'Volume', 'SMA_50', 'RSI']
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(df[features], df['Target'])
        
        latest_data = df.iloc[-1:]
        prediction = model.predict(latest_data[features])[0]
        confidence = model.predict_proba(latest_data[features])[0].max() * 100
        
        if prediction == 1 and rsi < 40 and price > sma50 and confidence > 55:
            return "BUY", price
        elif prediction == 0 and rsi > 65:
            return "SELL", price
        else:
            return "HOLD", price
    except:
        return "HOLD", 0

# ================= UI DASHBOARD =================
st.subheader("📡 Live ML Scanner & Charts")

if st.button("🔄 Refresh Market Data"):
    st.cache_data.clear()

cols = st.columns(len(stocks))

for i, stock in enumerate(stocks):
    df = get_data(stock)
    signal, price = advanced_engine(df)

    with cols[i]:
        st.metric(label=stock, value=signal, delta=f"₹{price:.2f}" if price > 0 else "")
        if df is not None:
            st.line_chart(df['Close'].tail(30), height=150)

    # Trade logic
    if stock not in st.session_state.positions:
        st.session_state.positions[stock] = 0
    qty = st.session_state.positions[stock]

    if signal == "BUY" and qty == 0 and price > 0:
        invest = st.session_state.balance * 0.1
        q = int(invest / price)
        if q > 0:
            st.session_state.positions[stock] = q
            st.session_state.balance -= q * price
            send_telegram(f"📈 BUY Alert: {stock} at ₹{price:.2f}")

    elif signal == "SELL" and qty > 0 and price > 0:
        st.session_state.balance += qty * price
        st.session_state.positions[stock] = 0
        send_telegram(f"📉 SELL Alert: {stock} at ₹{price:.2f}")

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("💼 Virtual Portfolio")
    st.write(f"**Cash Balance:** ₹{st.session_state.balance:,.2f}")
    for s, q in st.session_state.positions.items():
        if q > 0:
            st.write(f"- {s}: {q} Shares")
with col2:
    st.subheader("🛠 System Testing")
    if st.button("Test Telegram Connection"):
        send_telegram("🔥 QuantEdge AI is Online & Ready!")
        st.success("Test message sent!")
