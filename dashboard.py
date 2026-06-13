import streamlit as st
from datetime import datetime, date

# ================== STOCK LIST (YOUR ORIGINAL) ==================
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

mode = "intraday"

# ================== GLOBAL SETTINGS ==================
MAX_POSITIONS = 10
RISK_PER_TRADE = 0.02
STOP_LOSS_PCT = 0.02

# ================== SESSION ==================
if "balance" not in st.session_state:
    st.session_state.balance = 100000

if "positions" not in st.session_state:
    st.session_state.positions = {}

if "entry_price" not in st.session_state:
    st.session_state.entry_price = {}

if "history" not in st.session_state:
    st.session_state.history = []

if "highest_price" not in st.session_state:
    st.session_state.highest_price = {}

if "start_balance" not in st.session_state:
    st.session_state.start_balance = st.session_state.balance

if "last_day" not in st.session_state:
    st.session_state.last_day = date.today()

# ================== DAILY RESET ==================
if st.session_state.last_day != date.today():
    st.session_state.last_day = date.today()

# ================== MAX LOSS PROTECTION ==================
drawdown = (st.session_state.balance - st.session_state.start_balance) / st.session_state.start_balance
if drawdown < -0.1:
    st.error("🚨 Max Loss Hit - Trading Stopped")
    st.stop()

# ================== DUMMY ENGINE ==================
def get_data(stock, mode):
    import pandas as pd
    return pd.DataFrame({"Close": [100 + i for i in range(50)]})

def advanced_engine(stock, df, mode):
    import random
    signal = random.choice(["BUY", "SELL", "HOLD"])
    price = df["Close"].iloc[-1]
    score = random.randint(50, 95)
    return signal, price, score, "OK"

# ================== LEADERBOARD ==================
leaderboard = []

for stock in stocks:
    df = get_data(stock, mode)
    signal, price, score, status = advanced_engine(stock, df, mode)
    leaderboard.append((stock, signal, score, price))

leaderboard = sorted(leaderboard, key=lambda x: x[2], reverse=True)

# REMOVE HOLD
leaderboard = [s for s in leaderboard if s[1] != "HOLD"]

# ================== UI ==================
st.subheader("🏆 Top Opportunities")

for s in leaderboard[:10]:
    st.write(f"{s[0]} | {s[1]} | Score: {s[2]} | ₹{s[3]:.2f}")
    st.progress(s[2] / 100)

# BEST TRADE
if len(leaderboard) > 0 and leaderboard[0][2] > 70:
    st.success(f"🔥 Best Trade: {leaderboard[0][0]} | Score: {leaderboard[0][2]}")

# ================== TRADING ==================
for stock, signal, score, price in leaderboard:

    open_positions = sum(1 for q in st.session_state.positions.values() if q > 0)

    if open_positions >= MAX_POSITIONS:
        continue

    # BUY
    if signal == "BUY" and stock not in st.session_state.positions:
        risk_amount = st.session_state.balance * RISK_PER_TRADE
        sl_distance = price * STOP_LOSS_PCT
        qty = int(risk_amount / sl_distance) if sl_distance > 0 else 0

        if qty > 0:
            st.session_state.positions[stock] = qty
            st.session_state.entry_price[stock] = price
            st.session_state.highest_price[stock] = price
            st.session_state.balance -= qty * price

            st.session_state.history.append({
                "stock": stock,
                "type": "BUY",
                "price": price,
                "time": datetime.now().strftime("%H:%M:%S")
            })

    # SELL
    if signal == "SELL" and stock in st.session_state.positions:
        qty = st.session_state.positions[stock]
        st.session_state.balance += qty * price
        st.session_state.positions.pop(stock)

        st.session_state.history.append({
            "stock": stock,
            "type": "SELL",
            "price": price,
            "time": datetime.now().strftime("%H:%M:%S")
        })

# ================== TRAILING SL ==================
for s in list(st.session_state.positions.keys()):
    price = get_data(s, mode)["Close"].iloc[-1]
    entry = st.session_state.entry_price[s]

    st.session_state.highest_price.setdefault(s, entry)

    if price > st.session_state.highest_price[s]:
        st.session_state.highest_price[s] = price

    if price < st.session_state.highest_price[s] * 0.98:
        qty = st.session_state.positions[s]
        st.session_state.balance += qty * price
        st.session_state.positions.pop(s)

        st.session_state.history.append({
            "stock": s,
            "type": "TRAIL_SL",
            "price": price,
            "time": datetime.now().strftime("%H:%M:%S")
        })

# ================== DASHBOARD ==================
st.subheader("💰 Balance")
st.write(f"₹ {st.session_state.balance:.2f}")

st.subheader("📦 Positions")
st.write(st.session_state.positions)

st.subheader("📜 Trade History")
st.write(st.session_state.history)
