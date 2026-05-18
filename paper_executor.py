import requests
import pandas as pd
import pickle
import time

# Load model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

position = "flat"
entry_price = None
realized_pnl = 0

def get_latest_candle():
    url = "https://www.okx.com/api/v5/market/candles"
    params = {
        "instId": "BTC-USDT",
        "bar": "1m",
        "limit": "2"
    }
    response = requests.get(url, params=params)
    data = response.json()["data"]
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "volCcy", "volCcyQuote", "confirm"
    ])
    df = df.astype(float)
    return df

def get_signal(df):
    df["return"] = df["close"].pct_change()
    df["high_low"] = df["high"] - df["low"]
    df["close_open"] = df["close"] - df["open"]
    df["vol_change"] = df["volume"].pct_change()

    row = df.iloc[-1]

    X = [[
        row["return"],
        row["high_low"],
        row["close_open"],
        row["vol_change"]
    ]]

    return model.predict(X)[0]

while True:
    df = get_latest_candle()
    signal = get_signal(df)
    price = df.iloc[-1]["close"]

    global position, entry_price, realized_pnl

    if position == "flat":
        if signal == 1:
            position = "long"
            entry_price = price
            print(f"Opened LONG at {price}")
        else:
            position = "short"
            entry_price = price
            print(f"Opened SHORT at {price}")

    elif position == "long":
        if signal == 0:
            pnl = price - entry_price
            realized_pnl += pnl
            print(f"Closed LONG at {price} | PnL: {pnl}")
            position = "short"
            entry_price = price
            print(f"Opened SHORT at {price}")

    elif position == "short":
        if signal == 1:
            pnl = entry_price - price
            realized_pnl += pnl
            print(f"Closed SHORT at {price} | PnL: {pnl}")
            position = "long"
            entry_price = price
            print(f"Opened LONG at {price}")

    print(f"Current Position: {position} | Entry: {entry_price} | Realized PnL: {realized_pnl}")
    print("Waiting for next candle...\n")

    time.sleep(60)
