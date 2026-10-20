# backend/model_loader.py — lazy loads LSTM to save RAM
import joblib, json, os
from pathlib import Path

BASE = Path("models")

class ModelStore:
  xgb_model = None
  xgb_scaler = None
  xgb_meta = None
  lstm_model = None # loaded lazily on first forecast request
  lstm_scaler = None
  lstm_meta = None
  iso_model = None
  iso_scaler = None
  iso_meta = None
  heatmap_cache = None

def load_all_models():
  print("📦 Loading models (LSTM loads on first forecast)...")

  # XGBoost — small, load eagerly
  ModelStore.xgb_model = joblib.load(BASE/"xgboost_model.pkl")
  ModelStore.xgb_scaler = joblib.load(BASE/"scaler.pkl")
  with open(BASE/"xgb_metrics.json") as f:
    ModelStore.xgb_meta = json.load(f)
  print(" ✅ XGBoost loaded")

  # Isolation Forest — small, load eagerly
  ModelStore.iso_model = joblib.load(BASE/"isolation_forest.pkl")
  ModelStore.iso_scaler = joblib.load(BASE/"anomaly_scaler.pkl")
  with open(BASE/"anomaly_meta.json") as f:
    ModelStore.iso_meta = json.load(f)
  print(" ✅ Isolation Forest loaded")

  # LSTM meta only — actual model loads on first /api/forecast call
  ModelStore.lstm_scaler = joblib.load(BASE/"lstm_scaler.pkl")
  with open(BASE/"lstm_metrics.json") as f:
    ModelStore.lstm_meta = json.load(f)
  print(" ✅ LSTM scaler loaded (model loads on first forecast)")

  # Heatmap cache
  with open("data/heatmap.json") as f:
    ModelStore.heatmap_cache = json.load(f)
  print(" ✅ Heatmap cache loaded")
  print("🚀 Core models ready! (uses ~200MB less RAM)")

def get_lstm():
  """Load LSTM only when first forecast is requested"""
  if ModelStore.lstm_model is None:
    print(" 🔄 Loading LSTM on demand...")
    import tensorflow as tf
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    ModelStore.lstm_model = tf.keras.models.load_model(
      str(BASE/"lstm_model.h5")
    )
    print(" ✅ LSTM loaded")
  return ModelStore.lstm_model