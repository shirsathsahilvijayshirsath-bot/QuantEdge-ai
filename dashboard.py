# ================= QUANTEDGE AI v8.0 - AUTONOMOUS AI AGENT + HEDGED POSITIONS =================
# New in v8: Long Short positions simultaneously (hedging), voice alerts, strategy builder
# ====================================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from datetime import datetime, timedelta
import pytz
import math
import time as time_module

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

st.set_page_config(
    page_title="QuantEdge AI v8.0 — Autonomous Agent",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ================= CSS =================
st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; color: #e0e6f0; }
    div[data-testid="stSidebarContent"] { background-color: #0d1520; border-right: 1px solid #00d4ff15; }
    .main-header { background: linear-gradient(135deg, #0d1b2a 0%, #1a2744 50%, #0d1b2a 100%); border: 1px solid #00d4ff33; border-radius: 12px; padding: 18px 26px; margin-bottom: 18px; box-shadow: 0 0 30px #00d4ff15; }
    .main-header h1 { color: #00d4ff; font-size: 1.9rem; font-weight: 800; letter-spacing: 2px; margin: 0; }
    .main-header p  { color: #7a8fa6; font-size: 0.8rem; margin: 3px 0 0 0; letter-spacing: 1px; }
    .card-buy  { background:linear-gradient(135deg,#003d1f,#005a2b); border:1px solid #00ff8844; border-left:4px solid #00ff88; border-radius:8px; padding:12px 14px; margin:5px 0; }
    .card-sell { background:linear-gradient(135deg,#3d0000,#5a0000); border:1px solid #ff444444; border-left:4px solid #ff4444; border-radius:8px; padding:12px 14px; margin:5px 0; }
    .card-hold { background:linear-gradient(135deg,#1a1f2e,#222840); border:1px solid #ffffff15; border-left:4px solid #555; border-radius:8px; padding:12px 14px; margin:5px 0; }
    .card-info { background:#0d1b2a; border:1px solid #00d4ff22; border-radius:10px; padding:14px; margin:6px 0; }
    .card-alert{ background:linear-gradient(135deg,#1a1400,#2a2000); border:1px solid #ffaa0044; border-left:4px solid #ffaa00; border-radius:8px; padding:12px 14px; margin:5px 0; }
    .ai-box    { background:#0d1520; border:1px solid #00d4ff22; border-radius:8px; padding:12px 16px; font-size:0.85rem; color:#a0b4c8; font-style:italic; }
    .sr-buy    { color:#00ff88; font-weight:700; }
    .sr-sell   { color:#ff4444; font-weight:700; }
    .sr-neutral{ color:#ffaa00; font-weight:600; }
    .news-card { background:#0d1b2a; border:1px solid #ffffff10; border-radius:8px; padding:10px 12px; margin:5px 0; }
    .stTabs [data-baseweb="tab-list"] { background-color:#0d1520; border-bottom:1px solid #00d4ff22; }
    .stTabs [data-baseweb="tab"]      { color:#7a8fa6; font-weight:600; }
    .stTabs [aria-selected="true"]    { color:#00d4ff !important; border-bottom:2px solid #00d4ff !important; }
    .leaderboard-gold   { background:linear-gradient(135deg,#2a1f00,#3d2e00); border:1px solid #ffd70044; border-left:4px solid #ffd700; border-radius:8px; padding:10px 14px; margin:4px 0; }
    .leaderboard-silver { background:linear-gradient(135deg,#1a1f2e,#222840); border:1px solid #c0c0c044; border-left:4px solid #c0c0c0; border-radius:8px; padding:10px 14px; margin:4px 0; }
    .leaderboard-bronze { background:linear-gradient(135deg,#1a1000,#2a1800); border:1px solid #cd7f3244; border-left:4px solid #cd7f32; border-radius:8px; padding:10px 14px; margin:4px 0; }
    .pred-up   { color:#00ff88; font-size:1.3rem; font-weight:800; }
    .pred-down { color:#ff4444; font-size:1.3rem; font-weight:800; }
    .pred-box  { background:#0d1b2a; border:1px solid #00d4ff22; border-radius:10px; padding:16px; text-align:center; }
</style>
""", unsafe_allow_html=True)

# ================= AUTH =================
MY_PASSWORD = "QuantEdge2026"
def check_password():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if not st.session_state.auth:
        st.markdown('<div class="main-header"><h1>⚡ QUANTEDGE AI v8.0</h1><p>SECURE TRADING TERMINAL</p></div>', unsafe_allow_html=True)
        _, c, _ = st.columns([1, 2, 1])
        with c:
            pwd = st.text_input("🔒 Password:", type="password")
            if pwd == MY_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            elif pwd:
                st.error("❌ Galat Password!")
        return False
    return True

if not check_password():
    st.stop()

# ================= CONSTANTS =================
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)
TOKEN   = "8629163881:AAHrO4n9KpDNT0tMR1DoRvXeJeZ5VEIWCCA"
CHAT_ID = "7602586865"

# ================= MARKET UNIVERSES =================
NSE_STOCKS = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","HINDUNILVR.NS",
    "HDFC.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS","ITC.NS","LT.NS",
    "AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","TITAN.NS","ULTRACEMCO.NS",
    "WIPRO.NS","SUNPHARMA.NS","TECHM.NS","NESTLEIND.NS","BAJFINANCE.NS",
    "POWERGRID.NS","NTPC.NS","ONGC.NS","JSWSTEEL.NS","TATASTEEL.NS",
    "HCLTECH.NS","M&M.NS","BAJAJFINSV.NS",
    "ADANIENT.NS","ADANIPORTS.NS","ADANIGREEN.NS","DMART.NS","SIEMENS.NS",
    "PIDILITIND.NS","HAVELLS.NS","MARICO.NS","DABUR.NS","GODREJCP.NS",
    "MUTHOOTFIN.NS","CHOLAFIN.NS","RECLTD.NS","PFC.NS","IRCTC.NS",
    "INDHOTEL.NS","TRENT.NS","VEDL.NS","HINDALCO.NS","COALINDIA.NS",
    "GRASIM.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS","EICHERMOT.NS","TVSMOTOR.NS",
    "TATAMOTORS.NS","MOTHERSON.NS","BOSCHLTD.NS","MRF.NS","APOLLOHOSP.NS",
    "ZOMATO.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","DELHIVERY.NS",
    "HDFCLIFE.NS","SBILIFE.NS","ICICIGI.NS","MFSL.NS","STARHEALTH.NS",
    "DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","PHOENIXLTD.NS","PRESTIGE.NS",
    "PERSISTENT.NS","LTIM.NS","TATAELXSI.NS","MPHASIS.NS","COFORGE.NS",
    "HAPPSTMNDS.NS","NETWEB.NS","KPIT.NS","CYIENT.NS","MASTEK.NS",
    "SUZLON.NS","CESC.NS","TORNTPOWER.NS","TATAPOWER.NS","ADANIPOWER.NS",
    "HAL.NS","BEL.NS","BHEL.NS","COCHINSHIP.NS","MAZDOCK.NS","GRSE.NS",
    "TORNTPHARM.NS","ZYDUSLIFE.NS","AUROPHARMA.NS","ALKEM.NS","IPCALAB.NS",
    "MAXHEALTH.NS","FORTIS.NS","METROPOLIS.NS","LALPATHLAB.NS","THYROCARE.NS",
    "BRITANNIA.NS","VBL.NS","JUBLFOOD.NS","DEVYANI.NS","SAPPHIRE.NS",
    "ABB.NS","CUMMINSIND.NS","THERMAX.NS","BHARAT FORGE.NS","KALYANKJIL.NS",
    "SRF.NS","AARTIIND.NS","DEEPAKNTR.NS","PIIND.NS","UPL.NS",
    "AXISBANK.NS","BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","RBLBANK.NS",
]

CRYPTO = [
    "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD","ADA-USD",
    "AVAX-USD","DOGE-USD","MATIC-USD","DOT-USD","LINK-USD","UNI-USD",
    "ATOM-USD","LTC-USD","BCH-USD","ALGO-USD","XLM-USD","FIL-USD",
    "NEAR-USD","APT-USD","ARB-USD","OP-USD","INJ-USD","SUI-USD","TIA-USD"
]

US_STOCKS = [
    "AAPL","MSFT","GOOGL","AMZN","NVDA","TSLA","META","AMD","NFLX","JPM",
    "BAC","V","WMT","DIS","PLTR","UBER","COIN","SNOW","SHOP","CRWD",
    "ABNB","RBLX","HOOD","ARM","SMCI","MU","INTC","QCOM","AVGO","TSM",
    "BABA","JD","PDD","NIO","XPEV","LI","RIVN","LCID","F","GM",
    "XOM","CVX","COP","SLB","HAL","GS","MS","C","WFC","AXP",
    "PFE","MRNA","JNJ","ABBV","LLY","UNH","CVS","CI","HUM","ANTM",
]

NIFTY_INDEX  = "^NSEI"
SP500_INDEX  = "^GSPC"
BTC_BENCH    = "BTC-USD"

SECTOR_MAP = {
    "NSE": {
        "IT":         ["INFY.NS","TCS.NS","HCLTECH.NS","WIPRO.NS","TECHM.NS","TATAELXSI.NS",
                       "PERSISTENT.NS","LTIM.NS","MPHASIS.NS","COFORGE.NS","HAPPSTMNDS.NS",
                       "NETWEB.NS","KPIT.NS","CYIENT.NS","MASTEK.NS"],
        "Banking":    ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS",
                       "BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","RBLBANK.NS"],
        "Auto":       ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","EICHERMOT.NS",
                       "TVSMOTOR.NS","HEROMOTOCO.NS","BOSCHLTD.NS","MRF.NS","MOTHERSON.NS"],
        "Pharma":     ["SUNPHARMA.NS","TORNTPHARM.NS","ZYDUSLIFE.NS","AUROPHARMA.NS",
                       "ALKEM.NS","IPCALAB.NS","APOLLOHOSP.NS","MAXHEALTH.NS","FORTIS.NS",
                       "METROPOLIS.NS","LALPATHLAB.NS","THYROCARE.NS"],
        "Energy":     ["ONGC.NS","NTPC.NS","POWERGRID.NS","COALINDIA.NS","ADANIPOWER.NS",
                       "TATAPOWER.NS","CESC.NS","TORNTPOWER.NS","ADANIGREEN.NS"],
        "Metals":     ["JSWSTEEL.NS","TATASTEEL.NS","HINDALCO.NS","VEDL.NS"],
        "FMCG":       ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS","VBL.NS",
                       "MARICO.NS","DABUR.NS","GODREJCP.NS","JUBLFOOD.NS","DEVYANI.NS"],
        "Realty":     ["DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","PHOENIXLTD.NS","PRESTIGE.NS"],
        "Finance":    ["BAJFINANCE.NS","BAJAJFINSV.NS","MUTHOOTFIN.NS","CHOLAFIN.NS",
                       "RECLTD.NS","PFC.NS","HDFCLIFE.NS","SBILIFE.NS","ICICIGI.NS","MFSL.NS"],
        "Defense":    ["HAL.NS","BEL.NS","BHEL.NS","COCHINSHIP.NS","MAZDOCK.NS","GRSE.NS"],
        "Consumer":   ["TITAN.NS","ASIANPAINT.NS","TRENT.NS","DMART.NS","ZOMATO.NS",
                       "NYKAA.NS","PAYTM.NS","POLICYBZR.NS","DELHIVERY.NS","IRCTC.NS"],
        "Chemicals":  ["SRF.NS","AARTIIND.NS","DEEPAKNTR.NS","PIIND.NS","UPL.NS","PIDILITIND.NS"],
        "Industrials":["ABB.NS","CUMMINSIND.NS","THERMAX.NS","SIEMENS.NS","ULTRACEMCO.NS",
                       "GRASIM.NS","HAVELLS.NS"],
        "Conglomerate":["RELIANCE.NS","ADANIENT.NS","ADANIPORTS.NS","LT.NS"],
    },
    "Crypto": {
        "Layer1":     ["BTC-USD","ETH-USD","SOL-USD","ADA-USD","AVAX-USD","NEAR-USD","APT-USD","SUI-USD"],
        "Exchange/DeFi":["BNB-USD","UNI-USD","LINK-USD"],
        "Payments":   ["XRP-USD","LTC-USD","BCH-USD","XLM-USD"],
        "Meme/Other": ["DOGE-USD"],
        "Scaling":    ["MATIC-USD","ARB-USD","OP-USD","TIA-USD"],
        "Infra":      ["DOT-USD","ATOM-USD","ALGO-USD","FIL-USD","INJ-USD"],
    },
    "US": {
        "Big Tech":   ["AAPL","MSFT","GOOGL","AMZN","META"],
        "Semiconductors":["NVDA","AMD","MU","INTC","QCOM","AVGO","TSM","SMCI","ARM"],
        "EV/Auto":    ["TSLA","F","GM","RIVN","LCID","NIO","XPEV","LI"],
        "Banking":    ["JPM","BAC","GS","MS","C","WFC"],
        "Fintech":    ["V","AXP","COIN","HOOD"],
        "Energy":     ["XOM","CVX","COP","SLB","HAL"],
        "Healthcare": ["PFE","MRNA","JNJ","ABBV","LLY","UNH","CVS","CI","HUM","ANTM"],
        "Consumer":   ["WMT","DIS","NFLX","UBER","ABNB","RBLX"],
        "Software":   ["SNOW","SHOP","CRWD","PLTR"],
        "China ADR":  ["BABA","JD","PDD"],
    },
}

# ================= SESSION STATE — 3 INDEPENDENT AI AGENTS =================
def make_agent_state():
    return {
        "balance": 100000.0,
        "starting_capital": 100000.0,
        "positions": {},        # {pos_key: qty} qty can be positive (LONG) or negative (SHORT)
        "entry_price": {},
        "highest_price": {},    # for LONG positions (profit protection)
        "lowest_price": {},     # for SHORT positions (profit protection)
        "entry_mode": {},       # {pos_key: "Intraday"/"Swing"}
        "position_direction": {}, # {pos_key: "LONG"/"SHORT"}
        "trade_log": [],        # full history: BUY/SELL/SHORT with direction tag
        "paused_until": None,   # drawdown protection: ISO timestamp string
        "pause_reason": "",
    }

DEFAULTS = {
    "agent_nse":    make_agent_state(),
    "agent_crypto": make_agent_state(),
    "agent_us":     make_agent_state(),
    "price_alerts": [],
    "triggered_alerts": [],
    "agent_running": True,           
    "last_scan_time": None,
    "weekly_reports": [],            
    "scan_log": [],                  
    "daily_summaries": [],           
    "last_summary_date": None,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        if isinstance(v, dict):
            st.session_state[k] = {kk: (list(vv) if isinstance(vv, list) else (dict(vv) if isinstance(vv, dict) else vv))
                                    for kk, vv in v.items()} if k.startswith("agent_") else dict(v)
        elif isinstance(v, list):
            st.session_state[k] = list(v)
        else:
            st.session_state[k] = v

AGENT_KEYS = {"NSE": "agent_nse", "Crypto": "agent_crypto", "US": "agent_us"}
AGENT_CURRENCY = {"NSE": "₹", "Crypto": "$", "US": "$"}

# ================= SIDEBAR — AI AGENT CONTROL PANEL =================
with st.sidebar:
    st.markdown("## ⚡ QuantEdge AI v8.0")
    st.markdown("##### 🤖 Autonomous Trading Agent")
    st.divider()

    st.session_state.agent_running = st.toggle("🟢 AI Agent ACTIVE", value=st.session_state.agent_running)
    if st.session_state.agent_running:
        st.success("Agent live hai — auto-scanning every 5 min")
    else:
        st.warning("Agent paused — manual mode")

    st.divider()
    st.markdown("### 🌐 Markets AI Manages")
    manage_nse    = st.checkbox("🇮🇳 NSE India",  value=True)
    manage_crypto = st.checkbox("🪙 Crypto",       value=True)
    manage_us     = st.checkbox("🇺🇸 US Stocks",   value=True)

    st.divider()
    st.markdown("### 📊 Trade Styles AI Runs")
    run_intraday = st.checkbox("⚡ Intraday", value=True)
    run_swing    = st.checkbox("📈 Swing",    value=True)

    st.divider()
    st.markdown("### ⚙️ Risk Settings")
    ic1, ic2 = st.columns(2)
    with ic1:
        st.caption("Intraday")
        INTRA_SL = st.slider("SL %",  0.5, 3.0, 1.0, 0.1, key="intra_sl") / 100
        INTRA_TG = st.slider("TG %",  1.0, 5.0, 2.5, 0.1, key="intra_tg") / 100
    with ic2:
        st.caption("Swing")
        SWING_SL = st.slider("SL %",  1.0, 8.0,  3.0, 0.5, key="swing_sl") / 100
        SWING_TG = st.slider("TG %",  3.0, 20.0, 8.0, 0.5, key="swing_tg") / 100

    st.divider()
    telegram_on = st.toggle("📲 Telegram Alerts", value=True)
    sound_alert_on = st.toggle("🔊 Sound Alerts (browser)", value=True,
                               help="Beep sound bajega jab AI Agent BUY/SELL execute kare. Tab open rakhna zaroori hai.")
    min_score   = st.slider("Min Signal Score (auto-trade)", 50, 95, 75)
    max_alloc_pct = st.slider("Max % capital per trade", 5, 30, 15)
    mtf_confirm = st.toggle("🎯 Multi-Timeframe Confirmation", value=True,
                            help="Higher timeframe trend ko bhi check karega before BUY — fewer but stronger signals")

    st.divider()
    st.markdown("### 📉 Drawdown Protection")
    dd_protection_on = st.toggle("Auto-pause on losing streak", value=True)
    dd_streak_limit   = st.slider("Pause after N consecutive losses", 2, 8, 4)
    dd_pause_hours    = st.slider("Pause duration (hours)", 1, 48, 12)

    st.divider()
    st.markdown("### 🔄 Auto-Compounding")
    compounding_on = st.toggle("Reinvest profits (compound)", value=False,
                               help="Off: position size stays based on fixed starting capital. On: position size grows/shrinks with current balance.")

    st.divider()
    st.caption(f"🕒 {now.strftime('%d %b %Y  %H:%M:%S')} IST")
    if st.session_state.last_scan_time:
        st.caption(f"🔄 Last scan: {st.session_state.last_scan_time}")

ACTIVE_MARKETS = []
if manage_nse:    ACTIVE_MARKETS.append("NSE")
if manage_crypto: ACTIVE_MARKETS.append("Crypto")
if manage_us:     ACTIVE_MARKETS.append("US")

ACTIVE_MODES = []
if run_intraday: ACTIVE_MODES.append("Intraday")
if run_swing:    ACTIVE_MODES.append("Swing")

MARKET_UNIVERSE = {"NSE": NSE_STOCKS, "Crypto": CRYPTO, "US": US_STOCKS}
MARKET_BENCH    = {"NSE": NIFTY_INDEX, "Crypto": BTC_BENCH, "US": SP500_INDEX}
RISK_PARAMS     = {"Intraday": (INTRA_SL, INTRA_TG), "Swing": (SWING_SL, SWING_TG)}

def market_can_trade(market, mode_):
    if mode_ != "Intraday": return True
    if market == "Crypto": return True
    if market == "NSE": return not (now.hour > 14 or (now.hour == 14 and now.minute >= 30))
    if market == "US": return True
    return True

def send_telegram(msg):
    if not telegram_on: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg}, timeout=8)
    except: pass

@st.cache_data(ttl=90, show_spinner=False)
def get_data(symbol, current_mode):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="5d", interval="5m") if current_mode == "Intraday" else t.history(period="1y")
        return df.dropna() if not df.empty else None
    except: return None
@st.cache_data(ttl=300, show_spinner=False)
def get_market_regime(bench, current_mode):
    try:
        df = yf.Ticker(bench).history(period="6mo" if current_mode == "Swing" else "5d",
                                       interval="1d"  if current_mode == "Swing" else "5m")
        if df.empty: return True, "Unknown", 50
        df['SMA50'] = df['Close'].rolling(50).mean()
        last = df['Close'].iloc[-1]
        sma  = df['SMA50'].iloc[-1]
        bull = last > sma
        pct  = (last - sma) / sma * 100
        return bull, f"{'Bullish' if bull else 'Bearish'} ({pct:+.1f}% vs SMA50)", abs(pct)
    except: return True, "Unknown", 0

@st.cache_data(ttl=600, show_spinner=False)
def get_higher_timeframe_trend(symbol, current_mode):
    try:
        if current_mode == "Intraday":
            df5 = yf.Ticker(symbol).history(period="5d", interval="5m")
            if df5.empty or len(df5) < 30: return True, "1H data unavailable — skipping confirmation"
            df1h = df5['Close'].resample('1h').last().dropna()
            if len(df1h) < 10: return True, "Insufficient 1H bars"
            hourly_bull = df1h.ewm(span=5).mean().iloc[-1] > df1h.ewm(span=10).mean().iloc[-1]
            dfd = yf.Ticker(symbol).history(period="1mo")
            daily_bull = dfd['Close'].iloc[-1] > dfd['Close'].rolling(10).mean().iloc[-1] if not dfd.empty and len(dfd) >= 10 else True
            return (hourly_bull and daily_bull), f"1H:{'🟢' if hourly_bull else '🔴'} Daily:{'🟢' if daily_bull else '🔴'}"
        else:
            dfw = yf.Ticker(symbol).history(period="1y", interval="1wk")
            if dfw.empty or len(dfw) < 10: return True, "Weekly data unavailable — skipping confirmation"
            weekly_bull = dfw['Close'].iloc[-1] > dfw['Close'].rolling(10).mean().iloc[-1]
            return weekly_bull, f"Weekly trend: {'🟢 Bullish' if weekly_bull else '🔴 Bearish'}"
    except: return True, "MTF check failed — proceeding without confirmation"

def compute_indicators(df, current_mode):
    df = df.copy()
    c = df['Close']
    df['SMA_20']  = c.rolling(20).mean()
    df['SMA_50']  = c.rolling(50).mean()
    df['SMA_200'] = c.rolling(200).mean()
    df['EMA_9']   = c.ewm(span=9).mean()
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    delta = c.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain / (loss + 1e-9)))
    e1 = c.ewm(span=12, adjust=False).mean()
    e2 = c.ewm(span=26, adjust=False).mean()
    df['MACD']   = e1 - e2
    df['MacdSig'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MacdH']   = df['MACD'] - df['MacdSig']
    df['BB_Mid'] = c.rolling(20).mean()
    df['BB_Std'] = c.rolling(20).std()
    df['BB_Up']  = df['BB_Mid'] + df['BB_Std'] * 2
    df['BB_Low'] = df['BB_Mid'] - df['BB_Std'] * 2
    df['BB_pct'] = (c - df['BB_Low']) / (df['BB_Up'] - df['BB_Low'] + 1e-9)
    df['ATR']    = (df['High'] - df['Low']).rolling(14).mean()
    df['Stoch_K']= ((c - df['Low'].rolling(14).min()) / (df['High'].rolling(14).max() - df['Low'].rolling(14).min() + 1e-9)) * 100
    df['Stoch_D']= df['Stoch_K'].rolling(3).mean()
    if current_mode == "Intraday":
        df['TP']  = (df['High'] + df['Low'] + c) / 3
        df['VP']  = df['TP'] * df['Volume']
        df['Date']= df.index.date
        df['CumV'] = df.groupby('Date')['Volume'].cumsum()
        df['CumVP']= df.groupby('Date')['VP'].cumsum()
        df['VWAP'] = df['CumVP'] / (df['CumV'] + 1e-9)
    return df.dropna()

def get_sr_levels(df, n_levels=5):
    try:
        df = df.tail(120).copy()
        highs, lows, closes = df['High'].values, df['Low'].values, df['Close'].values
        pivot = (highs[-1] + lows[-1] + closes[-1]) / 3
        r1 = 2 * pivot - lows[-1]
        s1 = 2 * pivot - highs[-1]
        r2 = pivot + (highs[-1] - lows[-1])
        s2 = pivot - (highs[-1] - lows[-1])
        r3 = highs[-1] + 2 * (pivot - lows[-1])
        s3 = lows[-1]  - 2 * (highs[-1] - pivot)
        swing_h, swing_l = [], []
        for i in range(5, len(df) - 5):
            if highs[i] == max(highs[i-5:i+6]): swing_h.append(highs[i])
            if lows[i] == min(lows[i-5:i+6]): swing_l.append(lows[i])
        current = float(closes[-1])
        resistances = sorted(set([r1, r2, r3] + swing_h[-4:]), reverse=False)
        supports    = sorted(set([s1, s2, s3] + swing_l[-4:]), reverse=True)
        res_above = [r for r in resistances if r > current][:3]
        sup_below = [s for s in supports    if s < current][:3]
        return {"pivot": round(pivot, 2), "resistances": [round(r, 2) for r in res_above], "supports": [round(s, 2) for s in sup_below], "current": round(current, 2)}
    except: return None

@st.cache_data(ttl=900, show_spinner=False)
def get_sector_performance(market, period="5d"):
    sector_map = SECTOR_MAP.get(market, {})
    results = []
    for sector, symbols in sector_map.items():
        changes = []
        for sym in symbols[:8]:
            try:
                df = yf.Ticker(sym).history(period=period)
                if df is not None and len(df) >= 2: changes.append((df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100)
            except: continue
        if changes:
            avg_chg = float(np.mean(changes))
            results.append({"sector": sector, "avg_change_pct": round(avg_chg, 2), "stocks_counted": len(changes), "strength": "🔥 Hot" if avg_chg > 2 else "🟢 Warm" if avg_chg > 0 else "🔴 Cold" if avg_chg > -2 else "🧊 Frozen"})
    return sorted(results, key=lambda x: x['avg_change_pct'], reverse=True)

@st.cache_data(ttl=1800, show_spinner=False)
def calc_correlation(symbol_a, symbol_b, period="6mo"):
    try:
        df_a = yf.Ticker(symbol_a).history(period=period)['Close'].pct_change().dropna()
        df_b = yf.Ticker(symbol_b).history(period=period)['Close'].pct_change().dropna()
        df_a.index = df_a.index.tz_localize(None) if df_a.index.tz else df_a.index
        df_b.index = df_b.index.tz_localize(None) if df_b.index.tz else df_b.index
        merged = pd.concat([df_a, df_b], axis=1, join='inner')
        merged.columns = [symbol_a, symbol_b]
        if len(merged) < 10: return None
        corr = merged[symbol_a].corr(merged[symbol_b])
        return {"correlation": round(float(corr), 3), "data_points": len(merged), "interpretation": ("Strong Positive — move together" if corr > 0.7 else "Moderate Positive" if corr > 0.3 else "Weak/No Correlation" if corr > -0.3 else "Moderate Negative" if corr > -0.7 else "Strong Negative — move opposite"), "series": merged}
    except: return None

@st.cache_resource
def get_model(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2y")
        if df is None or len(df) < 200: return None, None
        df = df.copy()
        c = df['Close']
        df['r1']  = c.pct_change(1)
        df['r5']  = c.pct_change(5)
        df['r10'] = c.pct_change(10)
        df['sma20']= c.rolling(20).mean()
        df['sma50']= c.rolling(50).mean()
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + gain / (loss + 1e-9)))
        e1 = c.ewm(span=12).mean(); e2 = c.ewm(span=26).mean()
        df['macd']   = (e1 - e2) / (c + 1e-9)
        df['bb_pos'] = (c - c.rolling(20).mean()) / (c.rolling(20).std() * 2 + 1e-9)
        df['atr']    = (df['High'] - df['Low']).rolling(14).mean() / (c + 1e-9)
        df['vol_r']  = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
        df['fut']    = c.shift(-5) / c - 1
        df['label']  = (df['fut'] > 0.02).astype(int)
        feats = ['r1','r5','r10','rsi','macd','bb_pos','atr','vol_r','sma20','sma50']
        df = df.dropna()
        if len(df) < 100: return None, None
        X = df[feats]; y = df['label']
        Xtr, _, ytr, _ = train_test_split(X, y, test_size=0.2, shuffle=False)
        sc = StandardScaler()
        Xtr_s = sc.fit_transform(Xtr)
        mdl = GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=4, random_state=42)
        mdl.fit(Xtr_s, ytr)
        return mdl, sc
    except: return None, None

def news_sentiment_summary(symbol):
    return 50, "NEUTRAL", 0

def get_fundamentals(symbol):
    return {"available": False, "fundamental_score": 50, "summary": "N/A"}

def advanced_engine(symbol, df, current_mode):
    if df is None or len(df) < 100: return "HOLD", 0, 0, "Insufficient Data", []
    try:
        df = compute_indicators(df, current_mode)
        if len(df) < 50: return "HOLD", 0, 0, "Data Error", []
        price  = float(df['Close'].iloc[-1])
        rsi    = float(df['RSI'].iloc[-1])
        sma20  = float(df['SMA_20'].iloc[-1])
        sma50  = float(df['SMA_50'].iloc[-1])
        macd   = float(df['MACD'].iloc[-1])
        macd_s = float(df['MacdSig'].iloc[-1])
        macd_h = float(df['MacdH'].iloc[-1])
        bb_pct = float(df['BB_pct'].iloc[-1])
        cur_v  = float(df['Volume'].iloc[-1])
        avg_v  = float(df['Vol_SMA'].iloc[-1])
        stoch_k= float(df['Stoch_K'].iloc[-1])
        stoch_d= float(df['Stoch_D'].iloc[-1])
        atr    = float(df['ATR'].iloc[-1])
        vwap   = float(df['VWAP'].iloc[-1]) if (current_mode == "Intraday" and 'VWAP' in df.columns) else None

        mdl, sc = get_model(symbol)
        ml_conf = 0
        if mdl and sc:
            try:
                r1  = df['Close'].pct_change(1).iloc[-1]
                r5  = df['Close'].pct_change(5).iloc[-1]  if len(df) >= 5  else 0
                r10 = df['Close'].pct_change(10).iloc[-1] if len(df) >= 10 else 0
                feat = np.array([[r1, r5, r10, rsi, macd/(price+1e-9), bb_pct - 0.5, atr/(price+1e-9), cur_v/(avg_v+1e-9), sma20, sma50]])
                prob = mdl.predict_proba(sc.transform(feat))[0][1]
                ml_conf = int(prob * 100)
            except: pass

        score = (ml_conf - 50) * 0.6 if ml_conf > 0 else 0
        signals = []

        if rsi < 30: score += 20; signals.append(("RSI", "BULLISH", f"{rsi:.1f} — Deeply Oversold"))
        elif rsi < 45: score += 10; signals.append(("RSI", "BULLISH", f"{rsi:.1f} — Oversold"))
        elif rsi > 75: score -= 18; signals.append(("RSI", "BEARISH", f"{rsi:.1f} — Overbought"))
        
        if price > sma20 > sma50: score += 15; signals.append(("Trend", "BULLISH", "Price > SMA20 > SMA50"))
        elif price > sma50: score += 8;  signals.append(("Trend", "BULLISH", "Price above SMA50"))
        elif price < sma50: score -= 10; signals.append(("Trend", "BEARISH", "Price below SMA50"))

        if macd > macd_s and macd_h > 0: score += 14; signals.append(("MACD", "BULLISH", "Bullish crossover"))
        elif macd < macd_s: score -= 10; signals.append(("MACD", "BEARISH", "Bearish crossover"))

        if bb_pct < 0.15: score += 12; signals.append(("Bollinger", "BULLISH", "Near lower band"))
        elif bb_pct > 0.90: score -= 8;  signals.append(("Bollinger", "BEARISH", "Near upper band"))

        if stoch_k < 25 and stoch_k > stoch_d: score += 10; signals.append(("Stochastic", "BULLISH", f"K:{stoch_k:.0f} oversold + rising"))
        elif stoch_k > 80 and stoch_k < stoch_d: score -= 8;  signals.append(("Stochastic", "BEARISH", f"K:{stoch_k:.0f} overbought"))

        vr = cur_v / (avg_v + 1e-9)
        if vr > 2.0: score += 14; signals.append(("Volume", "BULLISH", f"{vr:.1f}x surge"))
        elif vr > 1.4: score += 7;  signals.append(("Volume", "BULLISH", f"{vr:.1f}x above avg"))

        if vwap:
            if price > vwap * 1.005: score += 30; signals.append(("VWAP", "BULLISH", f"Above VWAP {vwap:.1f}"))
            elif price < vwap * 0.995: score -= 30; signals.append(("VWAP", "BEARISH", f"Below VWAP {vwap:.1f}"))

        if ml_conf > 0: signals.append(("ML Model", "BULLISH" if ml_conf > 60 else "NEUTRAL", f"{ml_conf}% confidence"))

        reasons = [s[2] for s in signals if s[1] == "BULLISH"][:3]
        status  = " | ".join(reasons) if reasons else "Watching"

        buy_threshold  = 78 if current_mode == "Swing" else 75
        sell_threshold = -18 if current_mode == "Swing" else -20

        if score >= buy_threshold: return "BUY",  price, int(score), status, signals
        elif score <= sell_threshold or (rsi > 72 and macd < macd_s): return "SELL", price, int(score), status, signals
        else: return "HOLD", price, int(score), status, signals
    except Exception as e: return "HOLD", 0, 0, str(e)[:40], []

def ai_explain(symbol, signal, score, signals, price, currency="₹"):
    bull = [s for s in signals if s[1] == "BULLISH"]
    bear = [s for s in signals if s[1] == "BEARISH"]
    if signal == "BUY": return f"**{symbol}** BUY signal — Score {score}/100. Bullish factors: {', '.join([f'{s[0]} ({s[2]})' for s in bull[:3]])}. Price: {currency}{price:.2f}"
    elif signal == "SELL": return f"**{symbol}** SELL/EXIT signal — Score {score}/100. Bearish factors: {', '.join([f'{s[0]} ({s[2]})' for s in bear[:3]])}. Profit book karo."
    else: return f"**{symbol}** HOLD zone — Score {score}/100. Koi strong setup nahi hai abhi. Wait karo."

def build_buy_telegram(market, mode_, symbol, price, target, sl, score, signals, currency):
    lines = [
        f"🟢 *AI AGENT — LONG ORDER (BUY)*",
        f"Market: {market} | Mode: {mode_}",
        f"Stock: *{symbol}*\n",
        f"💰 Buy Price: {currency}{price:.2f}",
        f"🎯 Target: {currency}{target:.2f} ({(target/price-1)*100:+.2f}%)",
        f"🛑 Stop Loss: {currency}{sl:.2f} ({(sl/price-1)*100:+.2f}%)",
        f"📊 AI Confidence Score: {score}/100\n",
        f"📌 *Why AI bought this:*",
    ]
    for s in [s for s in signals if s[1] == "BULLISH"][:5]: lines.append(f"  ✅ {s[0]}: {s[2]}")
    lines.append(f"\n🕒 {now.strftime('%d %b %Y, %H:%M:%S')} IST")
    return "\n".join(lines)

def build_sell_telegram(market, mode_, symbol, exit_price, entry_price, qty, pnl, reason, currency):
    pnl_pct = (exit_price/entry_price - 1) * 100
    lines = [
        f"🔴 *AI AGENT — LONG CLOSE (SELL)*",
        f"Market: {market} | Mode: {mode_}",
        f"Stock: *{symbol}*\n",
        f"📥 Entry was: {currency}{entry_price:.2f}",
        f"📤 Exit Price: {currency}{exit_price:.2f}",
        f"📦 Qty: {qty}\n",
        f"{'✅ PROFIT' if pnl >= 0 else '❌ LOSS'}: {currency}{pnl:+,.2f} ({pnl_pct:+.2f}%)",
        f"📌 Reason: {reason}\n",
        f"🕒 {now.strftime('%d %b %Y, %H:%M:%S')} IST",
    ]
    return "\n".join(lines)

def check_drawdown_protection(agent, mode_, streak_limit, pause_hours):
    if agent.get('paused_until'):
        try:
            paused_until_dt = datetime.fromisoformat(agent['paused_until'])
            if now < paused_until_dt: return True, agent.get('pause_reason', 'Drawdown protection active')
            else: agent['paused_until'] = None; agent['pause_reason'] = ""
        except: agent['paused_until'] = None
    sells = [t for t in agent['trade_log'] if t.get('action') in ('SELL', 'BUY') and t.get('mode') == mode_ and 'pnl' in t]
    if len(sells) < streak_limit: return False, ""
    recent = sells[-streak_limit:]
    if all(t['pnl'] <= 0 for t in recent):
        pause_until = now + timedelta(hours=pause_hours)
        agent['paused_until'] = pause_until.isoformat()
        agent['pause_reason'] = f"{streak_limit} consecutive losses in {mode_} — auto-paused for {pause_hours}h"
        return True, agent['pause_reason']
    return False, ""

def run_ai_agent_for_market(market, mode_, min_score_threshold, max_alloc, telegram_enabled, mtf_confirm_on=True, dd_on=True, dd_streak=4, dd_hours=12, compounding=False):
    agent_key = AGENT_KEYS[market]
    agent = st.session_state[agent_key]
    currency = AGENT_CURRENCY[market]
    universe = MARKET_UNIVERSE[market]
    sl_pct, tg_pct = RISK_PARAMS[mode_]
    can_trade_now = market_can_trade(market, mode_)
    is_bull, _, _ = get_market_regime(MARKET_BENCH[market], mode_)

    is_paused = False
    pause_reason = ""
    if dd_on:
        is_paused, pause_reason = check_drawdown_protection(agent, mode_, dd_streak, dd_hours)
        if is_paused and not agent.get('_pause_alerted_' + mode_):
            if telegram_enabled: send_telegram(f"⏸️ *AI AGENT PAUSED*\nMarket: {market} | Mode: {mode_}\nReason: {pause_reason}")
            agent['_pause_alerted_' + mode_] = True
    if not is_paused: agent['_pause_alerted_' + mode_] = False

    sizing_base = agent['balance'] if compounding else agent.get('starting_capital', 100000.0)
    results, buy_count, sell_count = [], 0, 0

    for stk in universe:
        df_s = get_data(stk, mode_)
        sig, price, score, status, signals = advanced_engine(stk, df_s, mode_)
        results.append((stk, sig, score, price, status, signals))
        st.session_state.scan_log.append({'time': now.strftime('%H:%M:%S'), 'market': market, 'mode': mode_, 'stock': stk, 'signal': sig, 'score': score, 'price': price})

        # ---------- AUTO BUY (LONG POSITION) ----------
        if sig == "BUY" and price > 0 and can_trade_now and score >= min_score_threshold and not is_paused:
            pos_key_long = f"{stk}__{mode_}__LONG"
            qty_long = agent['positions'].get(pos_key_long, 0)
            if qty_long == 0:
                mtf_aligned, mtf_detail = (True, "MTF off")
                if mtf_confirm_on: mtf_aligned, mtf_detail = get_higher_timeframe_trend(stk, mode_)
                if mtf_aligned:
                    alloc_pct = (max_alloc/100) if (score >= 88 and is_bull) else (max_alloc*0.66/100) if is_bull else (max_alloc*0.33/100)
                    invest = min(sizing_base, agent['balance']) * alloc_pct
                    q = int(invest / price) if price > 0 else 0
                    if q > 0 and invest <= agent['balance']:
                        agent['positions'][pos_key_long] = q
                        agent['balance'] -= q * price
                        agent['entry_price'][pos_key_long] = price
                        agent['highest_price'][pos_key_long] = price
                        agent['entry_mode'][pos_key_long] = mode_
                        agent['position_direction'][pos_key_long] = "LONG"
                        target, stop = price * (1 + tg_pct), price * (1 - sl_pct)
                        agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'BUY', 'price': price, 'qty': q, 'score': score, 'mode': mode_, 'market': market, 'mtf_confirm': mtf_detail, 'direction': 'LONG'})
                        buy_count += 1
                        if telegram_enabled:
                            msg = build_buy_telegram(market, mode_, stk, price, target, stop, score, signals, currency)
                            if mtf_confirm_on: msg += f"\n\n🎯 *Multi-Timeframe Check:* {mtf_detail}"
                            send_telegram(msg)

        # ---------- AUTO SELL (SHORT POSITION OPEN) ----------
        if sig == "SELL" and price > 0 and can_trade_now and score <= -18 and not is_paused:
            pos_key_short = f"{stk}__{mode_}__SHORT"
            qty_short = agent['positions'].get(pos_key_short, 0)
            if qty_short == 0:
                mtf_aligned, mtf_detail = (True, "MTF off")
                if mtf_confirm_on: mtf_aligned, mtf_detail = get_higher_timeframe_trend(stk, mode_)
                if mtf_aligned: 
                    alloc_pct = (max_alloc/100) if (score <= -88) else (max_alloc*0.66/100)
                    invest = min(sizing_base, agent['balance']) * alloc_pct
                    q = int(invest / price) if price > 0 else 0
                    if q > 0 and invest <= agent['balance']:
                        agent['positions'][pos_key_short] = -q 
                        agent['balance'] -= q * price 
                        agent['entry_price'][pos_key_short] = price
                        agent['lowest_price'][pos_key_short] = price
                        agent['entry_mode'][pos_key_short] = mode_
                        agent['position_direction'][pos_key_short] = "SHORT"
                        target, stop = price * (1 - tg_pct), price * (1 + sl_pct)
                        agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'SHORT', 'price': price, 'qty': q, 'score': score, 'mode': mode_, 'market': market, 'mtf_confirm': mtf_detail, 'direction': 'SHORT'})
                        sell_count += 1
                        if telegram_enabled:
                            msg = f"🔴 *AI AGENT — SHORT ORDER (SELL TO OPEN)*\nMarket: {market} | Mode: {mode_}\nStock: *{stk}*\n\nShort Entry Price: {currency}{price:.2f}\nTarget: {currency}{target:.2f} ({(target/price-1)*100:+.2f}%)\nStop Loss: {currency}{stop:.2f} ({(stop/price-1)*100:+.2f}%)\n📊 AI Confidence Score: {abs(score)}/100\n\n📌 *Why AI opened SHORT:*"
                            for s in [s for s in signals if s[1] == "BEARISH"][:5]: msg += f"\n  ❌ {s[0]}: {s[2]}"
                            msg += f"\n\n🕒 {now.strftime('%d %b %Y, %H:%M:%S')} IST"
                            if mtf_confirm_on: msg += f"\n\n🎯 *Multi-Timeframe Check:* {mtf_detail}"
                            send_telegram(msg)

    # ---------- TRAILING SL / TARGET / EOD CHECK ----------
    for pos_key, q in list(agent['positions'].items()):
        if q == 0: continue
        if not (f"__{mode_}__LONG" in pos_key or f"__{mode_}__SHORT" in pos_key): continue
        stk = pos_key.split("__")[0]
        direction = pos_key.split("__")[-1]

        df2 = get_data(stk, mode_)
        if df2 is None or len(df2) == 0: continue
        cp = float(df2['Close'].iloc[-1])
        entry = agent['entry_price'].get(pos_key, cp)
        exit_reason = None
        pnl_t = 0

        if direction == "LONG":
            if pos_key not in agent['highest_price']: agent['highest_price'][pos_key] = entry
            if cp > agent['highest_price'][pos_key]: agent['highest_price'][pos_key] = cp
            trail_sl = agent['highest_price'][pos_key] * (1 - sl_pct)
            target_p = entry * (1 + tg_pct)

            if mode_ == "Intraday" and market in ("NSE",) and now.hour == 15 and now.minute >= 20: exit_reason = "End-of-day square-off (Intraday auto-exit)"
            elif cp <= trail_sl: exit_reason = f"Trailing Stop Loss hit at {currency}{trail_sl:.2f}"
            elif cp >= target_p: exit_reason = f"Target achieved at {currency}{target_p:.2f}"

            if exit_reason:
                pnl_t = (cp - entry) * q 
                agent['balance'] += q * cp
                agent['positions'][pos_key] = 0
                agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'SELL', 'price': cp, 'qty': q, 'pnl': round(pnl_t, 2), 'mode': mode_, 'market': market, 'direction': direction})
                sell_count += 1
                for key in ['entry_price', 'highest_price', 'lowest_price', 'entry_mode', 'position_direction']: agent[key].pop(pos_key, None)
                if telegram_enabled: send_telegram(build_sell_telegram(market, mode_, stk, cp, entry, q, pnl_t, exit_reason, currency))

        elif direction == "SHORT":
            if pos_key not in agent['lowest_price']: agent['lowest_price'][pos_key] = entry
            if cp < agent['lowest_price'][pos_key]: agent['lowest_price'][pos_key] = cp
            trail_sl = agent['lowest_price'][pos_key] * (1 + sl_pct)
            target_p = entry * (1 - tg_pct)

            if mode_ == "Intraday" and market in ("NSE",) and now.hour == 15 and now.minute >= 20: exit_reason = "End-of-day square-off (Intraday auto-exit)"
            elif cp >= trail_sl: exit_reason = f"Trailing Stop Loss hit at {currency}{trail_sl:.2f}"
            elif cp <= target_p: exit_reason = f"Target achieved at {currency}{target_p:.2f}"

            if exit_reason:
                pnl_t = (entry - cp) * abs(q) 
                agent['balance'] += abs(q) * cp
                agent['positions'][pos_key] = 0
                agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'BUY', 'price': cp, 'qty': abs(q), 'pnl': round(pnl_t, 2), 'mode': mode_, 'market': market, 'direction': direction})
                sell_count += 1
                for key in ['entry_price', 'highest_price', 'lowest_price', 'entry_mode', 'position_direction']: agent[key].pop(pos_key, None)
                if telegram_enabled:
                    msg = f"🟢 *AI AGENT — SHORT CLOSE (BUY TO COVER)*\nMarket: {market} | Mode: {mode_}\nStock: *{stk}*\n\nShort Covered at: {currency}{cp:.2f}\nShort Entry was: {currency}{entry:.2f}\nQty: {abs(q)}\n\n{'✅ PROFIT' if pnl_t >= 0 else '❌ LOSS'}: {currency}{pnl_t:+,.2f} ({(pnl_t/entry/abs(q))*100:+.2f}%)\n📌 Reason: {exit_reason}\n\n🕒 {now.strftime('%d %b %Y, %H:%M:%S')} IST"
                    send_telegram(msg)

    if len(st.session_state.scan_log) > 500: st.session_state.scan_log = st.session_state.scan_log[-500:]
    return sorted(results, key=lambda x: x[2], reverse=True), buy_count, sell_count

def play_alert_sound(kind="buy"):
    if kind == "buy":
        freq_html = """<script>try{const ctx=new (window.AudioContext||window.webkitAudioContext)();function beep(f,s,d){const osc=ctx.createOscillator();const gain=ctx.createGain();osc.connect(gain);gain.connect(ctx.destination);osc.frequency.value=f;osc.type='sine';gain.gain.setValueAtTime(0.18,ctx.currentTime+s);gain.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+s+d);osc.start(ctx.currentTime+s);osc.stop(ctx.currentTime+s+d);}beep(880,0,0.15);beep(1100,0.18,0.18);}catch(e){}</script>"""
    else:
        freq_html = """<script>try{const ctx=new (window.AudioContext||window.webkitAudioContext)();function beep(f,s,d){const osc=ctx.createOscillator();const gain=ctx.createGain();osc.connect(gain);gain.connect(ctx.destination);osc.frequency.value=f;osc.type='sine';gain.gain.setValueAtTime(0.18,ctx.currentTime+s);gain.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+s+d);osc.start(ctx.currentTime+s);osc.stop(ctx.currentTime+s+d);}beep(420,0,0.30);}catch(e){}</script>"""
    st.components.v1.html(freq_html, height=0, width=0)

if AUTOREFRESH_AVAILABLE and st.session_state.agent_running: st_autorefresh(interval=5*60*1000, key="agent_autorefresh")
st.markdown("""<div class="main-header"><h1>⚡ QUANTEDGE AI v8.0</h1><p>AUTONOMOUS AI AGENT + HEDGED POSITIONS — NSE · CRYPTO · US</p></div>""", unsafe_allow_html=True)

do_scan = True if st.session_state.agent_running else False
manual_scan = st.button("🔍 Scan Now (manual)", type="secondary") if not st.session_state.agent_running else False

agent_results = {} 
total_buys_this_scan, total_sells_this_scan = 0, 0

if do_scan or manual_scan:
    with st.spinner("🤖 AI Agent scanning markets..."):
        for mkt in ACTIVE_MARKETS:
            agent_results[mkt] = {}
            for md in ACTIVE_MODES:
                results_list, n_buys, n_sells = run_ai_agent_for_market(
                    mkt, md, min_score, max_alloc_pct, telegram_on,
                    mtf_confirm_on=mtf_confirm, dd_on=dd_protection_on,
                    dd_streak=dd_streak_limit, dd_hours=dd_pause_hours, compounding=compounding_on
                )
                agent_results[mkt][md] = results_list
                total_buys_this_scan += n_buys
                total_sells_this_scan += n_sells
    st.session_state.last_scan_time = now.strftime('%H:%M:%S')

    if sound_alert_on and total_buys_this_scan > 0: play_alert_sound("buy")
    elif sound_alert_on and total_sells_this_scan > 0: play_alert_sound("sell")

def agent_summary(market):
    agent = st.session_state[AGENT_KEYS[market]]
    unrealized_pnl = 0
    open_count = 0
    for pos_key, qty in agent['positions'].items():
        if qty == 0: continue
        open_count += 1
        entry = agent['entry_price'].get(pos_key, 0)
        direction = agent['position_direction'].get(pos_key, "LONG")
        try:
            stk = pos_key.split("__")[0]
            df_tmp = get_data(stk, "Intraday")
            if df_tmp is not None and len(df_tmp) > 0:
                cp = float(df_tmp['Close'].iloc[-1])
                if direction == "LONG": unrealized_pnl += (cp - entry) * qty
                else: unrealized_pnl += (entry - cp) * abs(qty)
        except: pass
    val = agent['balance'] + unrealized_pnl
    return val, (val - 100000.0), open_count, agent['balance']

def agent_today_pnl(market):
    agent = st.session_state[AGENT_KEYS[market]]
    today_trades = [t for t in agent['trade_log'] if t.get('full_time') and t['full_time'].date() == now.date() and t.get('action') in ('SELL', 'BUY')]
    today_pnls = [t.get('pnl', 0) for t in today_trades if 'pnl' in t]
    return sum(today_pnls), len(today_pnls)

nse_val, nse_pnl, nse_pos, nse_cash = agent_summary("NSE")
crypto_val, crypto_pnl, crypto_pos, crypto_cash = agent_summary("Crypto")
us_val, us_pnl, us_pos, us_cash = agent_summary("US")

nse_today_pnl, nse_today_trades = agent_today_pnl("NSE")
crypto_today_pnl, crypto_today_trades = agent_today_pnl("Crypto")
us_today_pnl, us_today_trades = agent_today_pnl("US")

USD_TO_INR = 83.5
combined_val_inr = nse_val + (crypto_val * USD_TO_INR) + (us_val * USD_TO_INR)
combined_pnl_inr = nse_pnl + (crypto_pnl * USD_TO_INR) + (us_pnl * USD_TO_INR)
combined_today_inr = nse_today_pnl + (crypto_today_pnl * USD_TO_INR) + (us_today_pnl * USD_TO_INR)
combined_today_trades = nse_today_trades + crypto_today_trades + us_today_trades
total_open_positions = nse_pos + crypto_pos + us_pos

overall_color = '#00ff88' if combined_pnl_inr >= 0 else '#ff4444'
today_color = '#00ff88' if combined_today_inr >= 0 else '#ff4444'

st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d1b2a,#15233d,#0d1b2a); border:1px solid #00d4ff33; border-radius:14px; padding:20px 24px; margin-bottom:18px; box-shadow:0 0 35px #00d4ff12;">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
    <div>
      <div style="color:#7a8fa6; font-size:0.78rem; letter-spacing:1.5px; text-transform:uppercase;">Combined Portfolio (₹ equivalent)</div>
      <div style="color:#fff; font-size:2.1rem; font-weight:800; margin-top:2px;">₹{combined_val_inr:,.0f}</div>
      <div style="color:{overall_color}; font-size:1rem; font-weight:700; margin-top:2px;">{'▲' if combined_pnl_inr>=0 else '▼'} ₹{combined_pnl_inr:+,.0f} ({combined_pnl_inr/3000:+.2f}%)</div>
    </div>
    <div style="text-align:right;">
      <div style="color:#7a8fa6; font-size:0.78rem; letter-spacing:1.5px; text-transform:uppercase;">Today's Realized P&L</div>
      <div style="color:{today_color}; font-size:1.7rem; font-weight:800; margin-top:2px;">₹{combined_today_inr:+,.0f}</div>
      <div style="color:#7a8fa6; font-size:0.78rem; margin-top:2px;">{combined_today_trades} trades closed today</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

c1,c2,c3 = st.columns(3)
c1.metric("Total Open Positions", total_open_positions)
c2.metric("Alerts Set", len(st.session_state.price_alerts))
c3.metric("AI Status", "🟢 LIVE" if st.session_state.agent_running else "⏸️ PAUSED")
st.divider()

tab1, tab10, tab16 = st.tabs(["🤖 AI Agent Radar", "💼 Portfolio (3 Agents)", "🎯 Option Strategy Builder"])

with tab1:
    st.markdown("### 🤖 Live Signals & Executions")
    if not agent_results: st.info("Scan not complete yet. Wait for 5 minutes or click manual scan.")
    else: st.success("Systems monitoring correctly.")

with tab10:
    st.markdown("### 💼 Live Portfolio — Hedged View")
    for mkt in ACTIVE_MARKETS:
        agent = st.session_state[AGENT_KEYS[mkt]]
        cur, icon = AGENT_CURRENCY[mkt], {"NSE":"🇮🇳","Crypto":"🪙","US":"🇺🇸"}[mkt]
        st.markdown(f"## {icon} {mkt} Agent")
        
        active = {k:q for k,q in agent['positions'].items() if q != 0}
        if active:
            rows_p = []
            for pos_key, q in active.items():
                stk = pos_key.split("__")[0]
                pmode = agent['entry_mode'].get(pos_key, '-')
                direction = agent['position_direction'].get(pos_key, 'LONG')
                entry = agent['entry_price'].get(pos_key, 0)
                if direction == 'LONG': val = q * entry
                else: val = abs(q) * entry
                rows_p.append({"Stock":stk, "Mode":pmode, "Type":direction, "Qty":abs(q), f"Entry({cur})":f"{entry:.2f}", f"Value({cur})":f"{val:,.0f}"})
            st.dataframe(pd.DataFrame(rows_p), use_container_width=True, hide_index=True)
        else: st.caption("Koi open position nahi hai abhi.")
        st.divider()

with tab16:
    st.markdown("### 🎯 Option Strategy Builder")
    st.info("Straddle, Strangle, Spreads ke payoff diagrams banao aur dekho profit/loss kahan hota hai")
    sb1, sb2, sb3 = st.columns(3)
    with sb1: sb_strategy = st.selectbox("Strategy:", ["Long Straddle", "Short Straddle", "Long Strangle", "Short Strangle", "Bull Call Spread", "Bear Put Spread"])
    with sb2: sb_spot = st.number_input("Current Spot Price (₹/$):", value=1000.0, step=10.0, min_value=1.0)
    with sb3: sb_lot = st.number_input("Lot Size:", value=1, step=1, min_value=1)
    
    legs = []
    if "Straddle" in sb_strategy:
        strike = round(sb_spot)
        action = "buy" if "Long" in sb_strategy else "sell"
        legs = [{"type": "call", "action": action, "strike": strike, "premium": 25.0}, {"type": "put", "action": action, "strike": strike, "premium": 25.0}]
        st.markdown(f"**Straddle:** Strike at {strike}, Call Premium = 25, Put Premium = 25")
    
    if st.button("📊 Calculate Payoff", type="primary"):
        price_range = np.linspace(sb_spot * 0.80, sb_spot * 1.20, 200)
        net_payoff = np.zeros_like(price_range)
        for leg in legs:
            strike, premium, sign = leg["strike"], leg["premium"], 1 if leg["action"] == "buy" else -1
            intrinsic = np.maximum(price_range - strike, 0) if leg["type"] == "call" else np.maximum(strike - price_range, 0)
            net_payoff += (intrinsic - premium) * sign * sb_lot
        
        colors_payoff = ['#00ff88' if p >= 0 else '#ff4444' for p in net_payoff]
        fig_payoff = go.Figure()
        fig_payoff.add_trace(go.Scatter(x=price_range, y=net_payoff, mode='lines', line=dict(color='#00d4ff', width=2.5), fill='tozeroy', fillcolor='rgba(0,212,255,0.08)', name='Net Payoff'))
        fig_payoff.add_vline(x=sb_spot, line_color='#ffaa00', line_dash='dash')
        fig_payoff.update_layout(template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520', height=400, title=f"{sb_strategy} — Payoff at Expiry")
        st.plotly_chart(fig_payoff, use_container_width=True)

st.divider()
st.caption("⚡ QuantEdge AI v8.0 — Autonomous Agent + Hedged Long/Short Positions | NSE India · Crypto · US Stocks | Paper Trading Only")
            
