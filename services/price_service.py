import yfinance as yf
import streamlit as st

@st.cache_data(ttl=30)
def get_price_data(symbol, interval="1m"):   # ✅ FIX: add interval
    try:
        df = yf.download(
            symbol,
            period="1d",
            interval=interval,
            progress=False
        )

        if df is None or df.empty:
            return None

        # Fix multi-index
        if hasattr(df.columns, "levels"):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        if "Datetime" not in df.columns:
            df.rename(columns={"Date": "Datetime"}, inplace=True)

        return df[["Datetime", "Open", "High", "Low", "Close", "Volume"]]

    except Exception as e:
        print("Error:", e)
        return None