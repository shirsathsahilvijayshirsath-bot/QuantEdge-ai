# ================= QUANTEDGE AI v9.0 - KELLY + RESET-LEARN + BACKTESTER =================
# New in v9: Kelly Criterion sizing, Reset-and-Learn loop, Honest Backtester on real history
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
        "positions": {},        # {pos_key: qty} — qty can be positive (LONG) or negative (SHORT)
        "entry_price": {},
        "highest_price": {},    # for LONG positions
        "lowest_price": {},     # for SHORT positions
        "entry_mode": {},       # {pos_key: "Intraday"/"Swing"}
        "position_direction": {}, # {pos_key: "LONG"/"SHORT"}
        "trade_log": [],        # full history: BUY/SELL/SHORT with direction tag
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
    st.markdown("### 📊 Kelly Criterion Sizing")
    kelly_on = st.toggle("Use Kelly Criterion", value=True,
                         help="Math-optimal position sizing based on win-rate. Adjusts size dynamically as agent learns.")
    if kelly_on:
        st.caption("🎲 Kelly will auto-adjust position size based on trading history.")
    
    st.divider()
    st.markdown("### 🧪 Backtester")
    run_backtest = st.button("▶️ Test Strategies on History", type="primary")
    
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
    try:
        df = df.tail(120).copy()
        highs, lows, closes = df['High'].values, df['Low'].values, df['Close'].values
        pivot = (highs[-1] + lows[-1] + closes[-1]) / 3
        r1, s1 = 2 * pivot - lows[-1], 2 * pivot - highs[-1]
        r2, s2 = pivot + (highs[-1] - lows[-1]), pivot - (highs[-1] - lows[-1])
        r3, s3 = highs[-1] + 2 * (pivot - lows[-1]), lows[-1] - 2 * (highs[-1] - pivot)
        swing_h, swing_l = [], []
        for i in range(5, len(df) - 5):
            if highs[i] == max(highs[i-5:i+6]): swing_h.append(highs[i])
            if lows[i] == min(lows[i-5:i+6]): swing_l.append(lows[i])
        current = float(closes[-1])
        resistances = sorted(set([r1, r2, r3] + swing_h[-4:]), reverse=False)
        supports    = sorted(set([s1, s2, s3] + swing_l[-4:]), reverse=True)
        return {"pivot": round(pivot, 2), "resistances": [round(r, 2) for r in resistances if r > current][:3], 
                "supports": [round(s, 2) for s in supports if s < current][:3], "current": round(current, 2)}
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
            results.append({"sector": sector, "avg_change_pct": round(avg_chg, 2), "stocks_counted": len(changes), 
                            "strength": "🔥 Hot" if avg_chg > 2 else "🟢 Warm" if avg_chg > 0 else "🔴 Cold" if avg_chg > -2 else "🧊 Frozen"})
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
        return {"correlation": round(float(corr), 3), "data_points": len(merged), "interpretation": "Strong Positive — move together" if corr > 0.7 else "Moderate Positive" if corr > 0.3 else "Weak/No Correlation" if corr > -0.3 else "Moderate Negative" if corr > -0.7 else "Strong Negative — move opposite", "series": merged}
    except: return None

@st.cache_resource
def get_model(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2y")
        if df is None or len(df) < 200: return None, None
        df = df.copy()
        c = df['Close']
        df['r1'], df['r5'], df['r10'] = c.pct_change(1), c.pct_change(5), c.pct_change(10)
        df['sma20'], df['sma50'] = c.rolling(20).mean(), c.rolling(50).mean()
        delta = c.diff()
        df['rsi'] = 100 - (100 / (1 + delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0)).rolling(14).mean() + 1e-9))
        df['macd'] = (c.ewm(span=12).mean() - c.ewm(span=26).mean()) / (c + 1e-9)
        df['bb_pos'] = (c - c.rolling(20).mean()) / (c.rolling(20).std() * 2 + 1e-9)
        df['atr'] = (df['High'] - df['Low']).rolling(14).mean() / (c + 1e-9)
        df['vol_r'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
        df['label'] = (c.shift(-5) / c - 1 > 0.02).astype(int)
        df = df.dropna()
        if len(df) < 100: return None, None
        X = df[['r1','r5','r10','rsi','macd','bb_pos','atr','vol_r','sma20','sma50']]
        y = df['label']
        Xtr, _, ytr, _ = train_test_split(X, y, test_size=0.2, shuffle=False)
        sc = StandardScaler()
        mdl = GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=4, random_state=42)
        mdl.fit(sc.fit_transform(Xtr), ytr)
        return mdl, sc
    except: return None, None

def advanced_engine(symbol, df, current_mode):
    if df is None or len(df) < 100: return "HOLD", 0, 0, "Insufficient Data", []
    try:
        df = compute_indicators(df, current_mode)
        if len(df) < 50: return "HOLD", 0, 0, "Data Error", []
        price, rsi, sma20, sma50, macd, macd_s, macd_h, bb_pct, cur_v, avg_v, stoch_k, stoch_d, atr = df['Close'].iloc[-1], df['RSI'].iloc[-1], df['SMA_20'].iloc[-1], df['SMA_50'].iloc[-1], df['MACD'].iloc[-1], df['MacdSig'].iloc[-1], df['MacdH'].iloc[-1], df['BB_pct'].iloc[-1], df['Volume'].iloc[-1], df['Vol_SMA'].iloc[-1], df['Stoch_K'].iloc[-1], df['Stoch_D'].iloc[-1], df['ATR'].iloc[-1]
        vwap = df['VWAP'].iloc[-1] if (current_mode == "Intraday" and 'VWAP' in df.columns) else None

        mdl, sc = get_model(symbol)
        ml_conf = 0
        if mdl and sc:
            try:
                feat = np.array([[df['Close'].pct_change(1).iloc[-1], df['Close'].pct_change(5).iloc[-1] if len(df)>=5 else 0, df['Close'].pct_change(10).iloc[-1] if len(df)>=10 else 0, rsi, macd/(price+1e-9), bb_pct-0.5, atr/(price+1e-9), cur_v/(avg_v+1e-9), sma20, sma50]])
                ml_conf = int(mdl.predict_proba(sc.transform(feat))[0][1] * 100)
            except: pass

        score = (ml_conf - 50) * 0.6 if ml_conf > 0 else 0
        signals = []

        if rsi < 30: score += 20; signals.append(("RSI", "BULLISH", f"{rsi:.1f} — Deeply Oversold"))
        elif rsi < 45: score += 10; signals.append(("RSI", "BULLISH", f"{rsi:.1f} — Oversold"))
        elif rsi > 75: score -= 18; signals.append(("RSI", "BEARISH", f"{rsi:.1f} — Overbought"))
        else: signals.append(("RSI", "NEUTRAL", f"{rsi:.1f}"))

        if price > sma20 > sma50: score += 15; signals.append(("Trend", "BULLISH", "Price > SMA20 > SMA50"))
        elif price > sma50: score += 8; signals.append(("Trend", "BULLISH", "Price above SMA50"))
        elif price < sma50: score -= 10; signals.append(("Trend", "BEARISH", "Price below SMA50"))

        if macd > macd_s and macd_h > 0: score += 14; signals.append(("MACD", "BULLISH", "Bullish crossover"))
        elif macd < macd_s: score -= 10; signals.append(("MACD", "BEARISH", "Bearish crossover"))
        else: signals.append(("MACD", "NEUTRAL", "Converging"))

        if bb_pct < 0.15: score += 12; signals.append(("Bollinger", "BULLISH", "Near lower band — bounce zone"))
        elif bb_pct > 0.90: score -= 8; signals.append(("Bollinger", "BEARISH", "Near upper band — caution"))
        else: signals.append(("Bollinger", "NEUTRAL", f"{bb_pct:.2f}"))

        if stoch_k < 25 and stoch_k > stoch_d: score += 10; signals.append(("Stochastic", "BULLISH", f"K:{stoch_k:.0f} oversold + rising"))
        elif stoch_k > 80 and stoch_k < stoch_d: score -= 8; signals.append(("Stochastic", "BEARISH", f"K:{stoch_k:.0f} overbought"))
        else: signals.append(("Stochastic", "NEUTRAL", f"K:{stoch_k:.0f} D:{stoch_d:.0f}"))

        vr = cur_v / (avg_v + 1e-9)
        if vr > 2.0: score += 14; signals.append(("Volume", "BULLISH", f"{vr:.1f}x surge"))
        elif vr > 1.4: score += 7; signals.append(("Volume", "BULLISH", f"{vr:.1f}x above avg"))
        else: signals.append(("Volume", "NEUTRAL", f"{vr:.1f}x avg"))

        if vwap:
            if price > vwap * 1.005: score += 30; signals.append(("VWAP", "BULLISH", f"Above VWAP {vwap:.1f}"))
            elif price < vwap * 0.995: score -= 30; signals.append(("VWAP", "BEARISH", f"Below VWAP {vwap:.1f}"))
            else: signals.append(("VWAP", "NEUTRAL", f"Near VWAP {vwap:.1f}"))

        if ml_conf > 0: signals.append(("ML Model", "BULLISH" if ml_conf > 60 else "NEUTRAL", f"{ml_conf}% confidence"))

        if current_mode == "Swing":
            fund_data = get_fundamentals(symbol)
            f_score = fund_data.get('fundamental_score', 50)
            if f_score >= 65: score += 15; signals.append(("Fundamentals", "BULLISH", fund_data.get('summary','Strong fundamentals')[:60]))
            elif f_score <= 35: score -= 15; signals.append(("Fundamentals", "BEARISH", fund_data.get('summary','Weak fundamentals')[:60]))
            else: signals.append(("Fundamentals", "NEUTRAL", fund_data.get('summary','Mixed fundamentals')[:60]))

            sent_avg, sent_label, n_articles = news_sentiment_summary(symbol)
            if n_articles > 0:
                if sent_label == "POSITIVE": score += 10; signals.append(("News Sentiment", "BULLISH", f"{sent_label} ({n_articles} articles)"))
                elif sent_label == "NEGATIVE": score -= 10; signals.append(("News Sentiment", "BEARISH", f"{sent_label} ({n_articles} articles)"))
                else: signals.append(("News Sentiment", "NEUTRAL", f"{sent_label} ({n_articles} articles)"))

        reasons = [s[2] for s in signals if s[1] == "BULLISH"][:3]
        status  = " | ".join(reasons) if reasons else "Watching"
        buy_threshold, sell_threshold = (78, -18) if current_mode == "Swing" else (75, -20)

        if score >= buy_threshold: return "BUY", price, int(score), status, signals
        elif score <= sell_threshold or (rsi > 72 and macd < macd_s): return "SELL", price, int(score), status, signals
        else: return "HOLD", price, int(score), status, signals
    except Exception as e: return "HOLD", 0, 0, str(e)[:40], []

def ai_explain(symbol, signal, score, signals, price, currency="₹"):
    bull, bear = [s for s in signals if s[1] == "BULLISH"], [s for s in signals if s[1] == "BEARISH"]
    if signal == "BUY": return f"**{symbol}** BUY signal — Score {score}/100. Bullish factors: {', '.join([f'{s[0]} ({s[2]})' for s in bull[:3]])}.{' ⚠️ Watch: '+', '.join([s[0] for s in bear[:2]]) if bear else ''} Price: {currency}{price:.2f}"
    elif signal == "SELL": return f"**{symbol}** SELL/EXIT signal — Score {score}/100. Bearish: {', '.join([f'{s[0]} ({s[2]})' for s in bear[:3]])}. Profit book karo."
    return f"**{symbol}** HOLD zone — Score {score}/100. Koi strong setup nahi hai abhi. Wait karo."

def build_buy_telegram(market, mode_, symbol, price, target, sl, score, signals, currency):
    lines = [f"🟢 *AI AGENT — BUY ORDER*", f"Market: {market} | Mode: {mode_}", f"Stock: *{symbol}*\n", f"💰 Buy Price: {currency}{price:.2f}", f"🎯 Target: {currency}{target:.2f} ({(target/price-1)*100:+.2f}%)", f"🛑 Stop Loss: {currency}{sl:.2f} ({(sl/price-1)*100:+.2f}%)", f"📊 AI Confidence Score: {score}/100\n", f"📌 *Why AI bought this:*"]
    for s in [s for s in signals if s[1] == "BULLISH"][:5]: lines.append(f"  ✅ {s[0]}: {s[2]}")
    bear = [s for s in signals if s[1] == "BEARISH"]
    if bear:
        lines.append(f"\n⚠️ *Risk factors noted:*")
        for s in bear[:2]: lines.append(f"  • {s[0]}: {s[2]}")
    lines.append(f"\n🕒 {now.strftime('%d %b %Y, %H:%M:%S')} IST")
    return "\n".join(lines)

def build_sell_telegram(market, mode_, symbol, exit_price, entry_price, qty, pnl, reason, currency):
    pnl_pct = (exit_price/entry_price - 1) * 100
    lines = [f"🔴 *AI AGENT — SELL ORDER*", f"Market: {market} | Mode: {mode_}", f"Stock: *{symbol}*\n", f"📥 Entry was: {currency}{entry_price:.2f}", f"📤 Exit Price: {currency}{exit_price:.2f}", f"📦 Qty: {qty}\n", f"{'✅ PROFIT' if pnl >= 0 else '❌ LOSS'}: {currency}{pnl:+,.2f} ({pnl_pct:+.2f}%)", f"📌 Reason: {reason}\n", f"🕒 {now.strftime('%d %b %Y, %H:%M:%S')} IST"]
    return "\n".join(lines)

def plot_chart(df, symbol, current_mode):
    tail = 60 if current_mode == "Intraday" else 90
    d = df.tail(tail).copy()
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.6, 0.2, 0.2], subplot_titles=[f"{symbol}", "Volume", "RSI / Stoch"])
    fig.add_trace(go.Candlestick(x=d.index, open=d['Open'], high=d['High'], low=d['Low'], close=d['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff4444', name="Price"), row=1, col=1)
    for col, color, name in [('SMA_20','#00d4ff','SMA20'),('SMA_50','#ffaa00','SMA50')]:
        if col in d.columns: fig.add_trace(go.Scatter(x=d.index, y=d[col], line=dict(color=color, width=1.2), name=name, opacity=0.85), row=1, col=1)
    if 'BB_Up' in d.columns:
        fig.add_trace(go.Scatter(x=d.index, y=d['BB_Up'], line=dict(color='#9988ff', width=0.8, dash='dot'), name='BB+', opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d['BB_Low'], line=dict(color='#9988ff', width=0.8, dash='dot'), name='BB-', opacity=0.6, fill='tonexty', fillcolor='rgba(153,136,255,0.05)'), row=1, col=1)
    if 'VWAP' in d.columns and current_mode == "Intraday": fig.add_trace(go.Scatter(x=d.index, y=d['VWAP'], line=dict(color='#ff88ff', width=1.5), name='VWAP'), row=1, col=1)
    colors_v = ['#00ff88' if c >= o else '#ff4444' for c, o in zip(d['Close'], d['Open'])]
    fig.add_trace(go.Bar(x=d.index, y=d['Volume'], marker_color=colors_v, name='Vol', opacity=0.7), row=2, col=1)
    if 'Vol_SMA' in d.columns: fig.add_trace(go.Scatter(x=d.index, y=d['Vol_SMA'], line=dict(color='#ffaa00', width=1), name='VolAvg'), row=2, col=1)
    if 'RSI' in d.columns: fig.add_trace(go.Scatter(x=d.index, y=d['RSI'], line=dict(color='#00d4ff', width=1.5), name='RSI'), row=3, col=1)
    if 'Stoch_K' in d.columns: fig.add_trace(go.Scatter(x=d.index, y=d['Stoch_K'], line=dict(color='#ff88aa', width=1, dash='dot'), name='Stoch K'), row=3, col=1)
    gs = dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True, zeroline=False)
    fig.update_layout(template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520', height=560, showlegend=False, xaxis_rangeslider_visible=False, margin=dict(l=8, r=8, t=30, b=8), font=dict(color='#7a8fa6', size=11), xaxis=gs, xaxis2=gs, xaxis3=gs, yaxis=gs, yaxis2=gs, yaxis3=gs)
    for y_val, color in [(70,'#ff4444'),(30,'#00ff88'),(80,'#ff8800'),(20,'#00ff88')]:
        fig.add_trace(go.Scatter(x=[d.index[0], d.index[-1]], y=[y_val, y_val], mode="lines", line=dict(color=color, dash="dot", width=0.8), opacity=0.4, showlegend=False), row=3, col=1)
    return fig

@st.cache_data(ttl=21600, show_spinner=False)
def get_fundamentals(symbol):
    if "-USD" in symbol: return {"available": False, "fundamental_score": 50, "summary": "Crypto — no traditional fundamentals, sentiment/technicals drive decision."}
    try:
        info = yf.Ticker(symbol).info
        pe, rev_growth, earn_growth, profit_m, roe, debt_eq, target_mean, current_p, recommendation = info.get('trailingPE'), info.get('revenueGrowth'), info.get('earningsGrowth'), info.get('profitMargins'), info.get('returnOnEquity'), info.get('debtToEquity'), info.get('targetMeanPrice'), info.get('currentPrice') or info.get('regularMarketPrice'), info.get('recommendationKey', 'none')
        score, notes = 50, []
        if rev_growth is not None:
            if rev_growth > 0.15: score += 12; notes.append(f"Strong revenue growth ({rev_growth*100:.1f}%)")
            elif rev_growth > 0.05: score += 6; notes.append(f"Decent revenue growth ({rev_growth*100:.1f}%)")
            elif rev_growth < 0: score -= 10; notes.append(f"Revenue declining ({rev_growth*100:.1f}%)")
        if earn_growth is not None:
            if earn_growth > 0.15: score += 10; notes.append(f"Strong earnings growth ({earn_growth*100:.1f}%)")
            elif earn_growth < 0: score -= 8; notes.append("Earnings declining")
        if profit_m is not None:
            if profit_m > 0.15: score += 8; notes.append(f"Healthy margins ({profit_m*100:.1f}%)")
            elif profit_m < 0.03: score -= 5; notes.append("Thin margins")
        if roe is not None:
            if roe > 0.18: score += 8; notes.append(f"High ROE ({roe*100:.1f}%)")
            elif roe < 0.05: score -= 5
        if debt_eq is not None:
            if debt_eq > 150: score -= 8; notes.append("High debt load")
            elif debt_eq < 50: score += 5; notes.append("Low debt")
        if pe is not None and pe > 0:
            if pe < 20: score += 6; notes.append(f"Reasonable P/E ({pe:.1f})")
            elif pe > 60: score -= 6; notes.append(f"Expensive P/E ({pe:.1f})")
        if target_mean and current_p:
            upside = (target_mean - current_p) / current_p * 100
            if upside > 10: score += 10; notes.append(f"Analyst target {upside:+.1f}% upside")
            elif upside < -5: score -= 8; notes.append(f"Analyst target {upside:+.1f}% downside")
        if recommendation in ('buy', 'strong_buy'): score += 8; notes.append(f"Analyst rating: {recommendation}")
        elif recommendation in ('sell', 'strong_sell'): score -= 10; notes.append(f"Analyst rating: {recommendation}")
        return {"available": True, "fundamental_score": max(0, min(100, score)), "pe": pe, "rev_growth": rev_growth, "earn_growth": earn_growth, "profit_margin": profit_m, "roe": roe, "debt_equity": debt_eq, "recommendation": recommendation, "summary": " | ".join(notes[:4]) if notes else "Limited fundamental data available"}
    except: return {"available": False, "fundamental_score": 50, "summary": "Fundamentals fetch failed"}

@st.cache_data(ttl=3600, show_spinner=False)
def backtest_strategy(symbol, strategy_name="intraday", period="1y"):
    try:
        df = yf.Ticker(symbol).history(period=period)
        if df is None or len(df) < 100: return None
        df = compute_indicators(df.copy(), strategy_name)
        positions, trade_log, balance = [], [], 100000.0
        for i in range(50, len(df) - 5):
            test_df = df.iloc[:i+1].copy()
            sig, price, score, msg, signals = advanced_engine(symbol, test_df, strategy_name)
            threshold = 75 if strategy_name == "Intraday" else 78
            if sig == "BUY" and score >= threshold and not positions:
                entry_price = float(df['Close'].iloc[i])
                positions.append({'entry': entry_price, 'entry_idx': i, 'qty': int(1000 / entry_price)})
            if positions and (sig == "SELL" or (i - positions[0]['entry_idx']) >= 5):
                exit_price = float(df['Close'].iloc[i])
                pos = positions.pop(0)
                pnl = (exit_price - pos['entry']) * pos['qty']
                trade_log.append({'entry': pos['entry'], 'exit': exit_price, 'pnl': pnl})
                balance += pnl
        if not trade_log: return None
        wins, losses = [t['pnl'] for t in trade_log if t['pnl'] > 0], [t['pnl'] for t in trade_log if t['pnl'] <= 0]
        equity = [100000]
        for t in trade_log: equity.append(equity[-1] + t['pnl'])
        max_dd = min([(e - max(equity[:i+1])) / max(equity[:i+1]) * 100 for i, e in enumerate(equity)])
        returns = [(trade_log[i]['pnl'] / trade_log[i]['entry'] / trade_log[i].get('qty', 1)) if i < len(trade_log) else 0 for i in range(len(trade_log))]
        sharpe = (np.mean(returns) / (np.std(returns) + 1e-9)) * np.sqrt(252) if returns else 0
        return {'symbol': symbol, 'strategy': strategy_name, 'total_trades': len(trade_log), 'wins': len(wins), 'losses': len(losses), 'win_rate': round(len(wins) / len(trade_log) * 100, 1) if trade_log else 0, 'total_pnl': round(sum(t['pnl'] for t in trade_log), 2), 'avg_win': round(np.mean(wins), 2) if wins else 0, 'avg_loss': round(np.mean(losses), 2) if losses else 0, 'max_dd': round(max_dd, 2), 'sharpe': round(sharpe, 2), 'passed': len(wins) / len(trade_log) > 0.50 if trade_log else False}
    except: return None

@st.cache_data(ttl=3600, show_spinner=False)
def predict_price(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2y")
        if df is None or len(df) < 150: return None
        c = df['Close']
        df['r1'], df['r3'], df['r5'], df['r10'], df['r20'] = c.pct_change(1), c.pct_change(3), c.pct_change(5), c.pct_change(10), c.pct_change(20)
        df['sma10'], df['sma20'], df['sma50'], df['std10'] = c.rolling(10).mean(), c.rolling(20).mean(), c.rolling(50).mean(), c.rolling(10).std()
        delta = c.diff()
        df['rsi'] = 100 - (100 / (1 + delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0)).rolling(14).mean() + 1e-9))
        df['macd'] = (c.ewm(span=12).mean() - c.ewm(span=26).mean()) / (c + 1e-9)
        df['atr'] = (df['High'] - df['Low']).rolling(14).mean() / (c + 1e-9)
        df['vol_r'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
        df['bb_pos'] = (c - c.rolling(20).mean()) / (c.rolling(20).std() * 2 + 1e-9)
        df['momentum'], df['close_norm'] = c / c.shift(10) - 1, c / c.rolling(50).mean()
        feats = ['r1','r3','r5','r10','r20','rsi','macd','atr','vol_r','bb_pos','momentum','close_norm','std10']
        results, current_price = {}, float(c.iloc[-1])
        for horizon in [1, 3, 5]:
            df[f'fut_{horizon}'] = c.shift(-horizon) / c - 1
            df[f'lbl_{horizon}'] = (df[f'fut_{horizon}'] > 0).astype(int)
            dfc = df[feats + [f'fut_{horizon}', f'lbl_{horizon}']].dropna()
            if len(dfc) < 80: continue
            X, y_cls, y_reg = dfc[feats].values, dfc[f'lbl_{horizon}'].values, dfc[f'fut_{horizon}'].values
            split = int(len(X) * 0.8)
            Xtr, Xte, ytr_c, yte_c, ytr_r = X[:split], X[split:], y_cls[:split], y_cls[split:], y_reg[:split]
            sc = StandardScaler()
            Xtr_s, Xte_s = sc.fit_transform(Xtr), sc.transform(Xte)
            clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.08, max_depth=3, random_state=42).fit(Xtr_s, ytr_c)
            reg = Ridge(alpha=1.0).fit(Xtr_s, ytr_r)
            latest = sc.transform(X[-1:])
            prob = clf.predict_proba(latest)[0][1]
            ret = float(reg.predict(latest)[0])
            acc = float(np.mean(clf.predict(Xte_s) == yte_c))
            results[horizon] = {'direction': "UP" if prob > 0.5 else "DOWN", 'confidence': int(max(prob, 1 - prob) * 100), 'pred_return': round(ret * 100, 2), 'pred_price': round(current_price * (1 + ret), 2), 'model_acc': round(acc * 100, 1), 'current': round(current_price, 2)}
        return results if results else None
    except: return None

# ================= KELLY CRITERION SIZING =================
def calc_kelly_fraction(agent, mode_):
    sells = [t for t in agent['trade_log'] if t.get('action') in ('SELL', 'BUY') and t.get('mode') == mode_ and 'pnl' in t]
    if len(sells) < 5: return 0.02
    wins = [t['pnl'] for t in sells if t['pnl'] > 0]
    losses = [t['pnl'] for t in sells if t['pnl'] <= 0]
    if not wins or not losses: return 0.02
    p = len(wins) / len(sells)
    q = 1 - p
    avg_win = np.mean(wins)
    avg_loss = abs(np.mean(losses))
    if avg_loss == 0: return 0.02
    b = avg_win / avg_loss
    kelly_f = (b * p - q) / b if b > 0 else 0
    return max(0.01, min(0.25, kelly_f))
# ================= LEADERBOARD =================
def update_leaderboard(trade_log, initial_capital=100000.0):
    if not trade_log: return None
    sells = [t for t in trade_log if t.get('action') == 'SELL' and 'pnl' in t]
    if not sells: return None
    pnls = [t['pnl'] for t in sells]
    total_pnl = sum(pnls)
    wins, losses = [p for p in pnls if p > 0], [p for p in pnls if p <= 0]
    win_rate = len(wins) / len(pnls) * 100 if pnls else 0
    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    max_dd, best_trade = min(pnls) if pnls else 0, max(pnls) if pnls else 0
    portfolio_ret = total_pnl / initial_capital * 100
    streak, cur_streak, streak_type = 0, 0, ""
    for p in reversed(pnls):
        if p > 0:
            if streak_type == "WIN" or streak_type == "": cur_streak += 1; streak_type = "WIN"
            else: break
        else:
            if streak_type == "LOSS" or streak_type == "": cur_streak += 1; streak_type = "LOSS"
            else: break
    streak = cur_streak
    stock_pnl = {}
    for t in sells: stock_pnl[t.get('stock','?')] = stock_pnl.get(t.get('stock','?'), 0) + t['pnl']
    return {'total_trades': len(pnls), 'total_pnl': round(total_pnl, 2), 'portfolio_ret': round(portfolio_ret, 2), 'win_rate': round(win_rate, 1), 'avg_win': round(avg_win, 2), 'avg_loss': round(avg_loss, 2), 'rr_ratio': round(rr_ratio, 2), 'max_dd': round(max_dd, 2), 'best_trade': round(best_trade, 2), 'streak': streak, 'streak_type': streak_type, 'top_winners': sorted(stock_pnl.items(), key=lambda x: x[1], reverse=True)[:5], 'top_losers': sorted(stock_pnl.items(), key=lambda x: x[1])[:3], 'pnl_series': pnls}

def calc_weekly_winrate(trade_log, mode_filter=None):
    sells = [t for t in trade_log if t.get('action') == 'SELL' and 'pnl' in t]
    if mode_filter: sells = [t for t in sells if t.get('mode') == mode_filter]
    if not sells: return None
    cutoff = now - timedelta(days=7)
    recent = []
    for t in sells:
        try:
            t_time = t.get('full_time')
            if t_time and t_time >= cutoff: recent.append(t)
            elif not t_time: recent.append(t)
        except: recent.append(t)
    if not recent: return {"trades": 0, "win_rate": 0, "wins": 0, "losses": 0, "total_pnl": 0}
    wins, losses = len([t for t in recent if t['pnl'] > 0]), len([t for t in recent if t['pnl'] <= 0])
    return {"trades": len(recent), "wins": wins, "losses": losses, "win_rate": round(wins/len(recent)*100, 1) if recent else 0, "total_pnl": round(sum(t['pnl'] for t in recent), 2)}

def generate_daily_summary(active_markets, active_modes):
    lines = [f"📝 *DAILY AI MARKET SUMMARY* — {now.strftime('%d %b %Y')}\n"]
    for mkt in active_markets:
        icon, cur = {"NSE":"🇮🇳","Crypto":"🪙","US":"🇺🇸"}[mkt], AGENT_CURRENCY[mkt]
        agent = st.session_state[AGENT_KEYS[mkt]]
        is_bull, regime_txt, _ = get_market_regime(MARKET_BENCH[mkt], "Swing")
        lines.append(f"{icon} *{mkt}* — {'🟢' if is_bull else '🔴'} {regime_txt}")
        today_trades = [t for t in agent['trade_log'] if t.get('full_time') and t['full_time'].date() == now.date()]
        buys_today, sells_today = [t for t in today_trades if t['action'] == 'BUY'], [t for t in today_trades if t['action'] == 'SELL']
        if buys_today or sells_today:
            lines.append(f"   Trades today: {len(buys_today)} BUY, {len(sells_today)} SELL")
            if sells_today: lines.append(f"   Today's realized P&L: {cur}{sum(t.get('pnl', 0) for t in sells_today):+,.2f}")
        else: lines.append("   No trades executed today")
        val = agent['balance'] + sum(agent['entry_price'].get(k, 0) * q for k, q in agent['positions'].items() if q > 0)
        lines.append(f"   Portfolio: {cur}{val:,.0f} ({(val-100000)/1000:+.2f}%)\n")
    todays_logs = [l for l in st.session_state.scan_log if l['time'] and l['signal'] == 'BUY']
    if todays_logs:
        lines.append("🌟 *Top AI Picks Today (highest scores):*")
        for p in sorted(todays_logs, key=lambda x: x['score'], reverse=True)[:5]:
            lines.append(f"   {p['stock']} ({p['market']}/{p['mode']}) — Score {p['score']} @ {AGENT_CURRENCY.get(p['market'], '')}{p['price']:.2f}")
        lines.append("")
    if "NSE" in active_markets:
        try:
            sectors = get_sector_performance("NSE", period="1d")
            if sectors:
                lines.append("🔥 *Sector Movers Today (NSE):*")
                for s in sectors[:3]: lines.append(f"   {s['strength']} {s['sector']}: {s['avg_change_pct']:+.2f}%")
                lines.append("")
        except: pass
    lines.append(f"🕒 Generated {now.strftime('%H:%M:%S')} IST")
    return "\n".join(lines)

def chat_assistant_respond(query, active_markets):
    q = query.lower().strip()
    detected_symbol, detected_market = None, None
    for mkt in active_markets:
        for sym in MARKET_UNIVERSE[mkt]:
            if sym.replace(".NS", "").replace("-USD", "").lower() in q or sym.lower() in q:
                detected_symbol, detected_market = sym, mkt; break
        if detected_symbol: break

    if any(w in q for w in ["portfolio", "balance", "kitna paisa", "kitna profit", "total p&l", "p&l", "kaisa chal"]):
        reply = ["📊 **Portfolio Summary:**\n"]
        for mkt in active_markets:
            agent, cur = st.session_state[AGENT_KEYS[mkt]], AGENT_CURRENCY[mkt]
            val = agent['balance'] + sum(agent['entry_price'].get(k, 0) * qy for k, qy in agent['positions'].items() if qy > 0)
            pnl_ = val - 100000.0
            reply.append(f"**{mkt}:** {cur}{val:,.0f} ({'+' if pnl_>=0 else ''}{pnl_:,.0f}, {pnl_/1000:+.2f}%)")
        return "\n".join(reply)
    if any(w in q for w in ["win rate", "winning", "success rate", "kitne trade"]):
        reply = ["🏆 **Win-Rate Summary:**\n"]
        for mkt in active_markets:
            for md in ["Intraday", "Swing"]:
                wr = calc_weekly_winrate(st.session_state[AGENT_KEYS[mkt]]['trade_log'], mode_filter=md)
                if wr and wr['trades'] > 0: reply.append(f"**{mkt} {md}:** {wr['win_rate']}% ({wr['wins']}W/{wr['losses']}L, {wr['trades']} trades this week)")
        return "\n".join(reply) if len(reply) > 1 else "Abhi tak koi completed trades nahi hain."
    if detected_symbol:
        currency_s = AGENT_CURRENCY[detected_market]
        mode_for_q = "Swing" if "swing" in q else "Intraday" if "intraday" in q else "Swing"
        sig, price, score, status, signals = advanced_engine(detected_symbol, get_data(detected_symbol, mode_for_q), mode_for_q)
        reply = [f"📈 **{detected_symbol}** ({mode_for_q} analysis):\n", f"Current Price: {currency_s}{price:.2f}", f"AI Signal: {'🟢' if sig=='BUY' else '🔴' if sig=='SELL' else '⚪'} **{sig}** (Score: {score}/100)"]
        bull, bear = [s for s in signals if s[1]=="BULLISH"], [s for s in signals if s[1]=="BEARISH"]
        if bull: reply.append(f"\n✅ Bullish factors: " + ", ".join([f"{s[0]} ({s[2]})" for s in bull[:3]]))
        if bear: reply.append(f"⚠️ Bearish factors: " + ", ".join([f"{s[0]} ({s[2]})" for s in bear[:3]]))
        agent = st.session_state[AGENT_KEYS[detected_market]]
        for md in ["Intraday", "Swing"]:
            qty = agent['positions'].get(f"{detected_symbol}__{md}", 0)
            if qty > 0:
                entry = agent['entry_price'].get(f"{detected_symbol}__{md}", 0)
                reply.append(f"\n💼 AI ka open position hai ({md}): {qty} shares @ {currency_s}{entry:.2f} entry, unrealized P&L: {currency_s}{(price - entry) * qty:+,.2f}")
        if mode_for_q == "Swing" and "-USD" not in detected_symbol:
            fund = get_fundamentals(detected_symbol)
            if fund.get('available'): reply.append(f"\n📋 Fundamentals: {fund.get('summary','N/A')}")
        return "\n".join(reply)
    if any(w in q for w in ["kyu liya", "kyun kharida", "why buy", "why sell", "reason"]): return "Kisi specific stock ka naam batao (e.g. 'RELIANCE kyu liya?') — main uski poori AI reasoning dikha dunga."
    if any(w in q for w in ["sector", "kaunsa sector", "which sector"]):
        if "NSE" in active_markets:
            sectors = get_sector_performance("NSE", period="5d")
            if sectors: return "\n".join(["🔥 **Sector Performance (5 days, NSE):**\n"] + [f"{s['strength']} **{s['sector']}**: {s['avg_change_pct']:+.2f}%" for s in sectors[:6]])
        return "Sector data abhi available nahi hai. NSE market ko active karo."
    if any(w in q for w in ["open position", "kya khareeda", "current holding", "kitne stock"]):
        reply, found_any = ["💼 **Open Positions:**\n"], False
        for mkt in active_markets:
            agent, cur = st.session_state[AGENT_KEYS[mkt]], AGENT_CURRENCY[mkt]
            for pos_key, qty in {k: v for k, v in agent['positions'].items() if v > 0}.items():
                reply.append(f"**{pos_key.split('__')[0]}** ({mkt}/{agent['entry_mode'].get(pos_key, '-')}): {qty} qty @ {cur}{agent['entry_price'].get(pos_key, 0):.2f}")
                found_any = True
        return "\n".join(reply) if found_any else "Abhi koi open position nahi hai."
    return "Main yeh sawal samajh nahi paya 🤔 Try karo:\n\n- *\"RELIANCE ka analysis?\"*\n- *\"Portfolio kaisa chal raha hai?\"*\n- *\"Win rate kya hai?\"*\n- *\"Kaunsa sector garam hai?\"*\n- *\"Open positions dikhao\"*"

    # ================= DRAWDOWN PROTECTION =================
def check_drawdown_protection(agent, mode_, streak_limit, pause_hours):
    if agent.get('paused_until'):
        try:
            paused_until_dt = datetime.fromisoformat(agent['paused_until'])
            if now < paused_until_dt:
                return True, agent.get('pause_reason', 'Drawdown protection active')
            else:
                agent['paused_until'] = None
                agent['pause_reason'] = ""
        except:
            agent['paused_until'] = None

    # Check recent trades that have a P&L
    sells = [t for t in agent['trade_log'] if 'pnl' in t and t.get('mode') == mode_]
    if len(sells) < streak_limit:
        return False, ""

    recent = sells[-streak_limit:]
    if all(t['pnl'] <= 0 for t in recent):
        pause_until = now + timedelta(hours=pause_hours)
        agent['paused_until'] = pause_until.isoformat()
        agent['pause_reason'] = f"{streak_limit} consecutive losses in {mode_} — auto-paused for {pause_hours}h"
        return True, agent['pause_reason']

    return False, ""
    
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
        
        pos_key = f"{stk}__{mode_}"
        qty = agent['positions'].get(pos_key, 0)

        if sig == "BUY" and qty == 0 and price > 0 and can_trade_now and score >= min_score_threshold and not is_paused:
            mtf_aligned, mtf_detail = (True, "MTF off")
            if mtf_confirm_on: mtf_aligned, mtf_detail = get_higher_timeframe_trend(stk, mode_)
            if mtf_aligned:
                alloc_pct = (max_alloc/100) if (score >= 88 and is_bull) else (max_alloc*0.66/100) if is_bull else (max_alloc*0.33/100)
                invest = min(sizing_base, agent['balance']) * alloc_pct
                q = int(invest / price) if price > 0 else 0
                if q > 0 and invest <= agent['balance']:
                    agent['positions'][pos_key] = q
                    agent['balance'] -= q * price
                    agent['entry_price'][pos_key] = price
                    agent['highest_price'][pos_key] = price
                    agent['entry_mode'][pos_key] = mode_
                    target, stop = price * (1 + tg_pct), price * (1 - sl_pct)
                    agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'BUY', 'price': price, 'qty': q, 'score': score, 'mode': mode_, 'market': market, 'mtf_confirm': mtf_detail})
                    buy_count += 1
                    if telegram_enabled:
                        msg = build_buy_telegram(market, mode_, stk, price, target, stop, score, signals, currency)
                        if mtf_confirm_on: msg += f"\n\n🎯 *Multi-Timeframe Check:* {mtf_detail}"
                        send_telegram(msg)

        elif sig == "SELL" and qty > 0 and price > 0:
            entry = agent['entry_price'].get(pos_key, price)
            pnl_t = (price - entry) * qty
            agent['balance'] += qty * price
            agent['positions'][pos_key] = 0
            agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'SELL', 'price': price, 'qty': qty, 'pnl': round(pnl_t, 2), 'mode': mode_, 'market': market})
            sell_count += 1
            for k in ['entry_price', 'highest_price', 'entry_mode']: agent[k].pop(pos_key, None)
            if telegram_enabled: send_telegram(build_sell_telegram(market, mode_, stk, price, entry, qty, pnl_t, "AI signal reversed", currency))

    for pos_key, q in list(agent['positions'].items()):
        if q <= 0 or not pos_key.endswith(f"__{mode_}"): continue
        stk = pos_key.replace(f"__{mode_}", "")
        df2 = get_data(stk, mode_)
        if df2 is None or len(df2) == 0: continue
        cp = float(df2['Close'].iloc[-1])
        if pos_key not in agent['highest_price']: agent['highest_price'][pos_key] = agent['entry_price'].get(pos_key, cp)
        if cp > agent['highest_price'][pos_key]: agent['highest_price'][pos_key] = cp
        
        trail_sl, entry = agent['highest_price'][pos_key] * (1 - sl_pct), agent['entry_price'].get(pos_key, cp)
        target_p = entry * (1 + tg_pct)
        exit_reason = "End-of-day square-off (Intraday auto-exit)" if mode_ == "Intraday" and market in ("NSE",) and now.hour == 15 and now.minute >= 20 else f"Trailing Stop Loss hit at {currency}{trail_sl:.2f}" if cp <= trail_sl else f"Target achieved at {currency}{target_p:.2f}" if cp >= target_p else None

        if exit_reason:
            pnl_t = (cp - entry) * q
            agent['balance'] += q * cp
            agent['positions'][pos_key] = 0
            agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'SELL', 'price': cp, 'qty': q, 'pnl': round(pnl_t, 2), 'mode': mode_, 'market': market})
            sell_count += 1
            for k in ['entry_price', 'highest_price', 'entry_mode']: agent[k].pop(pos_key, None)
            if telegram_enabled: send_telegram(build_sell_telegram(market, mode_, stk, cp, entry, q, pnl_t, exit_reason, currency))

    if len(st.session_state.scan_log) > 500: st.session_state.scan_log = st.session_state.scan_log[-500:]
    return sorted(results, key=lambda x: x[2], reverse=True), buy_count, sell_count

def play_alert_sound(kind="buy"):
    freq_html = """<script>try{const ctx=new (window.AudioContext||window.webkitAudioContext)();function beep(f,s,d){const osc=ctx.createOscillator();const gain=ctx.createGain();osc.connect(gain);gain.connect(ctx.destination);osc.frequency.value=f;osc.type='sine';gain.gain.setValueAtTime(0.18,ctx.currentTime+s);gain.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+s+d);osc.start(ctx.currentTime+s);osc.stop(ctx.currentTime+s+d);}beep(880,0,0.15);beep(1100,0.18,0.18);}catch(e){}</script>""" if kind == "buy" else """<script>try{const ctx=new (window.AudioContext||window.webkitAudioContext)();function beep(f,s,d){const osc=ctx.createOscillator();const gain=ctx.createGain();osc.connect(gain);gain.connect(ctx.destination);osc.frequency.value=f;osc.type='sine';gain.gain.setValueAtTime(0.18,ctx.currentTime+s);gain.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+s+d);osc.start(ctx.currentTime+s);osc.stop(ctx.currentTime+s+d);}beep(420,0,0.30);}catch(e){}</script>"""
    st.components.v1.html(freq_html, height=0, width=0)

if AUTOREFRESH_AVAILABLE and st.session_state.agent_running: st_autorefresh(interval=5*60*1000, key="agent_autorefresh")
# ===================== HEADER =====================
st.markdown("""
<div class="main-header">
    <h1>⚡ QUANTEDGE AI v9.0</h1>
    <p>KELLY CRITERION + HONEST BACKTESTER — NSE · CRYPTO · US</p>
</div>
""", unsafe_allow_html=True)

do_scan = True if st.session_state.agent_running else False
manual_scan = st.button("🔍 Scan Now (manual)", type="secondary") if not st.session_state.agent_running else False

agent_results = {}
total_buys_this_scan, total_sells_this_scan = 0, 0

if do_scan or manual_scan:
    with st.spinner("🤖 AI Agent scanning markets..."):
        for mkt in ACTIVE_MARKETS:
            agent_results[mkt] = {}
            for md in ACTIVE_MODES:
                results_list, n_buys, n_sells = run_ai_agent_for_market(mkt, md, min_score, max_alloc_pct, telegram_on, mtf_confirm_on=mtf_confirm, dd_on=dd_protection_on, dd_streak=dd_streak_limit, dd_hours=dd_pause_hours, compounding=compounding_on)
                agent_results[mkt][md] = results_list
                total_buys_this_scan += n_buys
                total_sells_this_scan += n_sells
    st.session_state.last_scan_time = now.strftime('%H:%M:%S')

    if sound_alert_on and total_buys_this_scan > 0: play_alert_sound("buy")
    elif sound_alert_on and total_sells_this_scan > 0: play_alert_sound("sell")

    all_current_prices = {}
    for mkt, modes_dict in agent_results.items():
        for md, results in modes_dict.items():
            for stk, sig, sc, pr, msg, sigs in results:
                if pr > 0: all_current_prices[stk] = pr
    triggered, st.session_state.price_alerts = check_alerts(st.session_state.price_alerts, all_current_prices)
    if triggered:
        st.session_state.triggered_alerts.extend(triggered)
        if sound_alert_on: play_alert_sound("buy")

def agent_summary(market):
    agent = st.session_state[AGENT_KEYS[market]]
    unrealized_pnl, open_count = 0, 0
    for pos_key, qty in agent['positions'].items():
        if qty == 0: continue
        open_count += 1
        entry, direction = agent['entry_price'].get(pos_key, 0), agent['position_direction'].get(pos_key, "LONG")
        try:
            df_tmp = get_data(pos_key.split("__")[0], "Intraday")
            if df_tmp is not None and len(df_tmp) > 0:
                cp = float(df_tmp['Close'].iloc[-1])
                unrealized_pnl += (cp - entry) * qty if direction == "LONG" else (entry - cp) * abs(qty)
        except: pass
    val = agent['balance'] + unrealized_pnl
    return val, val - 100000.0, open_count, agent['balance']

def agent_today_pnl(market):
    agent = st.session_state[AGENT_KEYS[market]]
    today_pnls = [t.get('pnl', 0) for t in agent['trade_log'] if t.get('full_time') and t['full_time'].date() == now.date() and 'pnl' in t]
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

overall_color, today_color = '#00ff88' if combined_pnl_inr >= 0 else '#ff4444', '#00ff88' if combined_today_inr >= 0 else '#ff4444'

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
  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-top:18px;">
    <div style="background:#0a0e1a55; border:1px solid #00d4ff15; border-radius:10px; padding:10px 12px;">
      <div style="font-size:0.75rem; color:#7a8fa6;">🇮🇳 NSE</div>
      <div style="font-size:1.05rem; font-weight:700; color:#fff;">₹{nse_val:,.0f}</div>
      <div style="font-size:0.78rem; color:{'#00ff88' if nse_pnl>=0 else '#ff4444'};">{'+' if nse_pnl>=0 else ''}{nse_pnl:,.0f} total | Today: {'+' if nse_today_pnl>=0 else ''}{nse_today_pnl:,.0f}</div>
      <div style="font-size:0.72rem; color:#555;">{nse_pos} open positions</div>
    </div>
    <div style="background:#0a0e1a55; border:1px solid #00d4ff15; border-radius:10px; padding:10px 12px;">
      <div style="font-size:0.75rem; color:#7a8fa6;">🪙 Crypto</div>
      <div style="font-size:1.05rem; font-weight:700; color:#fff;">${crypto_val:,.0f}</div>
      <div style="font-size:0.78rem; color:{'#00ff88' if crypto_pnl>=0 else '#ff4444'};">{'+' if crypto_pnl>=0 else ''}{crypto_pnl:,.0f} total | Today: {'+' if crypto_today_pnl>=0 else ''}{crypto_today_pnl:,.0f}</div>
      <div style="font-size:0.72rem; color:#555;">{crypto_pos} open positions</div>
    </div>
    <div style="background:#0a0e1a55; border:1px solid #00d4ff15; border-radius:10px; padding:10px 12px;">
      <div style="font-size:0.75rem; color:#7a8fa6;">🇺🇸 US</div>
      <div style="font-size:1.05rem; font-weight:700; color:#fff;">${us_val:,.0f}</div>
      <div style="font-size:0.78rem; color:{'#00ff88' if us_pnl>=0 else '#ff4444'};">{'+' if us_pnl>=0 else ''}{us_pnl:,.0f} total | Today: {'+' if us_today_pnl>=0 else ''}{us_today_pnl:,.0f}</div>
      <div style="font-size:0.72rem; color:#555;">{us_pos} open positions</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

c1,c2,c3 = st.columns(3)
c1.metric("Total Open Positions", total_open_positions)
c2.metric("Alerts Set", len(st.session_state.price_alerts))
c3.metric("AI Status", "🟢 LIVE" if st.session_state.agent_running else "⏸️ PAUSED")
st.divider()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17 = st.tabs(["🤖 AI Agent Radar", "📊 Chart + S&R", "🔮 Price Prediction", "🏆 Win-Rate & Leaderboard", "📈 Options Chain", "⚠️ Risk Calculator", "🔔 Price Alerts", "📰 News", "🧪 Backtest", "💼 Portfolio (3 Agents)", "🧠 AI Reasoning Log", "💬 AI Chat Assistant", "🗺️ Sector Heatmap", "📈 Correlation Checker", "📝 Daily Summary", "🎯 Strategy Builder", "📊 Kelly + Honest Backtest"])

with tab1: st.markdown("### 🤖 Live Signals & Executions")

with tab3:
    st.markdown("### 🔮 AI Price Prediction")
    pred_sym = st.selectbox("Stock:", MARKET_UNIVERSE["NSE"], key="pred_sym_v9")
    if st.button("🔮 Predict"):
        res = predict_price(pred_sym)
        if res and 1 in res:
            r = res[1]
            st.markdown(f"**{r['direction']}** | Confidence: {r['confidence']}% | Target: {r['pred_price']} ({r['pred_return']}%)")
        else: st.warning("Not enough data.")

with tab10:
    st.markdown("### 💼 Live Portfolio — 3 Agents")
    for mkt in ACTIVE_MARKETS:
        agent, cur = st.session_state[AGENT_KEYS[mkt]], AGENT_CURRENCY[mkt]
        st.markdown(f"## {mkt} Agent")
        active = {k:q for k,q in agent['positions'].items() if q != 0}
        if active:
            st.dataframe(pd.DataFrame([{"Stock":k.split("__")[0], "Qty":q, "Entry":agent['entry_price'].get(k, 0)} for k,q in active.items()]))
        else: st.caption("No open positions.")
        st.divider()

with tab17:
    st.markdown("### 📊 Kelly Criterion Sizing + Honest Backtester")
    st.info("🎲 **Kelly Criterion**: Mathematically optimal position sizing based on win-rate and payoff ratio. Safe capped at 25%.")
    kc1, kc2, kc3 = st.columns(3)
    for mkt, col in [("NSE", kc1), ("Crypto", kc2), ("US", kc3)]:
        agent = st.session_state[AGENT_KEYS[mkt]]
        with col:
            st.markdown(f"**{mkt}**")
            for md in ["Intraday", "Swing"]:
                kelly_f = calc_kelly_fraction(agent, md)
                sells = [t for t in agent['trade_log'] if t.get('mode') == md and 'pnl' in t]
                st.caption(f"{md}: **{kelly_f * 100:.1f}%** (WR: {len([t for t in sells if t['pnl'] > 0]) / len(sells) * 100:.0f}% if sells else 'No trades yet')")
    st.divider()
    st.markdown("#### 🧪 Strategy Backtester")
    bt_market = st.selectbox("Market:", ACTIVE_MARKETS if ACTIVE_MARKETS else ["NSE"], key="backtest_mkt")
    bt_mode = st.selectbox("Mode:", ["Intraday", "Swing"], key="backtest_mode")
    bt_period = st.selectbox("Historical Period:", ["3mo", "6mo", "1y", "2y"], value="1y", key="backtest_period")
    if st.button("🚀 Run Full Backtest", type="primary"):
        with st.spinner(f"🧪 Backtesting {bt_mode} on {bt_market} stocks..."):
            bt_symbols = MARKET_UNIVERSE.get(bt_market, [])[:15]
            backtest_results = [result for sym in bt_symbols if (result := backtest_strategy(sym, bt_mode, bt_period)) and result['total_trades'] >= 3]
            if backtest_results:
                passed = len([r for r in backtest_results if r['passed']])
                st.success(f"✅ Backtested {len(backtest_results)} stocks")
                st.metric("Passed Stocks", f"{passed}/{len(backtest_results)}")
                passed_results = [r for r in backtest_results if r['passed']]
                if passed_results:
                    st.dataframe(pd.DataFrame([{"Stock": r['symbol'], "Trades": r['total_trades'], "Win-Rate": f"{r['win_rate']}%", "Total P&L": f"₹{r['total_pnl']:+,.0f}", "Status": "✅ PASS"} for r in sorted(passed_results, key=lambda x: x['win_rate'], reverse=True)]), use_container_width=True, hide_index=True)
                else: st.warning("❌ No stocks passed the >50% win-rate threshold")
            else: st.warning("❌ No valid backtests — try more symbols or longer period")

# ================= FOOTER =================
st.divider()
st.caption("⚡ QuantEdge AI v9.0 — Kelly Criterion + Honest Backtester | NSE India · Crypto · US Stocks | Paper Trading Only")
st.caption("⚠️ Educational purpose only. AI decisions simulated hain — real money invest karne se pehle SEBI/financial advisor se salah lein.")
    
