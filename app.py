import streamlit as st
import time
import plotly.graph_objects as go
import datetime
import re
import pytz

from services.price_service import get_price_data
from utils.helpers import format_price

# ===== CONFIG =====
st.set_page_config(page_title="AI Market Pro", layout="wide")

# ===== CSS =====
st.markdown("""
<style>
body {background-color: #0e1117; color: white;}
.ticker {font-size:22px;font-weight:bold;padding:10px;text-align:center;}
.green {color:#00ff9f;}
.red {color:#ff4b4b;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 AI Market Dashboard")

# ===== MARKET STATUS =====
ist = pytz.timezone("Asia/Kolkata")
now = datetime.datetime.now(ist)

if now.weekday() >= 5:
    st.info("🔴 Market Closed (Weekend)")
elif datetime.time(9,15) <= now.time() <= datetime.time(15,30):
    st.info("🟢 Market Open")
elif now.time() < datetime.time(9,15):
    st.info("🟡 Pre-Market")
else:
    st.info("🔴 Market Closed")

# ===== SYMBOL MAP =====
name_map = {
    "nifty": "^NSEI",
    "bank nifty": "^NSEBANK",
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "sbi": "SBIN.NS"
}

def resolve_symbol(text):
    text = re.sub(r'[^a-z0-9 ]', '', text.lower())
    for k in name_map:
        if k in text:
            return name_map[k]
    return text.upper() + ".NS"

# ===== STATE =====
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["^NSEI"]

if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = st.session_state.watchlist[0]

# ===== SEARCH =====
search = st.text_input("Search stock")

if search:
    symbol = resolve_symbol(search)
    if st.button("Add"):
        if symbol not in st.session_state.watchlist:
            st.session_state.watchlist.append(symbol)
else:
    symbol = st.session_state.selected_stock

# ===== WATCHLIST =====
st.sidebar.subheader("Watchlist")

remove = None
for i, s in enumerate(st.session_state.watchlist):
    c1, c2 = st.sidebar.columns([4,1])

    if c1.button(s, key=f"s{i}"):
        st.session_state.selected_stock = s

    if c2.button("x", key=f"d{i}"):
        remove = s

if remove:
    st.session_state.watchlist.remove(remove)
    st.rerun()

# ===== TIMEFRAME =====
user_tf = st.selectbox("Timeframe", ["1m","5m","15m"], index=1)

# ===== SMART FETCH =====
def fetch_smart(symbol):
    for tf in ["1m","5m","15m","30m","60m","1d"]:
        df = get_price_data(symbol, tf)
        if df is not None and len(df) > 20:
            return df, tf
    return None, None

df, used_tf = fetch_smart(symbol)

if df is None:
    st.error("❌ Data not available")
    st.stop()

if used_tf != user_tf:
    st.caption(f"⚡ Using {used_tf} for stable data")

# ===== INDICATORS =====
df["EMA20"] = df["Close"].ewm(span=20).mean()
df["EMA50"] = df["Close"].ewm(span=50).mean()

df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / df["Volume"].cumsum()

# ===== RSI (NO DROPNA FIX) =====
delta = df["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14, min_periods=1).mean()
avg_loss = loss.rolling(14, min_periods=1).mean()

rs = avg_gain / avg_loss
df["RSI"] = 100 - (100 / (1 + rs))

# ===== SAFE PRICE =====
price = float(df["Close"].iloc[-1])
prev = float(df["Close"].iloc[-2]) if len(df) > 1 else price

change = round(price - prev, 2)
pct = round((change / prev) * 100, 2) if prev != 0 else 0

cls = "green" if change > 0 else "red"
arrow = "▲" if change > 0 else "▼"

st.markdown(f"""
<div class="ticker {cls}">
{symbol} {arrow} {format_price(price)} ({change} | {pct}%)
</div>
""", unsafe_allow_html=True)

# ===== RSI DISPLAY =====
rsi_val = float(df["RSI"].iloc[-1])
st.metric("RSI", round(rsi_val,2))

# ===== SIGNAL =====
ema20 = df["EMA20"].iloc[-1]
ema50 = df["EMA50"].iloc[-1]

if ema20 > ema50 and rsi_val < 70:
    signal = "🟢 BULLISH"
elif ema20 < ema50 and rsi_val > 30:
    signal = "🔴 BEARISH"
else:
    signal = "🟡 NEUTRAL"

st.write("Signal:", signal)

# ===== CHART =====
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["Datetime"],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"]
))

fig.add_trace(go.Scatter(x=df["Datetime"], y=df["EMA20"], name="EMA20"))
fig.add_trace(go.Scatter(x=df["Datetime"], y=df["EMA50"], name="EMA50"))
fig.add_trace(go.Scatter(x=df["Datetime"], y=df["VWAP"], name="VWAP"))

st.plotly_chart(fig, use_container_width=True)

# ===== RSI CHART =====
st.subheader("RSI")

rsi_fig = go.Figure()
rsi_fig.add_trace(go.Scatter(x=df["Datetime"], y=df["RSI"]))
rsi_fig.add_hline(y=70)
rsi_fig.add_hline(y=30)

st.plotly_chart(rsi_fig, use_container_width=True)

# ===== AUTO REFRESH =====
if st.sidebar.checkbox("Auto Refresh"):
    sec = st.sidebar.slider("Seconds", 5, 60, 10)
    time.sleep(sec)
    st.rerun()