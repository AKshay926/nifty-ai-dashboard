import streamlit as st
import time
import plotly.express as px

from services.price_service import get_price_data
from core.strategy import generate_signals
from utils.helpers import format_price

# ===== PAGE CONFIG =====
st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

# ===== CUSTOM CSS (COMPACT UI) =====
st.markdown("""
<style>
html, body, [class*="css"]  {
    font-size: 14px;
}

h1 {
    font-size: 24px !important;
}

h2 {
    font-size: 18px !important;
}

[data-testid="stMetricValue"] {
    font-size: 18px;
}

[data-testid="stMetricLabel"] {
    font-size: 12px;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ===== TITLE =====
st.title("📊 AI Market Analyzer")

# ===== CATEGORY =====
category = st.selectbox("Select Category", ["Index", "Stocks"])

# ===== DATA MAP =====
if category == "Index":
    symbols = {
        "NIFTY 50": "^NSEI",
        "BANK NIFTY": "^NSEBANK",
        "SENSEX": "^BSESN",
        "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
        "MIDCAP NIFTY": "NIFTY_MIDCAP_100.NS"
    }
else:
    symbols = {
        "RELIANCE": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "INFY": "INFY.NS",
        "HDFCBANK": "HDFCBANK.NS",
        "SBIN": "SBIN.NS",
        "ICICIBANK": "ICICIBANK.NS"
    }

# ===== INPUT =====
col1, col2 = st.columns(2)

with col1:
    selected = st.selectbox("Select", list(symbols.keys()))

with col2:
    manual_input = st.text_input("Or Enter Symbol (e.g., LT.NS, AXISBANK.NS)")

symbol = manual_input if manual_input else symbols[selected]

st.write(f"📌 Selected Symbol: **{symbol}**")

# ===== AUTO REFRESH =====
auto_refresh = st.sidebar.checkbox("Auto Refresh (5 sec)")

# ===== FETCH DATA =====
df = get_price_data(symbol)

if df is None:
    st.error("❌ Failed to load data (check symbol or market closed)")
else:
    result = generate_signals(df)

    if result:
        # ===== METRICS =====
        m1, m2, m3, m4, m5 = st.columns(5)

        m1.metric("Price", format_price(result["price"]))
        m2.metric("Trend", result["trend"])
        m3.metric("Signal", result["signal"])
        m4.metric("RSI", result["rsi"])
        m5.metric("Breakout", result["breakout"])

        # ===== SUPPORT / RESISTANCE =====
        st.subheader("📍 Key Levels")

        s1, s2 = st.columns(2)
        s1.metric("Support", result["support"])
        s2.metric("Resistance", result["resistance"])

        # ===== CHART =====
        st.subheader("📈 Price Chart")

        fig = px.line(
            result["df"],
            x="Time",
            y="Price",
            title=f"{symbol} Price Movement"
        )

        st.plotly_chart(fig, width="stretch")

        # ===== DATA =====
        st.subheader("📋 Latest Data")
        st.dataframe(result["df"].tail(50), width="stretch")

# ===== AUTO REFRESH =====
if auto_refresh:
    time.sleep(5)
    st.rerun()