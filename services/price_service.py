import yfinance as yf
import streamlit as st

@st.cache_data(ttl=30)
def get_price_data(symbol, interval="1m"):
    try:
        df = yf.download(
            symbol,
            period="1d",
            interval=interval,
            progress=False,
            auto_adjust=False
        )

        if df is None or df.empty:
            return None

        # ===== FIX MULTI-INDEX COLUMNS =====
        if isinstance(df.columns, tuple) or hasattr(df.columns, "levels"):
            df.columns = df.columns.get_level_values(0)

        # ===== RESET INDEX =====
        df = df.reset_index()

        # ===== STANDARDIZE DATETIME COLUMN =====
        if "Datetime" not in df.columns:
            if "Date" in df.columns:
                df.rename(columns={"Date": "Datetime"}, inplace=True)

        # ===== KEEP ONLY REQUIRED COLUMNS =====
        required_cols = ["Datetime", "Open", "High", "Low", "Close", "Volume"]

        # Ensure all required columns exist
        df = df[[col for col in required_cols if col in df.columns]]

        # Drop NA rows (important for indicators)
        df = df.dropna()

        # Ensure numeric types (prevents dtype issues later)
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df.columns:
                df[col] = df[col].astype(float)

        return df

    except Exception as e:
        print("Error fetching data:", e)
        return None