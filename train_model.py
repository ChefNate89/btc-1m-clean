import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle

# Load data
df = pd.read_csv("BTCUSDT_1m.csv")

# Convert to numeric
df["open"] = pd.to_numeric(df["open"])
df["high"] = pd.to_numeric(df["high"])
df["low"] = pd.to_numeric(df["low"])
df["close"] = pd.to_numeric(df["close"])
df["volume"] = pd.to_numeric(df["volume"])

# Create features
df["return"] = df["close"].pct_change()
df["high_low"] = df["high"] - df["low"]
df["close_open"] = df["close"] - df["open"]
df["vol_change"] = df["volume"].pct_change()

# Drop NaN
df = df.dropna()

# Target: 1 if next close is higher, else 0
df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

# Drop last row (no target)
df = df.dropna()

X = df[["return", "high_low", "close_open", "vol_change"]]
y = df["target"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Train model
model = RandomForestClassifier(n_estimators=200)
model.fit(X_train, y_train)

# Save model
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved as model.pkl")
