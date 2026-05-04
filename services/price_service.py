import yfinance as yf

def get_price_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d", interval="1m")

        if df.empty:
            return None

        df = df.reset_index()

        df = df.rename(columns={
            "Datetime": "Time",
            "Close": "Price"
        })

        return df

    except Exception as e:
        print("Price Fetch Error:", e)
        return None