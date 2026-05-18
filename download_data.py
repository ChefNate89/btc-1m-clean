import requests
import pandas as pd

url = "https://www.okx.com/api/v5/market/candles"

params = {
    "instId": "BTC-USDT",
    "bar": "1m",
    "limit": "1000"
}

response = requests.get(url, params=params)
data = response.json()

# Validate response
if "data" not in data or not isinstance(data["data"], list):
    print("OKX returned an error instead of data:")
    print(data)
    raise SystemExit(1)

rows = []
for candle in data["data"]:
    rows.append({
        "timestamp": candle[0],
        "open": candle[1],
        "high": candle[2],
        "low": candle[3],
        "close": candle[4],
        "volume": candle[5]
    })

df = pd.DataFrame(rows)
df.to_csv("BTCUSDT_1m.csv", index=False)

print("Saved BTCUSDT_1m.csv")
