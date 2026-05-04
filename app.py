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
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS"
}

# ===== WATCHLIST =====
watchlist = st.sidebar.multiselect(
    "📌 Watchlist",
    list(symbols.keys()),
    default=["NIFTY", "BANKNIFTY"]
)

# ===== MAIN STOCK =====
selected = st.selectbox("Select Main Chart", list(symbols.keys()))
symbol = symbols[selected]

# ===== AUTO REFRESH =====
auto_refresh = st.sidebar.checkbox("Auto Refresh (5 sec)")

# ===== LOAD DATA =====
with st.spinner("Fetching data..."):
    df = get_price_data(symbol)

if df is None:
    st.error("❌ Failed to load data")
else:
    result = generate_signals(df)

    # ===== METRICS =====
    c1, c2, c3, c4 = st.columns(4)

    signal_color = "green" if "BUY" in result["signal"] else "red"

    c1.metric("Price", format_price(result["price"]))
    c2.metric("Trend", result["trend"])
    c3.markdown(f"<div class='{signal_color}'>Signal: {result['signal']}</div>", unsafe_allow_html=True)
    c4.metric("RSI", result["rsi"])

    # ===== ALERT =====
    if result["signal"] == "BUY 🚀":
        st.success("🚀 BUY Signal Triggered!")
    elif result["signal"] == "SELL 🔻":
        st.error("🔻 SELL Signal Triggered!")

    # ===== CHART =====
    st.subheader("📈 Price Chart")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=result["df"]["Time"],
        y=result["df"]["Price"],
        mode='lines',
        name=selected
    ))

    st.plotly_chart(fig, width="stretch")

    # ===== COMPARISON =====
    st.subheader("📊 Comparison View")

    comp_fig = go.Figure()

    for item in watchlist:
        d = get_price_data(symbols[item])
        if d is not None:
            comp_fig.add_trace(go.Scatter(
                x=d["Time"],
                y=d["Price"],
                mode='lines',
                name=item
            ))

    st.plotly_chart(comp_fig, width="stretch")

    # ===== WATCHLIST SUMMARY =====
    st.subheader("📋 Watchlist Signals")

    for item in watchlist:
        d = get_price_data(symbols[item])
        if d is not None:
            r = generate_signals(d)

            color = "🟢" if "BUY" in r["signal"] else "🔴"
            st.write(f"{color} {item} → {r['signal']} | RSI: {r['rsi']}")

    # ===== TIME =====
    st.caption(f"Last Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

# ===== AUTO REFRESH =====
if auto_refresh:
    time.sleep(5)
    st.rerun()