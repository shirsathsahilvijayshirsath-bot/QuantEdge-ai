# ================= QUANTEDGE AI v5.0 - AUTONOMOUS AI AGENT =================
# Features: Fully Autonomous AI Trading Agent (NSE + Crypto + US)
#           Auto BUY/SELL decisions, Telegram alerts with full reasoning,
#           Separate Intraday + Swing logic, Weekly Win-Rate Reports,
#           Fundamental + Technical + Sentiment fusion for Swing trades
# ==============================================================================

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
    page_title="QuantEdge AI v5.0 — Autonomous Agent",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ================= CSS =================
st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; color: #e0e6f0; }
    div[data-testid="stSidebarContent"] {
        background-color: #0d1520;
        border-right: 1px solid #00d4ff15;
    }
    .main-header {
        background: linear-gradient(135deg, #0d1b2a 0%, #1a2744 50%, #0d1b2a 100%);
        border: 1px solid #00d4ff33;
        border-radius: 12px;
        padding: 18px 26px;
        margin-bottom: 18px;
        box-shadow: 0 0 30px #00d4ff15;
    }
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
        st.markdown('<div class="main-header"><h1>⚡ QUANTEDGE AI v3.0</h1><p>SECURE TRADING TERMINAL</p></div>', unsafe_allow_html=True)
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
    # Nifty 50
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","HINDUNILVR.NS",
    "HDFC.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS","ITC.NS","LT.NS",
    "AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","TITAN.NS","ULTRACEMCO.NS",
    "WIPRO.NS","SUNPHARMA.NS","TECHM.NS","NESTLEIND.NS","BAJFINANCE.NS",
    "POWERGRID.NS","NTPC.NS","ONGC.NS","JSWSTEEL.NS","TATASTEEL.NS",
    "HCLTECH.NS","M&M.NS","BAJAJFINSV.NS",
    # Nifty Next 50
    "ADANIENT.NS","ADANIPORTS.NS","ADANIGREEN.NS","DMART.NS","SIEMENS.NS",
    "PIDILITIND.NS","HAVELLS.NS","MARICO.NS","DABUR.NS","GODREJCP.NS",
    "MUTHOOTFIN.NS","CHOLAFIN.NS","RECLTD.NS","PFC.NS","IRCTC.NS",
    "INDHOTEL.NS","TRENT.NS","VEDL.NS","HINDALCO.NS","COALINDIA.NS",
    "GRASIM.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS","EICHERMOT.NS","TVSMOTOR.NS",
    "TATAMOTORS.NS","MOTHERSON.NS","BOSCHLTD.NS","MRF.NS","APOLLOHOSP.NS",
    # Midcap Stars
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
    "IT":      ["INFY.NS","TCS.NS","HCLTECH.NS","TATAELXSI.NS","PERSISTENT.NS","LTIM.NS"],
    "Banking": ["SBIN.NS","KOTAKBANK.NS","AXISBANK.NS"],
    "Auto":    ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","EICHERMOT.NS","TVSMOTOR.NS"],
    "Pharma":  ["TORNTPHARM.NS","ZYDUSLIFE.NS"],
    "Infra":   ["DLF.NS","GODREJPROP.NS","NTPC.NS","HAL.NS","ABB.NS"],
    "FMCG":    ["BRITANNIA.NS","HINDUNILVR.NS","VBL.NS"],
    "Others":  ["ZOMATO.NS","TITAN.NS","SUZLON.NS","HINDALCO.NS","TRENT.NS","SRF.NS","NETWEB.NS","RELIANCE.NS"],
}

# ================= SESSION STATE — 3 INDEPENDENT AI AGENTS =================
# Each market (NSE / Crypto / US) gets its own portfolio, positions, and trade history
# Each trade is tagged with mode (Intraday/Swing) for separate win-rate tracking

def make_agent_state():
    return {
        "balance": 100000.0,
        "positions": {},        # {symbol: qty}
        "entry_price": {},
        "highest_price": {},
        "entry_mode": {},        # {symbol: "Intraday"/"Swing"} - tracks which mode each position was opened in
        "trade_log": [],         # full history: BUY/SELL with mode tag
    }

DEFAULTS = {
    "agent_nse":    make_agent_state(),
    "agent_crypto": make_agent_state(),
    "agent_us":     make_agent_state(),
    "price_alerts": [],
    "triggered_alerts": [],
    "agent_running": True,           # master on/off switch for AI agent
    "last_scan_time": None,
    "weekly_reports": [],            # stores generated weekly win-rate snapshots
    "scan_log": [],                  # rolling log of AI's analysis decisions (for "show reasoning" panel)
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
    st.markdown("## ⚡ QuantEdge AI v5.0")
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
    min_score   = st.slider("Min Signal Score (auto-trade)", 50, 95, 75)
    max_alloc_pct = st.slider("Max % capital per trade", 5, 30, 15)

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
    """Intraday only during market hours for NSE/US. Crypto trades 24/7."""
    if mode_ != "Intraday":
        return True
    if market == "Crypto":
        return True
    if market == "NSE":
        return not (now.hour > 14 or (now.hour == 14 and now.minute >= 30))
    if market == "US":
        # US market hours roughly 19:30-02:00 IST (varies with DST) — keep permissive
        return True
    return True

# ================= HELPERS =================
def send_telegram(msg):
    if not telegram_on:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg}, timeout=8)
    except:
        pass

# ================= DATA =================
@st.cache_data(ttl=90, show_spinner=False)
def get_data(symbol, current_mode):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="5d", interval="5m") if current_mode == "Intraday" else t.history(period="1y")
        return df.dropna() if not df.empty else None
    except:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def get_market_regime(bench, current_mode):
    try:
        df = yf.Ticker(bench).history(period="6mo" if current_mode == "Swing" else "5d",
                                       interval="1d"  if current_mode == "Swing" else "5m")
        if df.empty:
            return True, "Unknown", 50
        df['SMA50'] = df['Close'].rolling(50).mean()
        last = df['Close'].iloc[-1]
        sma  = df['SMA50'].iloc[-1]
        bull = last > sma
        pct  = (last - sma) / sma * 100
        return bull, f"{'Bullish' if bull else 'Bearish'} ({pct:+.1f}% vs SMA50)", abs(pct)
    except:
        return True, "Unknown", 0

# ================= INDICATORS =================
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
    df['Stoch_K']= ((c - df['Low'].rolling(14).min()) /
                    (df['High'].rolling(14).max() - df['Low'].rolling(14).min() + 1e-9)) * 100
    df['Stoch_D']= df['Stoch_K'].rolling(3).mean()

    if current_mode == "Intraday":
        df['TP']  = (df['High'] + df['Low'] + c) / 3
        df['VP']  = df['TP'] * df['Volume']
        df['Date']= df.index.date
        df['CumV'] = df.groupby('Date')['Volume'].cumsum()
        df['CumVP']= df.groupby('Date')['VP'].cumsum()
        df['VWAP'] = df['CumVP'] / (df['CumV'] + 1e-9)
    return df.dropna()

# ================= SUPPORT & RESISTANCE =================
def get_sr_levels(df, n_levels=5):
    """Pivot-based S&R + recent swing highs/lows"""
    try:
        df = df.tail(120).copy()
        highs = df['High'].values
        lows  = df['Low'].values
        closes= df['Close'].values

        # Classic Pivot
        pivot = (highs[-1] + lows[-1] + closes[-1]) / 3
        r1 = 2 * pivot - lows[-1]
        s1 = 2 * pivot - highs[-1]
        r2 = pivot + (highs[-1] - lows[-1])
        s2 = pivot - (highs[-1] - lows[-1])
        r3 = highs[-1] + 2 * (pivot - lows[-1])
        s3 = lows[-1]  - 2 * (highs[-1] - pivot)

        # Swing highs/lows (local extrema)
        swing_h, swing_l = [], []
        for i in range(5, len(df) - 5):
            if highs[i] == max(highs[i-5:i+6]):
                swing_h.append(highs[i])
            if lows[i] == min(lows[i-5:i+6]):
                swing_l.append(lows[i])

        current = float(closes[-1])

        resistances = sorted(set([r1, r2, r3] + swing_h[-4:]), reverse=False)
        supports    = sorted(set([s1, s2, s3] + swing_l[-4:]), reverse=True)

        res_above = [r for r in resistances if r > current][:3]
        sup_below = [s for s in supports    if s < current][:3]

        return {
            "pivot": round(pivot, 2),
            "resistances": [round(r, 2) for r in res_above],
            "supports":    [round(s, 2) for s in sup_below],
            "current":     round(current, 2),
        }
    except:
        return None

# ================= ML MODEL =================
@st.cache_resource
def get_model(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2y")
        if df is None or len(df) < 200:
            return None, None
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
        if len(df) < 100:
            return None, None
        X = df[feats]; y = df['label']
        Xtr, _, ytr, _ = train_test_split(X, y, test_size=0.2, shuffle=False)
        sc = StandardScaler()
        Xtr_s = sc.fit_transform(Xtr)
        mdl = GradientBoostingClassifier(n_estimators=150, learning_rate=0.05,
                                         max_depth=4, random_state=42)
        mdl.fit(Xtr_s, ytr)
        return mdl, sc
    except:
        return None, None

# ================= SIGNAL ENGINE =================
def advanced_engine(symbol, df, current_mode):
    if df is None or len(df) < 100:
        return "HOLD", 0, 0, "Insufficient Data", []
    try:
        df = compute_indicators(df, current_mode)
        if len(df) < 50:
            return "HOLD", 0, 0, "Data Error", []

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
                feat = np.array([[r1, r5, r10, rsi, macd/(price+1e-9),
                                  bb_pct - 0.5, atr/(price+1e-9), cur_v/(avg_v+1e-9),
                                  sma20, sma50]])
                prob = mdl.predict_proba(sc.transform(feat))[0][1]
                ml_conf = int(prob * 100)
            except:
                pass

        score = (ml_conf - 50) * 0.6 if ml_conf > 0 else 0
        signals = []

        # RSI
        if rsi < 30:
            score += 20; signals.append(("RSI", "BULLISH", f"{rsi:.1f} — Deeply Oversold"))
        elif rsi < 45:
            score += 10; signals.append(("RSI", "BULLISH", f"{rsi:.1f} — Oversold"))
        elif rsi > 75:
            score -= 18; signals.append(("RSI", "BEARISH", f"{rsi:.1f} — Overbought"))
        else:
            signals.append(("RSI", "NEUTRAL", f"{rsi:.1f}"))

        # Trend
        if price > sma20 > sma50:
            score += 15; signals.append(("Trend", "BULLISH", "Price > SMA20 > SMA50"))
        elif price > sma50:
            score += 8;  signals.append(("Trend", "BULLISH", "Price above SMA50"))
        elif price < sma50:
            score -= 10; signals.append(("Trend", "BEARISH", "Price below SMA50"))

        # MACD
        if macd > macd_s and macd_h > 0:
            score += 14; signals.append(("MACD", "BULLISH", "Bullish crossover"))
        elif macd < macd_s:
            score -= 10; signals.append(("MACD", "BEARISH", "Bearish crossover"))
        else:
            signals.append(("MACD", "NEUTRAL", "Converging"))

        # Bollinger
        if bb_pct < 0.15:
            score += 12; signals.append(("Bollinger", "BULLISH", "Near lower band — bounce zone"))
        elif bb_pct > 0.90:
            score -= 8;  signals.append(("Bollinger", "BEARISH", "Near upper band — caution"))
        else:
            signals.append(("Bollinger", "NEUTRAL", f"{bb_pct:.2f}"))

        # Stochastic
        if stoch_k < 25 and stoch_k > stoch_d:
            score += 10; signals.append(("Stochastic", "BULLISH", f"K:{stoch_k:.0f} oversold + rising"))
        elif stoch_k > 80 and stoch_k < stoch_d:
            score -= 8;  signals.append(("Stochastic", "BEARISH", f"K:{stoch_k:.0f} overbought"))
        else:
            signals.append(("Stochastic", "NEUTRAL", f"K:{stoch_k:.0f} D:{stoch_d:.0f}"))

        # Volume
        vr = cur_v / (avg_v + 1e-9)
        if vr > 2.0:
            score += 14; signals.append(("Volume", "BULLISH", f"{vr:.1f}x surge"))
        elif vr > 1.4:
            score += 7;  signals.append(("Volume", "BULLISH", f"{vr:.1f}x above avg"))
        else:
            signals.append(("Volume", "NEUTRAL", f"{vr:.1f}x avg"))

        # VWAP (intraday)
        if vwap:
            if price > vwap * 1.005:
                score += 30; signals.append(("VWAP", "BULLISH", f"Above VWAP {vwap:.1f}"))
            elif price < vwap * 0.995:
                score -= 30; signals.append(("VWAP", "BEARISH", f"Below VWAP {vwap:.1f}"))
            else:
                signals.append(("VWAP", "NEUTRAL", f"Near VWAP {vwap:.1f}"))

        if ml_conf > 0:
            signals.append(("ML Model", "BULLISH" if ml_conf > 60 else "NEUTRAL",
                            f"{ml_conf}% confidence"))

        # ===== SWING ONLY: fuse Fundamentals + News Sentiment =====
        fund_data = None
        sent_score = None
        if current_mode == "Swing":
            fund_data = get_fundamentals(symbol)
            f_score = fund_data.get('fundamental_score', 50)
            if f_score >= 65:
                score += 15; signals.append(("Fundamentals", "BULLISH", fund_data.get('summary','Strong fundamentals')[:60]))
            elif f_score <= 35:
                score -= 15; signals.append(("Fundamentals", "BEARISH", fund_data.get('summary','Weak fundamentals')[:60]))
            else:
                signals.append(("Fundamentals", "NEUTRAL", fund_data.get('summary','Mixed fundamentals')[:60]))

            sent_avg, sent_label, n_articles = news_sentiment_summary(symbol)
            sent_score = sent_avg
            if n_articles > 0:
                if sent_label == "POSITIVE":
                    score += 10; signals.append(("News Sentiment", "BULLISH", f"{sent_label} ({n_articles} articles)"))
                elif sent_label == "NEGATIVE":
                    score -= 10; signals.append(("News Sentiment", "BEARISH", f"{sent_label} ({n_articles} articles)"))
                else:
                    signals.append(("News Sentiment", "NEUTRAL", f"{sent_label} ({n_articles} articles)"))

        reasons = [s[2] for s in signals if s[1] == "BULLISH"][:3]
        status  = " | ".join(reasons) if reasons else "Watching"

        # Swing requires a slightly higher bar since more factors are fused in
        buy_threshold  = 78 if current_mode == "Swing" else 75
        sell_threshold = -18 if current_mode == "Swing" else -20

        if score >= buy_threshold:
            return "BUY",  price, int(score), status, signals
        elif score <= sell_threshold or (rsi > 72 and macd < macd_s):
            return "SELL", price, int(score), status, signals
        else:
            return "HOLD", price, int(score), status, signals
    except Exception as e:
        return "HOLD", 0, 0, str(e)[:40], []

# ================= AI EXPLANATION =================
def ai_explain(symbol, signal, score, signals, price, currency="₹"):
    bull = [s for s in signals if s[1] == "BULLISH"]
    bear = [s for s in signals if s[1] == "BEARISH"]
    if signal == "BUY":
        r = ", ".join([f"{s[0]} ({s[2]})" for s in bull[:3]])
        risk = f" ⚠️ Watch: {', '.join([s[0] for s in bear[:2]])}" if bear else ""
        return f"**{symbol}** BUY signal — Score {score}/100. Bullish factors: {r}.{risk} Price: {currency}{price:.2f}"
    elif signal == "SELL":
        r = ", ".join([f"{s[0]} ({s[2]})" for s in bear[:3]])
        return f"**{symbol}** SELL/EXIT signal — Score {score}/100. Bearish: {r}. Profit book karo."
    else:
        return f"**{symbol}** HOLD zone — Score {score}/100. Koi strong setup nahi hai abhi. Wait karo."

def build_buy_telegram(market, mode_, symbol, price, target, sl, score, signals, currency):
    """Full reasoning BUY alert for Telegram — includes fundamentals if Swing"""
    bull = [s for s in signals if s[1] == "BULLISH"]
    bear = [s for s in signals if s[1] == "BEARISH"]

    lines = [
        f"🟢 *AI AGENT — BUY ORDER*",
        f"Market: {market} | Mode: {mode_}",
        f"Stock: *{symbol}*",
        f"",
        f"💰 Buy Price: {currency}{price:.2f}",
        f"🎯 Target: {currency}{target:.2f} ({(target/price-1)*100:+.2f}%)",
        f"🛑 Stop Loss: {currency}{sl:.2f} ({(sl/price-1)*100:+.2f}%)",
        f"📊 AI Confidence Score: {score}/100",
        f"",
        f"📌 *Why AI bought this:*",
    ]
    for s in bull[:5]:
        lines.append(f"  ✅ {s[0]}: {s[2]}")
    if bear:
        lines.append(f"")
        lines.append(f"⚠️ *Risk factors noted:*")
        for s in bear[:2]:
            lines.append(f"  • {s[0]}: {s[2]}")
    lines.append(f"")
    lines.append(f"🕒 {now.strftime('%d %b %Y, %H:%M:%S')} IST")
    return "\n".join(lines)

def build_sell_telegram(market, mode_, symbol, exit_price, entry_price, qty, pnl, reason, currency):
    """Full reasoning SELL alert for Telegram"""
    pnl_pct = (exit_price/entry_price - 1) * 100
    result_icon = "✅ PROFIT" if pnl >= 0 else "❌ LOSS"
    lines = [
        f"🔴 *AI AGENT — SELL ORDER*",
        f"Market: {market} | Mode: {mode_}",
        f"Stock: *{symbol}*",
        f"",
        f"📥 Entry was: {currency}{entry_price:.2f}",
        f"📤 Exit Price: {currency}{exit_price:.2f}",
        f"📦 Qty: {qty}",
        f"",
        f"{result_icon}: {currency}{pnl:+,.2f} ({pnl_pct:+.2f}%)",
        f"📌 Reason: {reason}",
        f"",
        f"🕒 {now.strftime('%d %b %Y, %H:%M:%S')} IST",
    ]
    return "\n".join(lines)

# ================= CANDLESTICK CHART =================
def plot_chart(df, symbol, current_mode):
    tail = 60 if current_mode == "Intraday" else 90
    d = df.tail(tail).copy()

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.04, row_heights=[0.6, 0.2, 0.2],
        subplot_titles=[f"{symbol}", "Volume", "RSI / Stoch"]
    )

    fig.add_trace(go.Candlestick(
        x=d.index, open=d['Open'], high=d['High'], low=d['Low'], close=d['Close'],
        increasing_line_color='#00ff88', decreasing_line_color='#ff4444', name="Price"
    ), row=1, col=1)

    for col, color, name in [('SMA_20','#00d4ff','SMA20'),('SMA_50','#ffaa00','SMA50')]:
        if col in d.columns:
            fig.add_trace(go.Scatter(x=d.index, y=d[col], line=dict(color=color, width=1.2),
                                     name=name, opacity=0.85), row=1, col=1)
    if 'BB_Up' in d.columns:
        fig.add_trace(go.Scatter(x=d.index, y=d['BB_Up'],
            line=dict(color='#9988ff', width=0.8, dash='dot'), name='BB+', opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d['BB_Low'],
            line=dict(color='#9988ff', width=0.8, dash='dot'), name='BB-', opacity=0.6,
            fill='tonexty', fillcolor='rgba(153,136,255,0.05)'), row=1, col=1)
    if 'VWAP' in d.columns and current_mode == "Intraday":
        fig.add_trace(go.Scatter(x=d.index, y=d['VWAP'],
            line=dict(color='#ff88ff', width=1.5), name='VWAP'), row=1, col=1)

    colors_v = ['#00ff88' if c >= o else '#ff4444' for c, o in zip(d['Close'], d['Open'])]
    fig.add_trace(go.Bar(x=d.index, y=d['Volume'], marker_color=colors_v,
                         name='Vol', opacity=0.7), row=2, col=1)
    if 'Vol_SMA' in d.columns:
        fig.add_trace(go.Scatter(x=d.index, y=d['Vol_SMA'],
            line=dict(color='#ffaa00', width=1), name='VolAvg'), row=2, col=1)

    if 'RSI' in d.columns:
        fig.add_trace(go.Scatter(x=d.index, y=d['RSI'],
            line=dict(color='#00d4ff', width=1.5), name='RSI'), row=3, col=1)
    if 'Stoch_K' in d.columns:
        fig.add_trace(go.Scatter(x=d.index, y=d['Stoch_K'],
            line=dict(color='#ff88aa', width=1, dash='dot'), name='Stoch K'), row=3, col=1)

    gs = dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True, zeroline=False)
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520',
        height=560, showlegend=False, xaxis_rangeslider_visible=False,
        margin=dict(l=8, r=8, t=30, b=8), font=dict(color='#7a8fa6', size=11),
        xaxis=gs, xaxis2=gs, xaxis3=gs, yaxis=gs, yaxis2=gs, yaxis3=gs
    )
    for y_val, color in [(70,'#ff4444'),(30,'#00ff88'),(80,'#ff8800'),(20,'#00ff88')]:
        fig.add_trace(go.Scatter(x=[d.index[0], d.index[-1]], y=[y_val, y_val],
            mode="lines", line=dict(color=color, dash="dot", width=0.8),
            opacity=0.4, showlegend=False), row=3, col=1)
    return fig

# ================= OPTIONS CHAIN =================
@st.cache_data(ttl=300, show_spinner=False)
def get_options_data(symbol):
    try:
        t = yf.Ticker(symbol)
        exps = t.options
        if not exps:
            return None, None, None
        exp = exps[0]
        chain = t.option_chain(exp)
        calls = chain.calls[['strike','lastPrice','volume','openInterest','impliedVolatility']].copy()
        puts  = chain.puts [['strike','lastPrice','volume','openInterest','impliedVolatility']].copy()
        calls.columns = ['Strike','Call Price','Call Vol','Call OI','Call IV']
        puts.columns  = ['Strike','Put Price', 'Put Vol', 'Put OI', 'Put IV']
        merged = pd.merge(calls, puts, on='Strike', how='outer').fillna(0)
        total_call_oi = calls['Call OI'].sum()
        total_put_oi  = puts['Put OI'].sum()
        pcr = round(total_put_oi / (total_call_oi + 1e-9), 2)
        return merged, pcr, exp
    except:
        return None, None, None

# ================= RISK MANAGEMENT =================
def calc_position_size(capital, risk_pct, entry, sl, target):
    risk_amt  = capital * (risk_pct / 100)
    sl_dist   = abs(entry - sl)
    if sl_dist == 0:
        return 0, 0, 0, 0, 0
    qty       = int(risk_amt / sl_dist)
    invest    = qty * entry
    max_loss  = qty * sl_dist
    max_gain  = qty * abs(target - entry)
    rr_ratio  = round(max_gain / (max_loss + 1e-9), 2)
    return qty, round(invest, 2), round(max_loss, 2), round(max_gain, 2), rr_ratio

# ================= PRICE ALERTS =================
def check_alerts(alerts, current_prices):
    triggered = []
    remaining = []
    for alert in alerts:
        sym   = alert['symbol']
        cur   = AGENT_CURRENCY.get(alert.get('market','NSE'), '₹')
        price = current_prices.get(sym, 0)
        if price == 0:
            remaining.append(alert)
            continue
        hit = False
        if alert['condition'] == "Above" and price >= alert['target']:
            hit = True
        elif alert['condition'] == "Below" and price <= alert['target']:
            hit = True
        if hit:
            triggered.append({**alert, 'triggered_price': price,
                               'triggered_at': now.strftime('%H:%M:%S')})
            send_telegram(f"🔔 ALERT: {sym} {alert['condition']} {cur}{alert['target']:.2f}\nCurrent: {cur}{price:.2f}")
        else:
            remaining.append(alert)
    return triggered, remaining

# ================= NEWS =================
@st.cache_data(ttl=1800, show_spinner=False)
def get_news(symbol):
    try:
        news = yf.Ticker(symbol).news or []
        pos_w = ['surge','gain','profit','growth','bullish','rally','buy','strong','record','upgrade','beat','rise']
        neg_w = ['fall','drop','loss','bearish','sell','decline','weak','downgrade','miss','crash','risk','cut']
        out = []
        for n in news[:5]:
            title = n.get('title','')
            tl    = title.lower()
            pos   = sum(1 for w in pos_w if w in tl)
            neg   = sum(1 for w in neg_w if w in tl)
            sent  = "POSITIVE" if pos > neg else "NEGATIVE" if neg > pos else "NEUTRAL"
            score = min(100, 50 + pos*15) if pos > neg else max(0, 50 - neg*15) if neg > pos else 50
            ts    = n.get('providerPublishTime', 0)
            dt    = datetime.fromtimestamp(ts).strftime('%d %b %H:%M') if ts else "Recent"
            out.append({'title': title, 'link': n.get('link','#'),
                        'sentiment': sent, 'score': score, 'time': dt})
        return out
    except:
        return []

def news_sentiment_summary(symbol):
    """Returns (avg_score 0-100, label, headline_count) for use in Swing AI scoring"""
    items = get_news(symbol)
    if not items:
        return 50, "NEUTRAL", 0
    avg = np.mean([n['score'] for n in items])
    label = "POSITIVE" if avg > 58 else "NEGATIVE" if avg < 42 else "NEUTRAL"
    return avg, label, len(items)

# ================= FUNDAMENTALS (for Swing trades) =================
@st.cache_data(ttl=21600, show_spinner=False)
def get_fundamentals(symbol):
    """
    Fetch quarterly/fundamental snapshot for Swing analysis.
    Returns a dict of key ratios + a derived fundamental_score (0-100).
    Crypto has no fundamentals — returns neutral score.
    """
    if "-USD" in symbol:
        return {
            "available": False, "fundamental_score": 50,
            "summary": "Crypto — no traditional fundamentals, sentiment/technicals drive decision."
        }
    try:
        info = yf.Ticker(symbol).info
        pe        = info.get('trailingPE')
        forward_pe= info.get('forwardPE')
        peg       = info.get('pegRatio')
        profit_m  = info.get('profitMargins')
        rev_growth= info.get('revenueGrowth')
        earn_growth = info.get('earningsGrowth')
        roe       = info.get('returnOnEquity')
        debt_eq   = info.get('debtToEquity')
        target_mean = info.get('targetMeanPrice')
        current_p   = info.get('currentPrice') or info.get('regularMarketPrice')
        recommendation = info.get('recommendationKey', 'none')

        score = 50
        notes = []

        if rev_growth is not None:
            if rev_growth > 0.15:
                score += 12; notes.append(f"Strong revenue growth ({rev_growth*100:.1f}%)")
            elif rev_growth > 0.05:
                score += 6; notes.append(f"Decent revenue growth ({rev_growth*100:.1f}%)")
            elif rev_growth < 0:
                score -= 10; notes.append(f"Revenue declining ({rev_growth*100:.1f}%)")

        if earn_growth is not None:
            if earn_growth > 0.15:
                score += 10; notes.append(f"Strong earnings growth ({earn_growth*100:.1f}%)")
            elif earn_growth < 0:
                score -= 8; notes.append("Earnings declining")

        if profit_m is not None:
            if profit_m > 0.15:
                score += 8; notes.append(f"Healthy margins ({profit_m*100:.1f}%)")
            elif profit_m < 0.03:
                score -= 5; notes.append("Thin margins")

        if roe is not None:
            if roe > 0.18:
                score += 8; notes.append(f"High ROE ({roe*100:.1f}%)")
            elif roe < 0.05:
                score -= 5

        if debt_eq is not None:
            if debt_eq > 150:
                score -= 8; notes.append("High debt load")
            elif debt_eq < 50:
                score += 5; notes.append("Low debt")

        if pe is not None and pe > 0:
            if pe < 20:
                score += 6; notes.append(f"Reasonable P/E ({pe:.1f})")
            elif pe > 60:
                score -= 6; notes.append(f"Expensive P/E ({pe:.1f})")

        if target_mean and current_p:
            upside = (target_mean - current_p) / current_p * 100
            if upside > 10:
                score += 10; notes.append(f"Analyst target {upside:+.1f}% upside")
            elif upside < -5:
                score -= 8; notes.append(f"Analyst target {upside:+.1f}% downside")

        if recommendation in ('buy', 'strong_buy'):
            score += 8; notes.append(f"Analyst rating: {recommendation}")
        elif recommendation in ('sell', 'strong_sell'):
            score -= 10; notes.append(f"Analyst rating: {recommendation}")

        score = max(0, min(100, score))

        return {
            "available": True,
            "fundamental_score": score,
            "pe": pe, "rev_growth": rev_growth, "earn_growth": earn_growth,
            "profit_margin": profit_m, "roe": roe, "debt_equity": debt_eq,
            "recommendation": recommendation,
            "summary": " | ".join(notes[:4]) if notes else "Limited fundamental data available"
        }
    except:
        return {"available": False, "fundamental_score": 50, "summary": "Fundamentals fetch failed"}


@st.cache_data(ttl=3600, show_spinner=False)
def predict_price(symbol):
    """
    Multi-model price prediction for next 1, 3, 5 days.
    Uses: Linear Regression trend + GBM classification + momentum
    """
    try:
        df = yf.Ticker(symbol).history(period="2y")
        if df is None or len(df) < 150:
            return None

        df = df.copy()
        c  = df['Close']

        # Feature engineering
        df['r1']    = c.pct_change(1)
        df['r3']    = c.pct_change(3)
        df['r5']    = c.pct_change(5)
        df['r10']   = c.pct_change(10)
        df['r20']   = c.pct_change(20)
        df['sma10'] = c.rolling(10).mean()
        df['sma20'] = c.rolling(20).mean()
        df['sma50'] = c.rolling(50).mean()
        df['std10'] = c.rolling(10).std()
        delta       = c.diff()
        gain        = delta.clip(lower=0).rolling(14).mean()
        loss        = (-delta.clip(upper=0)).rolling(14).mean()
        df['rsi']   = 100 - (100 / (1 + gain / (loss + 1e-9)))
        e1          = c.ewm(span=12).mean(); e2 = c.ewm(span=26).mean()
        df['macd']  = (e1 - e2) / (c + 1e-9)
        df['atr']   = (df['High'] - df['Low']).rolling(14).mean() / (c + 1e-9)
        df['vol_r'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
        df['bb_pos']= (c - c.rolling(20).mean()) / (c.rolling(20).std() * 2 + 1e-9)
        df['momentum'] = c / c.shift(10) - 1
        df['close_norm'] = c / c.rolling(50).mean()

        feats = ['r1','r3','r5','r10','r20','rsi','macd','atr','vol_r',
                 'bb_pos','momentum','close_norm','std10']

        results = {}
        current_price = float(c.iloc[-1])

        for horizon in [1, 3, 5]:
            df[f'fut_{horizon}'] = c.shift(-horizon) / c - 1
            df[f'lbl_{horizon}'] = (df[f'fut_{horizon}'] > 0).astype(int)

            dfc = df[feats + [f'fut_{horizon}', f'lbl_{horizon}']].dropna()
            if len(dfc) < 80:
                continue

            X = dfc[feats].values
            y_cls = dfc[f'lbl_{horizon}'].values
            y_reg = dfc[f'fut_{horizon}'].values

            split = int(len(X) * 0.8)
            Xtr, Xte = X[:split], X[split:]
            ytr_c, yte_c = y_cls[:split], y_cls[split:]
            ytr_r = y_reg[:split]

            sc = StandardScaler()
            Xtr_s = sc.fit_transform(Xtr)
            Xte_s = sc.transform(Xte)

            # GBM Classifier for direction
            clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.08,
                                             max_depth=3, random_state=42)
            clf.fit(Xtr_s, ytr_c)

            # Regression for magnitude
            from sklearn.linear_model import Ridge
            reg = Ridge(alpha=1.0)
            reg.fit(Xtr_s, ytr_r)

            latest = sc.transform(X[-1:])
            direction_prob = clf.predict_proba(latest)[0][1]  # prob of going UP
            pred_return    = float(reg.predict(latest)[0])

            # Accuracy on test
            acc = float(np.mean(clf.predict(Xte_s) == yte_c))

            pred_price = current_price * (1 + pred_return)
            direction  = "UP" if direction_prob > 0.5 else "DOWN"
            confidence = int(max(direction_prob, 1 - direction_prob) * 100)

            results[horizon] = {
                'direction':   direction,
                'confidence':  confidence,
                'pred_return': round(pred_return * 100, 2),
                'pred_price':  round(pred_price, 2),
                'model_acc':   round(acc * 100, 1),
                'current':     round(current_price, 2),
            }

        return results if results else None

    except Exception as e:
        return None

# ================= LEADERBOARD =================
def update_leaderboard(trade_log, initial_capital=100000.0):
    """Build performance stats from trade log"""
    if not trade_log:
        return None

    sells = [t for t in trade_log if t.get('action') == 'SELL' and 'pnl' in t]
    if not sells:
        return None

    pnls       = [t['pnl'] for t in sells]
    total_pnl  = sum(pnls)
    wins       = [p for p in pnls if p > 0]
    losses     = [p for p in pnls if p <= 0]
    win_rate   = len(wins) / len(pnls) * 100 if pnls else 0
    avg_win    = np.mean(wins)   if wins   else 0
    avg_loss   = np.mean(losses) if losses else 0
    rr_ratio   = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    max_dd     = min(pnls) if pnls else 0
    best_trade = max(pnls) if pnls else 0
    portfolio_ret = total_pnl / initial_capital * 100

    # Streak
    streak = 0; cur_streak = 0; streak_type = ""
    for p in reversed(pnls):
        if p > 0:
            if streak_type == "WIN" or streak_type == "":
                cur_streak += 1; streak_type = "WIN"
            else:
                break
        else:
            if streak_type == "LOSS" or streak_type == "":
                cur_streak += 1; streak_type = "LOSS"
            else:
                break
    streak = cur_streak

    # Stock-wise performance
    stock_pnl = {}
    for t in sells:
        stk = t.get('stock','?')
        stock_pnl[stk] = stock_pnl.get(stk, 0) + t['pnl']

    top_winners = sorted(stock_pnl.items(), key=lambda x: x[1], reverse=True)[:5]
    top_losers  = sorted(stock_pnl.items(), key=lambda x: x[1])[:3]

    return {
        'total_trades':   len(pnls),
        'total_pnl':      round(total_pnl, 2),
        'portfolio_ret':  round(portfolio_ret, 2),
        'win_rate':       round(win_rate, 1),
        'avg_win':        round(avg_win, 2),
        'avg_loss':       round(avg_loss, 2),
        'rr_ratio':       round(rr_ratio, 2),
        'max_dd':         round(max_dd, 2),
        'best_trade':     round(best_trade, 2),
        'streak':         streak,
        'streak_type':    streak_type,
        'top_winners':    top_winners,
        'top_losers':     top_losers,
        'pnl_series':     pnls,
    }

# ================= WEEKLY WIN-RATE CALCULATOR =================
def calc_weekly_winrate(trade_log, mode_filter=None):
    """Calculate win rate for trades closed in the last 7 days, optionally filtered by mode"""
    sells = [t for t in trade_log if t.get('action') == 'SELL' and 'pnl' in t]
    if mode_filter:
        sells = [t for t in sells if t.get('mode') == mode_filter]
    if not sells:
        return None

    cutoff = now - timedelta(days=7)
    recent = []
    for t in sells:
        try:
            t_time = t.get('full_time')
            if t_time and t_time >= cutoff:
                recent.append(t)
            elif not t_time:
                recent.append(t)  # fallback: include if no timestamp (older trades)
        except:
            recent.append(t)

    if not recent:
        return {"trades": 0, "win_rate": 0, "wins": 0, "losses": 0, "total_pnl": 0}

    wins   = len([t for t in recent if t['pnl'] > 0])
    losses = len([t for t in recent if t['pnl'] <= 0])
    total  = len(recent)
    total_pnl = sum(t['pnl'] for t in recent)
    return {
        "trades": total, "wins": wins, "losses": losses,
        "win_rate": round(wins/total*100, 1) if total > 0 else 0,
        "total_pnl": round(total_pnl, 2)
    }

# ================= CORE AI AGENT — SCAN, DECIDE, EXECUTE =================
def run_ai_agent_for_market(market, mode_, min_score_threshold, max_alloc, telegram_enabled):
    """
    The autonomous brain: scans every stock in the given market+mode universe,
    runs advanced_engine (technical + fundamental + sentiment fusion for Swing),
    and automatically opens/closes paper-trade positions with full Telegram reasoning.
    Returns a list of (symbol, signal, score, price, status, signals) for UI display.
    """
    agent_key = AGENT_KEYS[market]
    agent = st.session_state[agent_key]
    currency = AGENT_CURRENCY[market]
    universe = MARKET_UNIVERSE[market]
    sl_pct, tg_pct = RISK_PARAMS[mode_]
    can_trade_now = market_can_trade(market, mode_)
    is_bull, _, _ = get_market_regime(MARKET_BENCH[market], mode_)

    results = []
    for stk in universe:
        df_s = get_data(stk, mode_)
        sig, price, score, status, signals = advanced_engine(stk, df_s, mode_)
        results.append((stk, sig, score, price, status, signals))

        # log every decision for the "AI reasoning" panel (rolling buffer)
        st.session_state.scan_log.append({
            'time': now.strftime('%H:%M:%S'), 'market': market, 'mode': mode_,
            'stock': stk, 'signal': sig, 'score': score, 'price': price
        })

        # Position key is tagged by mode so Intraday & Swing positions on the
        # same symbol don't collide
        pos_key = f"{stk}__{mode_}"
        qty = agent['positions'].get(pos_key, 0)

        # ---------- AUTO BUY ----------
        if sig == "BUY" and qty == 0 and price > 0 and can_trade_now and score >= min_score_threshold:
            alloc_pct = (max_alloc/100) if (score >= 88 and is_bull) else (max_alloc*0.66/100) if is_bull else (max_alloc*0.33/100)
            invest = agent['balance'] * alloc_pct
            q = int(invest / price) if price > 0 else 0
            if q > 0 and invest <= agent['balance']:
                agent['positions'][pos_key] = q
                agent['balance'] -= q * price
                agent['entry_price'][pos_key] = price
                agent['highest_price'][pos_key] = price
                agent['entry_mode'][pos_key] = mode_

                target = price * (1 + tg_pct)
                stop   = price * (1 - sl_pct)

                agent['trade_log'].append({
                    'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk,
                    'action': 'BUY', 'price': price, 'qty': q, 'score': score,
                    'mode': mode_, 'market': market
                })

                if telegram_enabled:
                    msg = build_buy_telegram(market, mode_, stk, price, target, stop, score, signals, currency)
                    send_telegram(msg)

        # ---------- AUTO SELL (signal-based exit) ----------
        elif sig == "SELL" and qty > 0 and price > 0:
            entry = agent['entry_price'].get(pos_key, price)
            pnl_t = (price - entry) * qty
            agent['balance'] += qty * price
            agent['positions'][pos_key] = 0
            agent['trade_log'].append({
                'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk,
                'action': 'SELL', 'price': price, 'qty': qty, 'pnl': round(pnl_t, 2),
                'mode': mode_, 'market': market
            })
            agent['entry_price'].pop(pos_key, None)
            agent['highest_price'].pop(pos_key, None)
            agent['entry_mode'].pop(pos_key, None)

            if telegram_enabled:
                msg = build_sell_telegram(market, mode_, stk, price, entry, qty, pnl_t,
                                          "AI signal reversed — bearish indicators triggered", currency)
                send_telegram(msg)

    # ---------- TRAILING SL / TARGET / EOD CHECK for open positions in this market+mode ----------
    for pos_key, q in list(agent['positions'].items()):
        if q <= 0:
            continue
        if not pos_key.endswith(f"__{mode_}"):
            continue
        stk = pos_key.replace(f"__{mode_}", "")

        df2 = get_data(stk, mode_)
        if df2 is None or len(df2) == 0:
            continue
        cp = float(df2['Close'].iloc[-1])

        if pos_key not in agent['highest_price']:
            agent['highest_price'][pos_key] = agent['entry_price'].get(pos_key, cp)
        if cp > agent['highest_price'][pos_key]:
            agent['highest_price'][pos_key] = cp

        trail_sl = agent['highest_price'][pos_key] * (1 - sl_pct)
        entry    = agent['entry_price'].get(pos_key, cp)
        target_p = entry * (1 + tg_pct)

        exit_reason = None
        if mode_ == "Intraday" and market in ("NSE",) and now.hour == 15 and now.minute >= 20:
            exit_reason = "End-of-day square-off (Intraday auto-exit)"
        elif cp <= trail_sl:
            exit_reason = f"Trailing Stop Loss hit at {currency}{trail_sl:.2f}"
        elif cp >= target_p:
            exit_reason = f"Target achieved at {currency}{target_p:.2f}"

        if exit_reason:
            pnl_t = (cp - entry) * q
            agent['balance'] += q * cp
            agent['positions'][pos_key] = 0
            agent['trade_log'].append({
                'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk,
                'action': 'SELL', 'price': cp, 'qty': q, 'pnl': round(pnl_t, 2),
                'mode': mode_, 'market': market
            })
            agent['entry_price'].pop(pos_key, None)
            agent['highest_price'].pop(pos_key, None)
            agent['entry_mode'].pop(pos_key, None)

            if telegram_enabled:
                msg = build_sell_telegram(market, mode_, stk, cp, entry, q, pnl_t, exit_reason, currency)
                send_telegram(msg)

    # keep scan_log bounded
    if len(st.session_state.scan_log) > 500:
        st.session_state.scan_log = st.session_state.scan_log[-500:]

    return sorted(results, key=lambda x: x[2], reverse=True)

# ================= AUTO-REFRESH (5 min) =================
if AUTOREFRESH_AVAILABLE and st.session_state.agent_running:
    st_autorefresh(interval=5*60*1000, key="agent_autorefresh")
elif st.session_state.agent_running:
    st.sidebar.warning("⚠️ Add `streamlit-autorefresh` to requirements.txt for true auto-refresh. Click 'Scan Now' manually meanwhile.")

# ===================== HEADER =====================
st.markdown("""
<div class="main-header">
    <h1>⚡ QUANTEDGE AI v5.0</h1>
    <p>AUTONOMOUS AI TRADING AGENT — NSE · CRYPTO · US STOCKS — AUTO BUY/SELL · TELEGRAM REASONING</p>
</div>
""", unsafe_allow_html=True)

# ===================== RUN AI AGENTS (auto-scan) =====================
if st.session_state.agent_running:
    do_scan = True
else:
    do_scan = False

manual_scan = st.button("🔍 Scan Now (manual)", type="secondary") if not st.session_state.agent_running else False

agent_results = {}  # {market: {mode: [results]}}

if do_scan or manual_scan:
    with st.spinner("🤖 AI Agent scanning markets..."):
        for mkt in ACTIVE_MARKETS:
            agent_results[mkt] = {}
            for md in ACTIVE_MODES:
                agent_results[mkt][md] = run_ai_agent_for_market(
                    mkt, md, min_score, max_alloc_pct, telegram_on
                )
    st.session_state.last_scan_time = now.strftime('%H:%M:%S')

    # Check price alerts using latest scanned prices across all markets
    all_current_prices = {}
    for mkt, modes_dict in agent_results.items():
        for md, results in modes_dict.items():
            for stk, sig, sc, pr, msg, sigs in results:
                if pr > 0:
                    all_current_prices[stk] = pr
    triggered, st.session_state.price_alerts = check_alerts(
        st.session_state.price_alerts, all_current_prices)
    if triggered:
        st.session_state.triggered_alerts.extend(triggered)

# ===================== TOP BAR — Combined across 3 agents =====================
def agent_summary(market):
    agent = st.session_state[AGENT_KEYS[market]]
    inv = sum(agent['entry_price'].get(k, 0) * q for k, q in agent['positions'].items() if q > 0)
    val = agent['balance'] + inv
    pnl_ = val - 100000.0
    open_p = len([q for q in agent['positions'].values() if q > 0])
    return val, pnl_, open_p, agent['balance']

nse_val, nse_pnl, nse_pos, nse_cash = agent_summary("NSE")
crypto_val, crypto_pnl, crypto_pos, crypto_cash = agent_summary("Crypto")
us_val, us_pnl, us_pos, us_cash = agent_summary("US")

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("🇮🇳 NSE Portfolio",    f"₹{nse_val:,.0f}",    f"{'+' if nse_pnl>=0 else ''}{nse_pnl:,.0f}")
c2.metric("🪙 Crypto Portfolio",  f"${crypto_val:,.0f}",  f"{'+' if crypto_pnl>=0 else ''}{crypto_pnl:,.0f}")
c3.metric("🇺🇸 US Portfolio",     f"${us_val:,.0f}",      f"{'+' if us_pnl>=0 else ''}{us_pnl:,.0f}")
c4.metric("Open Positions",  nse_pos + crypto_pos + us_pos)
c5.metric("Alerts Set",      len(st.session_state.price_alerts))
c6.metric("AI Status",       "🟢 LIVE" if st.session_state.agent_running else "⏸️ PAUSED")

st.divider()

# ===================== TABS =====================
tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9,tab10,tab11 = st.tabs([
    "🤖 AI Agent Radar",
    "📊 Chart + S&R",
    "🔮 Price Prediction",
    "🏆 Win-Rate & Leaderboard",
    "📈 Options Chain",
    "⚠️ Risk Calculator",
    "🔔 Price Alerts",
    "📰 News",
    "🧪 Backtest",
    "💼 Portfolio (3 Agents)",
    "🧠 AI Reasoning Log"
])

# ========== TAB 1: AI AGENT RADAR (per market, per mode) ==========
with tab1:
    st.markdown("### 🤖 AI Agent — Live Decisions Across All Markets")

    if not agent_results:
        st.info("Agent abhi scan nahi hua. Toggle 'AI Agent ACTIVE' on karo sidebar mein, ya 'Scan Now' click karo.")
    else:
        for mkt in ACTIVE_MARKETS:
            currency_m = AGENT_CURRENCY[mkt]
            mkt_icon = {"NSE":"🇮🇳","Crypto":"🪙","US":"🇺🇸"}[mkt]
            st.markdown(f"## {mkt_icon} {mkt} Market")

            for md in ACTIVE_MODES:
                results = agent_results.get(mkt, {}).get(md, [])
                if not results:
                    continue
                st.markdown(f"#### {'⚡' if md=='Intraday' else '📈'} {md}")

                buys  = [r for r in results if r[1] == "BUY"]
                sells = [r for r in results if r[1] == "SELL"]

                cb, cs = st.columns(2)
                with cb:
                    st.markdown(f"**🟢 BUY Signals ({len(buys)})**")
                    if buys:
                        for stk,sig,sc,pr,msg,sigs in buys[:5]:
                            expl = ai_explain(stk, sig, sc, sigs, pr, currency_m)
                            bw = min(100, max(0, sc))
                            st.markdown(f"""<div class="card-buy">
                            <div style="display:flex;justify-content:space-between">
                              <span style="color:#00ff88;font-weight:700">{stk}</span>
                              <span style="color:#00ff88;font-weight:800">{currency_m}{pr:.2f}</span>
                            </div>
                            <div style="color:#aaa;font-size:0.76rem;margin:3px 0">{msg[:65]}</div>
                            <div style="background:#003d1f;border-radius:3px;height:5px;margin:5px 0">
                              <div style="background:#00ff88;width:{bw}%;height:5px;border-radius:3px"></div>
                            </div>
                            <div style="color:#00ff88;font-size:0.72rem">Score: {sc}/100</div>
                            <div class="ai-box" style="margin-top:6px;font-size:0.78rem">🤖 {expl}</div>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.caption("No BUY signals abhi.")

                with cs:
                    st.markdown(f"**🔴 SELL Signals ({len(sells)})**")
                    if sells:
                        for stk,sig,sc,pr,msg,sigs in sells[:5]:
                            expl = ai_explain(stk, sig, sc, sigs, pr, currency_m)
                            st.markdown(f"""<div class="card-sell">
                            <div style="display:flex;justify-content:space-between">
                              <span style="color:#ff4444;font-weight:700">{stk}</span>
                              <span style="color:#ff4444;font-weight:800">{currency_m}{pr:.2f}</span>
                            </div>
                            <div style="color:#aaa;font-size:0.76rem;margin:3px 0">{msg[:65]}</div>
                            <div class="ai-box" style="margin-top:6px;font-size:0.78rem">🤖 {expl}</div>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.caption("No SELL signals abhi.")

                with st.expander(f"📋 Full {md} scan table — {mkt}"):
                    rows = []
                    for stk,sig,sc,pr,msg,_ in results:
                        ico = "🟢" if sig=="BUY" else "🔴" if sig=="SELL" else "⚪"
                        rows.append({"Stock":stk,"Signal":f"{ico} {sig}","Score":sc,
                                     f"Price({currency_m})":f"{pr:.2f}" if pr>0 else "-","Analysis":msg[:55]})
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                        column_config={"Score": st.column_config.ProgressColumn("Score",min_value=0,max_value=100)})
            st.divider()

# ========== TAB 2: CHART + S&R ==========
with tab2:
    st.markdown("### 📊 Advanced Chart + Support & Resistance")
    cm1, cm2 = st.columns(2)
    with cm1:
        chart_market = st.selectbox("Market:", ACTIVE_MARKETS if ACTIVE_MARKETS else ["NSE"], key="chart_mkt")
    with cm2:
        chart_mode = st.selectbox("Mode:", ACTIVE_MODES if ACTIVE_MODES else ["Swing"], key="chart_mode")

    CURRENCY = AGENT_CURRENCY[chart_market]
    sel = st.selectbox("Stock:", MARKET_UNIVERSE[chart_market], key="chart_sel")
    df_c = get_data(sel, chart_mode)

    if df_c is not None and len(df_c) >= 50:
        df_c  = compute_indicators(df_c, chart_mode)
        sig,pr,sc,msg,sigs = advanced_engine(sel, df_c, chart_mode)
        sr    = get_sr_levels(df_c)

        # Metrics row
        m1,m2,m3,m4,m5 = st.columns(5)
        ico = "🟢" if sig=="BUY" else "🔴" if sig=="SELL" else "⚪"
        m1.metric("Signal", f"{ico} {sig}")
        m2.metric("Price",  f"{CURRENCY}{pr:.2f}")
        m3.metric("Score",  f"{sc}/100")
        m4.metric("RSI",    f"{df_c['RSI'].iloc[-1]:.1f}")
        m5.metric("ATR",    f"{CURRENCY}{df_c['ATR'].iloc[-1]:.2f}")

        # S&R levels alongside chart
        ch_col, sr_col = st.columns([3,1])

        with ch_col:
            fig = plot_chart(df_c, sel, chart_mode)
            # Add S&R lines using shapes (compatible with all plotly versions)
            if sr:
                shapes = []
                annotations = []
                for r in sr['resistances']:
                    shapes.append(dict(type='line', xref='paper', yref='y',
                        x0=0, x1=1, y0=r, y1=r,
                        line=dict(color='#ff4444', width=1, dash='dash'), opacity=0.5))
                    annotations.append(dict(xref='paper', yref='y', x=1.01, y=r,
                        text=f"R {CURRENCY}{r}", showarrow=False,
                        font=dict(color='#ff4444', size=10), xanchor='left'))
                for s_lvl in sr['supports']:
                    shapes.append(dict(type='line', xref='paper', yref='y',
                        x0=0, x1=1, y0=s_lvl, y1=s_lvl,
                        line=dict(color='#00ff88', width=1, dash='dash'), opacity=0.5))
                    annotations.append(dict(xref='paper', yref='y', x=1.01, y=s_lvl,
                        text=f"S {CURRENCY}{s_lvl}", showarrow=False,
                        font=dict(color='#00ff88', size=10), xanchor='left'))
                shapes.append(dict(type='line', xref='paper', yref='y',
                    x0=0, x1=1, y0=sr['pivot'], y1=sr['pivot'],
                    line=dict(color='#ffaa00', width=1, dash='dot'), opacity=0.6))
                annotations.append(dict(xref='paper', yref='y', x=1.01, y=sr['pivot'],
                    text=f"P {CURRENCY}{sr['pivot']}", showarrow=False,
                    font=dict(color='#ffaa00', size=10), xanchor='left'))
                fig.update_layout(shapes=shapes, annotations=annotations)
            st.plotly_chart(fig, use_container_width=True)

        with sr_col:
            st.markdown("#### 🎯 Key Levels")
            if sr:
                st.markdown(f"**Current:** `{CURRENCY}{sr['current']}`")
                st.markdown(f"**Pivot:**   `{CURRENCY}{sr['pivot']}`")
                st.markdown("---")
                st.markdown("**Resistances 🔴**")
                for r in sr['resistances']:
                    diff = ((r - sr['current'])/sr['current']*100)
                    st.markdown(f"<span class='sr-sell'>{CURRENCY}{r}</span> <span style='color:#555;font-size:0.78rem'>(+{diff:.1f}%)</span>", unsafe_allow_html=True)
                st.markdown("**Supports 🟢**")
                for s in sr['supports']:
                    diff = ((s - sr['current'])/sr['current']*100)
                    st.markdown(f"<span class='sr-buy'>{CURRENCY}{s}</span> <span style='color:#555;font-size:0.78rem'>({diff:.1f}%)</span>", unsafe_allow_html=True)
            else:
                st.info("S&R data unavailable.")

        # Signal breakdown
        st.markdown("#### 🔍 Signal Breakdown")
        if sigs:
            sig_rows = [{"Indicator":s[0],
                         "Status": f"{'🟢' if s[1]=='BULLISH' else '🔴' if s[1]=='BEARISH' else '🟡'} {s[1]}",
                         "Detail":s[2]} for s in sigs]
            st.dataframe(pd.DataFrame(sig_rows), use_container_width=True, hide_index=True)

        st.markdown("#### 🤖 AI Analysis")
        expl = ai_explain(sel, sig, sc, sigs, pr, CURRENCY)
        st.markdown(f'<div class="ai-box" style="font-size:0.93rem;padding:14px">🤖 {expl}</div>', unsafe_allow_html=True)
    else:
        st.warning("Data load nahi hua. Dobara try karo.")

# ========== TAB 3: PRICE PREDICTION ==========
with tab3:
    st.markdown("### 🔮 AI Price Prediction — Next 1, 3, 5 Days")
    st.info("ML model (GBM + Ridge Regression) trained on 2 years of historical data. Educational only — not financial advice!")

    pred_col0, pred_col1, pred_col2 = st.columns([1,2,1])
    with pred_col0:
        pred_market = st.selectbox("Market:", ACTIVE_MARKETS if ACTIVE_MARKETS else ["NSE"], key="pred_mkt")
    with pred_col1:
        pred_sym = st.selectbox("Stock Select Karo:", MARKET_UNIVERSE[pred_market], key="pred_sym")
    with pred_col2:
        run_pred = st.button("🔮 Run Prediction", type="primary")

    PRED_CURRENCY = AGENT_CURRENCY[pred_market]

    if run_pred or st.session_state.get('last_pred_sym') == pred_sym:
        st.session_state['last_pred_sym'] = pred_sym
        with st.spinner(f"🧠 {pred_sym} ka ML model train ho raha hai..."):
            pred_results = predict_price(pred_sym)

        if pred_results:
            st.markdown("#### 📊 Prediction Results")
            p1, p2, p3 = st.columns(3)

            for col, horizon, label in [(p1,1,"Tomorrow"),(p2,3,"3 Days"),(p3,5,"5 Days")]:
                if horizon in pred_results:
                    r = pred_results[horizon]
                    dir_icon  = "📈" if r['direction']=="UP" else "📉"
                    dir_color = "#00ff88" if r['direction']=="UP" else "#ff4444"
                    with col:
                        st.markdown(f"""<div class="pred-box">
                        <div style="color:#7a8fa6;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px">{label}</div>
                        <div style="font-size:2rem;margin:6px 0">{dir_icon}</div>
                        <div style="color:{dir_color};font-size:1.4rem;font-weight:800">{r['direction']}</div>
                        <div style="color:#fff;font-size:1.1rem;font-weight:700;margin:4px 0">{PRED_CURRENCY}{r['pred_price']}</div>
                        <div style="color:{dir_color};font-size:0.85rem">{r['pred_return']:+.2f}%</div>
                        <div style="color:#7a8fa6;font-size:0.75rem;margin-top:6px">Confidence: {r['confidence']}%</div>
                        <div style="color:#555;font-size:0.72rem">Model Acc: {r['model_acc']}%</div>
                        </div>""", unsafe_allow_html=True)

            st.divider()

            # Confidence chart
            horizons  = [h for h in [1,3,5] if h in pred_results]
            confs     = [pred_results[h]['confidence'] for h in horizons]
            rets      = [pred_results[h]['pred_return'] for h in horizons]
            colors_p  = ['#00ff88' if pred_results[h]['direction']=="UP" else '#ff4444' for h in horizons]
            labels_p  = [f"{h}D" for h in horizons]

            fig_pred = make_subplots(rows=1, cols=2,
                subplot_titles=["Predicted Return %", "Model Confidence %"])
            fig_pred.add_trace(go.Bar(x=labels_p, y=rets, marker_color=colors_p, name="Return %"), row=1, col=1)
            fig_pred.add_trace(go.Bar(x=labels_p, y=confs, marker_color='#00d4ff', name="Confidence %"), row=1, col=2)
            gs = dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True)
            fig_pred.update_layout(
                template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520',
                height=280, showlegend=False, margin=dict(l=8,r=8,t=35,b=8),
                font=dict(color='#7a8fa6',size=11),
                xaxis=gs, xaxis2=gs, yaxis=gs, yaxis2=gs
            )
            fig_pred.add_hline(y=0, line_color='#ffffff33')
            st.plotly_chart(fig_pred, use_container_width=True)

            # Disclaimer
            st.markdown("""<div class="ai-box">
            ⚠️ <strong>Important:</strong> Yeh predictions ML model ke basis par hain jo historical patterns use karta hai.
            Market unpredictable hota hai — black swan events, news, macro factors model nahi pakad sakta.
            Ise sirf ek additional data point ki tarah use karo, final decision apna judgment lagao.
            </div>""", unsafe_allow_html=True)

            # Batch prediction for top stocks
            st.divider()
            st.markdown("#### 🔭 Quick Scan — Top 10 Stocks Prediction")
            if st.button("▶️ Scan Top 10 Stocks (1-Day)"):
                scan_stocks = MARKET_UNIVERSE[pred_market][:10]
                scan_results = []
                prog = st.progress(0)
                for i, stk in enumerate(scan_stocks):
                    res = predict_price(stk)
                    if res and 1 in res:
                        r = res[1]
                        scan_results.append({
                            "Stock": stk,
                            "Direction": f"{'📈' if r['direction']=='UP' else '📉'} {r['direction']}",
                            f"Pred Price({PRED_CURRENCY})": r['pred_price'],
                            "Return %": f"{r['pred_return']:+.2f}%",
                            "Confidence": f"{r['confidence']}%",
                            "Model Acc": f"{r['model_acc']}%",
                        })
                    prog.progress((i+1)/len(scan_stocks))
                if scan_results:
                    st.dataframe(pd.DataFrame(scan_results), use_container_width=True, hide_index=True)
        else:
            st.warning("Prediction model nahi bana — data insufficient ya fetch error. Dobara try karo.")

# ========== TAB 4: LEADERBOARD & WEEKLY WIN-RATE ==========
with tab4:
    st.markdown("### 🏆 AI Agent Performance — Win-Rate & Leaderboard")

    # ---------- Weekly win-rate summary across all markets/modes ----------
    st.markdown("#### 📅 This Week's AI Performance (Intraday vs Swing)")
    wk_cols = st.columns(len(ACTIVE_MARKETS) if ACTIVE_MARKETS else 1)
    for idx, mkt in enumerate(ACTIVE_MARKETS):
        agent = st.session_state[AGENT_KEYS[mkt]]
        cur = AGENT_CURRENCY[mkt]
        with wk_cols[idx]:
            st.markdown(f"**{ {'NSE':'🇮🇳','Crypto':'🪙','US':'🇺🇸'}[mkt] } {mkt}**")
            for md in ACTIVE_MODES:
                wr = calc_weekly_winrate(agent['trade_log'], mode_filter=md)
                if wr and wr['trades'] > 0:
                    color = '#00ff88' if wr['win_rate'] >= 55 else '#ffaa00' if wr['win_rate'] >= 40 else '#ff4444'
                    icon = "⚡" if md == "Intraday" else "📈"
                    st.markdown(f"""<div class="card-info">
                    <div style="font-size:0.78rem;color:#7a8fa6">{icon} {md}</div>
                    <div style="font-size:1.3rem;font-weight:800;color:{color}">{wr['win_rate']}%</div>
                    <div style="font-size:0.72rem;color:#888">{wr['wins']}W / {wr['losses']}L of {wr['trades']} trades</div>
                    <div style="font-size:0.72rem;color:{'#00ff88' if wr['total_pnl']>=0 else '#ff4444'}">{cur}{wr['total_pnl']:+,.0f} this week</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.caption(f"{md}: No trades this week yet")

    st.divider()

    # ---------- Detailed per-market leaderboard ----------
    lb_market = st.selectbox("📊 Detailed Analytics for Market:", ACTIVE_MARKETS if ACTIVE_MARKETS else ["NSE"], key="lb_market")
    LB_CURRENCY = AGENT_CURRENCY[lb_market]
    lb_agent = st.session_state[AGENT_KEYS[lb_market]]
    lb = update_leaderboard(lb_agent['trade_log'])

    if lb:
        rank_pnl = lb['portfolio_ret']
        if rank_pnl >= 20:
            rank_label, rank_class = "🏆 Elite Trader", "leaderboard-gold"
        elif rank_pnl >= 10:
            rank_label, rank_class = "🥈 Pro Trader", "leaderboard-silver"
        elif rank_pnl >= 0:
            rank_label, rank_class = "🥉 Good Trader", "leaderboard-bronze"
        else:
            rank_label, rank_class = "📉 Needs Work", "card-hold"

        st.markdown(f"""<div class="{rank_class}">
        <span style="font-size:1.5rem;font-weight:800">{rank_label}</span>
        <span style="color:#888;font-size:0.85rem;margin-left:16px">{lb_market} Portfolio Return: {lb['portfolio_ret']:+.2f}%</span>
        </div>""", unsafe_allow_html=True)

        st.divider()
        s1,s2,s3,s4,s5,s6 = st.columns(6)
        s1.metric("Total Trades",  lb['total_trades'])
        s2.metric("Win Rate",      f"{lb['win_rate']}%")
        s3.metric("Total P&L",     f"{LB_CURRENCY}{lb['total_pnl']:+,.0f}")
        s4.metric("Avg Win",       f"{LB_CURRENCY}{lb['avg_win']:+.0f}")
        s5.metric("Avg Loss",      f"{LB_CURRENCY}{lb['avg_loss']:+.0f}")
        s6.metric("R:R Ratio",     f"1:{lb['rr_ratio']:.1f}")

        s7,s8,s9 = st.columns(3)
        s7.metric("Best Trade",    f"{LB_CURRENCY}{lb['best_trade']:+.0f}")
        s8.metric("Worst Trade",   f"{LB_CURRENCY}{lb['max_dd']:+.0f}")
        streak_icon = "🔥" if lb['streak_type']=="WIN" else "❄️"
        s9.metric("Current Streak",f"{streak_icon} {lb['streak']} {lb['streak_type']}")

        st.divider()
        pnls = lb['pnl_series']
        colors_lb = ['#00ff88' if p > 0 else '#ff4444' for p in pnls]
        fig_lb = go.Figure(go.Bar(
            x=list(range(1, len(pnls)+1)), y=pnls,
            marker_color=colors_lb, name="P&L per Trade"))
        gs = dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True)
        fig_lb.update_layout(
            template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520',
            height=300, title=f"{lb_market} — Trade-by-Trade P&L",
            margin=dict(l=8,r=8,t=38,b=8), font=dict(color='#7a8fa6',size=11),
            xaxis={**gs,'title':'Trade #'}, yaxis={**gs,'title':f'P&L ({LB_CURRENCY})'},
            shapes=[
                dict(type='line', xref='paper', yref='y', x0=0, x1=1, y0=0, y1=0,
                     line=dict(color='#ffffff33', width=1)),
                dict(type='line', xref='paper', yref='y', x0=0, x1=1,
                     y0=lb['avg_win'], y1=lb['avg_win'], line=dict(color='#00ff8866', width=1, dash='dot')),
                dict(type='line', xref='paper', yref='y', x0=0, x1=1,
                     y0=lb['avg_loss'], y1=lb['avg_loss'], line=dict(color='#ff444466', width=1, dash='dot')),
            ],
            annotations=[
                dict(xref='paper', yref='y', x=1.01, y=lb['avg_win'], text="Avg Win",
                     showarrow=False, font=dict(color='#00ff88', size=10), xanchor='left'),
                dict(xref='paper', yref='y', x=1.01, y=lb['avg_loss'], text="Avg Loss",
                     showarrow=False, font=dict(color='#ff4444', size=10), xanchor='left'),
            ]
        )
        st.plotly_chart(fig_lb, use_container_width=True)

        cum = np.cumsum([100000] + pnls)
        fig_eq = go.Figure(go.Scatter(
            y=cum, mode='lines+markers', line=dict(color='#00d4ff', width=2),
            marker=dict(size=4, color=['#00ff88' if p > 0 else '#ff4444' for p in [0]+pnls]),
            fill='tozeroy', fillcolor='rgba(0,212,255,0.06)'))
        fig_eq.update_layout(
            template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520',
            height=260, title=f"{lb_market} — Portfolio Equity Curve",
            margin=dict(l=8,r=8,t=38,b=8), font=dict(color='#7a8fa6',size=11),
            xaxis={**gs,'title':'Trade #'}, yaxis={**gs,'title':f'Portfolio Value ({LB_CURRENCY})'},
            shapes=[dict(type='line', xref='paper', yref='y', x0=0, x1=1,
                         y0=100000, y1=100000, line=dict(color='#ffffff33', width=1, dash='dot'))],
            annotations=[dict(xref='paper', yref='y', x=1.01, y=100000, text="Start",
                              showarrow=False, font=dict(color='#aaa', size=10), xanchor='left')]
        )
        st.plotly_chart(fig_eq, use_container_width=True)

        st.divider()
        lb_col1, lb_col2 = st.columns(2)
        with lb_col1:
            st.markdown("#### 🥇 Top Winning Stocks")
            for i, (stk, pnl) in enumerate(lb['top_winners']):
                medal = ["🥇","🥈","🥉","4️⃣","5️⃣"][i] if i < 5 else "•"
                cls = ["leaderboard-gold","leaderboard-silver","leaderboard-bronze","card-hold","card-hold"][min(i,4)]
                st.markdown(f"""<div class="{cls}">
                {medal} <strong>{stk}</strong>
                <span style="float:right;color:#00ff88;font-weight:700">{LB_CURRENCY}{pnl:+,.0f}</span>
                </div>""", unsafe_allow_html=True)
        with lb_col2:
            st.markdown("#### 📉 Stocks to Avoid")
            for stk, pnl in lb['top_losers']:
                st.markdown(f"""<div class="card-sell">
                ❌ <strong>{stk}</strong>
                <span style="float:right;color:#ff4444;font-weight:700">{LB_CURRENCY}{pnl:+,.0f}</span>
                </div>""", unsafe_allow_html=True)

        st.divider()
        st.markdown("#### 📋 Trader Report Card")
        grade_items = [
            ("Win Rate",    lb['win_rate'],    60, 70, "%"),
            ("R:R Ratio",   lb['rr_ratio']*10, 10, 20, ""),
            ("Portfolio Return", max(0,lb['portfolio_ret']), 5, 15, "%"),
        ]
        for name, val, good, great, unit in grade_items:
            norm = min(100, val / max(great, 1) * 100)
            color = '#00ff88' if val >= great else '#ffaa00' if val >= good else '#ff4444'
            grade = 'A' if val >= great else 'B' if val >= good else 'C'
            st.markdown(f"""
            <div style="margin:8px 0">
              <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                <span style="color:#a0b4c8;font-size:0.85rem">{name}</span>
                <span style="color:{color};font-weight:700">{val:.1f}{unit} — Grade {grade}</span>
              </div>
              <div style="background:#1a2744;border-radius:4px;height:6px">
                <div style="background:{color};width:{norm:.0f}%;height:6px;border-radius:4px"></div>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info(f"{lb_market} mein abhi koi completed trades nahi hain. AI Agent jab BUY/SELL execute karega, tab yahan stats dikhenge.")
        st.markdown("""<div class="ai-box">
        💡 <strong>Tip:</strong> Sidebar mein 'AI Agent ACTIVE' on rakho. Agent har 5 min mein scan karega aur jab trades close honge (target/SL hit), tab leaderboard populate hoga.
        </div>""", unsafe_allow_html=True)

# ========== TAB 5: OPTIONS CHAIN (was tab3) ==========
with tab5:
    st.markdown("### 📈 F&O Options Chain")
    fo_market = st.selectbox("Market:", ACTIVE_MARKETS if ACTIVE_MARKETS else ["NSE"], key="fo_market")
    if fo_market == "NSE":
        fo_stocks = ["NIFTY","BANKNIFTY","RELIANCE.NS","TCS.NS","INFY.NS","TATAMOTORS.NS",
                     "SBIN.NS","KOTAKBANK.NS","HCLTECH.NS","BHARTIARTL.NS","AXISBANK.NS"]
    elif fo_market == "US":
        fo_stocks = ["AAPL","TSLA","NVDA","AMZN","MSFT","GOOGL","AMD","META"]
    else:
        fo_stocks = ["BTC-USD","ETH-USD"]

    fo_sel = st.selectbox("Select Stock/Index:", fo_stocks)
    fo_sym = fo_sel.replace("NIFTY","^NSEI").replace("BANKNIFTY","^NSEBANK")

    with st.spinner("Options data fetch ho rahi hai..."):
        chain, pcr, expiry = get_options_data(fo_sym)

    if chain is not None and pcr is not None:
        pc1,pc2,pc3 = st.columns(3)
        pcr_color   = "🟢" if pcr < 0.8 else "🔴" if pcr > 1.2 else "🟡"
        pcr_signal  = "Bullish (Calls dominant)" if pcr < 0.8 else "Bearish (Puts dominant)" if pcr > 1.2 else "Neutral"
        pc1.metric("Put/Call Ratio (PCR)", f"{pcr_color} {pcr}")
        pc2.metric("PCR Signal", pcr_signal)
        pc3.metric("Expiry", str(expiry))

        st.info("**PCR Guide:** PCR < 0.8 = Bullish | PCR 0.8-1.2 = Neutral | PCR > 1.2 = Bearish")

        # OI Chart
        if 'Call OI' in chain.columns and 'Put OI' in chain.columns:
            top_chain = chain.nlargest(15, 'Call OI').sort_values('Strike')
            fig_oi = go.Figure()
            fig_oi.add_trace(go.Bar(x=top_chain['Strike'], y=top_chain['Call OI'],
                name='Call OI', marker_color='#00ff88', opacity=0.8))
            fig_oi.add_trace(go.Bar(x=top_chain['Strike'], y=top_chain['Put OI'],
                name='Put OI',  marker_color='#ff4444', opacity=0.8))
            fig_oi.update_layout(
                template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520',
                height=320, barmode='group', title="Open Interest by Strike",
                margin=dict(l=8,r=8,t=35,b=8), font=dict(color='#7a8fa6',size=11),
                xaxis=dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True),
                yaxis=dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True),
            )
            st.plotly_chart(fig_oi, use_container_width=True)

        st.markdown("#### 📋 Options Chain Table")
        display_cols = [c for c in ['Strike','Call Price','Call OI','Call Vol',
                                     'Put Price','Put OI','Put Vol'] if c in chain.columns]
        show = chain[display_cols].sort_values('Strike').reset_index(drop=True)
        st.dataframe(show.head(20), use_container_width=True, hide_index=True)
    else:
        st.warning(f"**{fo_sel}** ke liye options data nahi mila.")
        st.info("NSE F&O data ke liye yfinance limited hai. Try: AAPL, TSLA (US stocks) better options data dete hain.")

# ========== TAB 6: RISK CALCULATOR (was tab4) ==========
with tab6:
    st.markdown("### ⚠️ Risk Management Calculator")
    st.info("Har trade se pehle risk calculate karo — professional traders always do this!")

    CURRENCY = st.radio("Currency:", ["₹","$"], horizontal=True, key="risk_currency")

    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown("#### 📥 Trade Parameters")
        cap     = st.number_input(f"Capital ({CURRENCY})", value=100000, step=5000, min_value=1000)
        risk_p  = st.slider("Risk per trade (%)", 0.5, 5.0, 1.5, 0.1)
        entry_p = st.number_input(f"Entry Price ({CURRENCY})", value=500.0, step=0.5, min_value=0.1)
        sl_p    = st.number_input(f"Stop Loss Price ({CURRENCY})", value=480.0, step=0.5, min_value=0.1)
        tg_p    = st.number_input(f"Target Price ({CURRENCY})", value=560.0, step=0.5, min_value=0.1)

    qty_r, invest_r, max_loss_r, max_gain_r, rr = calc_position_size(cap, risk_p, entry_p, sl_p, tg_p)

    with rc2:
        st.markdown("#### 📊 Calculated Results")
        st.markdown(f"""<div class="risk-box">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px">
          <div>
            <div style="color:#7a8fa6;font-size:0.75rem;text-transform:uppercase">Qty to Buy</div>
            <div style="color:#00d4ff;font-size:1.5rem;font-weight:700">{qty_r}</div>
          </div>
          <div>
            <div style="color:#7a8fa6;font-size:0.75rem;text-transform:uppercase">Investment</div>
            <div style="color:#00d4ff;font-size:1.5rem;font-weight:700">{CURRENCY}{invest_r:,.0f}</div>
          </div>
          <div>
            <div style="color:#7a8fa6;font-size:0.75rem;text-transform:uppercase">Max Loss</div>
            <div style="color:#ff4444;font-size:1.5rem;font-weight:700">-{CURRENCY}{max_loss_r:,.0f}</div>
          </div>
          <div>
            <div style="color:#7a8fa6;font-size:0.75rem;text-transform:uppercase">Max Gain</div>
            <div style="color:#00ff88;font-size:1.5rem;font-weight:700">+{CURRENCY}{max_gain_r:,.0f}</div>
          </div>
          <div>
            <div style="color:#7a8fa6;font-size:0.75rem;text-transform:uppercase">Risk:Reward</div>
            <div style="color:{'#00ff88' if rr >= 2 else '#ffaa00' if rr >= 1 else '#ff4444'};font-size:1.5rem;font-weight:700">1 : {rr}</div>
          </div>
          <div>
            <div style="color:#7a8fa6;font-size:0.75rem;text-transform:uppercase">Portfolio %</div>
            <div style="color:#00d4ff;font-size:1.5rem;font-weight:700">{invest_r/cap*100:.1f}%</div>
          </div>
        </div>
        </div>""", unsafe_allow_html=True)

        rr_msg = "✅ Excellent R:R (>2:1)" if rr >= 2 else "🟡 Acceptable R:R (1-2:1)" if rr >= 1 else "❌ Bad R:R — Adjust Target"
        st.markdown(f"**{rr_msg}**")

    # Position sizing across portfolio
    st.divider()
    st.markdown("#### 🧮 Portfolio Allocation Guide")
    alloc_data = {
        "Risk Level":   ["Conservative","Moderate","Aggressive","YOLO (avoid)"],
        "Risk per Trade":[  "0.5%",        "1-2%",     "3-5%",      ">5%"],
        "Suitable for": ["Beginners","Most traders","Experienced","Not recommended"],
        "Max Drawdown": ["~5%",       "~15%",        "~30%",       "100%+"],
    }
    st.dataframe(pd.DataFrame(alloc_data), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### 📐 Breakeven & Fees Calculator")
    bro_col1, bro_col2 = st.columns(2)
    with bro_col1:
        brokerage_pct = st.number_input("Brokerage % (each side)", value=0.03, step=0.01, format="%.3f")
        stt_pct       = st.number_input("STT % (on sell)", value=0.1, step=0.01)
    with bro_col2:
        total_brokerage = invest_r * (brokerage_pct/100) * 2
        stt_cost        = invest_r * (stt_pct/100)
        total_fees      = total_brokerage + stt_cost + 20  # +20 flat Zerodha style
        breakeven_move  = (total_fees / (invest_r + 1e-9)) * 100
        st.metric("Total Fees",    f"{CURRENCY}{total_fees:.2f}")
        st.metric("Breakeven Move", f"{breakeven_move:.3f}%")
        st.metric("Net Max Gain",   f"{CURRENCY}{max(0, max_gain_r - total_fees):.2f}")

# ========== TAB 7: PRICE ALERTS (was tab5) ==========
with tab7:
    st.markdown("### 🔔 Price Alert System")
    st.info("Alerts check hote hain jab bhi AI Agent scan karta hai (har 5 min).")

    a1, a2 = st.columns(2)
    with a1:
        st.markdown("#### ➕ New Alert")
        alert_market = st.selectbox("Market:", ACTIVE_MARKETS if ACTIVE_MARKETS else ["NSE"], key="alert_mkt")
        ALERT_CUR = AGENT_CURRENCY[alert_market]
        alert_sym  = st.selectbox("Stock:", MARKET_UNIVERSE[alert_market], key="alert_sym")
        alert_cond = st.radio("Condition:", ["Above", "Below"], horizontal=True)
        alert_tgt  = st.number_input(f"Target Price ({ALERT_CUR}):", value=500.0, step=1.0, min_value=0.1)
        alert_note = st.text_input("Note (optional):", placeholder="e.g. Breakout level")

        if st.button("🔔 Set Alert", type="primary"):
            new_alert = {
                'symbol': alert_sym, 'market': alert_market, 'condition': alert_cond,
                'target': alert_tgt, 'note': alert_note,
                'created': now.strftime('%H:%M:%S')
            }
            st.session_state.price_alerts.append(new_alert)
            st.success(f"✅ Alert set: {alert_sym} {alert_cond} {ALERT_CUR}{alert_tgt:.2f}")

    with a2:
        st.markdown("#### 📋 Active Alerts")
        if st.session_state.price_alerts:
            for i, al in enumerate(st.session_state.price_alerts):
                col_al1, col_al2 = st.columns([4,1])
                with col_al1:
                    icon = "⬆️" if al['condition']=="Above" else "⬇️"
                    note = f" — {al['note']}" if al.get('note') else ""
                    al_cur = AGENT_CURRENCY.get(al.get('market','NSE'), '₹')
                    st.markdown(f"""<div class="card-alert">
                    <span style="color:#ffaa00;font-weight:700">{al['symbol']}</span>
                    {icon} <span style="color:#fff">{al_cur}{al['target']:.2f}</span>
                    <span style="color:#555;font-size:0.78rem">{note} | Set: {al['created']}</span>
                    </div>""", unsafe_allow_html=True)
                with col_al2:
                    if st.button("🗑️", key=f"del_alert_{i}"):
                        st.session_state.price_alerts.pop(i)
                        st.rerun()
        else:
            st.info("Koi active alert nahi hai.")

    st.divider()
    st.markdown("#### ✅ Triggered Alerts History")
    if st.session_state.triggered_alerts:
        trig_rows = [{"Stock":t['symbol'],"Condition":t['condition'],
                      "Target":f"{AGENT_CURRENCY.get(t.get('market','NSE'),'₹')}{t['target']}",
                      "Hit At":f"{AGENT_CURRENCY.get(t.get('market','NSE'),'₹')}{t.get('triggered_price','-')}",
                      "Time":t.get('triggered_at','-'),
                      "Note":t.get('note','')} for t in st.session_state.triggered_alerts]
        st.dataframe(pd.DataFrame(trig_rows), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear History"):
            st.session_state.triggered_alerts = []
            st.rerun()
    else:
        st.info("Koi alert abhi tak trigger nahi hua.")

# ========== TAB 8: NEWS (was tab6) ==========
with tab8:
    st.markdown("### 📰 Live News & Sentiment")
    news_market = st.selectbox("Market:", ACTIVE_MARKETS if ACTIVE_MARKETS else ["NSE"], key="news_mkt")
    news_sel = st.selectbox("Stock:", MARKET_UNIVERSE[news_market], key="news_sel")

    with st.spinner("Fetching news..."):
        news_items = get_news(news_sel)

    if news_items:
        avg_sent = np.mean([n['score'] for n in news_items])
        slabel   = "🟢 POSITIVE" if avg_sent > 60 else "🔴 NEGATIVE" if avg_sent < 40 else "🟡 NEUTRAL"
        n1,n2 = st.columns(2)
        n1.metric("Overall Sentiment", slabel, f"Score: {avg_sent:.0f}/100")
        n2.metric("Articles Found",    len(news_items))
        st.divider()
        for n in news_items:
            color = "#00ff88" if n['sentiment']=="POSITIVE" else "#ff4444" if n['sentiment']=="NEGATIVE" else "#ffaa00"
            icon  = "🟢" if n['sentiment']=="POSITIVE" else "🔴" if n['sentiment']=="NEGATIVE" else "🟡"
            st.markdown(f"""<div class="news-card">
            <div style="display:flex;justify-content:space-between;margin-bottom:5px">
              <span style="color:{color};font-weight:600;font-size:0.78rem">{icon} {n['sentiment']}</span>
              <span style="color:#444;font-size:0.73rem">{n['time']}</span>
            </div>
            <div style="color:#c0cfe0;font-size:0.87rem;line-height:1.5">{n['title']}</div>
            <a href="{n['link']}" target="_blank" style="color:#00d4ff;font-size:0.73rem;text-decoration:none">📎 Read more →</a>
            </div>""", unsafe_allow_html=True)
    else:
        st.info(f"{news_sel} ke liye news nahi mili.")

# ========== TAB 9: BACKTEST (was tab7) ==========
with tab9:
    st.markdown("### 🧪 Backtesting Engine")
    st.info("Strategy: RSI < 45 + Price > SMA50 + MACD Bullish + Volume > 1.3x | 1 Year Data")

    bt1, bt2 = st.columns(2)
    with bt1:
        bt_market = st.selectbox("Market:", ACTIVE_MARKETS if ACTIVE_MARKETS else ["NSE"], key="bt_mkt")
        bt_stk = st.selectbox("Stock:", MARKET_UNIVERSE[bt_market], key="bt_sel")
        bt_sl  = st.slider("Stop Loss %",  1.0, 10.0, 3.0, 0.5)
        bt_tg  = st.slider("Target %",     2.0, 25.0, 8.0, 0.5)
    with bt2:
        st.markdown("#### Strategy Logic")
        st.markdown("""
        - **Entry:** RSI<45 + Price>SMA50 + MACD cross + Vol 1.3x
        - **Exit:** Target hit / Stop Loss / 20-day timeout
        - **Universe:** 1 year historical OHLCV
        """)

    if st.button("▶️ Run Backtest", type="primary"):
        with st.spinner("Running backtest..."):
            try:
                df_bt = yf.Ticker(bt_stk).history(period="1y")
                if df_bt is not None and len(df_bt) >= 100:
                    df_bt = compute_indicators(df_bt, "Swing").dropna()
                    trades_bt = []
                    in_t = False; ep = 0; ei = 0
                    for i in range(50, len(df_bt)):
                        row = df_bt.iloc[i]
                        p   = row['Close']
                        if not in_t:
                            if (row['RSI']<45 and p>row['SMA_50'] and
                                row['MACD']>row['MacdSig'] and row['Volume']>row['Vol_SMA']*1.3):
                                in_t=True; ep=p; ei=i
                        else:
                            pct = (p-ep)/ep; days = i-ei
                            if pct >= bt_tg/100:
                                trades_bt.append({'type':'WIN','pnl':pct,'days':days}); in_t=False
                            elif pct <= -bt_sl/100:
                                trades_bt.append({'type':'LOSS','pnl':pct,'days':days}); in_t=False
                            elif days >= 20:
                                trades_bt.append({'type':'TIMEOUT','pnl':pct,'days':days}); in_t=False

                    if trades_bt:
                        total = len(trades_bt)
                        wins  = len([t for t in trades_bt if t['type']=='WIN'])
                        losses= len([t for t in trades_bt if t['type']=='LOSS'])
                        pnls  = [t['pnl']*100 for t in trades_bt]
                        wr    = wins/total*100
                        avg_d = np.mean([t['days'] for t in trades_bt])
                        tot_pnl = sum(pnls)
                        max_dd  = min(pnls)

                        r1,r2,r3,r4,r5 = st.columns(5)
                        r1.metric("Trades",   total)
                        r2.metric("Win Rate", f"{wr:.1f}%", f"{wins}W / {losses}L")
                        r3.metric("Total P&L",f"{tot_pnl:+.1f}%")
                        r4.metric("Avg Days", f"{avg_d:.0f}")
                        r5.metric("Max Loss", f"{max_dd:.1f}%")

                        colors_bt = ['#00ff88' if p>=0 else '#ff4444' for p in pnls]
                        fig_bt = go.Figure(go.Bar(
                            x=list(range(1,len(pnls)+1)), y=pnls,
                            marker_color=colors_bt, name="P&L%"))
                        fig_bt.update_layout(
                            template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520',
                            height=300, title=f"{bt_stk} — Trade P&L",
                            margin=dict(l=8,r=8,t=38,b=8), font=dict(color='#7a8fa6',size=11),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.04)',showgrid=True),
                            yaxis=dict(gridcolor='rgba(255,255,255,0.04)',showgrid=True),
                            shapes=[dict(type='line', xref='paper', yref='y',
                                         x0=0, x1=1, y0=0, y1=0,
                                         line=dict(color='#ffffff44', width=1))]
                        )
                        st.plotly_chart(fig_bt, use_container_width=True)

                        cum = np.cumsum(pnls)
                        fig_cum = go.Figure(go.Scatter(
                            x=list(range(1,len(cum)+1)), y=cum,
                            fill='tozeroy', line=dict(color='#00d4ff',width=2),
                            fillcolor='rgba(0,212,255,0.08)'))
                        fig_cum.update_layout(
                            template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520',
                            height=240, title="Cumulative P&L Curve",
                            margin=dict(l=8,r=8,t=38,b=8), font=dict(color='#7a8fa6',size=11),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.04)',showgrid=True),
                            yaxis=dict(gridcolor='rgba(255,255,255,0.04)',showgrid=True),
                        )
                        st.plotly_chart(fig_cum, use_container_width=True)
                    else:
                        st.warning("Enough trades generate nahi hue. Different stock try karo.")
                else:
                    st.warning("Data load nahi hua.")
            except Exception as e:
                st.error(f"Backtest error: {e}")

# ========== TAB 10: PORTFOLIO (3 AGENTS) ==========
with tab10:
    st.markdown("### 💼 Live Portfolio — All 3 AI Agents")

    for mkt in ACTIVE_MARKETS:
        agent = st.session_state[AGENT_KEYS[mkt]]
        cur   = AGENT_CURRENCY[mkt]
        icon  = {"NSE":"🇮🇳","Crypto":"🪙","US":"🇺🇸"}[mkt]

        inv = sum(agent['entry_price'].get(k, 0) * q for k, q in agent['positions'].items() if q > 0)
        val = agent['balance'] + inv
        pnl_ = val - 100000.0
        open_p = len([q for q in agent['positions'].values() if q > 0])

        st.markdown(f"## {icon} {mkt} Agent")
        p1,p2,p3,p4 = st.columns(4)
        p1.metric("Total Value", f"{cur}{val:,.2f}", f"{'+' if pnl_>=0 else ''}{pnl_:,.2f}")
        p2.metric("Cash",        f"{cur}{agent['balance']:,.2f}")
        p3.metric("P&L %",       f"{pnl_/1000:+.2f}%")
        p4.metric("Positions",   open_p)

        active = {k:q for k,q in agent['positions'].items() if q>0}
        if active:
            st.markdown("##### 📂 Open Positions")
            rows_p = []
            for pos_key, q in active.items():
                stk    = pos_key.split("__")[0]
                pmode  = agent['entry_mode'].get(pos_key, '-')
                sl_pct_disp, tg_pct_disp = RISK_PARAMS.get(pmode, (0.03, 0.08))
                entry  = agent['entry_price'].get(pos_key, 0)
                high   = agent['highest_price'].get(pos_key, entry)
                trail  = high*(1 - sl_pct_disp)
                tg_px  = entry*(1 + tg_pct_disp)
                rows_p.append({"Stock":stk, "Mode":pmode, "Qty":q,
                                f"Entry({cur})":f"{entry:.2f}",
                                f"TrailSL({cur})":f"{trail:.2f}",
                                f"Target({cur})":f"{tg_px:.2f}",
                                f"Value({cur})":f"{q*entry:,.0f}"})
            st.dataframe(pd.DataFrame(rows_p), use_container_width=True, hide_index=True)
        else:
            st.caption("Koi open position nahi hai abhi.")

        with st.expander(f"📋 {mkt} — Full Trade Log"):
            if agent['trade_log']:
                log_display = []
                for t in agent['trade_log'][-50:]:
                    log_display.append({
                        "Time": t.get('time','-'), "Mode": t.get('mode','-'),
                        "Stock": t.get('stock','-'), "Action": t.get('action','-'),
                        f"Price({cur})": f"{t.get('price',0):.2f}",
                        "Qty": t.get('qty','-'),
                        "P&L": f"{cur}{t.get('pnl',0):+.2f}" if 'pnl' in t else "-",
                    })
                st.dataframe(pd.DataFrame(log_display), use_container_width=True, hide_index=True)
            else:
                st.caption("Abhi koi trade nahi hua.")

        sells = [t for t in agent['trade_log'] if t.get('action')=='SELL']
        if sells:
            cumulative = 100000 + np.cumsum([t.get('pnl',0) for t in sells])
            fig_eq = go.Figure(go.Scatter(
                y=cumulative, mode='lines', line=dict(color='#00d4ff',width=2),
                fill='tozeroy', fillcolor='rgba(0,212,255,0.07)'))
            fig_eq.update_layout(
                template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520',
                height=220, title=f"{mkt} Equity Curve",
                margin=dict(l=8,r=8,t=38,b=8), font=dict(color='#7a8fa6',size=11),
                xaxis=dict(gridcolor='rgba(255,255,255,0.04)',showgrid=True,title="Trades"),
                yaxis=dict(gridcolor='rgba(255,255,255,0.04)',showgrid=True,title=f"Value ({cur})"),
            )
            st.plotly_chart(fig_eq, use_container_width=True)

        st.divider()

    if st.button("🔁 Reset ALL Portfolios", type="secondary"):
        st.session_state.agent_nse    = make_agent_s
