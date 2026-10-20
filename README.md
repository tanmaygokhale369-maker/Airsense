# AirSense

AirSense is an air-quality monitoring dashboard for six Indian cities. It combines a Next.js frontend with a FastAPI backend to display AQI estimates, a 48-hour forecast, an India heatmap, and anomaly alerts.

## Features

- AQI estimates for Delhi, Mumbai, Kolkata, Chennai, Bangalore, and Hyderabad
- City-by-city air-quality readings and weather details
- 48-hour AQI forecasts from an LSTM model
- AQI heatmap visualization
- Anomaly detection with severity levels
- FastAPI health check and interactive API documentation

## Project structure

```text
airsense/
├── backend/       # FastAPI API, data, and ML training scripts
└── frontend/      # Next.js dashboard
```

## Requirements

- Python with support for the pinned packages in `backend/requirements.txt`
- Node.js and npm

## Run locally

Start the backend and frontend in separate terminals.

### 1. Prepare and start the backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The trained model binaries are excluded from Git. Before starting the API for the first time, generate them from the included training data while your working directory is `backend`:

```powershell
python ml/train_xgboost.py
python ml/anomaly_detection.py
python ml/train_lstm.py
```

Then start the API:

```powershell
python main.py
```

The API runs at [http://localhost:8000](http://localhost:8000). Interactive API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Start the frontend

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The frontend uses `http://localhost:8000` as its API URL by default. To use a different backend URL, create `frontend/.env.local` with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Restart the frontend after changing the environment variable.

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | API and model health |
| `GET` | `/api/cities` | AQI estimates and readings for all supported cities |
| `POST` | `/api/predict` | Predict AQI from a sensor reading |
| `POST` | `/api/forecast` | Generate a 48-hour AQI forecast |
| `GET` | `/api/heatmap` | Return heatmap data |
| `POST` | `/api/anomaly` | Check a sensor reading for anomalies |

See the interactive [API docs](http://localhost:8000/docs) for request and response schemas.

## Frontend scripts

Run these commands from `frontend/`:

```bash
npm run dev    # Start the development server
npm run build  # Create a production build
npm start      # Serve the production build
npm run lint   # Run ESLint
```
