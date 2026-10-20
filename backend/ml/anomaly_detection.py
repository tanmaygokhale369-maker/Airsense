# backend/ml/anomaly_detection.py
# Isolation Forest — detects pollution spikes and anomalies

import pandas as pd
import numpy as np
import joblib, json, os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime

print("🌲 Starting Isolation Forest training...")

# ── FEATURES USED FOR ANOMALY DETECTION ─────────
# These are the sensor readings we monitor for spikes
ANOMALY_FEATURES = [
  "pm25", "pm10", "no2", "so2", "o3", "co",
  "temperature", "humidity", "wind_speed"
]

# ── LOAD CLEANED DATA ────────────────────────────
df = pd.read_csv("data/cleaned_data.csv")
print(f"Loaded {len(df)} rows")

# Keep only the sensor columns we care about
# Some columns may be one-hot encoded (city_Delhi etc)
available = [f for f in ANOMALY_FEATURES if f in df.columns]
X = df[available].copy()
print(f"Using features: {available}")

# ── SCALE DATA ───────────────────────────────────
# StandardScaler: mean=0, std=1 (better than MinMax for anomaly detection)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print("Data scaled with StandardScaler")

# ── TRAIN ISOLATION FOREST ──────────────────────
print("🌲 Training Isolation Forest...")
model = IsolationForest(
  n_estimators = 200, # number of isolation trees
  contamination = 0.05, # expect ~5% of readings to be anomalies
  max_samples = "auto", # auto-select sample size per tree
  random_state = 42,
  n_jobs = -1 # use all CPU cores
)
model.fit(X_scaled)
print("✅ Training complete!")

# ── PREDICT ON TRAINING DATA ────────────────────
# -1 = anomaly, +1 = normal
predictions = model.predict(X_scaled)
scores = model.score_samples(X_scaled) # lower = more anomalous

df["anomaly_label"] = predictions # -1 or +1
df["anomaly_score"] = scores # float, lower = more suspicious
df["is_anomaly"] = (predictions == -1).astype(int)

n_anomalies = (predictions == -1).sum()
n_normal = (predictions == 1).sum()
pct = round(n_anomalies / len(predictions) * 100, 2)

print(f"\n📊 Anomaly Detection Results:")
print(f" Normal readings : {n_normal} ({100-pct:.1f}%)")
print(f" Anomaly readings : {n_anomalies} ({pct}%)")

# ── TOP ANOMALIES (most extreme) ────────────────
anomaly_df = df[df["is_anomaly"] == 1].copy()
anomaly_df = anomaly_df.sort_values("anomaly_score")

print(f"\n🔍 Top 5 Most Extreme Anomalies:")
top5 = anomaly_df.head(5)[available + ["anomaly_score"]]
print(top5.to_string(index=False))

# ── ALERT SEVERITY LEVELS ───────────────────────
def get_severity(score: float) -> str:
  """
  Isolation Forest score: closer to -1 = more anomalous
  We map score ranges to human-readable severity
  """
  if score < -0.35: return "CRITICAL" # extreme spike
  if score < -0.20: return "WARNING" # significant anomaly
  if score < -0.10: return "WATCH" # mild anomaly
  return "NORMAL"

def get_likely_cause(row: dict) -> str:
  """Guess the likely cause based on which pollutant spiked most"""
  causes = []
  if row.get("pm25", 0) > 200: causes.append("crop burning / wildfire")
  if row.get("co", 0) > 3.0: causes.append("vehicle / industrial emission")
  if row.get("so2", 0) > 80: causes.append("industrial / power plant")
  if row.get("no2", 0) > 150: causes.append("heavy traffic / diesel")
  if row.get("o3", 0) > 120: causes.append("photochemical smog")
  return ", ".join(causes) if causes else "unknown source"

def build_alert(row: dict, score: float, city: str = "Unknown") -> dict:
  """Build a structured alert object for the API to serve"""
  severity = get_severity(score)
  cause = get_likely_cause(row)
  return {
    "city": city,
    "severity": severity,
    "anomaly_score": round(score, 4),
    "is_anomaly": severity != "NORMAL",
    "likely_cause": cause,
    "readings": {k: round(float(row.get(k,0)),2) for k in available},
    "timestamp": datetime.now().isoformat(),
    "message": (
      f"[{severity}] Anomaly detected in {city}. "
      f"Score: {score:.3f}. Likely: {cause}."
    ) if severity != "NORMAL" else
      f"All readings normal in {city}."
  }

print("\n🚨 Sample alerts from training data:")
for _, row in anomaly_df.head(3).iterrows():
  alert = build_alert(row.to_dict(), row["anomaly_score"], "Delhi")
  print(f" {alert['message']}")

  # ── SAVE MODEL + SCALER ─────────────────────────
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/isolation_forest.pkl")
joblib.dump(scaler, "models/anomaly_scaler.pkl")

# Save model metadata
meta = {
  "features": available,
  "contamination": 0.05,
  "n_estimators": 200,
  "anomaly_pct": pct,
  "severity_thresholds": {
    "CRITICAL": -0.35,
    "WARNING": -0.20,
    "WATCH": -0.10
  }
}
with open("models/anomaly_meta.json", "w") as f:
  json.dump(meta, f, indent=2)

# Save flagged anomalies for dashboard display
top_anomalies = []
for _, row in anomaly_df.head(50).iterrows():
  top_anomalies.append(build_alert(
    row.to_dict(), row["anomaly_score"], "Delhi"
  ))
with open("data/anomalies.json", "w") as f:
  json.dump(top_anomalies, f, indent=2)

print("\n💾 Saved:")
print(" models/isolation_forest.pkl")
print(" models/anomaly_scaler.pkl")
print(" models/anomaly_meta.json")
print(" data/anomalies.json")

# ── LIVE DETECTION FUNCTION (used by FastAPI) ───
def detect_anomaly(sensor_data: dict, city: str = "Unknown") -> dict:
  """
  Input: dict with sensor readings
          {pm25, pm10, no2, so2, o3, co,
           temperature, humidity, wind_speed}
  Output: alert dict with severity + message
  """
  clf = joblib.load("models/isolation_forest.pkl")
  scl = joblib.load("models/anomaly_scaler.pkl")
  meta_j = json.load(open("models/anomaly_meta.json"))
  feats = meta_j["features"]

  # Build feature row in correct order
  row = np.array([[sensor_data.get(f, 0) for f in feats]])
  row_sc = scl.transform(row)

  pred = clf.predict(row_sc)[0] # -1 or +1
  score = clf.score_samples(row_sc)[0] # anomaly score

  return build_alert(sensor_data, score, city)

# ── QUICK TEST ──────────────────────────────────
print("\n🧪 Testing live detection...")

# Test 1: Normal reading
normal = {"pm25":55,"pm10":95,"no2":40,"so2":12,
          "o3":38,"co":0.8,"temperature":28,
          "humidity":55,"wind_speed":14}
r1 = detect_anomaly(normal, "Bangalore")
print(f"Normal test → {r1['severity']} (score: {r1['anomaly_score']})")

# Test 2: Spike reading (Diwali-like event)
spike = {"pm25":380,"pm10":520,"no2":180,"so2":65,
         "o3":88,"co":4.2,"temperature":24,
         "humidity":72,"wind_speed":3}
r2 = detect_anomaly(spike, "Delhi")
print(f"Spike test → {r2['severity']} (score: {r2['anomaly_score']})")
print(f"Likely cause → {r2['likely_cause']}")
print("\n✅ Anomaly detection pipeline complete!")

  