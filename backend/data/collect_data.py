# backend/data/collect_data.py
# This script fetches real AQI + weather data for Indian cities

import requests, json, os
from datetime import datetime
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
OPENAQ_KEY = os.getenv("OPENAQ_API_KEY")
OWM_KEY = os.getenv("OPENWEATHER_API_KEY")

# Cities we want data for
CITIES = [
  {"name":"Mumbai", "lat":18.96, "lon":72.82},
  {"name":"Delhi", "lat":28.61, "lon":77.20},
  {"name":"Bangalore", "lat":12.97, "lon":77.59},
  {"name":"Chennai", "lat":13.08, "lon":80.27},
  {"name":"Kolkata", "lat":22.57, "lon":88.36},
  {"name":"Hyderabad", "lat":17.38, "lon":78.49},
]

def fetch_air_quality(lat, lon):
  """Fetch PM2.5, PM10, NO2 from OpenAQ"""
  url = "https://api.openaq.org/v3/locations"
  headers = {"X-API-Key": OPENAQ_KEY}
  params = {"coordinates": f"{lat},{lon}", "radius": 25000, "limit": 5}
  res = requests.get(url, headers=headers, params=params)
  return res.json()

def fetch_weather(lat, lon):
  """Fetch temperature, humidity, wind from OpenWeatherMap"""
  url = "https://api.openweathermap.org/data/2.5/weather"
  params = {"lat":lat, "lon":lon, "appid":OWM_KEY, "units":"metric"}
  res = requests.get(url, params=params)
  data = res.json()
  return {
    "temp": data["main"]["temp"],
    "humidity": data["main"]["humidity"],
    "wind": data["wind"]["speed"],
    "pressure": data["main"]["pressure"],
  }

# Run for all cities and save to JSON
results = []
for city in CITIES:
  print(f"Fetching data for {city['name']}...")
  weather = fetch_weather(city["lat"], city["lon"])
  results.append({"city": city["name"], "weather": weather,
    "timestamp": datetime.now().isoformat()})

# Save results
with open("data/raw_data.json", "w") as f:
  json.dump(results, f, indent=2)
print("✅ Data saved to data/raw_data.json")