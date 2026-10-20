import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json, os

print("🚀 Loading training data...")

# ── LOAD DATA ───────────────────────────────────
X_train = pd.read_csv("data/X_train.csv")
X_test = pd.read_csv("data/X_test.csv")
y_train = pd.read_csv("data/y_train.csv").squeeze() # squeeze → Series
y_test = pd.read_csv("data/y_test.csv").squeeze()

print(f"Train: {X_train.shape} | Test: {X_test.shape}")

# ── DEFINE MODEL ────────────────────────────────
model = xgb.XGBRegressor(
  n_estimators = 500, # number of trees
  max_depth = 6, # how deep each tree goes
  learning_rate = 0.05, # how fast it learns (lower = more careful)
  subsample = 0.8, # use 80% of rows per tree (avoids overfitting)
  colsample_bytree= 0.8, # use 80% of features per tree
  reg_alpha = 0.1, # L1 regularization
  reg_lambda = 1.0, # L2 regularization
  random_state = 42,
  n_jobs = -1, # use all CPU cores
  verbosity = 0
)

# ── TRAIN ───────────────────────────────────────
print("🌲 Training XGBoost (500 trees)... please wait ~20 seconds")
model.fit(
  X_train, y_train,
  eval_set=[(X_test, y_test)],
  verbose=False
)
print("✅ Training complete!")

# ── EVALUATE ────────────────────────────────────
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n📊 Model Performance:")
print(f" MAE (avg error) : {mae:.2f} AQI units")
print(f" RMSE (big errors) : {rmse:.2f} AQI units")
print(f" R² (accuracy) : {r2:.4f}")

if r2 >= 0.90:
  print(" ✅ Excellent model! Ready for production.")
elif r2 >= 0.75:
  print(" ⚠️ Good model. Consider tuning hyperparameters.")
else:
  print(" ❌ Needs improvement. Check your data.")

# ── FEATURE IMPORTANCE ──────────────────────────
importance = pd.Series(
  model.feature_importances_,
  index=X_train.columns
).sort_values(ascending=False)

print("\n🔍 Top 8 Most Important Features:")
print(importance.head(8).to_string())

# ── SAVE MODEL ──────────────────────────────────
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/xgboost_model.pkl")

# Save metrics for the API to serve
metrics = {
  "mae": round(mae, 2),
  "rmse": round(rmse, 2),
  "r2": round(r2, 4),
  "features": list(X_train.columns),
  "top_features": importance.head(8).index.tolist()
}
with open("models/xgb_metrics.json", "w") as f:
  json.dump(metrics, f, indent=2)

print("\n💾 Saved:")
print(" models/xgboost_model.pkl")
print(" models/xgb_metrics.json")

# ── LIVE PREDICTION FUNCTION ────────────────────
# This is what FastAPI will call when a user asks for AQI
def predict_aqi(sensor_data: dict) -> float:
  """
  Input: dict with keys: pm25, pm10, no2, so2, o3, co,
                    temperature, humidity, wind_speed,
                    hour, month, day_of_week, city
  Output: predicted AQI (float)
  """
  scaler = joblib.load("models/scaler.pkl")
  mdl = joblib.load("models/xgboost_model.pkl")

  # Build feature row (same columns as training)
  df = pd.DataFrame([sensor_data])
  df["is_weekend"] = int(df["day_of_week"].iloc[0] >= 5)
  df["is_rush_hour"] = int(8 <= df["hour"].iloc[0] <= 11 or
                            17 <= df["hour"].iloc[0] <= 21)
  df["is_winter"] = int(df["month"].iloc[0] in [11,12,1,2])
  df["hour_sin"] = np.sin(2*np.pi*df["hour"]/24)
  df["hour_cos"] = np.cos(2*np.pi*df["hour"]/24)
  df["pm25_wind_ratio"] = df["pm25"] / (df["wind_speed"] + 0.1)

  # One-hot encode city
  cities = ["Delhi","Mumbai","Kolkata","Chennai","Bangalore","Hyderabad"]
  for c in cities:
    df[f"city_{c}"] = int(sensor_data.get("city") == c)

  # Drop non-feature columns
  df = df.drop(columns=["city"], errors="ignore")
  df = df.reindex(columns=mdl.get_booster().feature_names, fill_value=0)

  scaled = scaler.transform(df)
  return round(float(mdl.predict(scaled)[0]), 1)

# ── QUICK TEST ──────────────────────────────────
test_input = {
  "city":"Delhi", "pm25":120, "pm10":200,
  "no2":80, "so2":30, "o3":50, "co":2.0,
  "temperature":38, "humidity":42,
  "wind_speed":8, "hour":9,
  "month":12, "day_of_week":1
}
predicted = predict_aqi(test_input)
print(f"\n🧪 Test prediction for Delhi:")
print(f" Input PM2.5={test_input['pm25']}, Temp={test_input['temperature']}°C")
print(f" Predicted AQI → {predicted}")