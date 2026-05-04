import streamlit as st
import time
import plotly.graph_objects as go
import datetime
import re

from services.price_service import get_price_data
from utils.helpers import format_price

# ===== CONFIG =====
st.set_page_config(page_title="AI Market Pro", layout="wide")

# ===== UI CSS =====
st.markdown("""
<style>
body {background-color: #0e1117; color: white;}

div[data-testid="stSidebar"] button {
    padding: 4px !important;
    font-size: 12px !important;
}

.ticker {
    font-size: 22px;
    font-weight: bold;
    padding: 10px;
    border-radius: 8px;
    text-align: center;
}

.green-flash {
    color: #00ff9f;
    animation: flashGreen 0.5s ease-in-out;
}

.red-flash {
    color: #ff4b4b;
    animation: flashRed 0.5s ease-in-out;
}

@keyframes flashGreen {
    0% {background-color: rgba(0,255,159,0.2);}
    100% {background-color: transparent;}
}

@keyframes flashRed {
    0% {background-color: rgba(255,75,75,0.2);}
    100% {background-color: transparent;}
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 AI Market Dashboard")

# ===== NAME MAP =====
name_map = {
    "nifty": "^NSEI",
    "bank nifty": "^NSEBANK",
    "sensex": "^BSESN",
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "state bank of india": "SBIN.NS",
    "sbi": "SBIN.NS",
    "bank of baroda": "BANKBARODA.NS"
}

# ===== HELPERS =====
def clean_text(text):
    return re.sub(r'[^a-z0-9 ]', '', text.lower()).strip()

def resolve_symbol(user_input):
    user_input = clean_text(user_input)
    for key in name_map:
        if key in user_input:
            return name_map[key]
    return user_input.upper() + ".NS"

# ===== STATE =====
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["^NSEI", "^NSEBANK"]

if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = st.session_state.watchlist[0]

# ===== SEARCH =====
st.subheader("🔍 Search Stock")

search_input = st.text_input("Type stock name (Reliance, TCS, Nifty)")

if search_input:
    symbol = resolve_symbol(search_input)

    col1, col2 = st.columns([3,1])
    col1.write(f"📌 Selected: **{symbol}**")

    if col2.button("➕ Add to Watchlist"):
        if symbol not in st.session_state.watchlist:
            st.session_state.watchlist.append(symbol)
else:
    symbol = st.session_state.selected_stock

# ===== WATCHLIST =====
st.sidebar.subheader("📌 Watchlist")

remove_item = None

for i, sym in enumerate(st.session_state.watchlist):
    row = st.sidebar.container()
    col1, col2 = row.columns([5, 1])

    if col1.button(sym, key=f"select_{i}", use_container_width=True):
        st.session_state.selected_stock = sym

    if col2.button("✕", key=f"del_{i}"):
        remove_item = sym

if remove_item:
    if len(st.session_state.watchlist) > 1:
        st.session_state.watchlist.remove(remove_item)
        st.rerun()

# ===== TIMEFRAME =====
timeframe = st.selectbox("⏱ Timeframe", ["1m", "5m", "15m"])

# ===== LOAD DATA =====
df = get_price_data(symbol, timeframe)

if df is None:
    st.error("❌ Data not available")

else:
    # ===== INDICATORS =====
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / df["Volume"].cumsum()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # ===== PRICE =====
    price = float(df["Close"].iloc[-1].item())
    prev = float(df["Close"].iloc[-2].item())

    change = round(price - prev, 2)
    pct = round((change / prev) * 100, 2)

    # ===== LIVE TICKER =====
    if change > 0:
        flash_class = "green-flash"
        arrow = "▲"
    elif change < 0:
        flash_class = "red-flash"
        arrow = "▼"
    else:
        flash_class = ""
        arrow = ""

    st.markdown(f"""
    <div class="ticker {flash_class}">
        {symbol} {arrow} {format_price(price)} ({change} | {pct}%)
    </div>
    """, unsafe_allow_html=True)

    # ===== RSI =====
    rsi = float(df["RSI"].iloc[-1].item())

    if rsi > 70:
        rsi_status = "Overbought 🔴"
        rsi_color = "red"
    elif rsi < 30:
        rsi_status = "Oversold 🟢"
        rsi_color = "green"
    else:
        rsi_status = "Neutral 🟡"
        rsi_color = "orange"

    st.markdown(f"### RSI: <span style='color:{rsi_color}'>{round(rsi,2)} ({rsi_status})</span>", unsafe_allow_html=True)

    # ===== SIGNAL =====
    ema20 = df["EMA20"].iloc[-1]
    ema50 = df["EMA50"].iloc[-1]

    if ema20 > ema50 and rsi < 70:
        signal = "BULLISH 🟢"
        color = "green"
    elif ema20 < ema50 and rsi > 30:
        signal = "BEARISH 🔴"
        color = "red"
    else:
        signal = "NEUTRAL 🟡"
        color = "orange"

    st.markdown(f"## Signal: <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)

    # ===== CHART =====
    st.subheader("📈 Chart")

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

    fig.update_layout(xaxis_rangeslider_visible=False)

    st.plotly_chart(fig, use_container_width=True)

    # ===== RSI CHART =====
    st.subheader("📊 RSI")

    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=df["Datetime"], y=df["RSI"]))
    rsi_fig.add_hline(y=70)
    rsi_fig.add_hline(y=30)

    st.plotly_chart(rsi_fig, use_container_width=True)

# ===== AUTO REFRESH =====
st.sidebar.markdown("### 🔄 Auto Refresh")

auto_refresh = st.sidebar.checkbox("Enable Auto Refresh")

if auto_refresh:
    refresh_time = st.sidebar.slider("Refresh Interval (sec)", 5, 60, 10)
    time.sleep(refresh_time)
    st.rerun()