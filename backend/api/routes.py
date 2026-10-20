# backend/api/routes.py
# All API endpoint definitions

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import pandas as pd
from datetime import datetime
from model_loader import ModelStore, get_lstm

router = APIRouter()

# ── REQUEST/RESPONSE SCHEMAS ────────────────────
class SensorReading(BaseModel):
  city: str
  pm25: float; pm10: float; no2: float
  so2: float; o3: float; co: float
  temperature: float; humidity: float; wind_speed: float
  hour: Optional[int] = None
  month: Optional[int] = None
  day_of_week: Optional[int] = None

class ForecastRequest(BaseModel):
  city: str
  recent_24h: List[dict] # 24 hourly readings

# ── CITY BASE DATA (used for /api/cities) ───────
CITIES_DATA = [
  {"name":"Delhi", "lat":28.61,"lon":77.20,"pm25":120,"pm10":200,"no2":80, "so2":30,"o3":50,"co":2.0,"temperature":38,"humidity":42,"wind_speed":8},
  {"name":"Mumbai", "lat":18.96,"lon":72.82,"pm25":62, "pm10":110,"no2":55, "so2":18,"o3":48,"co":1.2,"temperature":32,"humidity":74,"wind_speed":14},
  {"name":"Kolkata", "lat":22.57,"lon":88.36,"pm25":88, "pm10":165,"no2":70, "so2":25,"o3":52,"co":1.7,"temperature":35,"humidity":85,"wind_speed":10},
  {"name":"Chennai", "lat":13.08,"lon":80.27,"pm25":38, "pm10":72, "no2":42, "so2":14,"o3":44,"co":0.9,"temperature":34,"humidity":80,"wind_speed":18},
  {"name":"Bangalore","lat":12.97,"lon":77.59,"pm25":28, "pm10":55, "no2":30, "so2":8, "o3":38,"co":0.6,"temperature":26,"humidity":58,"wind_speed":12},
  {"name":"Hyderabad","lat":17.38,"lon":78.49,"pm25":48, "pm10":92, "no2":50, "so2":15,"o3":50,"co":1.1,"temperature":30,"humidity":55,"wind_speed":16},
]

def build_features(d: dict) -> pd.DataFrame:
  """Build feature row matching training columns"""
  now = datetime.now()
  hour = d.get("hour", now.hour)
  month = d.get("month", now.month)
  dow = d.get("day_of_week", now.weekday())
  row = {
    "pm25":d["pm25"],"pm10":d["pm10"],"no2":d["no2"],
    "so2":d["so2"], "o3":d["o3"], "co":d["co"],
    "temperature":d["temperature"],"humidity":d["humidity"],
    "wind_speed":d["wind_speed"],
    "hour":hour,"month":month,"day_of_week":dow,
    "is_weekend":int(dow>=5),
    "is_rush_hour":int((8<=hour<=11) or (17<=hour<=21)),
    "is_winter":int(month in [11,12,1,2]),
    "hour_sin":np.sin(2*np.pi*hour/24),
    "hour_cos":np.cos(2*np.pi*hour/24),
    "pm25_wind_ratio":d["pm25"]/(d["wind_speed"]+0.1),
  }
  cities = ["Delhi","Mumbai","Kolkata","Chennai","Bangalore","Hyderabad"]
  for c in cities:
    row[f"city_{c}"] = int(d.get("city","") == c)
  df = pd.DataFrame([row])
  return df.reindex(columns=ModelStore.xgb_meta["features"], fill_value=0)

# ── ENDPOINT 1: HEALTH CHECK ────────────────────
@router.get("/health")
def health():
  return {"status":"ok","models_loaded":ModelStore.xgb_model is not None}

# ── ENDPOINT 2: ALL CITIES AQI ──────────────────
@router.get("/api/cities")
def get_cities():
  results = []
  for city in CITIES_DATA:
    try:
      df = build_features(city)
      sc = ModelStore.xgb_scaler.transform(df)
      aqi = round(float(ModelStore.xgb_model.predict(sc)[0]),1)
      results.append({**city, "aqi":aqi, "timestamp":datetime.now().isoformat()})
    except Exception as e:
      results.append({**city, "aqi":-1, "error":str(e)})
  return {"cities":results, "count":len(results)}

# ── ENDPOINT 3: PREDICT AQI ─────────────────────
@router.post("/api/predict")
def predict_aqi(reading: SensorReading):
  try:
    df = build_features(reading.dict())
    sc = ModelStore.xgb_scaler.transform(df)
    aqi = round(float(ModelStore.xgb_model.predict(sc)[0]),1)
    return {"city":reading.city,"aqi":aqi,"model":"xgboost",
            "timestamp":datetime.now().isoformat()}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ── ENDPOINT 4: 48H FORECAST ────────────────────
@router.post("/api/forecast")
def forecast_aqi(req: ForecastRequest):
  try:
    FEATS = ["aqi","pm25","pm10","temperature","wind_speed"]
    df_in = pd.DataFrame(req.recent_24h)[FEATS]
    sc_in = ModelStore.lstm_scaler.transform(df_in)
    X = sc_in.reshape(1, 24, len(FEATS))
    lstm = get_lstm() # ← lazy load
    pred = lstm.predict(X, verbose=0)[0]
    dummy = np.zeros((48, len(FEATS)))
    dummy[:,0] = pred
    forecast = ModelStore.lstm_scaler.inverse_transform(dummy)[:,0]
    forecast = [round(float(v),1) for v in np.clip(forecast,0,500)]
    return {"city":req.city, "forecast_48h":forecast, "model":"lstm"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


# ── ENDPOINT 5: HEATMAP ─────────────────────────
@router.get("/api/heatmap")
def get_heatmap():
  if not ModelStore.heatmap_cache:
    raise HTTPException(status_code=503, detail="Heatmap not loaded")
  return ModelStore.heatmap_cache

# ── ENDPOINT 6: ANOMALY DETECTION ───────────────
@router.post("/api/anomaly")
def detect_anomaly(reading: SensorReading):
  try:
    feats = ModelStore.iso_meta["features"]
    d = reading.dict()
    row = np.array([[d.get(f,0) for f in feats]])
    sc = ModelStore.iso_scaler.transform(row)
    score = float(ModelStore.iso_model.score_samples(sc)[0])
    sev = ("CRITICAL" if score<-0.35 else
             "WARNING" if score<-0.20 else
             "WATCH" if score<-0.10 else "NORMAL")
    return {"city":reading.city,"severity":sev,
            "anomaly_score":round(score,4),
            "is_anomaly":sev!="NORMAL",
            "timestamp":datetime.now().isoformat()}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))