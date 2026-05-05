import yfinance as yf
import streamlit as st
import pandas as pd

@st.cache_data(ttl=60)
def get_price_data(symbol, interval="1m"):
    try:
        # ===== PERIOD LOGIC =====
        if interval == "1m":
            period = "1d"
        elif interval in ["5m", "15m", "30m", "60m"]:
            period = "5d"
        else:
            period = "1mo"

        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False
        )

        if df is None or df.empty:
            return None

        # ===== FIX MULTI-INDEX =====
        if hasattr(df.columns, "levels"):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        # ===== STANDARDIZE DATETIME =====
        if "Datetime" not in df.columns:
            if "Date" in df.columns:
                df.rename(columns={"Date": "Datetime"}, inplace=True)

        # ===== TIMEZONE FIX (SAFE) =====
        df["Datetime"] = pd.to_datetime(df["Datetime"])

        # Only convert if timezone exists (prevents double conversion)
        if df["Datetime"].dt.tz is not None:
            df["Datetime"] = df["Datetime"].dt.tz_convert("Asia/Kolkata")
        else:
            df["Datetime"] = df["Datetime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")

        # Remove timezone for clean plotting
        df["Datetime"] = df["Datetime"].dt.tz_localize(None)

        # ===== KEEP REQUIRED COLUMNS =====
        cols = ["Datetime", "Open", "High", "Low", "Close", "Volume"]
        df = df[[c for c in cols if c in df.columns]].dropna()

        # ===== ENSURE NUMERIC =====
        for c in ["Open", "High", "Low", "Close", "Volume"]:
            if c in df.columns:
                df[c] = df[c].astype(float)

        return df

    except Exception as e:
        print("Price fetch error:", e)
        return None