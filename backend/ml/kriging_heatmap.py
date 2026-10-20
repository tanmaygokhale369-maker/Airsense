# backend/ml/kriging_heatmap.py ← COMPLETE FILE (all 3 parts together)
import numpy as np
import json, os
from pykrige.ok import OrdinaryKriging

print("🗺 Starting Kriging heatmap generation...")

# ── SENSOR DATA ─────────────────────────────────
SENSORS = [
  ("Delhi", 28.61, 77.20, 234),
  ("Mumbai", 18.96, 72.82, 158),
  ("Kolkata", 22.57, 88.36, 186),
  ("Chennai", 13.08, 80.27, 95),
  ("Bangalore", 12.97, 77.59, 78),
  ("Hyderabad", 17.38, 78.49, 112),
  ("Ahmedabad", 23.02, 72.57, 140),
  ("Pune", 18.52, 73.85, 110),
  ("Jaipur", 26.91, 75.78, 175),
  ("Lucknow", 26.84, 80.94, 210),
  ("Bhopal", 23.25, 77.40, 145),
  ("Patna", 25.59, 85.13, 198),
]

lats = np.array([s[1] for s in SENSORS])
lons = np.array([s[2] for s in SENSORS])
aqis = np.array([s[3] for s in SENSORS], dtype=float)
print(f"Loaded {len(SENSORS)} sensor points")

# ── GRID SETUP ──────────────────────────────────
GRID_SIZE = 50
LAT_MIN, LAT_MAX = 8.0, 37.0
LON_MIN, LON_MAX = 68.0, 97.0

grid_lats = np.linspace(LAT_MIN, LAT_MAX, GRID_SIZE)
grid_lons = np.linspace(LON_MIN, LON_MAX, GRID_SIZE)
print(f"Grid: {GRID_SIZE}×{GRID_SIZE} = {GRID_SIZE**2} cells")

# ── RUN KRIGING ─────────────────────────────────
print("⚙️ Fitting Kriging model...")
OK = OrdinaryKriging(
  lons, lats, aqis,
  variogram_model="spherical",
  verbose=False, enable_plotting=False, nlags=6
)
print("🔄 Interpolating grid...")
z, ss = OK.execute("grid", grid_lons, grid_lats)
z = np.clip(z, 0, 500)
print(f"Interpolated AQI range: {z.min():.1f} – {z.max():.1f}")

# ── HELPER FUNCTIONS ────────────────────────────
def aqi_to_color(aqi):
  if aqi <= 50: return "#22c55e"
  if aqi <= 100: return "#84cc16"
  if aqi <= 200: return "#eab308"
  if aqi <= 300: return "#f97316"
  if aqi <= 400: return "#ef4444"
  return "#7f1d1d"

def grid_to_geojson(z_grid, g_lats, g_lons):
  points = []
  for i, lat in enumerate(g_lats):
    for j, lon in enumerate(g_lons):
      aqi_val = float(z_grid[i, j])
      points.append({
        "lat": round(lat, 3),
        "lon": round(lon, 3),
        "aqi": round(aqi_val, 1),
        "intensity": round(aqi_val / 500, 3),
        "color": aqi_to_color(aqi_val)
      })
  return points

# ── SAVE TO JSON ────────────────────────────────
heatmap_points = grid_to_geojson(z, grid_lats, grid_lons)
print(f"Generated {len(heatmap_points)} heatmap points")

os.makedirs("data", exist_ok=True)
output = {
  "grid_size": GRID_SIZE,
  "bounds": {"lat": [LAT_MIN, LAT_MAX], "lon": [LON_MIN, LON_MAX]},
  "sensors": [{"name":s[0],"lat":s[1],"lon":s[2],"aqi":s[3]} for s in SENSORS],
  "points": heatmap_points
}
with open("data/heatmap.json", "w") as f:
  json.dump(output, f)
print("💾 Saved: data/heatmap.json")

# ── LIVE API FUNCTION ───────────────────────────
def generate_heatmap(sensor_readings: list) -> dict:
  lats_in = np.array([s["lat"] for s in sensor_readings])
  lons_in = np.array([s["lon"] for s in sensor_readings])
  aqis_in = np.array([s["aqi"] for s in sensor_readings], dtype=float)
  ok = OrdinaryKriging(lons_in, lats_in, aqis_in,
                       variogram_model="spherical",
                       verbose=False, enable_plotting=False)
  z_live, _ = ok.execute("grid", grid_lons, grid_lats)
  z_live = np.clip(z_live, 0, 500)
  pts = grid_to_geojson(z_live, grid_lats, grid_lons)
  return {"points": pts, "sensors": sensor_readings}

print("✅ Kriging heatmap pipeline complete!")

# Run this in Python to see what was generated
import json
with open("data/heatmap.json") as f:
  data = json.load(f)
print(f"Total points: {len(data['points'])}")
print("First 3 points:")
for p in data["points"][:3]:
  print(f" lat={p['lat']} lon={p['lon']} aqi={p['aqi']} color={p['color']}")