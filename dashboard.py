# ================= QUANTEDGE AI v10.0 - INSTITUTIONAL GRADE =================
# New in v10: LLM AI, Volume Profile, Max Pain, Monte Carlo VaR, Macro Engine, 
# Ensemble ML, On-Chain Data, MPT, Voice Commands
# ============================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import pytz
import math
import time as time_module
import json
import warnings
warnings.filterwarnings('ignore')

# ================= NEW DEPENDENCIES =================
# Install these: pip install groq scipy speechrecognition
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from scipy import stats
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# ================= GROQ LLM CONFIG =================
GROQ_API_KEY = "gsk_yOUR_gROQ_aPI_kEY_hERE"  # Get free from console.groq.com
GROQ_MODEL = "llama-3.3-70b-versatile"  # Free, fast, powerful

# ================= VOLUME PROFILE CALCULATION =================
def calculate_volume_profile(df, num_bins=50):
    """
    Calculate Volume Profile with POC, VAH, VAL
    Returns: dict with profile data and key levels
    """
    if df is None or len(df) < 20:
        return None
    
    try:
        # Use typical price for better accuracy
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        volume = df['Volume']
        
        # Create price bins
        price_min = typical_price.min()
        price_max = typical_price.max()
        bins = np.linspace(price_min, price_max, num_bins + 1)
        
        # Calculate volume at each price level
        volume_profile = np.zeros(num_bins)
        for i in range(len(typical_price)):
            price_idx = np.digitize(typical_price.iloc[i], bins) - 1
            if 0 <= price_idx < num_bins:
                volume_profile[price_idx] += volume.iloc[i]
        
        # Find POC (Point of Control) - highest volume price
        poc_idx = np.argmax(volume_profile)
        poc_price = (bins[poc_idx] + bins[poc_idx + 1]) / 2
        
        # Calculate Value Area (70% of total volume)
        total_volume = volume_profile.sum()
        target_volume = total_volume * 0.70
        
        # Start from POC and expand outward
        accumulated_volume = volume_profile[poc_idx]
        lower_idx = poc_idx
        upper_idx = poc_idx
        
        while accumulated_volume < target_volume:
            # Expand to lower price
            if lower_idx > 0:
                lower_idx -= 1
                accumulated_volume += volume_profile[lower_idx]
            
            if accumulated_volume >= target_volume:
                break
            
            # Expand to higher price
            if upper_idx < num_bins - 1:
                upper_idx += 1
                accumulated_volume += volume_profile[upper_idx]
        
        vah_price = (bins[upper_idx] + bins[upper_idx + 1]) / 2  # Value Area High
        val_price = (bins[lower_idx] + bins[lower_idx + 1]) / 2  # Value Area Low
        
        return {
            'poc': round(poc_price, 2),
            'vah': round(vah_price, 2),
            'val': round(val_price, 2),
            'bins': bins,
            'volume_profile': volume_profile,
            'total_volume': total_volume
        }
    except Exception as e:
        return None

# ================= MAX PAIN CALCULATION =================
def calculate_max_pain(options_chain):
    """
    Calculate Max Pain price for options expiry
    Returns: price where option writers lose least money
    """
    if options_chain is None:
        return None
    
    try:
        calls = options_chain[options_chain['Call OI'] > 0][['Strike', 'Call OI']].copy()
        puts = options_chain[options_chain['Put OI'] > 0][['Strike', 'Put OI']].copy()
        
        if calls.empty or puts.empty:
            return None
        
        # Get all unique strikes
        all_strikes = sorted(set(calls['Strike'].tolist() + puts['Strike'].tolist()))
        
        # Calculate pain at each strike
        pain_values = []
        for test_price in all_strikes:
            total_pain = 0
            
            # Call writers pain
            for _, row in calls.iterrows():
                strike = row['Strike']
                oi = row['Call OI']
                if test_price > strike:
                    total_pain += (test_price - strike) * oi
            
            # Put writers pain
            for _, row in puts.iterrows():
                strike = row['Strike']
                oi = row['Put OI']
                if test_price < strike:
                    total_pain += (strike - test_price) * oi
            
            pain_values.append({'price': test_price, 'pain': total_pain})
        
        # Max pain is where total pain is minimum
        max_pain_df = pd.DataFrame(pain_values)
        max_pain_price = max_pain_df.loc[max_pain_df['pain'].idxmin(), 'price']
        
        return round(max_pain_price, 2)
    except:
        return None

# ================= OI CHANGE ANALYSIS =================
def analyze_oi_change(symbol):
    """
    Analyze Open Interest changes to detect:
    - Long Buildup (Price ↑, OI ↑)
    - Short Buildup (Price ↓, OI ↑)
    - Long Unwinding (Price ↓, OI ↓)
    - Short Covering (Price ↑, OI ↓)
    """
    try:
        # Get futures data (approximation using stock data)
        df = yf.Ticker(symbol).history(period="5d", interval="1d")
        if df is None or len(df) < 2:
            return None
        
        # Calculate price change
        price_change = (df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100
        
        # Approximate OI change using volume as proxy
        vol_change = (df['Volume'].iloc[-1] - df['Volume'].iloc[-2]) / df['Volume'].iloc[-2] * 100
        
        # Determine buildup type
        if price_change > 0 and vol_change > 10:
            buildup = "🟢 Long Buildup"
            signal = "BULLISH"
        elif price_change < 0 and vol_change > 10:
            buildup = "🔴 Short Buildup"
            signal = "BEARISH"
        elif price_change < 0 and vol_change < -10:
            buildup = "🟡 Long Unwinding"
            signal = "BEARISH"
        elif price_change > 0 and vol_change < -10:
            buildup = "🟡 Short Covering"
            signal = "BULLISH"
        else:
            buildup = "⚪ Neutral"
            signal = "NEUTRAL"
        
        return {
            'buildup': buildup,
            'signal': signal,
            'price_change': round(price_change, 2),
            'vol_change': round(vol_change, 2)
        }
    except:
        return None

# ================= MONTE CARLO VAR =================
def calculate_var_monte_carlo(portfolio_value, returns_data, confidence=0.95, simulations=10000):
    """
    Calculate Value at Risk using Monte Carlo simulation
    Returns: VaR at given confidence level
    """
    if not SCIPY_AVAILABLE or returns_data is None or len(returns_data) < 30:
        return None
    
    try:
        # Calculate historical mean and std
        mean_return = np.mean(returns_data)
        std_return = np.std(returns_data)
        
        # Monte Carlo simulation
        np.random.seed(42)
        simulated_returns = np.random.normal(mean_return, std_return, simulations)
        
        # Calculate VaR
        var_percentile = (1 - confidence) * 100
        var_return = np.percentile(simulated_returns, var_percentile)
        var_amount = portfolio_value * var_return
        
        # Expected Shortfall (CVaR)
        tail_returns = simulated_returns[simulated_returns <= var_return]
        cvar_return = np.mean(tail_returns) if len(tail_returns) > 0 else var_return
        cvar_amount = portfolio_value * cvar_return
        
        return {
            'var_95': round(abs(var_amount), 2),
            'var_percent': round(abs(var_return * 100), 2),
            'cvar_95': round(abs(cvar_amount), 2),
            'cvar_percent': round(abs(cvar_return * 100), 2),
            'confidence': confidence,
            'simulations': simulations
        }
    except:
        return None

# ================= MACRO CORRELATION ENGINE =================
def get_macro_correlation(symbol, period="6mo"):
    """
    Calculate correlation with macro indicators:
    - DXY (Dollar Index)
    - US 10Y Yield
    - Crude Oil
    - Gold
    """
    try:
        # Get stock returns
        stock_df = yf.Ticker(symbol).history(period=period)['Close'].pct_change().dropna()
        
        # Macro indicators
        macro_symbols = {
            'DXY': 'DX-Y.NYB',
            'US10Y': '^TNX',
            'Crude': 'CL=F',
            'Gold': 'GC=F'
        }
        
        correlations = {}
        for name, sym in macro_symbols.items():
            try:
                macro_df = yf.Ticker(sym).history(period=period)['Close'].pct_change().dropna()
                
                # Align dates
                merged = pd.concat([stock_df, macro_df], axis=1, join='inner').dropna()
                if len(merged) >= 20:
                    corr = merged.iloc[:, 0].corr(merged.iloc[:, 1])
                    correlations[name] = {
                        'correlation': round(corr, 3),
                        'interpretation': 'Strong Positive' if corr > 0.7 else 
                                        'Moderate Positive' if corr > 0.3 else
                                        'Weak' if abs(corr) < 0.3 else
                                        'Moderate Negative' if corr > -0.7 else 'Strong Negative'
                    }
            except:
                continue
        
        return correlations if correlations else None
    except:
        return None

# ================= ENSEMBLE ML MODEL =================
def ensemble_predict(symbol, df):
    """
    Combine multiple ML models for better predictions:
    - Gradient Boosting
    - Random Forest
    - Logistic Regression
    """
    if df is None or len(df) < 200:
        return None
    
    try:
        # Feature engineering
        c = df['Close']
        df = df.copy()
        df['r1'] = c.pct_change(1)
        df['r5'] = c.pct_change(5)
        df['rsi'] = 100 - (100 / (1 + (c.diff().clip(lower=0).rolling(14).mean() / 
                                        (-c.diff().clip(upper=0)).rolling(14).mean() + 1e-9)))
        df['macd'] = (c.ewm(span=12).mean() - c.ewm(span=26).mean()) / (c + 1e-9)
        df['bb_pos'] = (c - c.rolling(20).mean()) / (c.rolling(20).std() * 2 + 1e-9)
        df['vol_r'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
        
        df['label'] = (c.shift(-5) / c - 1 > 0.02).astype(int)
        
        feats = ['r1', 'r5', 'rsi', 'macd', 'bb_pos', 'vol_r']
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        X = df[feats].values
        y = df['label'].values
        
        split = int(len(X) * 0.8)
        Xtr, Xte = X[:split], X[split:]
        ytr, yte = y[:split], y[split:]
        
        sc = StandardScaler()
        Xtr_s = sc.fit_transform(Xtr)
        Xte_s = sc.transform(Xte)
        
        # Train multiple models
        models = {
            'GBM': GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42),
            'RF': RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
            'LR': LogisticRegression(random_state=42)
        }
        
        predictions = {}
        accuracies = {}
        
        for name, model in models.items():
            model.fit(Xtr_s, ytr)
            pred_proba = model.predict_proba(Xte_s)[:, 1]
            predictions[name] = pred_proba
            accuracies[name] = np.mean(model.predict(Xte_s) == yte)
        
        # Ensemble: average probabilities
        ensemble_proba = np.mean(list(predictions.values()), axis=0)
        ensemble_pred = (ensemble_proba > 0.5).astype(int)
        ensemble_acc = np.mean(ensemble_pred == yte)
        
        # Latest prediction
        latest = sc.transform(X[-1:])
        latest_proba = {}
        for name, model in models.items():
            latest_proba[name] = model.predict_proba(latest)[0][1]
        
        ensemble_latest = np.mean(list(latest_proba.values()))
        
        return {
            'ensemble_confidence': int(ensemble_latest * 100),
            'direction': 'UP' if ensemble_latest > 0.5 else 'DOWN',
            'model_accuracies': accuracies,
            'ensemble_accuracy': ensemble_acc,
            'individual_predictions': latest_proba
        }
    except:
        return None

# ================= ON-CHAIN CRYPTO DATA =================
def get_crypto_onchain(symbol):
    """
    Get on-chain metrics for crypto (simulated with available data)
    In production, use Glassnode, CryptoQuant, or CoinMetrics API
    """
    if '-USD' not in symbol:
        return None
    
    try:
        df = yf.Ticker(symbol).history(period="30d")
        if df is None or len(df) < 10:
            return None
        
        # Simulated metrics based on price/volume patterns
        volume_avg = df['Volume'].rolling(7).mean().iloc[-1]
        volume_current = df['Volume'].iloc[-1]
        volume_ratio = volume_current / (volume_avg + 1e-9)
        
        price_change_7d = (df['Close'].iloc[-1] / df['Close'].iloc[-7] - 1) * 100
        
        # Simulated whale activity (based on volume spikes)
        whale_activity = "High" if volume_ratio > 2 else "Medium" if volume_ratio > 1.3 else "Low"
        
        # Simulated funding rate (based on price momentum)
        funding_rate = 0.01 if price_change_7d > 5 else -0.01 if price_change_7d < -5 else 0.005
        
        return {
            'whale_activity': whale_activity,
            'volume_ratio': round(volume_ratio, 2),
            'price_change_7d': round(price_change_7d, 2),
            'funding_rate': round(funding_rate, 4),
            'exchange_inflow': "Neutral",  # Would need real API
            'sentiment': "Bullish" if price_change_7d > 0 else "Bearish"
        }
    except:
        return None

# ================= MODERN PORTFOLIO THEORY =================
def calculate_efficient_frontier(symbols, period="1y"):
    """
    Calculate efficient frontier using Markowitz MPT
    Returns optimal portfolio weights for different risk levels
    """
    if not SCIPY_AVAILABLE or len(symbols) < 2:
        return None
    
    try:
        # Get returns data
        returns_data = {}
        for sym in symbols:
            df = yf.Ticker(sym).history(period=period)
            if df is not None and len(df) > 50:
                returns_data[sym] = df['Close'].pct_change().dropna()
        
        if len(returns_data) < 2:
            return None
        
        # Create returns dataframe
        returns_df = pd.DataFrame(returns_data).dropna()
        
        if len(returns_df) < 50:
            return None
        
        # Calculate mean returns and covariance
        mean_returns = returns_df.mean() * 252  # Annualized
        cov_matrix = returns_df.cov() * 252  # Annualized
        
        # Portfolio optimization function
        def portfolio_stats(weights):
            weights = np.array(weights)
            port_return = np.sum(mean_returns * weights)
            port_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return port_return, port_std
        
        # Optimize for maximum Sharpe ratio
        def neg_sharpe(weights):
            ret, std = portfolio_stats(weights)
            return -(ret - 0.05) / std  # Risk-free rate = 5%
        
        # Constraints
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
        )
        bounds = tuple((0, 1) for _ in range(len(symbols)))  # Long only
        
        # Initial guess
        init_guess = np.array([1/len(symbols)] * len(symbols))
        
        # Optimize
        result = minimize(neg_sharpe, init_guess, method='SLSQP', 
                         bounds=bounds, constraints=constraints)
        
        if result.success:
            optimal_weights = result.x
            opt_return, opt_std = portfolio_stats(optimal_weights)
            sharpe_ratio = (opt_return - 0.05) / opt_std
            
            return {
                'symbols': list(returns_data.keys()),
                'weights': {sym: round(w * 100, 1) for sym, w in zip(returns_data.keys(), optimal_weights)},
                'expected_return': round(opt_return * 100, 2),
                'expected_volatility': round(opt_std * 100, 2),
                'sharpe_ratio': round(sharpe_ratio, 2)
            }
        return None
    except:
        return None

# ================= GROQ LLM INTEGRATION =================
def groq_ai_analysis(market_data, question):
    """
    Use Groq LLM for intelligent market analysis
    """
    if not GROQ_AVAILABLE or not GROQ_API_KEY.startswith('gsk_'):
        return "⚠️ Groq API key not configured. Add your free API key from console.groq.com"
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        system_prompt = """You are QuantEdge AI, an institutional-grade trading assistant. 
        Analyze market data and provide concise, actionable insights. 
        Focus on: technical levels, risk factors, and trade setup quality.
        Keep responses under 200 words. Use bullet points for clarity."""
        
        user_prompt = f"""Market Data:
{json.dumps(market_data, indent=2, default=str)}

Question: {question}

Provide your analysis:"""
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Groq API error: {str(e)}"

# ================= VOICE COMMAND SYSTEM =================
def voice_command_listener():
    """
    Listen for voice commands and return recognized text
    """
    if not VOICE_AVAILABLE:
        return None
    
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak now")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
        try:
            text = recognizer.recognize_google(audio)
            return text.lower()
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None
    except:
        return None

# ================= ENHANCED F&O ANALYSIS =================
def enhanced_fno_analysis(symbol):
    """
    Complete F&O analysis with Max Pain, OI Change, PCR, Support/Resistance
    """
    try:
        t = yf.Ticker(symbol)
        
        # Get options chain
        exps = t.options
        if not exps:
            return None
        
        exp = exps[0]
        chain = t.option_chain(exp)
        
        calls = chain.calls[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']].copy()
        puts = chain.puts[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']].copy()
        
        calls.columns = ['Strike', 'Call Price', 'Call Vol', 'Call OI', 'Call IV']
        puts.columns = ['Strike', 'Put Price', 'Put Vol', 'Put OI', 'Put IV']
        
        # Calculate metrics
        total_call_oi = calls['Call OI'].sum()
        total_put_oi = puts['Put OI'].sum()
        pcr = round(total_put_oi / (total_call_oi + 1e-9), 2)
        
        # Max Pain
        merged = pd.merge(calls, puts, on='Strike', how='outer').fillna(0)
        max_pain = calculate_max_pain(merged)
        
        # OI Change Analysis
        oi_analysis = analyze_oi_change(symbol)
        
        # Current price
        current_price = t.info.get('regularMarketPrice', t.info.get('currentPrice', 0))
        
        # Support/Resistance from options
        call_oi_sorted = calls.sort_values('Call OI', ascending=False).head(5)
        put_oi_sorted = puts.sort_values('Put OI', ascending=False).head(5)
        
        resistance_levels = call_oi_sorted[call_oi_sorted['Strike'] > current_price]['Strike'].tolist()[:3]
        support_levels = put_oi_sorted[put_oi_sorted['Strike'] < current_price]['Strike'].tolist()[:3]
        
        return {
            'pcr': pcr,
            'pcr_signal': 'Bullish' if pcr < 0.8 else 'Bearish' if pcr > 1.2 else 'Neutral',
            'max_pain': max_pain,
            'oi_analysis': oi_analysis,
            'current_price': current_price,
            'resistance_levels': resistance_levels,
            'support_levels': support_levels,
            'expiry': exp,
            'total_call_oi': int(total_call_oi),
            'total_put_oi': int(total_put_oi)
        }
    except:
        return None

# ================= NEW TABS FOR DASHBOARD =================
# These functions create the UI for new features

def tab_volume_profile():
    """Volume Profile & POC Tab"""
    st.markdown("### 📊 Volume Profile & Point of Control")
    st.info("Institutional-level volume analysis - Find where most trading happened")
    
    vp_market = st.selectbox("Market:", ["NSE", "Crypto", "US"], key="vp_market")
    vp_sym = st.selectbox("Stock:", MARKET_UNIVERSE.get(vp_market, ["RELIANCE.NS"]), key="vp_sym")
    vp_period = st.selectbox("Period:", ["5d", "1mo", "3mo"], index=1, key="vp_period")
    
    if st.button("📊 Calculate Volume Profile", type="primary"):
        with st.spinner("Calculating..."):
            df = yf.Ticker(vp_sym).history(period=vp_period)
            if df is not None and len(df) > 20:
                vp_data = calculate_volume_profile(df, num_bins=50)
                
                if vp_data:
                    # Display key levels
                    m1, m2, m3 = st.columns(3)
                    m1.metric("🎯 POC (Point of Control)", f"₹{vp_data['poc']}")
                    m2.metric("📈 VAH (Value Area High)", f"₹{vp_data['vah']}")
                    m3.metric("📉 VAL (Value Area Low)", f"₹{vp_data['val']}")
                    
                    # Volume Profile Chart
                    fig = go.Figure()
                    
                    # Add volume profile as horizontal bars
                    fig.add_trace(go.Bar(
                        y=vp_data['bins'][:-1],
                        x=vp_data['volume_profile'],
                        orientation='h',
                        marker_color='#00d4ff',
                        opacity=0.6,
                        name='Volume Profile'
                    ))
                    
                    # Add price line
                    fig.add_trace(go.Scatter(
                        x=list(range(len(df))),
                        y=df['Close'].values,
                        mode='lines',
                        line=dict(color='#00ff88', width=2),
                        name='Price',
                        xaxis='x2'
                    ))
                    
                    # Add POC, VAH, VAL lines
                    for level, color, name in [
                        (vp_data['poc'], '#ffaa00', 'POC'),
                        (vp_data['vah'], '#ff4444', 'VAH'),
                        (vp_data['val'], '#00ff88', 'VAL')
                    ]:
                        fig.add_hline(y=level, line_dash="dash", line_color=color,
                                     annotation_text=f"{name}: ₹{level}",
                                     annotation_font_color=color)
                    
                    fig.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='#0a0e1a',
                        plot_bgcolor='#0d1520',
                        height=500,
                        title=f"{vp_sym} - Volume Profile",
                        showlegend=True,
                        xaxis=dict(title="Volume", side="top"),
                        xaxis2=dict(title="Time", overlaying="y", side="bottom"),
                        yaxis=dict(title="Price")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Trading insights
                    st.markdown("#### 💡 Trading Insights")
                    current_price = df['Close'].iloc[-1]
                    
                    if current_price > vp_data['poc']:
                        st.success(f"✅ Price above POC - Bullish bias. POC at ₹{vp_data['poc']} acts as support.")
                    elif current_price < vp_data['poc']:
                        st.warning(f"⚠️ Price below POC - Bearish bias. POC at ₹{vp_data['poc']} acts as resistance.")
                    
                    if vp_data['vah'] - vp_data['val'] < current_price * 0.02:
                        st.info(f"📊 Narrow value area - Low volatility, breakout likely soon.")
                    else:
                        st.info(f"📊 Wide value area - High volatility range.")
                else:
                    st.error("Could not calculate volume profile")
            else:
                st.error("Insufficient data")

def tab_macro_engine():
    """Macro Correlation Engine Tab"""
    st.markdown("### 🌍 Macro Correlation Engine")
    st.info("See how your stock correlates with global macro indicators")
    
    me_market = st.selectbox("Market:", ["NSE", "Crypto", "US"], key="me_market")
    me_sym = st.selectbox("Stock:", MARKET_UNIVERSE.get(me_market, ["RELIANCE.NS"]), key="me_sym")
    
    if st.button("🔍 Analyze Macro Correlation", type="primary"):
        with st.spinner("Fetching macro data..."):
            correlations = get_macro_correlation(me_sym, period="6mo")
            
            if correlations:
                st.markdown(f"#### 📊 {me_sym} vs Global Indicators")
                
                for indicator, data in correlations.items():
                    corr = data['correlation']
                    interp = data['interpretation']
                    
                    color = '#00ff88' if abs(corr) < 0.3 else '#ffaa00' if abs(corr) < 0.7 else '#ff4444'
                    icon = "🟢" if corr > 0.3 else "🔴" if corr < -0.3 else "🟡"
                    
                    st.markdown(f"""
                    <div class="card-info">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <div>
                                <div style="font-size:1.2rem;font-weight:700;color:#fff">{indicator}</div>
                                <div style="font-size:0.85rem;color:#7a8fa6">{interp}</div>
                            </div>
                            <div style="text-align:right">
                                <div style="font-size:1.8rem;font-weight:800;color:{color}">{corr:+.3f}</div>
                                <div style="font-size:0.75rem;color:#555">{icon} {'Positive' if corr > 0 else 'Negative'}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("#### 💡 What This Means")
                st.markdown("""
                - **DXY (Dollar Index)**: Strong negative correlation = stock benefits from weak dollar
                - **US 10Y Yield**: High correlation = stock sensitive to interest rates
                - **Crude Oil**: Energy stocks correlate positively, others negatively
                - **Gold**: Safe haven - negative correlation with risk assets
                """)
            else:
                st.error("Could not fetch macro data")

def tab_monte_carlo():
    """Monte Carlo VaR Tab"""
    st.markdown("### 🎲 Monte Carlo VaR (Value at Risk)")
    st.info("Calculate maximum expected loss with 95% confidence using 10,000 simulations")
    
    mc_market = st.selectbox("Market:", ["NSE", "Crypto", "US"], key="mc_market")
    mc_agent = st.session_state.get(f'agent_{mc_market.lower()}', {})
    
    # Calculate current portfolio value
    portfolio_value = mc_agent.get('balance', 100000)
    for pos_key, qty in mc_agent.get('positions', {}).items():
        if qty > 0:
            entry = mc_agent.get('entry_price', {}).get(pos_key, 0)
            portfolio_value += qty * entry
    
    st.metric("Current Portfolio Value", f"₹{portfolio_value:,.0f}")
    
    # Get historical returns
    if st.button("🎲 Run Monte Carlo Simulation", type="primary"):
        with st.spinner("Running 10,000 simulations..."):
            # Get benchmark returns
            bench = {"NSE": "^NSEI", "Crypto": "BTC-USD", "US": "^GSPC"}.get(mc_market, "^NSEI")
            returns = yf.Ticker(bench).history(period="1y")['Close'].pct_change().dropna()
            
            var_data = calculate_var_monte_carlo(portfolio_value, returns, confidence=0.95)
            
            if var_data:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("VaR (95%)", f"₹{var_data['var_95']:,.0f}", 
                         f"-{var_data['var_percent']:.2f}%")
                m2.metric("CVaR (95%)", f"₹{var_data['cvar_95']:,.0f}",
                         f"-{var_data['cvar_percent']:.2f}%")
                m3.metric("Confidence", f"{var_data['confidence']*100:.0f}%")
                m4.metric("Simulations", f"{var_data['simulations']:,}")
                
                st.markdown("#### 💡 What This Means")
                st.markdown(f"""
                - **VaR (Value at Risk)**: With 95% confidence, your portfolio will NOT lose more than 
                  **₹{var_data['var_95']:,.0f}** ({var_data['var_percent']:.2f}%) tomorrow.
                
                - **CVaR (Conditional VaR)**: If you DO lose more than VaR, the average loss will be 
                  **₹{var_data['cvar_95']:,.0f}** ({var_data['cvar_percent']:.2f}%).
                
                - **Interpretation**: This is based on historical volatility. Actual losses can exceed 
                  this in black swan events.
                """)
                
                # Risk assessment
                if var_data['var_percent'] < 2:
                    st.success("✅ Low risk - Portfolio volatility is manageable")
                elif var_data['var_percent'] < 5:
                    st.warning("🟡 Moderate risk - Consider diversification")
                else:
                    st.error("🔴 High risk - Portfolio too volatile, reduce exposure")
            else:
                st.error("Could not calculate VaR")

def tab_mpt():
    """Modern Portfolio Theory Tab"""
    st.markdown("### 📈 Modern Portfolio Theory - Efficient Frontier")
    st.info("Optimal portfolio allocation using Markowitz MPT")
    
    mpt_market = st.selectbox("Market:", ["NSE", "US"], key="mpt_market")
    
    # Select stocks for portfolio
    available_stocks = MARKET_UNIVERSE.get(mpt_market, [])[:20]
    selected_stocks = st.multiselect("Select stocks for portfolio (min 2):", 
                                     available_stocks, 
                                     default=available_stocks[:5],
                                     key="mpt_stocks")
    
    if len(selected_stocks) >= 2:
        if st.button("🎯 Optimize Portfolio", type="primary"):
            with st.spinner("Calculating optimal weights..."):
                result = calculate_efficient_frontier(selected_stocks, period="1y")
                
                if result:
                    st.markdown("#### 🏆 Optimal Portfolio Allocation")
                    
                    # Display weights
                    weights_df = pd.DataFrame([
                        {'Stock': k, 'Weight %': v} 
                        for k, v in result['weights'].items()
                    ]).sort_values('Weight %', ascending=False)
                    
                    st.dataframe(weights_df, use_container_width=True, hide_index=True)
                    
                    # Metrics
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Expected Annual Return", f"{result['expected_return']:.2f}%")
                    m2.metric("Expected Volatility", f"{result['expected_volatility']:.2f}%")
                    m3.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
                    
                    # Pie chart
                    fig = go.Figure(data=[go.Pie(
                        labels=list(result['weights'].keys()),
                        values=list(result['weights'].values()),
                        hole=0.3,
                        marker_colors=['#00ff88', '#00d4ff', '#ffaa00', '#ff4444', '#9988ff']
                    )])
                    
                    fig.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='#0a0e1a',
                        plot_bgcolor='#0d1520',
                        height=400,
                        title="Portfolio Allocation"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("#### 💡 Interpretation")
                    st.markdown(f"""
                    - **Expected Return**: {result['expected_return']:.2f}% annually (based on historical data)
                    - **Volatility**: {result['expected_volatility']:.2f}% (risk measure)
                    - **Sharpe Ratio**: {result['sharpe_ratio']:.2f} (>1 is good, >2 is excellent)
                    
                    This allocation maximizes risk-adjusted returns based on past 1 year data.
                    Past performance ≠ future results. Rebalance quarterly.
                    """)
                else:
                    st.error("Could not optimize portfolio - insufficient data")
    else:
        st.warning("Select at least 2 stocks")

def tab_llm_chat():
    """LLM-Powered AI Chat Tab"""
    st.markdown("### 🤖 AI Chat Assistant (Powered by Groq Llama-3)")
    st.info("Ask anything about markets, stocks, or your portfolio - AI will analyze and respond")
    
    if not GROQ_AVAILABLE:
        st.error("⚠️ Groq library not installed. Run: `pip install groq`")
        return
    
    if not GROQ_API_KEY.startswith('gsk_'):
        st.warning("⚠️ Groq API key not configured. Get free key from console.groq.com")
        st.markdown("""
        **Setup Steps:**
        1. Go to https://console.groq.com
        2. Sign up (free)
        3. Create API key
        4. Replace `GROQ_API_KEY` in code with your key
        """)
        return
    
    # Initialize chat history
    if "llm_chat_history" not in st.session_state:
        st.session_state.llm_chat_history = []
    
    # Display chat history
    for msg in st.session_state.llm_chat_history[-10:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if user_input := st.chat_input("Ask about markets, stocks, or strategy..."):
        # Add user message
        st.session_state.llm_chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Prepare market context
        market_context = {
            "timestamp": datetime.now().isoformat(),
            "portfolio_summary": {}
        }
        
        for market in ["NSE", "Crypto", "US"]:
            agent = st.session_state.get(f'agent_{market.lower()}', {})
            if agent:
                balance = agent.get('balance', 0)
                positions = len([q for q in agent.get('positions', {}).values() if q > 0])
                trades = len(agent.get('trade_log', []))
                market_context["portfolio_summary"][market] = {
                    "balance": balance,
                    "open_positions": positions,
                    "total_trades": trades
                }
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🧠 AI is thinking..."):
                response = groq_ai_analysis(market_context, user_input)
                st.markdown(response)
        
        st.session_state.llm_chat_history.append({"role": "assistant", "content": response})
    
    # Clear chat button
    if st.session_state.llm_chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.llm_chat_history = []
            st.rerun()

def tab_voice_control():
    """Voice Command Control Tab"""
    st.markdown("### 🎤 Voice Command Terminal")
    st.info("Control your trading terminal with voice commands")
    
    if not VOICE_AVAILABLE:
        st.error("⚠️ SpeechRecognition not installed. Run: `pip install SpeechRecognition`")
        return
    
    st.markdown("""
    **Available Commands:**
    - "Show portfolio" - Display portfolio summary
    - "What is RELIANCE price" - Get stock price
    - "Scan NSE market" - Run market scan
    - "Show win rate" - Display win rate stats
    - "Clear chat" - Clear AI chat history
    """)
    
    if st.button("🎤 Start Listening", type="primary"):
        command = voice_command_listener()
        
        if command:
            st.success(f"🎤 Heard: '{command}'")
            
            # Process command
            if "portfolio" in command:
                st.info("📊 Portfolio Summary:")
                for market in ["NSE", "Crypto", "US"]:
                    agent = st.session_state.get(f'agent_{market.lower()}', {})
                    balance = agent.get('balance', 0)
                    st.write(f"**{market}:** ₹{balance:,.0f}")
            
            elif "price" in command:
                # Extract stock name (simplified)
                st.info("📈 Stock price lookup - use manual tab for detailed analysis")
            
            elif "scan" in command:
                st.info("🔍 Market scan initiated - check AI Agent Radar tab")
            
            elif "win rate" in command:
                st.info("🏆 Win rate stats - check Leaderboard tab")
            
            elif "clear" in command and "chat" in command:
                st.session_state.llm_chat_history = []
                st.success("✅ Chat cleared")
            
            else:
                st.warning("❓ Command not recognized. Try: 'show portfolio'")
        else:
            st.warning("🔇 Could not understand. Try again.")

# ================= INTEGRATION WITH EXISTING DASHBOARD =================
# Add these new tabs to your existing dashboard

def add_v10_tabs():
    """
    Add v10 tabs to existing dashboard
    Call this after your existing tabs
    """
    st.divider()
    st.markdown("## 🚀 QUANTEDGE AI v10.0 - Advanced Features")
    
    v10_tab1, v10_tab2, v10_tab3, v10_tab4, v10_tab5, v10_tab6, v10_tab7 = st.tabs([
        "📊 Volume Profile",
        "🌍 Macro Engine",
        "🎲 Monte Carlo VaR",
        "📈 MPT Optimizer",
        "🤖 LLM Chat",
        "🎤 Voice Control",
        "📈 Enhanced F&O"
    ])
    
    with v10_tab1:
        tab_volume_profile()
    
    with v10_tab2:
        tab_macro_engine()
    
    with v10_tab3:
        tab_monte_carlo()
    
    with v10_tab4:
        tab_mpt()
    
    with v10_tab5:
        tab_llm_chat()
    
    with v10_tab6:
        tab_voice_control()
    
    with v10_tab7:
        st.markdown("### 📈 Enhanced F&O Analysis")
        st.info("Complete F&O data with Max Pain, OI Change, PCR, and Support/Resistance")
        
        fno_market = st.selectbox("Market:", ["NSE", "US"], key="fno_market_v10")
        fno_stocks = ["NIFTY", "BANKNIFTY", "RELIANCE.NS", "TCS.NS", "INFY.NS"] if fno_market == "NSE" else ["AAPL", "TSLA", "NVDA"]
        fno_sym = st.selectbox("Stock/Index:", fno_stocks, key="fno_sym_v10")
        
        if st.button("🔍 Analyze F&O Data", type="primary"):
            with st.spinner("Fetching F&O data..."):
                fno_data = enhanced_fno_analysis(fno_sym.replace("NIFTY", "^NSEI").replace("BANKNIFTY", "^NSEBANK"))
                
                if fno_data:
                    # Key metrics
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("PCR", fno_data['pcr'], fno_data['pcr_signal'])
                    m2.metric("Max Pain", f"₹{fno_data['max_pain']}" if fno_data['max_pain'] else "N/A")
                    m3.metric("Current Price", f"₹{fno_data['current_price']:.2f}")
                    m4.metric("Expiry", fno_data['expiry'])
                    
                    # OI Analysis
                    if fno_data['oi_analysis']:
                        st.markdown("#### 📊 OI Change Analysis")
                        oi = fno_data['oi_analysis']
                        st.markdown(f"""
                        <div class="card-info">
                            <div style="font-size:1.3rem;font-weight:700;color:#00d4ff">{oi['buildup']}</div>
                            <div style="margin-top:8px">
                                <span style="color:#7a8fa6">Price Change:</span> 
                                <span style="color:{'#00ff88' if oi['price_change'] > 0 else '#ff4444'};font-weight:700">
                                    {oi['price_change']:+.2f}%
                                </span>
                            </div>
                            <div>
                                <span style="color:#7a8fa6">Volume Change:</span> 
                                <span style="color:{'#00ff88' if oi['vol_change'] > 0 else '#ff4444'};font-weight:700">
                                    {oi['vol_change']:+.2f}%
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Support/Resistance
                    st.markdown("#### 🎯 F&O-Based Support & Resistance")
                    sr_col1, sr_col2 = st.columns(2)
                    
                    with sr_col1:
                        st.markdown("**🔴 Resistance Levels**")
                        for r in fno_data['resistance_levels']:
                            st.markdown(f"- ₹{r:.2f}")
                    
                    with sr_col2:
                        st.markdown("**🟢 Support Levels**")
                        for s in fno_data['support_levels']:
                            st.markdown(f"- ₹{s:.2f}")
                    
                    # OI Chart
                    st.markdown("#### 📊 Open Interest Distribution")
                    # Would need full options chain data for chart
                    st.info(f"Total Call OI: {fno_data['total_call_oi']:,} | Total Put OI: {fno_data['total_put_oi']:,}")
                else:
                    st.error("Could not fetch F&O data")

# ================= USAGE INSTRUCTIONS =================
"""
To integrate v10.0 features into your existing dashboard:

1. Add all the new functions above to your code

2. At the end of your existing dashboard (after all current tabs), add:

```python
# ================= QUANTEDGE AI v10.0 FEATURES =================
add_v10_tabs()
```

3. Install new dependencies:
```bash
pip install groq scipy SpeechRecognition
```

4. Get free Groq API key:
   - Go to https://console.groq.com
   - Sign up and create API key
   - Replace GROQ_API_KEY in the code

5. Restart your Streamlit app

That's it! All v10 features will be available in new tabs.
"""

print("""
✅ QUANTEDGE AI v10.0 - Institutional Grade Terminal
=====================================================

New Features Added:
1. ✅ Volume Profile & POC - Institutional chart analysis
2. ✅ Macro Correlation Engine - DXY, Yields, Crude impact
3. ✅ Monte Carlo VaR - Advanced risk management
4. ✅ Modern Portfolio Theory - Efficient frontier optimization
5. ✅ Groq LLM Integration - AI-powered chat with Llama-3
6. ✅ Voice Commands - Control terminal with voice
7. ✅ Enhanced F&O - Max Pain, OI Change, PCR analysis
8. ✅ Ensemble ML - Multiple models combined for better predictions
9. ✅ On-Chain Crypto - Whale tracking, funding rates (simulated)

Next Steps:
- Install: pip install groq scipy SpeechRecognition
- Get Groq API key from console.groq.com
- Add add_v10_tabs() to your dashboard
- Run: streamlit run dashboard_v10.py

🚀 Ready to trade like an institution!
""")
