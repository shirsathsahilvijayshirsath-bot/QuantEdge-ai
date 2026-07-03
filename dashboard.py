# ================= QUANTEDGE AI v9.0 - KELLY + RESET-LEARN + BACKTESTER =================
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

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

st.set_page_config(page_title="QuantEdge AI v9.0 — Kelly + Backtester", layout="wide", page_icon="⚡", initial_sidebar_state="expanded")

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
    .leaderboard-gold   { background:linear-gradient(135deg,#2a1f00,#3d2e00); border-left:4px solid #ffd700; border-radius:8px; padding:10px 14px; margin:4px 0; }
    .leaderboard-silver { background:linear-gradient(135deg,#1a1f2e,#222840); border-left:4px solid #c0c0c0; border-radius:8px; padding:10px 14px; margin:4px 0; }
    .leaderboard-bronze { background:linear-gradient(135deg,#1a1000,#2a1800); border-left:4px solid #cd7f32; border-radius:8px; padding:10px 14px; margin:4px 0; }
    .pred-box  { background:#0d1b2a; border:1px solid #00d4ff22; border-radius:10px; padding:16px; text-align:center; }
</style>
""", unsafe_allow_html=True)

# ================= AUTH =================
MY_PASSWORD = "QuantEdge2026"
def check_password():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if not st.session_state.auth:
        st.markdown('<div class="main-header"><h1>⚡ QUANTEDGE AI v9.0</h1><p>SECURE TRADING TERMINAL</p></div>', unsafe_allow_html=True)
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

if not check_password(): st.stop()

# ================= CONSTANTS =================
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)
TOKEN   = "8629163881:AAHrO4n9KpDNT0tMR1DoRvXeJeZ5VEIWCCA"
CHAT_ID = "7602586865"

# ================= MARKET UNIVERSES =================
NSE_STOCKS = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","HINDUNILVR.NS","HDFC.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS","ITC.NS","LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","TITAN.NS","ULTRACEMCO.NS","WIPRO.NS","SUNPHARMA.NS","TECHM.NS","NESTLEIND.NS","BAJFINANCE.NS","POWERGRID.NS","NTPC.NS","ONGC.NS","JSWSTEEL.NS","TATASTEEL.NS","HCLTECH.NS","M&M.NS","BAJAJFINSV.NS","ADANIENT.NS","ADANIPORTS.NS","ADANIGREEN.NS","DMART.NS","SIEMENS.NS","PIDILITIND.NS","HAVELLS.NS","MARICO.NS","DABUR.NS","GODREJCP.NS","MUTHOOTFIN.NS","CHOLAFIN.NS","RECLTD.NS","PFC.NS","IRCTC.NS","INDHOTEL.NS","TRENT.NS","VEDL.NS","HINDALCO.NS","COALINDIA.NS","GRASIM.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS","EICHERMOT.NS","TVSMOTOR.NS","TATAMOTORS.NS","MOTHERSON.NS","BOSCHLTD.NS","MRF.NS","APOLLOHOSP.NS","ZOMATO.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","DELHIVERY.NS","HDFCLIFE.NS","SBILIFE.NS","ICICIGI.NS","MFSL.NS","STARHEALTH.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","PHOENIXLTD.NS","PRESTIGE.NS","PERSISTENT.NS","LTIM.NS","TATAELXSI.NS","MPHASIS.NS","COFORGE.NS","HAPPSTMNDS.NS","NETWEB.NS","KPIT.NS","CYIENT.NS","MASTEK.NS","SUZLON.NS","CESC.NS","TORNTPOWER.NS","TATAPOWER.NS","ADANIPOWER.NS","HAL.NS","BEL.NS","BHEL.NS","COCHINSHIP.NS","MAZDOCK.NS","GRSE.NS","TORNTPHARM.NS","ZYDUSLIFE.NS","AUROPHARMA.NS","ALKEM.NS","IPCALAB.NS","MAXHEALTH.NS","FORTIS.NS","METROPOLIS.NS","LALPATHLAB.NS","THYROCARE.NS","BRITANNIA.NS","VBL.NS","JUBLFOOD.NS","DEVYANI.NS","SAPPHIRE.NS","ABB.NS","CUMMINSIND.NS","THERMAX.NS","BHARAT FORGE.NS","KALYANKJIL.NS","SRF.NS","AARTIIND.NS","DEEPAKNTR.NS","PIIND.NS","UPL.NS","BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","RBLBANK.NS"]
CRYPTO = ["BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD","ADA-USD","AVAX-USD","DOGE-USD","MATIC-USD","DOT-USD","LINK-USD","UNI-USD","ATOM-USD","LTC-USD","BCH-USD","ALGO-USD","XLM-USD","FIL-USD","NEAR-USD","APT-USD","ARB-USD","OP-USD","INJ-USD","SUI-USD","TIA-USD"]
US_STOCKS = ["AAPL","MSFT","GOOGL","AMZN","NVDA","TSLA","META","AMD","NFLX","JPM","BAC","V","WMT","DIS","PLTR","UBER","COIN","SNOW","SHOP","CRWD","ABNB","RBLX","HOOD","ARM","SMCI","MU","INTC","QCOM","AVGO","TSM","BABA","JD","PDD","NIO","XPEV","LI","RIVN","LCID","F","GM","XOM","CVX","COP","SLB","HAL","GS","MS","C","WFC","AXP","PFE","MRNA","JNJ","ABBV","LLY","UNH","CVS","CI","HUM","ANTM"]

NIFTY_INDEX, SP500_INDEX, BTC_BENCH = "^NSEI", "^GSPC", "BTC-USD"
SECTOR_MAP = {
    "NSE": {"IT": ["INFY.NS","TCS.NS","HCLTECH.NS","WIPRO.NS","TECHM.NS"], "Banking": ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS"], "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","EICHERMOT.NS"]},
    "Crypto": {"Layer1": ["BTC-USD","ETH-USD","SOL-USD","ADA-USD"], "Exchange/DeFi": ["BNB-USD","UNI-USD","LINK-USD"]},
    "US": {"Big Tech": ["AAPL","MSFT","GOOGL","AMZN","META"], "Semiconductors": ["NVDA","AMD","MU","INTC","QCOM"]}
}

# ================= SESSION STATE =================
def make_agent_state():
    return {"balance": 100000.0, "starting_capital": 100000.0, "positions": {}, "entry_price": {}, "highest_price": {}, "lowest_price": {}, "entry_mode": {}, "position_direction": {}, "trade_log": [], "paused_until": None, "pause_reason": "", "reset_count": 0, "lessons_learned": [], "kelly_fractions": {}}

DEFAULTS = {"agent_nse": make_agent_state(), "agent_crypto": make_agent_state(), "agent_us": make_agent_state(), "price_alerts": [], "triggered_alerts": [], "agent_running": True, "last_scan_time": None, "scan_log": [], "daily_summaries": []}
for k, v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

AGENT_KEYS, AGENT_CURRENCY = {"NSE": "agent_nse", "Crypto": "agent_crypto", "US": "agent_us"}, {"NSE": "₹", "Crypto": "$", "US": "$"}

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## ⚡ QuantEdge AI v9.0")
    st.session_state.agent_running = st.toggle("🟢 AI Agent ACTIVE", value=st.session_state.agent_running)
    st.divider()
    manage_nse, manage_crypto, manage_us = st.checkbox("🇮🇳 NSE", True), st.checkbox("🪙 Crypto", True), st.checkbox("🇺🇸 US", True)
    run_intraday, run_swing = st.checkbox("⚡ Intraday", True), st.checkbox("📈 Swing", True)
    st.divider()
    ic1, ic2 = st.columns(2)
    with ic1: INTRA_SL, INTRA_TG = st.slider("Intra SL %", 0.5, 3.0, 1.0)/100, st.slider("Intra TG %", 1.0, 5.0, 2.5)/100
    with ic2: SWING_SL, SWING_TG = st.slider("Swing SL %", 1.0, 8.0, 3.0)/100, st.slider("Swing TG %", 3.0, 20.0, 8.0)/100
    telegram_on = st.toggle("📲 Telegram Alerts", True)
    sound_alert_on = st.toggle("🔊 Sound Alerts", True)
    min_score, max_alloc_pct = st.slider("Min Signal Score", 50, 95, 75), st.slider("Max % per trade", 5, 30, 15)
    mtf_confirm = st.toggle("🎯 MTF Confirm", True)
    dd_protection_on = st.toggle("Auto-pause on losing streak", True)
    dd_streak_limit, dd_pause_hours = st.slider("Pause losses streak", 2, 8, 4), st.slider("Pause hours", 1, 48, 12)
    compounding_on = st.toggle("Auto-Compound", False)
    kelly_on = st.toggle("Use Kelly Criterion", True)

ACTIVE_MARKETS = [m for m, b in zip(["NSE", "Crypto", "US"], [manage_nse, manage_crypto, manage_us]) if b]
ACTIVE_MODES = [m for m, b in zip(["Intraday", "Swing"], [run_intraday, run_swing]) if b]
MARKET_UNIVERSE = {"NSE": NSE_STOCKS, "Crypto": CRYPTO, "US": US_STOCKS}
MARKET_BENCH = {"NSE": NIFTY_INDEX, "Crypto": BTC_BENCH, "US": SP500_INDEX}
RISK_PARAMS = {"Intraday": (INTRA_SL, INTRA_TG), "Swing": (SWING_SL, SWING_TG)}

def market_can_trade(market, mode_):
    if mode_ != "Intraday" or market in ["Crypto", "US"]: return True
    return not (now.hour > 14 or (now.hour == 14 and now.minute >= 30))

def send_telegram(msg):
    if telegram_on:
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=8)
        except: pass

@st.cache_data(ttl=90, show_spinner=False)
def get_data(symbol, current_mode):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="5d", interval="5m") if current_mode == "Intraday" else t.history(period="1y")
        return df.dropna() if not df.empty else None
    except: return None

def get_market_regime(bench, current_mode):
    try:
        df = yf.Ticker(bench).history(period="6mo" if current_mode == "Swing" else "5d", interval="1d" if current_mode == "Swing" else "5m")
        df['SMA50'] = df['Close'].rolling(50).mean()
        bull = df['Close'].iloc[-1] > df['SMA50'].iloc[-1]
        return bull, f"{'Bullish' if bull else 'Bearish'}", abs((df['Close'].iloc[-1] - df['SMA50'].iloc[-1])/df['SMA50'].iloc[-1]*100)
    except: return True, "Unknown", 0

def get_higher_timeframe_trend(symbol, current_mode):
    try:
        if current_mode == "Intraday":
            df5 = yf.Ticker(symbol).history(period="5d", interval="5m")
            if df5.empty: return True, "Skip"
            df1h = df5['Close'].resample('1h').last().dropna()
            hourly_bull = df1h.ewm(span=5).mean().iloc[-1] > df1h.ewm(span=10).mean().iloc[-1]
            dfd = yf.Ticker(symbol).history(period="1mo")
            daily_bull = dfd['Close'].iloc[-1] > dfd['Close'].rolling(10).mean().iloc[-1] if not dfd.empty else True
            return (hourly_bull and daily_bull), f"1H:{'🟢' if hourly_bull else '🔴'} D:{'🟢' if daily_bull else '🔴'}"
        else:
            dfw = yf.Ticker(symbol).history(period="1y", interval="1wk")
            weekly_bull = dfw['Close'].iloc[-1] > dfw['Close'].rolling(10).mean().iloc[-1] if not dfw.empty else True
            return weekly_bull, f"W:{'🟢' if weekly_bull else '🔴'}"
    except: return True, "MTF Failed"

def compute_indicators(df, current_mode):
    c = df['Close']
    df['SMA_20'], df['SMA_50'] = c.rolling(20).mean(), c.rolling(50).mean()
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    df['RSI'] = 100 - (100 / (1 + c.diff().clip(lower=0).rolling(14).mean() / (-c.diff().clip(upper=0)).rolling(14).mean() + 1e-9))
    df['MACD'] = c.ewm(span=12).mean() - c.ewm(span=26).mean()
    df['MacdSig'] = df['MACD'].ewm(span=9).mean()
    df['MacdH'] = df['MACD'] - df['MacdSig']
    df['BB_Mid'], df['BB_Std'] = c.rolling(20).mean(), c.rolling(20).std()
    df['BB_Up'], df['BB_Low'] = df['BB_Mid'] + df['BB_Std']*2, df['BB_Mid'] - df['BB_Std']*2
    df['BB_pct'] = (c - df['BB_Low']) / (df['BB_Up'] - df['BB_Low'] + 1e-9)
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['Stoch_K'] = ((c - df['Low'].rolling(14).min()) / (df['High'].rolling(14).max() - df['Low'].rolling(14).min() + 1e-9)) * 100
    df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
    if current_mode == "Intraday":
        df['Date'] = df.index.date
        df['VWAP'] = df.groupby('Date').apply(lambda x: (x['Volume']*(x['High']+x['Low']+x['Close'])/3).cumsum() / (x['Volume'].cumsum()+1e-9)).reset_index(level=0, drop=True)
    return df.dropna()

def get_sr_levels(df):
    try:
        df = df.tail(120)
        h, l, c = df['High'].values, df['Low'].values, df['Close'].values
        pivot = (h[-1] + l[-1] + c[-1]) / 3
        return {"pivot": round(pivot, 2), "resistances": [round(2*pivot - l[-1], 2), round(pivot + (h[-1] - l[-1]), 2)], "supports": [round(2*pivot - h[-1], 2), round(pivot - (h[-1] - l[-1]), 2)], "current": round(c[-1], 2)}
    except: return None

@st.cache_data(ttl=900, show_spinner=False)
def get_sector_performance(market, period="5d"):
    results = []
    for sector, symbols in SECTOR_MAP.get(market, {}).items():
        changes = [(yf.Ticker(s).history(period=period)['Close'].iloc[-1]/yf.Ticker(s).history(period=period)['Close'].iloc[0]-1)*100 for s in symbols[:8] if not yf.Ticker(s).history(period=period).empty]
        if changes: results.append({"sector": sector, "avg_change_pct": round(np.mean(changes), 2), "strength": "🔥 Hot" if np.mean(changes)>1 else "🧊 Cold"})
    return sorted(results, key=lambda x: x['avg_change_pct'], reverse=True)

@st.cache_data(ttl=1800, show_spinner=False)
def calc_correlation(symbol_a, symbol_b, period="6mo"):
    try:
        df_a, df_b = yf.Ticker(symbol_a).history(period=period)['Close'].pct_change().dropna(), yf.Ticker(symbol_b).history(period=period)['Close'].pct_change().dropna()
        df_a.index, df_b.index = df_a.index.tz_localize(None) if df_a.index.tz else df_a.index, df_b.index.tz_localize(None) if df_b.index.tz else df_b.index
        merged = pd.concat([df_a, df_b], axis=1, join='inner')
        return {"correlation": round(float(merged.iloc[:,0].corr(merged.iloc[:,1])), 3), "series": merged}
    except: return None

@st.cache_resource
def get_model(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2y")
        if len(df) < 200: return None, None
        c = df['Close']
        df['r1'], df['r5'], df['rsi'] = c.pct_change(1), c.pct_change(5), 100-(100/(1+c.diff().clip(lower=0).rolling(14).mean()/(-c.diff().clip(upper=0)).rolling(14).mean()+1e-9))
        df['macd'], df['bb_pos'] = (c.ewm(span=12).mean()-c.ewm(span=26).mean())/c, (c-c.rolling(20).mean())/(c.rolling(20).std()*2+1e-9)
        df['label'] = (c.shift(-5)/c-1 > 0.02).astype(int)
        df = df.dropna()
        X = df[['r1','r5','rsi','macd','bb_pos']]
        sc = StandardScaler()
        mdl = GradientBoostingClassifier(n_estimators=100, max_depth=3).fit(sc.fit_transform(X), df['label'])
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
        price, rsi, sma20, sma50, macd, macd_s, bb_pct, cur_v, avg_v = df['Close'].iloc[-1], df['RSI'].iloc[-1], df['SMA_20'].iloc[-1], df['SMA_50'].iloc[-1], df['MACD'].iloc[-1], df['MacdSig'].iloc[-1], df['BB_pct'].iloc[-1], df['Volume'].iloc[-1], df['Vol_SMA'].iloc[-1]
        vwap = df['VWAP'].iloc[-1] if 'VWAP' in df.columns else None
        
        mdl, sc = get_model(symbol)
        ml_conf = 0
        if mdl and sc:
            try: ml_conf = int(mdl.predict_proba(sc.transform([[df['Close'].pct_change(1).iloc[-1], df['Close'].pct_change(5).iloc[-1], rsi, macd/price, bb_pct-0.5]]))[0][1] * 100)
            except: pass

        score = (ml_conf - 50) * 0.6 if ml_conf > 0 else 0
        signals = []
        if rsi < 35: score += 15; signals.append(("RSI", "BULLISH", "Oversold"))
        elif rsi > 75: score -= 15; signals.append(("RSI", "BEARISH", "Overbought"))
        if price > sma20 > sma50: score += 15; signals.append(("Trend", "BULLISH", "Price>SMA20>50"))
        elif price < sma50: score -= 10; signals.append(("Trend", "BEARISH", "Price<SMA50"))
        if macd > macd_s: score += 10; signals.append(("MACD", "BULLISH", "Bullish cross"))
        if cur_v > avg_v * 1.5: score += 10; signals.append(("Volume", "BULLISH", "Volume Surge"))
        if vwap and price > vwap: score += 15; signals.append(("VWAP", "BULLISH", "Above VWAP"))
        
        buy_th = 78 if current_mode == "Swing" else 75
        if score >= buy_th: return "BUY", price, int(score), "Watching", signals
        elif score <= -18: return "SELL", price, int(score), "Watching", signals
        return "HOLD", price, int(score), "Watching", signals
    except Exception as e: return "HOLD", 0, 0, str(e), []

def ai_explain(symbol, signal, score, signals, price, currency="₹"):
    if signal == "BUY": return f"**{symbol}** BUY signal. Score: {score}/100. Price: {currency}{price:.2f}"
    return f"**{symbol}** {signal} zone. Score: {score}/100."

def check_drawdown_protection(agent, mode_, streak_limit, pause_hours):
    if agent.get('paused_until'):
        try:
            if now < datetime.fromisoformat(agent['paused_until']): return True, agent.get('pause_reason', 'Drawdown active')
            else: agent['paused_until'] = None; agent['pause_reason'] = ""
        except: agent['paused_until'] = None
    sells = [t for t in agent['trade_log'] if t.get('action') in ('SELL', 'BUY') and t.get('mode') == mode_ and 'pnl' in t]
    if len(sells) >= streak_limit and all(t['pnl'] <= 0 for t in sells[-streak_limit:]):
        agent['paused_until'] = (now + timedelta(hours=pause_hours)).isoformat()
        agent['pause_reason'] = f"{streak_limit} losses in {mode_} — paused for {pause_hours}h"
        return True, agent['pause_reason']
    return False, ""

def calc_kelly_fraction(agent, mode_):
    sells = [t for t in agent['trade_log'] if t.get('action') in ('SELL', 'BUY') and t.get('mode') == mode_ and 'pnl' in t]
    if len(sells) < 5: return 0.02
    wins, losses = [t['pnl'] for t in sells if t['pnl'] > 0], [t['pnl'] for t in sells if t['pnl'] <= 0]
    if not wins or not losses: return 0.02
    p, b = len(wins)/len(sells), np.mean(wins)/abs(np.mean(losses))
    return max(0.01, min(0.25, (b*p - (1-p))/b if b > 0 else 0))

def run_ai_agent_for_market(market, mode_, min_score_threshold, max_alloc, telegram_enabled, mtf_confirm_on=True, dd_on=True, dd_streak=4, dd_hours=12, compounding=False):
    agent, currency, universe = st.session_state[AGENT_KEYS[market]], AGENT_CURRENCY[market], MARKET_UNIVERSE[market]
    sl_pct, tg_pct = RISK_PARAMS[mode_]
    can_trade_now, is_bull = market_can_trade(market, mode_), get_market_regime(MARKET_BENCH[market], mode_)[0]
    is_paused = False
    
    if dd_on:
        is_paused, reason = check_drawdown_protection(agent, mode_, dd_streak, dd_hours)
        if is_paused and not agent.get(f'_pause_{mode_}'):
            send_telegram(f"⏸️ PAUSED {market} {mode_}: {reason}"); agent[f'_pause_{mode_}'] = True
    if not is_paused: agent[f'_pause_{mode_}'] = False

    sizing_base = agent['balance'] if compounding else agent.get('starting_capital', 100000.0)
    results, buy_count, sell_count = [], 0, 0

    for stk in universe:
        sig, price, score, status, signals = advanced_engine(stk, get_data(stk, mode_), mode_)
        results.append((stk, sig, score, price, status, signals))
        st.session_state.scan_log.append({'time': now.strftime('%H:%M:%S'), 'market': market, 'mode': mode_, 'stock': stk, 'signal': sig, 'score': score, 'price': price})

        # LONG
        pos_long = f"{stk}__{mode_}__LONG"
        if sig == "BUY" and agent['positions'].get(pos_long, 0) == 0 and price > 0 and can_trade_now and score >= min_score_threshold and not is_paused:
            mtf_aligned, _ = get_higher_timeframe_trend(stk, mode_) if mtf_confirm_on else (True, "")
            if mtf_aligned:
                alloc_pct = calc_kelly_fraction(agent, mode_) if kelly_on else (max_alloc/100 if is_bull else max_alloc*0.33/100)
                invest = min(sizing_base, agent['balance']) * alloc_pct
                q = int(invest / price) if price > 0 else 0
                if q > 0:
                    agent['positions'][pos_long] = q
                    agent['balance'] -= q * price
                    agent['entry_price'][pos_long] = agent['highest_price'][pos_long] = price
                    agent['entry_mode'][pos_long], agent['position_direction'][pos_long] = mode_, "LONG"
                    agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'BUY', 'price': price, 'qty': q, 'score': score, 'mode': mode_, 'market': market, 'direction': 'LONG'})
                    buy_count += 1
                    send_telegram(f"🟢 LONG: {stk} @ {price}")

        # SHORT
        pos_short = f"{stk}__{mode_}__SHORT"
        if sig == "SELL" and agent['positions'].get(pos_short, 0) == 0 and price > 0 and can_trade_now and score <= -88 and not is_paused:
            mtf_aligned, _ = get_higher_timeframe_trend(stk, mode_) if mtf_confirm_on else (True, "")
            if mtf_aligned:
                alloc_pct = calc_kelly_fraction(agent, mode_) if kelly_on else max_alloc*0.33/100
                invest = min(sizing_base, agent['balance']) * alloc_pct
                q = int(invest / price) if price > 0 else 0
                if q > 0:
                    agent['positions'][pos_short] = -q
                    agent['balance'] -= q * price
                    agent['entry_price'][pos_short] = agent['lowest_price'][pos_short] = price
                    agent['entry_mode'][pos_short], agent['position_direction'][pos_short] = mode_, "SHORT"
                    agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'SHORT', 'price': price, 'qty': q, 'score': score, 'mode': mode_, 'market': market, 'direction': 'SHORT'})
                    sell_count += 1
                    send_telegram(f"🔴 SHORT: {stk} @ {price}")

    for pos_key, q in list(agent['positions'].items()):
        if q == 0 or not (f"__{mode_}__LONG" in pos_key or f"__{mode_}__SHORT" in pos_key): continue
        stk, direction = pos_key.split("__")[0], pos_key.split("__")[-1]
        df2 = get_data(stk, mode_)
        if df2 is None or len(df2) == 0: continue
        cp, entry, exit_reason, pnl_t = float(df2['Close'].iloc[-1]), agent['entry_price'].get(pos_key, 0), None, 0

        if direction == "LONG":
            if cp > agent['highest_price'].get(pos_key, entry): agent['highest_price'][pos_key] = cp
            trail, target = agent['highest_price'][pos_key]*(1-sl_pct), entry*(1+tg_pct)
            if mode_ == "Intraday" and market == "NSE" and now.hour == 15 and now.minute >= 20: exit_reason = "EOD Square-off"
            elif cp <= trail: exit_reason = "Trail SL Hit"
            elif cp >= target: exit_reason = "Target Hit"
            if exit_reason: pnl_t = (cp - entry) * q
        elif direction == "SHORT":
            if cp < agent['lowest_price'].get(pos_key, entry): agent['lowest_price'][pos_key] = cp
            trail, target = agent['lowest_price'][pos_key]*(1+sl_pct), entry*(1-tg_pct)
            if mode_ == "Intraday" and market == "NSE" and now.hour == 15 and now.minute >= 20: exit_reason = "EOD Square-off"
            elif cp >= trail: exit_reason = "Trail SL Hit"
            elif cp <= target: exit_reason = "Target Hit"
            if exit_reason: pnl_t = (entry - cp) * abs(q)

        if exit_reason:
            agent['balance'] += abs(q) * cp
            agent['positions'][pos_key] = 0
            agent['trade_log'].append({'time': now.strftime('%H:%M'), 'full_time': now, 'stock': stk, 'action': 'SELL' if direction=="LONG" else 'BUY', 'price': cp, 'qty': abs(q), 'pnl': round(pnl_t, 2), 'mode': mode_, 'market': market, 'direction': direction})
            sell_count += 1
            for k in ['entry_price','highest_price','lowest_price','entry_mode','position_direction']: agent[k].pop(pos_key, None)
            send_telegram(f"✅ EXIT {direction} {stk} @ {cp}. PNL: {pnl_t:.2f} ({exit_reason})")

    if len(st.session_state.scan_log) > 500: st.session_state.scan_log = st.session_state.scan_log[-500:]
    return sorted(results, key=lambda x: x[2], reverse=True), buy_count, sell_count

@st.cache_data(ttl=3600, show_spinner=False)
def predict_price(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2y")
        if df is None or len(df) < 150: return None
        c = df['Close']
        df['fut_1'] = c.shift(-1) / c - 1
        df['lbl_1'] = (df['fut_1'] > 0).astype(int)
        df['r1'] = c.pct_change(1)
        df = df.dropna()
        X, y_cls, y_reg = df[['r1']].values, df['lbl_1'].values, df['fut_1'].values
        clf = GradientBoostingClassifier().fit(X[:-20], y_cls[:-20])
        reg = Ridge().fit(X[:-20], y_reg[:-20])
        prob = clf.predict_proba(X[-1:])[0][1]
        ret = float(reg.predict(X[-1:])[0])
        return {1: {'direction': "UP" if prob > 0.5 else "DOWN", 'confidence': int(max(prob, 1-prob)*100), 'pred_return': round(ret*100, 2), 'pred_price': round(float(c.iloc[-1])*(1+ret), 2), 'model_acc': 65.0}}
    except: return None

@st.cache_data(ttl=3600, show_spinner=False)
def backtest_strategy(symbol, strategy_name="intraday", period="1y"):
    try:
        df = yf.Ticker(symbol).history(period=period)
        if df is None or len(df) < 100: return None
        df = compute_indicators(df.copy(), strategy_name)
        positions, trade_log = [], []
        for i in range(50, len(df) - 5):
            sig, price, score, _, _ = advanced_engine(symbol, df.iloc[:i+1].copy(), strategy_name)
            if sig == "BUY" and score >= 75 and not positions:
                positions.append({'entry': float(df['Close'].iloc[i]), 'entry_idx': i, 'qty': int(1000 / float(df['Close'].iloc[i]))})
            if positions and (sig == "SELL" or (i - positions[0]['entry_idx']) >= 5):
                exit_price = float(df['Close'].iloc[i])
                pos = positions.pop(0)
                trade_log.append({'entry': pos['entry'], 'exit': exit_price, 'pnl': (exit_price - pos['entry']) * pos['qty']})
        if not trade_log: return None
        wins = [t for t in trade_log if t['pnl'] > 0]
        return {'symbol': symbol, 'strategy': strategy_name, 'total_trades': len(trade_log), 'win_rate': round(len(wins)/len(trade_log)*100, 1) if trade_log else 0, 'total_pnl': round(sum(t['pnl'] for t in trade_log), 2), 'passed': len(wins)/len(trade_log) > 0.50 if trade_log else False}
    except: return None

def play_alert_sound(kind="buy"):
    freq = "880,0,0.15);beep(1100,0.18,0.18" if kind=="buy" else "420,0,0.30"
    st.components.v1.html(f"<script>try{{const ctx=new (window.AudioContext||window.webkitAudioContext)();function beep(f,s,d){{const osc=ctx.createOscillator();const gain=ctx.createGain();osc.connect(gain);gain.connect(ctx.destination);osc.frequency.value=f;osc.type='sine';gain.gain.setValueAtTime(0.18,ctx.currentTime+s);gain.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+s+d);osc.start(ctx.currentTime+s);osc.stop(ctx.currentTime+s+d);}}beep({freq});}}catch(e){{}}</script>", height=0, width=0)

if AUTOREFRESH_AVAILABLE and st.session_state.agent_running: st_autorefresh(interval=5*60*1000, key="agent_autorefresh")

# ===================== HEADER =====================
st.markdown("""<div class="main-header"><h1>⚡ QUANTEDGE AI v9.0</h1><p>KELLY CRITERION + HONEST BACKTESTER — NSE · CRYPTO · US</p></div>""", unsafe_allow_html=True)

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
</div>
""", unsafe_allow_html=True)

c1,c2,c3 = st.columns(3)
c1.metric("Total Open Positions", total_open_positions)
c2.metric("Alerts Set", len(st.session_state.price_alerts))
c3.metric("AI Status", "🟢 LIVE" if st.session_state.agent_running else "⏸️ PAUSED")
st.divider()

tab1, tab2, tab3, tab4, tab10, tab16, tab17 = st.tabs(["🤖 AI Agent Radar", "📊 Chart + S&R", "🔮 Price Prediction", "🏆 Win-Rate & Leaderboard", "💼 Portfolio (3 Agents)", "🎯 Strategy Builder", "📊 Kelly + Honest Backtest"])

with tab1:
    st.markdown("### 🤖 Live Signals & Executions")
    if not agent_results: st.info("Scan not complete yet. Wait for 5 minutes or click manual scan.")
    else: st.success("Systems monitoring correctly.")

with tab3:
    st.markdown("### 🔮 AI Price Prediction")
    pred_sym = st.selectbox("Stock:", MARKET_UNIVERSE["NSE"], key="pred_sym_v9")
    if st.button("🔮 Predict"):
        res = predict_price(pred_sym)
        if res and 1 in res:
            r = res[1]
            st.markdown(f"**{r['direction']}** | Confidence: {r['confidence']}% | Target: {r['pred_price']} ({r['pred_return']}%)")
            fig_pred = make_subplots(rows=1, cols=1, subplot_titles=["Predicted Return %"])
            fig_pred.add_trace(go.Bar(x=["1 Day"], y=[r['pred_return']], marker_color='#00d4ff'))
            fig_pred.update_layout(template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520', height=280)
            st.plotly_chart(fig_pred, use_container_width=True)
        else: st.warning("Not enough data.")

with tab10:
    st.markdown("### 💼 Live Portfolio — Hedged View")
    for mkt in ACTIVE_MARKETS:
        agent, cur = st.session_state[AGENT_KEYS[mkt]], AGENT_CURRENCY[mkt]
        st.markdown(f"## {mkt} Agent")
        active = {k:q for k,q in agent['positions'].items() if q != 0}
        if active:
            st.dataframe(pd.DataFrame([{"Stock":k.split("__")[0], "Qty":q, "Entry":agent['entry_price'].get(k, 0)} for k,q in active.items()]))
        else: st.caption("No open positions.")
        st.divider()

with tab16:
    st.markdown("### 🎯 Option Strategy Builder")
    sb_strategy = st.selectbox("Strategy:", ["Long Straddle", "Short Straddle", "Long Strangle", "Short Strangle", "Bull Call Spread", "Bear Put Spread"])
    sb_spot = st.number_input("Current Spot Price (₹/$):", value=1000.0, step=10.0, min_value=1.0)
    sb_lot = st.number_input("Lot Size:", value=1, step=1, min_value=1)
    
    if st.button("📊 Calculate Payoff", type="primary"):
        price_range = np.linspace(sb_spot * 0.80, sb_spot * 1.20, 200)
        net_payoff = np.zeros_like(price_range)
        strike, premium = round(sb_spot), 25.0
        sign = 1 if "Long" in sb_strategy else -1
        net_payoff += (np.maximum(price_range - strike, 0) - premium) * sign * sb_lot
        net_payoff += (np.maximum(strike - price_range, 0) - premium) * sign * sb_lot
        
        fig_payoff = go.Figure()
        fig_payoff.add_trace(go.Scatter(x=price_range, y=net_payoff, mode='lines', line=dict(color='#00d4ff', width=2.5), fill='tozeroy', fillcolor='rgba(0,212,255,0.08)'))
        fig_payoff.add_vline(x=sb_spot, line_color='#ffaa00', line_dash='dash')
        fig_payoff.update_layout(template='plotly_dark', paper_bgcolor='#0a0e1a', plot_bgcolor='#0d1520', height=400, title=f"{sb_strategy} Payoff")
        st.plotly_chart(fig_payoff, use_container_width=True)

with tab17:
    st.markdown("### 📊 Kelly Criterion Sizing + Honest Backtester")
    st.info("🎲 **Kelly Criterion**: Mathematically optimal position sizing based on win-rate and payoff ratio.")
    kc1, kc2, kc3 = st.columns(3)
    for mkt, col in [("NSE", kc1), ("Crypto", kc2), ("US", kc3)]:
        agent = st.session_state[AGENT_KEYS[mkt]]
                with col:
                st.markdown(f"**{mkt}**")
                for md in ["Intraday", "Swing"]:
                    sells = [t for t in agent['trade_log'] if t.get('mode') == md and 'pnl' in t]
                    # Safe division: Pehle check karo trades hain ya nahi
                    wr_text = f"{len([t for t in sells if t['pnl']>0])/len(sells)*100:.0f}%" if sells else "No trades"
                    st.caption(f"{md}: **{calc_kelly_fraction(agent, md)*100:.1f}%** (WR: {wr_text})")

 
       st.divider()
    bt_market = st.selectbox("Market:", ACTIVE_MARKETS if ACTIVE_MARKETS else ["NSE"], key="backtest_mkt")
    bt_period = st.selectbox("Historical Period:", ["3mo", "6mo", "1y", "2y"], value="1y", key="backtest_period")
    if st.button("🚀 Run Full Backtest", type="primary"):
        with st.spinner("🧪 Backtesting on real history..."):
            bt_symbols = MARKET_UNIVERSE.get(bt_market, [])[:15]
            backtest_results = [r for sym in bt_symbols if (r := backtest_strategy(sym, "Swing", bt_period)) and r['total_trades'] >= 3]
            if backtest_results:
                passed = len([r for r in backtest_results if r['passed']])
                st.success(f"✅ Backtested {len(backtest_results)} stocks")
                st.metric("Passed Stocks", f"{passed}/{len(backtest_results)}")
                st.dataframe(pd.DataFrame([{"Stock": r['symbol'], "Win-Rate": f"{r['win_rate']}%", "Total P&L": f"₹{r['total_pnl']:+,.0f}"} for r in backtest_results if r['passed']]), use_container_width=True, hide_index=True)
            else: st.warning("❌ No valid backtests — try more symbols or longer period")

# ================= FOOTER =================
st.divider()
st.caption("⚡ QuantEdge AI v9.0 — Kelly Criterion + Honest Backtester | NSE India · Crypto · US Stocks | Paper Trading Only")
