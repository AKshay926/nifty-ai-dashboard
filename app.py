import streamlit as st
import time
import plotly.graph_objects as go
import datetime

from services.price_service import get_price_data
from core.strategy import generate_signals
from utils.helpers import format_price

# ===== PAGE CONFIG =====
st.set_page_config(page_title="AI Market Pro", layout="wide")

# ===== PREMIUM UI =====
st.markdown("""
<style>
body {background-color: #0e1117; color: white;}
h1 {font-size: 26px !important;}
[data-testid="stMetricValue"] {font-size: 18px;}
.green {color: #00ff9f; font-weight: bold;}
.red {color: #ff4b4b; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 AI Market Dashboard")

# ===== SYMBOL MAP =====
symbols = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "SBIN": "SBIN.NS"
}

# ===== SEARCH BAR =====
st.subheader("🔍 Search Stock / Index")

colA, colB = st.columns(2)

with colA:
    search_input = st.text_input(
        "Type symbol (e.g., RELIANCE, TCS.NS, ^NSEI, ^BSESN)"
    )

with colB:
    selected = st.selectbox("Or Select", list(symbols.keys()))

# ===== SYMBOL LOGIC =====
if search_input:
    if "." not in search_input and not search_input.startswith("^"):
        symbol = search_input.upper() + ".NS"
    else:
        symbol = search_input.upper()
else:
    symbol = symbols[selected]

st.write(f"📌 Selected Symbol: **{symbol}**")

# ===== WATCHLIST =====
watchlist = st.sidebar.multiselect(
    "📌 Watchlist",
    list(symbols.keys()),
    default=["NIFTY", "BANKNIFTY"]
)

# ===== AUTO REFRESH =====
auto_refresh = st.sidebar.checkbox("Auto Refresh (5 sec)")

# ===== DATA CACHE (avoid multiple API calls) =====
data_cache = {}

def get_cached(symbol):
    if symbol not in data_cache:
        data_cache[symbol] = get_price_data(symbol)
    return data_cache[symbol]

# ===== MAIN DATA =====
with st.spinner("Loading market data..."):
    df = get_cached(symbol)

if df is None:
    st.error("❌ Failed to load data")
else:
    result = generate_signals(df)

    # ===== METRICS =====
    c1, c2, c3, c4 = st.columns(4)

    signal_color = "green" if "BUY" in result["signal"] else "red"

    c1.metric("Price", format_price(result["price"]))
    c2.metric("Trend", result["trend"])
    c3.markdown(
        f"<div class='{signal_color}'>Signal: {result['signal']}</div>",
        unsafe_allow_html=True
    )
    c4.metric("RSI", result["rsi"])

    # ===== ALERTS =====
    if result["signal"] == "BUY 🚀":
        st.success("🚀 BUY Signal Triggered!")
    elif result["signal"] == "SELL 🔻":
        st.error("🔻 SELL Signal Triggered!")

    # ===== MAIN CHART =====
    st.subheader("📈 Price Chart")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=result["df"]["Time"],
        y=result["df"]["Price"],
        mode='lines',
        name=symbol
    ))

    st.plotly_chart(fig, width="stretch")

    # ===== COMPARISON =====
    st.subheader("📊 Comparison View")

    comp_fig = go.Figure()

    for item in watchlist:
        sym = symbols[item]
        d = get_cached(sym)

        if d is not None:
            comp_fig.add_trace(go.Scatter(
                x=d["Time"],
                y=d["Price"],
                mode='lines',
                name=item
            ))

    st.plotly_chart(comp_fig, width="stretch")

    # ===== WATCHLIST SIGNALS =====
    st.subheader("📋 Watchlist Signals")

    for item in watchlist:
        sym = symbols[item]
        d = get_cached(sym)

        if d is not None:
            r = generate_signals(d)
            color = "🟢" if "BUY" in r["signal"] else "🔴"
            st.write(f"{color} {item} → {r['signal']} | RSI: {r['rsi']}")

    # ===== LAST UPDATED =====
    st.caption(f"Last Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

# ===== AUTO REFRESH =====
if auto_refresh:
    time.sleep(5)
    st.rerun()