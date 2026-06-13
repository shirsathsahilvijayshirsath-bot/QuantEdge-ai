
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# Page config
st.set_page_config(page_title="QuantEdge AI", layout="wide")

# ================= SECURITY LOGIN =================
MY_PASSWORD = "QuantEdge2026"
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]: 
        st.title("🔒 Security Gateway") 
        if st.text_input("Apna Password Darj Karein:", type="password") == MY_PASSWORD: 
            st.session_state["password_correct"] = True
            st.rerun()
        st.stop()
check_password()

st.title("📊 QuantEdge AI - Ultimate Apex Engine")
mode = st.radio("Select Trading Mode", ["Swing", "Intraday"])

# ================= SESSION =================
if "balance" not in st.session_state:
    st.session_state.balance = 100000.0
    st.session_state.positions = {}
    st.session_state.entry_price = {}
    st.session_state.highest_price = {}

# ================= STOCK LIST (Unlimited) =================
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

# ================= CORE LOGIC =================
@st.cache_data(ttl=300)
def get_data(symbol, mode):
    try:
        return yf.Ticker(symbol).history(period="5d" if mode == "Intraday" else "1y", interval="5m" if mode == "Intraday" else "1d")
    except: return None

def advanced_engine(df):
    if df is None or len(df) < 50: return "HOLD", 0, 0
    df = df.copy()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df = df.dropna()
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(df[['Close', 'SMA_50']], df['Target'])
    pred = model.predict(df[['Close', 'SMA_50']].tail(1))[0]
    score = 80 if pred == 1 else 20
    return ("BUY" if pred == 1 else "SELL"), float(df['Close'].iloc[-1]), score

# ================= MAIN UI =================
st.subheader("📡 Radar Scan")
leaderboard = []

for stock in stocks:
    df = get_data(stock, mode)
    signal, price, score = advanced_engine(df)
    leaderboard.append((stock, signal, price, score))

for s in sorted(leaderboard, key=lambda x: x[3], reverse=True):
    st.write(f"**{s[0]}** | Signal: {s[1]} | Score: {s[3]} | Price: ₹{s[2]:.2f}")
    if s[1] == "BUY" and s[3] > 70:
        if st.button(f"Execute {s[0]}", key=s[0]):
            st.success(f"Trade Executed: {s[0]}")
