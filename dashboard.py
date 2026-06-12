# ================= IMPORT =================
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

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

st.title("📊 QuantEdge AI - Pro Institutional Version")
mode = st.radio("Select Trading Mode", ["Swing", "Intraday"])

# ================= RISK & REWARD CONFIG =================
if mode == "Intraday":
    STOP_LOSS_PCT = 0.01 # 1%
    TARGET_PCT = 0.02    # 2%
else:
    STOP_LOSS_PCT = 0.03 # 3%
    TARGET_PCT = 0.06    # 6%

# ================= TELEGRAM =================
TOKEN = "8629163881:AAHrO4n9KpDNT0tMR1DoRvXeJeZ5VEIWCCA" 
CHAT_ID = "7602586865"

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
    st.session_state.entry_price = {}

# ================= EXPANDED STOCK LIST =================
stocks = [
    "TATAMOTORS.NS", "M&M.NS", "DLF.NS", "BRITANNIA.NS", "BHARTIARTL.NS", "SBIN.NS",
    "KOTAKBANK.NS", "ZOMATO.NS", "TITAN.NS", "MAXHEALTH.NS", "HAL.NS", "LTIM.NS",
    "TORNTPHARM.NS", "BBOX.NS", "CYIENT.NS", "E2E.NS", "ASALCBR.NS", "SUZLON.NS",
    "ABB.NS", "CCL.NS", "SVRL.NS", "GESHIP.NS", "TDPOWERSYS.NS", "ANANDRATHI.NS",
    "CHOLAHLDNG.NS", "PRESTIGE.NS", "NESCO.NS", "WIPRO.NS", "TECHM.NS", "NIRLON.BO",
    "GODREJPROP.NS", "HAPPSTMNDS.NS", "TATAELXSI.NS", "MPHASIS.NS", "COFORGE.NS",
    "PERSISTENT.NS", "HCLTECH.NS", "INFY.NS", "NELCO.NS", "GODFRYPHLP.NS", "RADICO.NS",
    "MAXESTATES.NS", "KFINTECH.NS", "NPST.NS", "MCX.NS", "360ONE.NS", "SKIPPER.NS",
    "RATNAMANI.NS", "KIOCL.NS", "MARUTI.NS", "HYUNDAI.NS", "HINDALCO.NS", "ASIANPAINT.NS",
    "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "NESTLEIND.NS", "TRENT.NS", "EICHERMOT.NS", "CIPLA.NS",
    "LUPIN.NS", "ALKEM.NS", "ABBOTINDIA.NS", "JBCHEPHARM.NS", "GLAXO.NS", "LAURUSLABS.NS",
    "IPCALAB.NS", "MTARTECH.NS", "VEDL.NS", "HITACHIENRG.NS", "MUTHOOTFIN.NS", "BSE.NS",
    "CDSL.NS", "TVSMOTOR.NS", "TATATECH.NS", "TATACHEM.NS", "DCMSHRIRAM.NS", "SIEMENS.NS",
    "BAJAJHLDNG.NS", "TVSHLTD.NS", "MAHSCOOTER.NS", "KIRLOSIND.NS", "PILANIINVS.NS", "INDIGO.NS",
    "TAALENT.BO", "NTPC.NS", "MOTHERSON.NS", "ZYDUSLIFE.NS", "MAZDOCK.NS", "MCDOWELL-N.NS",
    "GLOBUSSPR.NS", "INDIAGLYCO.NS", "ABDL.NS", "CUMMINSIND.NS", "DIVISLAB.NS", "PIDILITIND.NS",
    "NAVINFLUOR.NS", "AETHER.NS", "ALKYLAMINE.NS", "ATUL.NS", "3MINDIA.NS", "SRF.NS",
    "SOLARINDS.NS", "KELTECHEN.BO", "SHREECEM.NS", "DALBHARAT.NS", "JKCEMENT.NS", "VBL.NS",
    "AXISBANK.NS", "HINDUNILVR.NS", "EMAMILTD.NS", "GILLETTE.NS", "CUPID.NS", "ZYDUSWELL.NS",
    "COLPAL.NS", "PGHH.NS", "GET&D.NS", "NETWEB.NS"
]

# ================= DATA & ADVANCED ENGINE =================
@st.cache_data(ttl=120)
def get_data(symbol, current_mode):
    try:
        stock = yf.Ticker(symbol)
        if current_mode == "Intraday": 
            df = stock.history(period="5d", interval="5m")
        else: 
            df = stock.history(period="1y")
            
        if df is None or df.empty: 
            return None 
        return df.dropna() 
    except: 
        return None 

def advanced_engine(df, current_mode):
    if df is None or len(df) < 50:
        return "HOLD", 0, 0

    # 1. Base Indicators
    df['SMA_50'] = df['Close'].rolling(window=50).mean() 
    delta = df['Close'].diff() 
    gain = delta.clip(lower=0).rolling(14).mean() 
    loss = (-delta.clip(upper=0)).rolling(14).mean() 
    rs = gain / loss 
    df['RSI'] = 100 - (100 / (1 + rs)) 
    
    # 2. UPGRADE: MACD (Momentum)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 3. UPGRADE: Bollinger Bands (Volatility)
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Up'] = df['BB_Mid'] + (df['BB_Std'] * 2)
    df['BB_Low'] = df['BB_Mid'] - (df['BB_Std'] * 2)

    df['Tomorrow_Close'] = df['Close'].shift(-1) 
    df['Target'] = (df['Tomorrow_Close'] > df['Close']).astype(int) 
    df = df.dropna() 
    
    try: 
        # Current Values
        price = float(df["Close"].iloc[-1]) 
        rsi = float(df["RSI"].iloc[-1]) 
        sma50 = float(df["SMA_50"].iloc[-1]) 
        macd = float(df["MACD"].iloc[-1])
        signal_line = float(df["Signal_Line"].iloc[-1])
        bb_low = float(df["BB_Low"].iloc[-1])
        
        # ML Brain Update
        features = ['Close', 'Volume', 'SMA_50', 'RSI', 'MACD', 'BB_Up', 'BB_Low'] 
        model = RandomForestClassifier(n_estimators=100, random_state=42) 
        model.fit(df[features], df['Target']) 
        
        latest_data = df.iloc[-1:] 
        prediction = model.predict(latest_data[features])[0] 
        
        # 4. UPGRADE: The Conviction Scoring System (Out of 100)
        score = 0
        if prediction == 1: score += 40               # AI thinks it will go up
        if rsi < 45: score += 20                      # Sasta mil raha hai
        if price > sma50: score += 10                 # Long term trend positive hai
        if macd > signal_line: score += 15            # Momentum strong hai
        if price <= (bb_low * 1.02): score += 15      # Bottom pakad liya hai (Bounce zone)

        # Execution Logic Based on Score
        if score >= 75:  # Sniper Entry: Sirf Top Grade
            return "BUY", price, score
        elif prediction == 0 and rsi > 70:
            return "SELL", price, score
        else:
            return "HOLD", price, score
    except:
        return "HOLD", 0, 0

# ================= UI DASHBOARD =================
st.subheader("📡 Pro ML Scanner (With Conviction Score)")

if st.button("🔄 Refresh Market Data"):
    st.cache_data.clear()

cols = st.columns(2)

for i, stock in enumerate(stocks):
    df = get_data(stock, mode)
    signal, price, score = advanced_engine(df, mode)

    with cols[i % 2]: 
        # UI mein Score dikhayega
        st.metric(label=f"{stock} (Score: {score}/100)", value=signal, delta=f"₹{price:.2f}" if price > 0 else "") 
        if df is not None: 
            st.line_chart(df['Close'].tail(30), height=140) 
            
    if stock not in st.session_state.positions: 
        st.session_state.positions[stock] = 0 
    qty = st.session_state.positions[stock] 
    
    if signal == "BUY" and qty == 0 and price > 0: 
        invest = st.session_state.balance * 0.1 
        q = int(invest / price) 
        if q > 0: 
            st.session_state.positions[stock] = q 
            st.session_state.balance -= q * price 
            st.session_state.entry_price[stock] = price
            
            calc_tg = price * (1 + TARGET_PCT)
            calc_sl = price * (1 - STOP_LOSS_PCT)
            
            msg = (f"🟢 [{mode}] HIGH CONVICTION BUY: {stock}\n"
                   f"💯 AI Score: {score}/100\n"
                   f"💰 Entry Price: ₹{price:.2f}\n"
                   f"🎯 Target Price: ₹{calc_tg:.2f}\n"
                   f"🛑 Stop Loss: ₹{calc_sl:.2f}")
            send_telegram(msg) 
            
    elif signal == "SELL" and qty > 0 and price > 0: 
        st.session_state.balance += qty * price 
        st.session_state.positions[stock] = 0 
        if stock in st.session_state.entry_price:
            del st.session_state.entry_price[stock]
        send_telegram(f"🔴 [{mode}] AI SELL Alert: {stock} at ₹{price:.2f}") 

st.divider()

# ================= RISK MANAGEMENT =================
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)

for s, q in list(st.session_state.positions.items()):
    if q > 0:
        df2 = get_data(s, mode)
        if df2 is None or len(df2) == 0:
            continue

        current_price = float(df2["Close"].iloc[-1]) 
        entry = st.session_state.entry_price.get(s) 
        if entry is None: 
            continue 
            
        if mode == "Intraday" and now.hour == 15 and now.minute >= 20:
            st.session_state.balance += q * current_price 
            st.session_state.positions[s] = 0 
            send_telegram(f"⏳ [{mode}] EOD EXIT: {s} at ₹{current_price:.2f}") 
            
        elif current_price <= entry * (1 - STOP_LOSS_PCT): 
            st.session_state.balance += q * current_price 
            st.session_state.positions[s] = 0 
            send_telegram(f"🛑 [{mode}] STOP LOSS HIT: {s} at ₹{current_price:.2f}") 
            
        elif current_price >= entry * (1 + TARGET_PCT): 
            st.session_state.balance += q * current_price 
            st.session_state.positions[s] = 0 
            send_telegram(f"🎯 [{mode}] TARGET HIT: {s} at ₹{current_price:.2f}") 

# ================= UI PORTFOLIO DISPLAY =================
col1, col2 = st.columns(2)
with col1:
    st.subheader("💼 Virtual Portfolio")
    st.write(f"**Cash Balance:** ₹{st.session_state.balance:,.2f}")
    
    active_trades = False
    for s, q in st.session_state.positions.items():
        if q > 0:
            active_trades = True
            entry = st.session_state.entry_price.get(s, 0)
            target_p = entry * (1 + TARGET_PCT)
            sl_p = entry * (1 - STOP_LOSS_PCT)
            
            st.markdown(f"### 📦 {s}")
            st.write(f"- **Qty:** {q} Shares")
            st.write(f"- **Entry Price:** ₹{entry:.2f}")
            st.write(f"- **Target:** ₹{target_p:.2f} | **SL:** ₹{sl_p:.2f}")
            st.divider()
            
    if not active_trades:
        st.info("Abhi portfolio mein koi active trade nahi hai.")

with col2:
    st.subheader("🛠 System Info")
    st.info("Powered by RandomForest ML, MACD, Bollinger Bands, and Conviction Scoring Algorithm.")
