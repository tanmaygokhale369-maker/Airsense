# backend/data/generate_dataset.py
# Generates realistic AQI training data for Indian cities

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42) # makes results reproducible

# City base pollution profiles (realistic Indian city data)
CITIES = {
  "Delhi": {"pm25":120, "pm10":200, "no2":80, "so2":30, "o3":50, "co":2.0},
  "Mumbai": {"pm25":60, "pm10":110, "no2":55, "so2":18, "o3":48, "co":1.2},
  "Kolkata": {"pm25":90, "pm10":160, "no2":70, "so2":25, "o3":52, "co":1.7},
  "Chennai": {"pm25":40, "pm10":75, "no2":42, "so2":14, "o3":44, "co":0.9},
  "Bangalore": {"pm25":28, "pm10":55, "no2":30, "so2":8, "o3":38, "co":0.6},
  "Hyderabad": {"pm25":48, "pm10":92, "no2":50, "so2":15, "o3":50, "co":1.1},
}

rows = []
start = datetime(2023, 1, 1)

for city, base in CITIES.items():
  for i in range(365 * 24): # 1 year of hourly data
    dt = start + timedelta(hours=i)
    hour = dt.hour
    month = dt.month

    # Rush hour effect: worse at 8-11am and 5-9pm
    rush = 1.3 if (8 <= hour <= 11) or (17 <= hour <= 21) else 1.0

    # Winter effect: worse in Dec-Feb (fog traps pollution)
    season = 1.4 if month in [11,12,1,2] else 0.9

    # Random noise to simulate real sensor variation
    noise = lambda v: max(0, v * rush * season + np.random.normal(0, v*0.15))

    pm25 = noise(base["pm25"])
    temp = np.random.normal(28, 6) # temperature °C
    humidity = np.random.normal(60, 20) # humidity %
    wind = max(0, np.random.normal(12, 5)) # wind speed km/h

    rows.append({
      "city": city, "timestamp": dt,
      "hour": hour, "month": month, "day_of_week": dt.weekday(),
      "pm25": round(pm25, 2),
      "pm10": round(noise(base["pm10"]), 2),
      "no2": round(noise(base["no2"]), 2),
      "so2": round(noise(base["so2"]), 2),
      "o3": round(noise(base["o3"]), 2),
      "co": round(noise(base["co"]), 3),
      "temperature": round(temp, 1),
      "humidity": round(np.clip(humidity,10,100), 1),
      "wind_speed": round(wind, 1),
    })

df = pd.DataFrame(rows)
df.to_csv("data/raw_dataset.csv", index=False)
print(f"✅ Generated {len(df)} rows → data/raw_dataset.csv")
print(df.head(3))