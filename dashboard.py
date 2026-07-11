# ================= QUANTEDGE AI v9.0 - KELLY + RESET-LEARN + BACKTESTER =================
# Fixes in v9.1:
#  - Fixed orphaned SELL auto-close block (was causing NameError on every SELL signal)
#  - Restored predict_price() function body (was missing, broke Tab 3 & Tab 17)
#  - Wired Kelly Criterion into actual position sizing (was display-only)
#  - Fixed SHORT trailing SL math (now tracks highest_price, not lowest)
#  - Fixed SHORT balance accounting (clean debit/credit model)
#  - Telegram secrets moved to st.secrets with safe fallback
#  - Leaderboard uses agent's starting_capital (not hardcoded 100k)
#  - Cached price lookup in agent_summary (no more per-position API calls)
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
    page_title="QuantEdge AI v9.0 — Kelly + Backtester",
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
        st.markdown('<div class="main-header"><h1>⚡ QUANTEDGE AI v9.0</h1><p>SECURE TRADING TERMINAL</p</div>', unsafe_allow_html=True)
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

# ================= CONSTANTS & SECRETS =================
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)

# FIX: Telegram secrets moved to st.secrets with safe fallback
try:
    TOKEN = st.secrets["TELEGRAM_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
    SECRETS_AVAILABLE = True
except Exception:
    # Fallback for local dev — user must replace these in production
    TOKEN = ""
    CHAT_ID = ""
    SECRETS_AVAILABLE = False

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
    "ABB.NS","CUMMINSIND.NS","THERMAX.NS","BHARATFORGE.NS","KALYANKJIL.NS",
    "SRF.NS","AARTIIND.NS","DEEPAKNTR.NS","PIIND.NS","UPL.NS",
    "BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","RBLBANK.NS",
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
        "positions": {},        # {pos_key: qty} — qty positive (LONG) or negative (SHORT)
        "entry_price": {},
        "highest_price": {},    # for LONG positions (profit protection - tracks highs)
        "lowest_price": {},     # for SHORT positions (profit protection - tracks lows)
        "entry_mode": {},
        "position_direction": {}, # {pos_key: "LONG"/"SHORT"}
        "trade_log": [],
        "paused_until": None,
        "pause_reason": "",
        "reset_count": 0,
        "lessons_learned": [],
        "kelly_fractions": {},
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
    "_last_price_cache": {},   # FIX: cache of latest prices per symbol (avoid re-fetch in agent_summary)
    "_last_price_cache_time": None,
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
    st.markdown("## ⚡ QuantEdge AI v9.0")
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
    sound_alert_on = st.toggle("🔊 Sound Alerts (browser)", value=True)
    min_score   = st.slider("Min Signal Score (auto-trade)", 50, 95, 75)
    max_alloc_pct = st.slider("Max % capital per trade", 5, 30, 15)
    mtf_confirm = st.toggle("🎯 Multi-Timeframe Confirmation", value=True)

    st.divider()
    st.markdown("### 📉 Drawdown Protection")
    dd_protection_on = st.toggle("Auto-pause on losing streak", value=True)
    dd_streak_limit   = st.slider("Pause after N consecutive losses", 2, 8, 4)
    dd_pause_hours    = st.slider("Pause duration (hours)", 1, 48, 12)

    st.divider()
    st.markdown("### 🔄 Auto-Compounding")
    compounding_on = st.toggle("Reinvest profits (compound)", value=False)

    st.divider()
    st.markdown("### 📊 Kelly Criterion Sizing")
    kelly_on = st.toggle("Use Kelly Criterion", value=True,
                         help="Math-optimal position sizing based on win-rate. Adjusts size dynamically as agent learns.")
    if kelly_on:
        st.caption("🎲 Kelly will auto-adjust position size based on trading history.")

    st.divider()
    st.caption(f"🕒 {now.strftime('%d %b %Y  %H:%M:%S')} IST")
    if st.session_state.last_scan_time:
        st.caption(f"🔄 Last scan: {st.session_state.last_scan_time}")

    if not SECRETS_AVAILABLE and telegram_on:
        st.warning("⚠️ Telegram secrets not in `st.secrets`. Alerts will silently fail. Add TELEGRAM_TOKEN & TELEGRAM_CHAT_ID.")

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
        return True
    return True

# ================= HELPERS =================
def send_telegram(msg):
    if not telegram_on or not SECRETS_AVAILABLE or not TOKEN or not CHAT_ID:
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

# ================= MULTI-TIMEFRAME CONFIRMATION =================
@st.cache_data(ttl=600, show_spinner=False)
def get_higher_timeframe_trend(symbol, current_mode):
    try:
        if current_mode == "Intraday":
            df5 = yf.Ticker(symbol).history(period="5d", interval="5m")
            if df5.empty or len(df5) < 30:
                return True, "1H data unavailable — skipping confirmation"
            df1h = df5['Close'].resample('1h').last().dropna()
            if len(df1h) < 10:
                return True, "Insufficient 1H bars"
            ema_fast = df1h.ewm(span=5).mean().iloc[-1]
            ema_slow = df1h.ewm(span=10).mean().iloc[-1]
            hourly_bull = ema_fast > ema_slow

            dfd = yf.Ticker(symbol).history(period="1mo")
            daily_bull = True
            if not dfd.empty and len(dfd) >= 10:
                daily_bull = dfd['Close'].iloc[-1] > dfd['Close'].rolling(10).mean().iloc[-1]

            aligned = hourly_bull and daily_bull
            detail = f"1H:{'🟢' if hourly_bull else '🔴'} Daily:{'🟢' if daily_bull else '🔴'}"
            return aligned, detail
        else:
            dfw = yf.Ticker(symbol).history(period="1y", interval="1wk")
            if dfw.empty or len(dfw) < 10:
                return True, "Weekly data unavailable — skipping confirmation"
            weekly_bull = dfw['Close'].iloc[-1] > dfw['Close'].rolling(10).mean().iloc[-1]
            detail = f"Weekly trend: {'🟢 Bullish' if weekly_bull else '🔴 Bearish'}"
            return weekly_bull, detail
    except:
        return True, "MTF check failed — proceeding without confirmation"

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

        pivot = (highs[-1] + lows[-1] + closes[-1]) / 3
        r1 = 2 * pivot - lows[-1]
        s1 = 2 * pivot - highs[-1]
        r2 = pivot + (highs[-1] - lows[-1])
        s2 = pivot - (highs[-1] - lows[-1])
        r3 = highs[-1] + 2 * (pivot - lows[-1])
        s3 = lows[-1]  - 2 * (highs[-1] - pivot)

        swing_h, swing_l = [], []
        for i in range(5, len(df) - 5):
            if highs[i] == max(highs[i-5:i+6]):
                swing_h.append(highs[i])
            if lows[i] == min(lows[i-5:i+6]):
                swing_l.append(lows[i])

        current = float(closes[-1])

        resistances = sorted(set([r1, r2, r3] + swing_h[-4:]), reverse=False)
        supports    = sorted(set([s1, s2, s3] + swing_l[-4:
