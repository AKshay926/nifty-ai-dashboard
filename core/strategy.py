import pandas as pd

def generate_signals(df):
    if df is None or df.empty:
        return None

    # Indicators
    df["EMA9"] = df["Price"].ewm(span=9).mean()
    df["EMA21"] = df["Price"].ewm(span=21).mean()

    delta = df["Price"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # Support / Resistance
    recent = df.tail(50)
    support = recent["Price"].min()
    resistance = recent["Price"].max()

    latest = df.iloc[-1]

    price = latest["Price"]
    ema9 = latest["EMA9"]
    ema21 = latest["EMA21"]
    rsi = latest["RSI"]

    # Trend
    trend = "Bullish 📈" if ema9 > ema21 else "Bearish 📉"

    # Signal
    if ema9 > ema21 and rsi > 55 and price > ema9:
        signal = "BUY 🚀"
    elif ema9 < ema21 and rsi < 45 and price < ema9:
        signal = "SELL 🔻"
    else:
        signal = "WAIT ⚖️"

    # Breakout
    if price > resistance:
        breakout = "Breakout 🚀"
    elif price < support:
        breakout = "Breakdown 🔻"
    else:
        breakout = "Inside Range"

    return {
        "price": price,
        "trend": trend,
        "signal": signal,
        "rsi": round(rsi, 2),
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "breakout": breakout,
        "df": df
    }