import requests
import pandas as pd
import pickle
import time
from datetime import datetime

# ---- CONFIG ----
TAKE_PROFIT_PCT = 0.003   # 0.3%
STOP_LOSS_PCT   = 0.003   # 0.3%
RISK_PER_TRADE  = 0.01    # 1% of account
START_EQUITY    = 1000.0  # paper account size
LOG_FILE        = "paper_trades.csv"
# ----------------

with open("model.pkl", "rb") as f:
    model = pickle.load(f)

position = "flat"
entry_price = None
equity = START_EQUITY
size = 0.0  # position size in BTC

def get_latest_candle():
    url = "https://www.okx.com/api/v5/market/candles"
    params = {"instId": "BTC-USDT", "bar": "1m", "limit": "2"}
    r = requests.get(url, params=params)
    data = r.json()["data"]
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
    X = [[row["return"], row["high_low"], row["close_open"], row["vol_change"]]]
    return model.predict(X)[0]  # 1 = buy, 0 = sell

def log_trade(timestamp, side, price, pnl, equity_after, note):
    row = {
        "time": timestamp,
        "side": side,
        "price": price,
        "pnl": pnl,
        "equity": equity_after,
        "note": note,
    }
    try:
        df = pd.read_csv(LOG_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    except FileNotFoundError:
        df = pd.DataFrame([row])
    df.to_csv(LOG_FILE, index=False)

while True:
    df = get_latest_candle()
    price = df.iloc[-1]["close"]
    ts = datetime.utcnow().isoformat()

    signal = get_signal(df)

    # Use globals in loop scope
    global position, entry_price, equity, size

    # Calculate unrealized PnL if in position
    unrealized = 0.0
    if position == "long":
        unrealized = (price - entry_price) * size
    elif position == "short":
        unrealized = (entry_price - price) * size

    # Check exits (TP/SL)
    if position != "flat":
        tp_price_long  = entry_price * (1 + TAKE_PROFIT_PCT)
        sl_price_long  = entry_price * (1 - STOP_LOSS_PCT)
        tp_price_short = entry_price * (1 - TAKE_PROFIT_PCT)
        sl_price_short = entry_price * (1 + STOP_LOSS_PCT)

        exit_reason = None
        if position == "long":
            if price >= tp_price_long:
                exit_reason = "TP"
            elif price <= sl_price_long:
                exit_reason = "SL"
        elif position == "short":
            if price <= tp_price_short:
                exit_reason = "TP"
            elif price >= sl_price_short:
                exit_reason = "SL"

        if exit_reason:
            pnl = unrealized
            equity += pnl
            log_trade(ts, f"close_{position}", price, pnl, equity, exit_reason)
            print(f"{exit_reason}: Closed {position} at {price} | PnL: {pnl:.2f} | Equity: {equity:.2f}")
            position = "flat"
            entry_price = None
            size = 0.0

    # Entry logic (only if flat)
    if position == "flat":
        # position sizing: risk fixed % of equity over SL distance
        risk_amount = equity * RISK_PER_TRADE
        sl_distance = price * STOP_LOSS_PCT
        if sl_distance > 0:
            size = risk_amount / sl_distance
        else:
            size = 0.0

        if signal == 1:
            position = "long"
            entry_price = price
            log_trade(ts, "open_long", price, 0.0, equity, "signal")
            print(f"Opened LONG at {price} | size: {size:.6f} BTC | Equity: {equity:.2f}")
        else:
            position = "short"
            entry_price = price
            log_trade(ts, "open_short", price, 0.0, equity, "signal")
            print(f"Opened SHORT at {price} | size: {size:.6f} BTC | Equity: {equity:.2f}")

    print(f"{ts} | Pos: {position} | Price: {price} | Unrealized: {unrealized:.2f} | Equity: {equity:.2f}")
    print("Waiting for next candle...\n")
    time.sleep(60)
