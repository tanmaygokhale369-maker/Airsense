import pandas as pd
import numpy as np
import joblib, json, os
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, r2_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

print("🧠 Starting LSTM training pipeline...")
tf.random.set_seed(42)
np.random.seed(42)

# ── SETTINGS ────────────────────────────────────
LOOKBACK = 24 # hours of history to look at
FORECAST = 48 # hours ahead to predict
FEATURES = ["aqi", "pm25", "pm10", "temperature", "wind_speed"]
BATCH = 64
EPOCHS = 50 # max epochs (early stopping kicks in earlier)

# ── LOAD CLEANED DATA ───────────────────────────
print("📂 Loading cleaned_data.csv...")
df = pd.read_csv("data/cleaned_data.csv")
df = df.sort_values(["city" if "city" in df.columns else df.columns[0], "timestamp"])

# Use Delhi data for sequence training (most data points)
city_col = [c for c in df.columns if "city_Delhi" in c]
if city_col:
  city_df = df[df[city_col[0]] == 1][FEATURES].reset_index(drop=True)
else:
  city_df = df[FEATURES].reset_index(drop=True)
print(f"Using {len(city_df)} hourly rows for sequence training")

# ── SCALE FEATURES ──────────────────────────────
lstm_scaler = MinMaxScaler()
scaled = lstm_scaler.fit_transform(city_df)
joblib.dump(lstm_scaler, "models/lstm_scaler.pkl")

# ── BUILD SEQUENCES ─────────────────────────────
def make_sequences(data, lookback, forecast):
  """
  Slides a window across the time series.
  X = 24 hours of features
  y = next 48 hours of AQI (column 0)
  """
  X, y = [], []
  for i in range(len(data) - lookback - forecast):
    X.append(data[i : i+lookback]) # 24 rows × 5 features
    y.append(data[i+lookback : i+lookback+forecast, 0]) # 48 AQI values
  return np.array(X), np.array(y)

X, y = make_sequences(scaled, LOOKBACK, FORECAST)
print(f"Sequences — X: {X.shape} | y: {y.shape}")
# X shape: (samples, 24, 5) y shape: (samples, 48)

# ── TRAIN / VAL SPLIT ───────────────────────────
split = int(len(X) * 0.8)
X_train, X_val = X[:split], X[split:]
y_train, y_val = y[:split], y[split:]
print(f"Train sequences: {len(X_train)} | Val: {len(X_val)}")

# ── BUILD MODEL ─────────────────────────────────
print("\n🏗 Building LSTM architecture...")
model = Sequential([
  # Layer 1: LSTM with 128 units
  # return_sequences=True → passes output to next LSTM layer
  LSTM(128, return_sequences=True,
       input_shape=(LOOKBACK, len(FEATURES))),
  Dropout(0.2),

  # Layer 2: LSTM with 64 units
  # return_sequences=False → outputs single vector
  LSTM(64, return_sequences=False),
  Dropout(0.2),

  # Dense layers to map → 48 AQI predictions
  Dense(32, activation="relu"),
  Dense(FORECAST) # 48 output neurons = 48 hours forecast
])

model.compile(
  optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
  loss="huber" # huber loss = robust to outliers (better than MSE)
)
model.summary()

# ── CALLBACKS ───────────────────────────────────
# EarlyStopping: stops training if val_loss doesn't improve
early_stop = EarlyStopping(
  monitor="val_loss", patience=8,
  restore_best_weights=True, verbose=1
)
# ReduceLROnPlateau: cuts learning rate when stuck
reduce_lr = ReduceLROnPlateau(
  monitor="val_loss", factor=0.5,
  patience=4, min_lr=1e-6, verbose=1
)

# ── TRAIN ───────────────────────────────────────
print("\n🚀 Training LSTM... (3-8 min on CPU, watch val_loss drop)")
history = model.fit(
  X_train, y_train,
  validation_data=(X_val, y_val),
  epochs=EPOCHS,
  batch_size=BATCH,
  callbacks=[early_stop, reduce_lr],
  verbose=1
)
print("✅ LSTM training complete!")

# ── EVALUATE ────────────────────────────────────
y_pred_sc = model.predict(X_val)

# Inverse transform: convert scaled values back to real AQI
def inv_aqi(scaled_col):
  """Inverse transform only the AQI column (column 0)"""
  dummy = np.zeros((len(scaled_col), len(FEATURES)))
  dummy[:, 0] = scaled_col
  return lstm_scaler.inverse_transform(dummy)[:, 0]

# Evaluate on first forecast step (1-hour ahead accuracy)
y_true_real = inv_aqi(y_val[:, 0])
y_pred_real = inv_aqi(y_pred_sc[:, 0])

mae = mean_absolute_error(y_true_real, y_pred_real)
r2 = r2_score(y_true_real, y_pred_real)
print(f"\n📊 LSTM Performance (1h ahead):")
print(f" MAE : {mae:.2f} AQI units")
print(f" R² : {r2:.4f}")

# ── SAVE MODEL ──────────────────────────────────
model.save("models/lstm_model.h5")
metrics = {
  "mae": round(mae, 2), "r2": round(r2, 4),
  "lookback": LOOKBACK, "forecast_hours": FORECAST,
  "features": FEATURES,
  "epochs_trained": len(history.history["loss"])
}
with open("models/lstm_metrics.json", "w") as f:
  json.dump(metrics, f, indent=2)
print("💾 Saved: models/lstm_model.h5")

# ── FORECAST FUNCTION ───────────────────────────
# FastAPI calls this to get a 48-hour forecast
def forecast_aqi(recent_24h: list) -> list:
  """
  Input: list of 24 dicts, each with keys:
          aqi, pm25, pm10, temperature, wind_speed
  Output: list of 48 predicted AQI floats
  """
  mdl = tf.keras.models.load_model("models/lstm_model.h5")
  scaler = joblib.load("models/lstm_scaler.pkl")

  df_in = pd.DataFrame(recent_24h)[FEATURES]
  scaled_in = scaler.transform(df_in)
  X = scaled_in.reshape(1, LOOKBACK, len(FEATURES))

  pred_scaled = mdl.predict(X, verbose=0)[0]
  dummy = np.zeros((FORECAST, len(FEATURES)))
  dummy[:, 0] = pred_scaled
  forecast = scaler.inverse_transform(dummy)[:, 0]
  return [round(float(v), 1) for v in np.clip(forecast, 0, 500)]

# ── QUICK TEST ──────────────────────────────────
print("\n🧪 Testing 48h forecast...")
# Simulate 24 hours of recent Delhi data
sample = [{"aqi":230,"pm25":110,"pm10":190,
           "temperature":22,"wind_speed":6}] * 24
forecast = forecast_aqi(sample)
print(f"Next 48h AQI forecast (first 6 hours):")
print(" " + " → ".join([str(v) for v in forecast[:6]]))
print("✅ LSTM pipeline complete!")