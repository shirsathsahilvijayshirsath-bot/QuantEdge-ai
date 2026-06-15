# ================= IMPORTS =================
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
from datetime import datetime, timedelta
import pytz
import os
import joblib
import json

st.set_page_config(
    page_title="QuantEdge AI v2.0",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS =================
st.markdown("""
<style>
    /* Dark terminal theme */
    .stApp {
        background-color: #0a0e1a;
        color: #e0e6f0;
    }
    .main-header {
        background: linear-gradient(135deg, #0d1b2a 0%, #1a2744 50%, #0d1b2a 100%);
        border: 1px solid #00d4ff33;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 20px;
        box-shadow: 0 0 30px #00d4ff15;
    }
    .main-header h1 {
        color: #00d4ff;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 2px;
        margin: 0;
    }
    .main-header p {
        color: #7a8fa6;
        font-size: 0.85rem;
        margin: 4px 0 0 0;
        letter-spacing: 1px;
    }
    .signal-card-buy {
        background: linear-gradient(135deg, #003d1f, #005a2b);
        border: 1px solid #00ff8844;
        border-left: 4px solid #00ff88;
        border-radius: 8px;
        padding: 14px 16px;
        margin: 6px 0;
    }
    .signal-card-sell {
        background: linear-gradient(135deg, #3d0000, #5a0000);
        border: 1px solid #ff444444;
        border-left: 4px solid #ff4444;
        border-radius: 8px;
        padding: 14px 16px;
        margin: 6px 0;
    }
    .signal-card-hold {
        background: linear-gradient(135deg, #1a1f2e, #222840);
        border: 1px solid #ffffff15;
        border-left: 4px solid #888;
        border-radius: 8px;
        padding: 14px 16px;
        margin: 6px 0;
    }
    .metric-box {
        background: #0d1b2a;
        border: 1px solid #00d4ff22;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-box .value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #00d4ff;
    }
    .metric-box .label {
        font-size: 0.75rem;
        color: #7a8fa6;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .score-bar-container {
        background: #1a2744;
        border-radius: 4px;
        height: 6px;
        margin-top: 6px;
    }
    .ai-explanation {
        background: #0d1520;
        border: 1px solid #00d4ff22;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.85rem;
        color: #a0b4c8;
        font-style: italic;
    }
    .news-card {
        background: #0d1b2a;
        border: 1px solid #ffffff10;
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
    }
    .sentiment-positive { color: #00ff88; font-weight: 600; }
    .sentiment-negative { color: #ff4444; font-weight: 600; }
    .sentiment-neutral  { color: #ffaa00; font-weight: 600; }
    div[data-testid="stSidebarContent"] {
        background-color: #0d1520;
        border-right: 1px solid #00d4ff15;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0d1520;
        border-bottom: 1px solid #00d4ff22;
    }
    .stTabs [data-baseweb="tab"] {
        color: #7a8fa6;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #00d4ff !important;
        border-bottom: 2px solid #00d4ff !important;
    }
    .backtest-result {
        background: #0d1b2a;
        border: 1px solid #00d4ff22;
        border-radius: 10px;
        padding: 16px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ================= SECURITY LOGIN =================
MY_PASSWORD = "QuantEdge2026"

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.markdown("""
        <div class="main-header">
            <h1>⚡ QUANTEDGE AI v2.0</h1>
            <p>SECURE TRADING TERMINAL — AUTHORIZED ACCESS ONLY</p>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔒 Security Gateway")
            pwd = st.text_input("Password:", type="password", key="password_input")
            if pwd == MY_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            elif pwd:
                st.error("❌ Galat Password!")
        return False
    return True

if not check_password():
    st.stop()

# ================= CONFIG =================
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)

TOKEN = "8629163881:AAHrO4n9KpDNT0tMR1DoRvXeJeZ5VEIWCCA"
CHAT_ID = "7602586865"
NEWS_API_KEY = ""  # Optional: add your NewsAPI key here

# ================= SESSION STATE =================
defaults = {
    "balance": 100000.0,
    "positions": {},
    "entry_price": {},
    "highest_price": {},
    "trade_log": [],
    "backtest_results": {}
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= STOCKS =================
stocks = [
    "TATAMOTORS.NS", "M&M.NS", "DLF.NS", "BRITANNIA.NS", "BHARTIARTL.NS", "SBIN.NS",
    "KOTAKBANK.NS", "ZOMATO.NS", "TITAN.NS", "MAXHEALTH.NS", "HAL.NS", "LTIM.NS",
    "TORNTPHARM.NS", "SUZLON.NS", "ABB.NS", "GODREJPROP.NS", "HAPPSTMNDS.NS",
    "TATAELXSI.NS", "PERSISTENT.NS", "HCLTECH.NS", "INFY.NS", "MARUTI.NS",
    "HINDALCO.NS", "ASIANPAINT.NS", "BAJAJ-AUTO.NS", "TRENT.NS", "EICHERMOT.NS",
    "TVSMOTOR.NS", "NTPC.NS", "MOTHERSON.NS", "ZYDUSLIFE.NS", "AXISBANK.NS",
    "HINDUNILVR.NS", "PIDILITIND.NS", "SRF.NS", "VBL.NS", "NETWEB.NS"
]

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## ⚡ QuantEdge AI v2.0")
    st.divider()
    mode = st.radio("📊 Trading Mode", ["Swing", "Intraday"], index=0)
    st.divider()
    st.markdown("### ⚙️ Risk Settings")
    if mode == "Intraday":
        STOP_LOSS_PCT = st.slider("Stop Loss %", 0.5, 3.0, 1.0, 0.1) / 100
        TARGET_PCT = st.slider("Target %", 1.0, 5.0, 2.5, 0.1) / 100
    else:
        STOP_LOSS_PCT = st.slider("Stop Loss %", 1.0, 8.0, 3.0, 0.5) / 100
        TARGET_PCT = st.slider("Target %", 3.0, 20.0, 8.0, 0.5) / 100
    st.divider()
    st.markdown("### 🔔 Alerts")
    telegram_alerts = st.toggle("Telegram Alerts", value=True)
    min_score = st.slider("Min Score for Alert", 50, 95, 75)
    st.divider()
    st.caption(f"🕒 IST: {now.strftime('%d %b %Y, %H:%M:%S')}")
    st.caption(f"Mode: **{mode}** | SL: {STOP_LOSS_PCT*100:.1f}% | TG: {TARGET_PCT*100:.1f}%")

# ================= HEADER =================
st.markdown("""
<div class="main-header">
    <h1>⚡ QUANTEDGE AI v2.0</h1>
    <p>ADVANCED ALGORITHMIC TRADING TERMINAL — NSE INDIA</p>
</div>
""", unsafe_allow_html=True)

# ================= HELPERS =================
def send_telegram(msg):
    if not telegram_alerts:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

# ================= ML MODEL (Upgraded) =================
@st.cache_resource
def get_model(symbol):
    """Train per-symbol GradientBoosting model with proper features"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y")
        if df is None or len(df) < 200:
            return None, None

        df = df.copy()
        # Features
        df['Return_1d'] = df['Close'].pct_change(1)
        df['Return_5d'] = df['Close'].pct_change(5)
        df['Return_10d'] = df['Close'].pct_change(10)
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['SMA_200'] = df['Close'].rolling(200).mean()
        df['Vol_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()

        delta = df['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain / loss))

        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = (exp1 - exp2) / df['Close']

        df['BB_pos'] = (df['Close'] - df['Close'].rolling(20).mean()) / (df['Close'].rolling(20).std() * 2)
        df['ATR'] = (df['High'] - df['Low']).rolling(14).mean() / df['Close']

        # Label: did price go up >2% in next 5 days?
        df['Future_Return'] = df['Close'].shift(-5) / df['Close'] - 1
        df['Label'] = (df['Future_Return'] > 0.02).astype(int)

        feature_cols = ['Return_1d', 'Return_5d', 'Return_10d', 'RSI', 'MACD',
                        'BB_pos', 'Vol_ratio', 'ATR',
                        'SMA_20', 'SMA_50', 'SMA_200']

        df = df.dropna()
        if len(df) < 100:
            return None, None

        X = df[feature_cols]
        y = df['Label']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)

        model = GradientBoostingClassifier(n_estimators=150, learning_rate=0.05,
                                           max_depth=4, random_state=42)
        model.fit(X_train_s, y_train)
        return model, scaler
    except:
        return None, None

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

@st.cache_data(ttl=300, show_spinner=False)
def get_market_regime(current_mode):
    try:
        nifty = yf.Ticker("^NSEI")
        df = nifty.history(period="6mo") if current_mode == "Swing" else nifty.history(period="5d", interval="5m")
        if df.empty:
            return True, "Unknown", 50
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['SMA_20'] = df['Close'].rolling(20).mean()
        latest = df['Close'].iloc[-1]
        sma50 = df['SMA_50'].iloc[-1]
        sma20 = df['SMA_20'].iloc[-1]
        strength = min(100, int(abs(latest - sma50) / sma50 * 1000))
        is_bullish = latest > sma50
        trend = "Bullish" if is_bullish else "Bearish"
        return is_bullish, f"{trend} (SMA50: ₹{sma50:.0f})", strength
    except:
        return True, "Unknown", 50

# ================= INDICATORS ENGINE =================
def compute_indicators(df, current_mode):
    df = df.copy()
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['SMA_200'] = df['Close'].rolling(200).mean()
    df['EMA_9'] = df['Close'].ewm(span=9).mean()
    df['Volume_SMA_20'] = df['Volume'].rolling(20).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain / loss))

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

    df['BB_Mid'] = df['Close'].rolling(20).mean()
    df['BB_Std'] = df['Close'].rolling(20).std()
    df['BB_Up'] = df['BB_Mid'] + (df['BB_Std'] * 2)
    df['BB_Low'] = df['BB_Mid'] - (df['BB_Std'] * 2)
    df['BB_pct'] = (df['Close'] - df['BB_Low']) / (df['BB_Up'] - df['BB_Low'])

    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()

    if current_mode == "Intraday":
        df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['VP'] = df['Typical_Price'] * df['Volume']
        df['Date'] = df.index.date
        df['Cum_Vol'] = df.groupby('Date')['Volume'].cumsum()
        df['Cum_VP'] = df.groupby('Date')['VP'].cumsum()
        df['VWAP'] = df['Cum_VP'] / df['Cum_Vol']

    return df.dropna()

# ================= ADVANCED ENGINE =================
def advanced_engine(symbol, df, current_mode):
    if df is None or len(df) < 100:
        return "HOLD", 0, 0, "Insufficient Data", []

    try:
        df = compute_indicators(df, current_mode)
        if len(df) < 50:
            return "HOLD", 0, 0, "Data Error", []

        price   = float(df["Close"].iloc[-1])
        rsi     = float(df["RSI"].iloc[-1])
        sma20   = float(df["SMA_20"].iloc[-1])
        sma50   = float(df["SMA_50"].iloc[-1])
        macd    = float(df["MACD"].iloc[-1])
        sig_ln  = float(df["Signal_Line"].iloc[-1])
        macd_h  = float(df["MACD_Hist"].iloc[-1])
        bb_pct  = float(df["BB_pct"].iloc[-1])
        bb_up   = float(df["BB_Up"].iloc[-1])
        bb_low  = float(df["BB_Low"].iloc[-1])
        cur_vol = float(df["Volume"].iloc[-1])
        avg_vol = float(df["Volume_SMA_20"].iloc[-1])
        atr     = float(df["ATR"].iloc[-1])
        vwap    = float(df["VWAP"].iloc[-1]) if current_mode == "Intraday" else None

        # ML Prediction
        model, scaler = get_model(symbol)
        ml_score = 0
        ml_confidence = 0
        if model and scaler:
            try:
                ret1 = df['Close'].pct_change(1).iloc[-1]
                ret5 = df['Close'].pct_change(5).iloc[-1] if len(df) >= 5 else 0
                ret10 = df['Close'].pct_change(10).iloc[-1] if len(df) >= 10 else 0
                sma200 = float(df['SMA_200'].iloc[-1]) if 'SMA_200' in df.columns else price
                feat = np.array([[ret1, ret5, ret10, rsi, macd/price,
                                  bb_pct - 0.5, cur_vol/(avg_vol+1e-9) - 1,
                                  atr/price, sma20, sma50, sma200]])
                feat_s = scaler.transform(feat)
                prob = model.predict_proba(feat_s)[0][1]
                ml_confidence = int(prob * 100)
                if prob > 0.6:
                    ml_score = int((prob - 0.5) * 60)
            except:
                pass

        score = ml_score
        reasons = []
        signals = []

        # RSI
        if rsi < 35:
            score += 18; reasons.append("🔵 RSI Strongly Oversold"); signals.append(("RSI", rsi, "BULLISH", f"{rsi:.1f} < 35"))
        elif rsi < 45:
            score += 10; reasons.append("🔵 RSI Oversold"); signals.append(("RSI", rsi, "BULLISH", f"{rsi:.1f} < 45"))
        elif rsi > 72:
            score -= 15; reasons.append("🔴 RSI Overbought"); signals.append(("RSI", rsi, "BEARISH", f"{rsi:.1f} > 72"))
        else:
            signals.append(("RSI", rsi, "NEUTRAL", f"{rsi:.1f}"))

        # Trend
        if price > sma20 > sma50:
            score += 15; reasons.append("📈 Strong Uptrend"); signals.append(("Trend", price, "BULLISH", "Price > SMA20 > SMA50"))
        elif price > sma50:
            score += 8; reasons.append("📈 Above SMA50"); signals.append(("Trend", price, "BULLISH", "Price > SMA50"))
        elif price < sma50:
            score -= 8; signals.append(("Trend", price, "BEARISH", "Price < SMA50"))

        # MACD
        if macd > sig_ln and macd_h > 0:
            score += 14; reasons.append("⚡ MACD Bullish Cross"); signals.append(("MACD", macd, "BULLISH", "MACD > Signal"))
        elif macd < sig_ln and macd_h < 0:
            score -= 10; signals.append(("MACD", macd, "BEARISH", "MACD < Signal"))
        else:
            signals.append(("MACD", macd, "NEUTRAL", "Converging"))

        # Bollinger
        if bb_pct < 0.2:
            score += 12; reasons.append("📉 Near BB Low (Bounce)"); signals.append(("BB", bb_pct, "BULLISH", "Near lower band"))
        elif bb_pct > 0.85:
            score -= 8; signals.append(("BB", bb_pct, "BEARISH", "Near upper band"))
        else:
            signals.append(("BB", bb_pct, "NEUTRAL", f"{bb_pct:.2f}"))

        # Volume
        vol_ratio = cur_vol / (avg_vol + 1e-9)
        if vol_ratio > 2.0:
            score += 14; reasons.append("🔊 High Volume Surge"); signals.append(("Volume", vol_ratio, "BULLISH", f"{vol_ratio:.1f}x avg"))
        elif vol_ratio > 1.4:
            score += 7; signals.append(("Volume", vol_ratio, "BULLISH", f"{vol_ratio:.1f}x avg"))
        else:
            signals.append(("Volume", vol_ratio, "NEUTRAL", f"{vol_ratio:.1f}x avg"))

        # VWAP (Intraday)
        if current_mode == "Intraday" and vwap:
            if price > vwap * 1.005:
                score += 30; reasons.append("✅ Above VWAP"); signals.append(("VWAP", vwap, "BULLISH", f"Price ₹{price:.1f} > VWAP ₹{vwap:.1f}"))
            elif price < vwap * 0.995:
                score -= 30; reasons.append("❌ Below VWAP"); signals.append(("VWAP", vwap, "BEARISH", f"Price ₹{price:.1f} < VWAP ₹{vwap:.1f}"))
            else:
                signals.append(("VWAP", vwap, "NEUTRAL", "Near VWAP"))

        # ML signal
        if ml_confidence > 0:
            signals.append(("ML Model", ml_confidence, "BULLISH" if ml_confidence > 60 else "NEUTRAL", f"{ml_confidence}% confidence"))

        if score >= 75:
            return "BUY", price, score, " | ".join(reasons[:3]), signals
        elif score <= -20 or (rsi > 72 and macd < sig_ln):
            return "SELL", price, score, " | ".join(reasons[:3]), signals
        else:
            return "HOLD", price, score, " | ".join(reasons[:2]) if reasons else "Waiting", signals

    except Exception as e:
        return "HOLD", 0, 0, f"Error: {str(e)[:30]}", []

# ================= AI EXPLANATION =================
def generate_ai_explanation(symbol, signal, score, signals, price):
    """Generate human-readable AI explanation"""
    bullish = [s for s in signals if s[2] == "BULLISH"]
    bearish = [s for s in signals if s[2] == "BEARISH"]

    if signal == "BUY":
        parts = [f"**{symbol}** mein BUY signal hai (Score: {score}/100)."]
        if bullish:
            reasons = ", ".join([f"{s[0]} ({s[3]})" for s in bullish[:3]])
            parts.append(f"🟢 Bullish factors: {reasons}.")
        if bearish:
            risks = ", ".join([f"{s[0]}" for s in bearish[:2]])
            parts.append(f"⚠️ Risk: {risks} weak hai, isliye position size manage karo.")
        parts.append(f"Current price ₹{price:.2f} hai.")
    elif signal == "SELL":
        parts = [f"**{symbol}** mein SELL/EXIT signal hai (Score: {score}/100)."]
        if bearish:
            reasons = ", ".join([f"{s[0]} ({s[3]})" for s in bearish[:3]])
            parts.append(f"🔴 Bearish factors: {reasons}.")
        parts.append("Profit book karo ya stop loss lagao.")
    else:
        parts = [f"**{symbol}** abhi HOLD zone mein hai (Score: {score}/100)."]
        parts.append("Koi strong signal nahi hai. Wait karo clearer setup ke liye.")

    return " ".join(parts)

# ================= CANDLESTICK CHART =================
def plot_candlestick(df, symbol, current_mode):
    tail = 60 if current_mode == "Intraday" else 90
    df_plot = df.tail(tail).copy()

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=[f"{symbol} — Price", "Volume", "RSI"]
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df_plot.index,
        open=df_plot['Open'], high=df_plot['High'],
        low=df_plot['Low'], close=df_plot['Close'],
        increasing_line_color='#00ff88', decreasing_line_color='#ff4444',
        name="Price"
    ), row=1, col=1)

    # SMAs
    for col_name, color, name in [('SMA_20', '#00d4ff', 'SMA20'), ('SMA_50', '#ffaa00', 'SMA50')]:
        if col_name in df_plot.columns:
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot[col_name],
                line=dict(color=color, width=1.2), name=name, opacity=0.8), row=1, col=1)

    # BB
    if 'BB_Up' in df_plot.columns:
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['BB_Up'],
            line=dict(color='#8888ff', width=0.8, dash='dot'), name='BB Upper', opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['BB_Low'],
            line=dict(color='#8888ff', width=0.8, dash='dot'), name='BB Lower', opacity=0.6,
            fill='tonexty', fillcolor='rgba(136,136,255,0.05)'), row=1, col=1)

    # VWAP
    if 'VWAP' in df_plot.columns and current_mode == "Intraday":
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['VWAP'],
            line=dict(color='#ff88ff', width=1.5), name='VWAP'), row=1, col=1)

    # Volume
    colors = ['#00ff88' if c >= o else '#ff4444'
              for c, o in zip(df_plot['Close'], df_plot['Open'])]
    fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['Volume'],
        marker_color=colors, name='Volume', opacity=0.7), row=2, col=1)

    if 'Volume_SMA_20' in df_plot.columns:
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Volume_SMA_20'],
            line=dict(color='#ffaa00', width=1), name='Vol Avg'), row=2, col=1)

    # RSI
    if 'RSI' in df_plot.columns:
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI'],
            line=dict(color='#00d4ff', width=1.5), name='RSI'), row=3, col=1)
        fig.add_hline(y=70, line_color='#ff4444', line_dash='dot', opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_color='#00ff88', line_dash='dot', opacity=0.5, row=3, col=1)

    grid_style = dict(gridcolor='rgba(255,255,255,0.04)', showgrid=True, zeroline=False)

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0a0e1a',
        plot_bgcolor='#0d1520',
        height=550,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(color='#7a8fa6', size=11),
        xaxis=grid_style,
        xaxis2=grid_style,
        xaxis3=grid_style,
        yaxis=grid_style,
        yaxis2=grid_style,
        yaxis3=grid_style,
    )

    return fig

# ================= NEWS & SENTIMENT =================
@st.cache_data(ttl=1800, show_spinner=False)
def get_news_sentiment(symbol):
    """Get news using yfinance (no API key needed)"""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if not news:
            return []

        results = []
        for item in news[:5]:
            title = item.get('title', '')
            link  = item.get('link', '#')
            pub   = item.get('providerPublishTime', 0)

            # Simple keyword sentiment
            pos_words = ['surge', 'gain', 'profit', 'growth', 'bullish', 'rally', 'buy',
                         'strong', 'record', 'upgrade', 'beat', 'rise', 'positive', 'win']
            neg_words = ['fall', 'drop', 'loss', 'bearish', 'sell', 'decline', 'weak',
                         'downgrade', 'miss', 'crash', 'risk', 'negative', 'concern', 'cut']

            title_lower = title.lower()
            pos = sum(1 for w in pos_words if w in title_lower)
            neg = sum(1 for w in neg_words if w in title_lower)

            if pos > neg:
                sentiment = "POSITIVE"
                sent_score = min(100, 50 + pos * 15)
            elif neg > pos:
                sentiment = "NEGATIVE"
                sent_score = max(0, 50 - neg * 15)
            else:
                sentiment = "NEUTRAL"
                sent_score = 50

            pub_dt = datetime.fromtimestamp(pub).strftime('%d %b, %H:%M') if pub else "Recent"
            results.append({
                'title': title,
                'link': link,
                'sentiment': sentiment,
                'score': sent_score,
                'time': pub_dt
            })
        return results
    except:
        return []

# ================= BACKTESTING ENGINE =================
def run_backtest(symbol, current_mode, sl_pct, tg_pct):
    try:
        df = yf.Ticker(symbol).history(period="1y")
        if df is None or len(df) < 100:
            return None

        df = compute_indicators(df, "Swing")
        df = df.dropna()

        trades = []
        in_trade = False
        entry_p = 0
        entry_i = 0

        for i in range(50, len(df)):
            row = df.iloc[i]
            price = row['Close']
            rsi = row['RSI']
            macd = row['MACD']
            sig = row['Signal_Line']
            sma50 = row['SMA_50']
            vol = row['Volume']
            avg_vol = row['Volume_SMA_20']

            if not in_trade:
                # Entry condition
                if (rsi < 45 and price > sma50 and macd > sig and vol > avg_vol * 1.3):
                    in_trade = True
                    entry_p = price
                    entry_i = i
            else:
                pnl_pct = (price - entry_p) / entry_p
                days_held = i - entry_i

                if pnl_pct >= tg_pct:
                    trades.append({'type': 'WIN', 'pnl': pnl_pct, 'days': days_held})
                    in_trade = False
                elif pnl_pct <= -sl_pct:
                    trades.append({'type': 'LOSS', 'pnl': pnl_pct, 'days': days_held})
                    in_trade = False
                elif days_held >= 20:
                    trades.append({'type': 'TIMEOUT', 'pnl': pnl_pct, 'days': days_held})
                    in_trade = False

        if not trades:
            return None

        total = len(trades)
        wins  = len([t for t in trades if t['type'] == 'WIN'])
        losses= len([t for t in trades if t['type'] == 'LOSS'])
        total_pnl = sum(t['pnl'] for t in trades) * 100
        win_rate  = (wins / total * 100) if total > 0 else 0
        avg_days  = np.mean([t['days'] for t in trades])

        return {
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_pnl_pct': total_pnl,
            'avg_days': avg_days,
            'trades': trades
        }
    except:
        return None

# ================= MAIN APP =================
can_trade = not (mode == "Intraday" and (now.hour > 14 or (now.hour == 14 and now.minute >= 30)))
is_bullish, regime_status, regime_strength = get_market_regime(mode)

# Top metrics bar
m1, m2, m3, m4, m5 = st.columns(5)
total_invested = sum(st.session_state.entry_price.get(s, 0) * q
                     for s, q in st.session_state.positions.items() if q > 0)
total_val = st.session_state.balance + total_invested
pnl = total_val - 100000.0

with m1:
    trend_icon = "🟢" if is_bullish else "🔴"
    st.metric("Market", f"{trend_icon} {'Bullish' if is_bullish else 'Bearish'}", regime_status.split('(')[0].strip())
with m2:
    st.metric("Portfolio", f"₹{total_val:,.0f}", f"{'+'if pnl>=0 else ''}{pnl:,.0f}")
with m3:
    st.metric("Cash", f"₹{st.session_state.balance:,.0f}")
with m4:
    open_pos = len([q for q in st.session_state.positions.values() if q > 0])
    st.metric("Open Positions", open_pos)
with m5:
    pnl_pct = pnl / 1000
    st.metric("Total P&L %", f"{pnl_pct:+.2f}%")

st.divider()

# ================= TABS =================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📡 Live Radar",
    "📊 Charts & Analysis",
    "📰 News & Sentiment",
    "🧪 Backtest",
    "💼 Portfolio"
])

# ===================== TAB 1: RADAR =====================
with tab1:
    if st.button("🔄 Refresh Signals", type="primary"):
        st.cache_data.clear()
        st.rerun()

    leaderboard = []

    with st.spinner("📡 Scanning 37 stocks..."):
        for stock in stocks:
            df_s = get_data(stock, mode)
            signal, price, score, status_msg, signals = advanced_engine(stock, df_s, mode)
            leaderboard.append((stock, signal, score, price, status_msg, signals))

    leaderboard = sorted(leaderboard, key=lambda x: x[2], reverse=True)

    # Auto trade execution
    for stock, signal, score, price, _, sigs in leaderboard:
        qty = st.session_state.positions.get(stock, 0)
        if signal == "BUY" and qty == 0 and price > 0 and can_trade and score >= min_score:
            alloc_pct = 0.15 if score >= 85 and is_bullish else 0.10 if is_bullish else 0.05
            invest = st.session_state.balance * alloc_pct
            q = int(invest / price)
            if q > 0 and invest <= st.session_state.balance:
                st.session_state.positions[stock] = q
                st.session_state.balance -= q * price
                st.session_state.entry_price[stock] = price
                st.session_state.highest_price[stock] = price
                entry_time = now.strftime('%H:%M')
                st.session_state.trade_log.append({
                    'time': entry_time, 'stock': stock, 'action': 'BUY',
                    'price': price, 'qty': q, 'score': score
                })
                calc_tg = price * (1 + TARGET_PCT)
                calc_sl = price * (1 - STOP_LOSS_PCT)
                emoji = "🟢 [AGGRESSIVE]" if alloc_pct == 0.15 else "🔵 [STANDARD]"
                send_telegram(f"{emoji} {mode} BUY: {stock}\nScore: {score}\nEntry: ₹{price:.2f}\nTarget: ₹{calc_tg:.2f}\nSL: ₹{calc_sl:.2f}")

        elif signal == "SELL" and qty > 0 and price > 0:
            pnl_trade = (price - st.session_state.entry_price.get(stock, price)) * qty
            st.session_state.balance += qty * price
            st.session_state.positions[stock] = 0
            st.session_state.trade_log.append({
                'time': now.strftime('%H:%M'), 'stock': stock, 'action': 'SELL',
                'price': price, 'qty': qty, 'pnl': pnl_trade
            })
            st.session_state.entry_price.pop(stock, None)
            st.session_state.highest_price.pop(stock, None)
            send_telegram(f"🔴 [{mode}] SELL: {stock} @ ₹{price:.2f} | P&L: ₹{pnl_trade:+.0f}")

    # Trailing stop
    for s, q in list(st.session_state.positions.items()):
        if q > 0:
            df2 = get_data(s, mode)
            if df2 is None or len(df2) == 0:
                continue
            cp = float(df2["Close"].iloc[-1])
            if s not in st.session_state.highest_price:
                st.session_state.highest_price[s] = st.session_state.entry_price.get(s, cp)
            if cp > st.session_state.highest_price[s]:
                st.session_state.highest_price[s] = cp
            trailing_sl = st.session_state.highest_price[s] * (1 - STOP_LOSS_PCT)
            entry = st.session_state.entry_price.get(s, cp)
            if mode == "Intraday" and now.hour == 15 and now.minute >= 20:
                st.session_state.balance += q * cp
                st.session_state.positions[s] = 0
                send_telegram(f"⏳ EOD EXIT: {s} @ ₹{cp:.2f}")
            elif cp <= trailing_sl:
                st.session_state.balance += q * cp
                st.session_state.positions[s] = 0
                send_telegram(f"🛑 Trailing SL: {s} @ ₹{cp:.2f}")
            elif cp >= entry * (1 + TARGET_PCT):
                st.session_state.balance += q * cp
                st.session_state.positions[s] = 0
                send_telegram(f"🎯 Target Hit: {s} @ ₹{cp:.2f}")

    # Display signals
    col_b, col_s = st.columns(2)

    with col_b:
        st.markdown("### 🟢 BUY Signals")
        buy_list = [s for s in leaderboard if s[1] == "BUY"]
        if buy_list:
            for item in buy_list[:8]:
                stk, sig, sc, pr, msg, sigs = item
                explanation = generate_ai_explanation(stk, sig, sc, sigs, pr)
                bar_w = min(100, sc)
                st.markdown(f"""
                <div class="signal-card-buy">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#00ff88; font-weight:700; font-size:1rem;">{stk}</span>
                        <span style="color:#00ff88; font-size:1.1rem; font-weight:800;">₹{pr:.2f}</span>
                    </div>
                    <div style="color:#aaa; font-size:0.78rem; margin:4px 0;">{msg}</div>
                    <div class="score-bar-container">
                        <div style="background:#00ff88; width:{bar_w}%; height:6px; border-radius:4px;"></div>
                    </div>
                    <div style="color:#00ff88; font-size:0.75rem; margin-top:4px;">Score: {sc}/100</div>
                    <div class="ai-explanation" style="margin-top:8px;">🤖 {explanation}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No strong BUY signals right now. Market scan chal raha hai...")

    with col_s:
        st.markdown("### 🔴 SELL Signals")
        sell_list = [s for s in leaderboard if s[1] == "SELL"]
        if sell_list:
            for item in sell_list[:6]:
                stk, sig, sc, pr, msg, sigs = item
                explanation = generate_ai_explanation(stk, sig, sc, sigs, pr)
                st.markdown(f"""
                <div class="signal-card-sell">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#ff4444; font-weight:700;">{stk}</span>
                        <span style="color:#ff4444; font-weight:800;">₹{pr:.2f}</span>
                    </div>
                    <div style="color:#aaa; font-size:0.78rem; margin:4px 0;">{msg}</div>
                    <div class="ai-explanation" style="margin-top:8px;">🤖 {explanation}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No SELL signals.")

    st.divider()
    st.markdown("### 📋 All Stocks Radar")
    rows = []
    for stk, sig, sc, pr, msg, _ in leaderboard:
        emoji = "🟢" if sig == "BUY" else "🔴" if sig == "SELL" else "⚪"
        rows.append({"Stock": stk, "Signal": f"{emoji} {sig}", "Score": sc,
                     "Price (₹)": f"{pr:.2f}" if pr > 0 else "-", "Analysis": msg[:50]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100)})

# ===================== TAB 2: CHARTS =====================
with tab2:
    st.markdown("### 📊 Advanced Chart Analysis")
    selected = st.selectbox("Stock Select Karo:", stocks)
    df_chart = get_data(selected, mode)

    if df_chart is not None and len(df_chart) >= 50:
        df_chart = compute_indicators(df_chart, mode)
        sig, pr, sc, msg, sigs = advanced_engine(selected, df_chart, mode)

        c1, c2, c3, c4 = st.columns(4)
        signal_color = "🟢" if sig == "BUY" else "🔴" if sig == "SELL" else "⚪"
        c1.metric("Signal", f"{signal_color} {sig}")
        c2.metric("Price", f"₹{pr:.2f}")
        c3.metric("Score", f"{sc}/100")
        if df_chart is not None and 'RSI' in df_chart.columns:
            c4.metric("RSI", f"{df_chart['RSI'].iloc[-1]:.1f}")

        fig = plot_candlestick(df_chart, selected, mode)
        st.plotly_chart(fig, use_container_width=True)

        # Signal breakdown table
        st.markdown("### 🔍 Signal Breakdown")
        if sigs:
            sig_rows = []
            for s in sigs:
                color = "🟢" if s[2] == "BULLISH" else "🔴" if s[2] == "BEARISH" else "🟡"
                sig_rows.append({"Indicator": s[0], "Status": f"{color} {s[2]}", "Detail": s[3]})
            st.dataframe(pd.DataFrame(sig_rows), use_container_width=True, hide_index=True)

        # AI Explanation
        st.markdown("### 🤖 AI Analysis")
        explanation = generate_ai_explanation(selected, sig, sc, sigs, pr)
        st.markdown(f"""<div class="ai-explanation" style="font-size:0.95rem; padding:16px;">
        🤖 <strong>AI Explanation:</strong><br><br>{explanation}
        </div>""", unsafe_allow_html=True)
    else:
        st.warning("Data load nahi hua. Dobara try karo.")

# ===================== TAB 3: NEWS =====================
with tab3:
    st.markdown("### 📰 Live News & Sentiment Analysis")
    news_stock = st.selectbox("Stock Select Karo (News):", stocks, key="news_sel")

    with st.spinner("📰 News fetch ho rahi hai..."):
        news_items = get_news_sentiment(news_stock)

    if news_items:
        overall_sent = np.mean([n['score'] for n in news_items])
        sent_label = "POSITIVE 🟢" if overall_sent > 60 else "NEGATIVE 🔴" if overall_sent < 40 else "NEUTRAL 🟡"

        s1, s2 = st.columns(2)
        s1.metric("Overall Sentiment", sent_label, f"Score: {overall_sent:.0f}/100")
        s2.metric("News Count", len(news_items))

        st.divider()
        for n in news_items:
            color = "#00ff88" if n['sentiment'] == "POSITIVE" else "#ff4444" if n['sentiment'] == "NEGATIVE" else "#ffaa00"
            icon = "🟢" if n['sentiment'] == "POSITIVE" else "🔴" if n['sentiment'] == "NEGATIVE" else "🟡"
            st.markdown(f"""
            <div class="news-card">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="color:{color}; font-weight:600; font-size:0.8rem;">{icon} {n['sentiment']}</span>
                    <span style="color:#555; font-size:0.75rem;">{n['time']}</span>
                </div>
                <div style="color:#c0cfe0; font-size:0.88rem; line-height:1.5;">{n['title']}</div>
                <div style="margin-top:8px;">
                    <a href="{n['link']}" target="_blank" style="color:#00d4ff; font-size:0.75rem; text-decoration:none;">📎 Full Article →</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"{news_stock} ke liye abhi koi news nahi mili.")

    # Market-wide sentiment
    st.divider()
    st.markdown("### 🌐 Market Sentiment Overview")
    if st.button("🔄 Scan All Stocks Sentiment"):
        sentiment_data = []
        prog = st.progress(0)
        for i, stk in enumerate(stocks[:15]):
            items = get_news_sentiment(stk)
            if items:
                avg = np.mean([n['score'] for n in items])
                label = "🟢" if avg > 60 else "🔴" if avg < 40 else "🟡"
                sentiment_data.append({"Stock": stk, "Sentiment": label, "Score": int(avg)})
            prog.progress((i+1)/15)
        if sentiment_data:
            st.dataframe(pd.DataFrame(sentiment_data).sort_values('Score', ascending=False),
                        use_container_width=True, hide_index=True)

# ===================== TAB 4: BACKTEST =====================
with tab4:
    st.markdown("### 🧪 Backtesting Engine")
    st.info("Strategy: RSI < 45 + Price > SMA50 + MACD Bullish + Volume Surge | Timeframe: 1 Year")

    b1, b2 = st.columns(2)
    with b1:
        bt_stock = st.selectbox("Stock Select Karo:", stocks, key="bt_sel")
        bt_sl = st.slider("Backtest Stop Loss %", 1.0, 10.0, 3.0, 0.5)
        bt_tg = st.slider("Backtest Target %", 2.0, 25.0, 8.0, 0.5)

    with b2:
        st.markdown("#### Strategy Rules")
        st.markdown("""
        - **Entry:** RSI < 45 + Price > SMA50 + MACD Bullish + Vol > 1.3x
        - **Exit:** Target hit OR Stop Loss OR 20 days timeout
        - **Data:** 1 Year historical
        - **Model:** Rule-based (reproducible)
        """)

    if st.button("▶️ Run Backtest", type="primary"):
        with st.spinner(f"🧪 {bt_stock} backtest chal raha hai..."):
            result = run_backtest(bt_stock, mode, bt_sl/100, bt_tg/100)

        if result:
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Total Trades", result['total_trades'])
            r2.metric("Win Rate", f"{result['win_rate']:.1f}%",
                     delta=f"{result['wins']}W / {result['losses']}L")
            r3.metric("Total P&L", f"{result['total_pnl_pct']:+.1f}%")
            r4.metric("Avg Hold Days", f"{result['avg_days']:.0f}")

            # Trade distribution chart
            pnls = [t['pnl'] * 100 for t in result['trades']]
            colors = ['#00ff88' if p >= 0 else '#ff4444' for p in pnls]
            fig_bt = go.Figure(go.Bar(
                x=list(range(1, len(pnls)+1)), y=pnls,
                marker_color=colors, name="Trade P&L %"
            ))
            fig_bt.update_layout(
                template='plotly_dark', paper_bgcolor='#0a0e1a',
                plot_bgcolor='#0d1520', height=300,
                title=f"{bt_stock} — Trade-by-Trade P&L",
                xaxis_title="Trade #", yaxis_title="P&L %",
                margin=dict(l=10, r=10, t=40, b=10)
            )
            fig_bt.add_hline(y=0, line_color='#ffffff44')
            st.plotly_chart(fig_bt, use_container_width=True)

            # Cumulative
            cum_pnl = np.cumsum(pnls)
            fig_cum = go.Figure(go.Scatter(
                x=list(range(1, len(cum_pnl)+1)), y=cum_pnl,
                fill='tozeroy',
                line=dict(color='#00d4ff', width=2),
                fillcolor='rgba(0,212,255,0.1)'
            ))
            fig_cum.update_layout(
                template='plotly_dark', paper_bgcolor='#0a0e1a',
                plot_bgcolor='#0d1520', height=250,
                title="Cumulative P&L Curve",
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_cum, use_container_width=True)
        else:
            st.warning("Backtest ke liye enough trades generate nahi hue. Different stock try karo.")

# ===================== TAB 5: PORTFOLIO =====================
with tab5:
    st.markdown("### 💼 Live Portfolio")

    p1, p2, p3 = st.columns(3)
    p1.metric("Total Value", f"₹{total_val:,.2f}", f"{'+'if pnl>=0 else ''}{pnl:,.2f}")
    p2.metric("Cash", f"₹{st.session_state.balance:,.2f}")
    p3.metric("P&L %", f"{pnl/1000:+.2f}%")

    st.divider()
    active = {s: q for s, q in st.session_state.positions.items() if q > 0}

    if active:
        st.markdown("#### Open Positions")
        pos_rows = []
        for s, q in active.items():
            entry = st.session_state.entry_price.get(s, 0)
            high  = st.session_state.highest_price.get(s, entry)
            curr  = entry  # approximate since we don't re-fetch here
            trail_sl = high * (1 - STOP_LOSS_PCT)
            tg_price = entry * (1 + TARGET_PCT)
            pos_rows.append({
                "Stock": s, "Qty": q,
                "Entry ₹": f"{entry:.2f}",
                "Trail SL ₹": f"{trail_sl:.2f}",
                "Target ₹": f"{tg_price:.2f}",
                "Value ₹": f"{q*entry:,.0f}"
            })
        st.dataframe(pd.DataFrame(pos_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Koi open position nahi hai.")

    st.divider()
    if st.session_state.trade_log:
        st.markdown("#### 📋 Trade Log")
        log_df = pd.DataFrame(st.session_state.trade_log)
        st.dataframe(log_df, use_container_width=True, hide_index=True)

    st.divider()
    if st.button("🔁 Reset Portfolio", type="secondary"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.success("✅ Portfolio reset ho gaya!")
        st.rerun()

# ================= FOOTER =================
st.divider()
st.caption("⚡ QuantEdge AI v2.0 | Built for NSE India Paper Trading | Educational Purpose Only")
st.caption("⚠️ Real money invest karne se pehle SEBI registered advisor se zaroor salah lein.")
