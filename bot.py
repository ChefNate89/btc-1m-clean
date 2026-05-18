import requests
import pandas as pd
import pickle

# Load model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# Fetch latest candle
url = "https://www.okx.com/api/v5/market/candles"
params = {
    "instId": "BTC-USDT",
    "bar": "1m",
    "limit": "2"
}

response = requests.get(url, params=params)
data = response.json()["data"]

# Convert to DataFrame
df = pd.DataFrame(data, columns=[
    "timestamp", "open", "high", "low", "close", "volume",
    "volCcy", "volCcyQuote", "confirm"
])

df = df.astype(float)

# Build features from last candle
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

# Predict
pred = model.predict(X)[0]

if pred == 1:
    print("BUY signal")
else:
    print("SELL signal")
