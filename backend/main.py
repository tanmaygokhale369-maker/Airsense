# backend/main.py
# FastAPI application entry point
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" # silence TF logs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0" # silence oneDNN
os.environ["CUDA_VISIBLE_DEVICES"] = "-1" # disable GPU scan

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routes import router
from model_loader import load_all_models

# ── STARTUP: load models when server starts ──────
@asynccontextmanager
async def lifespan(app: FastAPI):
  load_all_models() # runs once on startup
  yield # server runs here
  print("Server shutting down...")

# ── CREATE APP ───────────────────────────────────
app = FastAPI(
  title="AirSense API",
  description="Real-time AQI prediction, forecasting and anomaly detection",
  version="1.0.0",
  lifespan=lifespan
)

# ── CORS ─────────────────────────────────────────
# Allows Next.js (localhost:3000) to call this API
app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000", "http://localhost:3001"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# ── REGISTER ROUTES ──────────────────────────────
app.include_router(router)

# ── RUN SERVER ───────────────────────────────────
if __name__ == "__main__":
  import uvicorn
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)