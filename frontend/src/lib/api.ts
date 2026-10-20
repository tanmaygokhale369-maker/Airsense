// src/lib/api.ts
const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── TYPES ─────────────────────────────────────
export interface CityData {
  name: string // ← was missing
  lat: number
  lon: number
  aqi: number
  pm25: number
  pm10: number
  no2: number
  so2: number
  o3: number
  co: number
  temperature: number
  humidity: number
  wind_speed: number // ← was missing
  timestamp: string
}

export interface HeatmapPoint {
  lat: number
  lon: number
  aqi: number
  intensity: number
  color: string
}

export interface AnomalyResult {
  city: string
  severity: string
  anomaly_score: number
  is_anomaly: boolean
  timestamp: string
}

// ── API FUNCTIONS ──────────────────────────────
export async function fetchCities(): Promise<CityData[]> {
  const res = await fetch(`${BASE}/api/cities`, { cache: 'no-store' })
  const data = await res.json()
  return data.cities
}

export async function fetchHeatmap() {
  const res = await fetch(`${BASE}/api/heatmap`, { cache: 'no-store' })
  return res.json()
}

export async function fetchForecast(city: string, recent24h: object[]) {
  const res = await fetch(`${BASE}/api/forecast`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ city, recent_24h: recent24h }),
  })
  return res.json()
}

export async function fetchAnomaly(reading: object): Promise<AnomalyResult> {
  const res = await fetch(`${BASE}/api/anomaly`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reading),
  })
  return res.json()
}

// ── HELPERS ────────────────────────────────────
export function aqiColor(aqi: number): string {
  if (aqi <= 50) return '#22c55e'
  if (aqi <= 100) return '#84cc16'
  if (aqi <= 200) return '#eab308'
  if (aqi <= 300) return '#f97316'
  if (aqi <= 400) return '#ef4444'
  return '#7f1d1d'
}

export function aqiLabel(aqi: number): string {
  if (aqi <= 50) return 'Good'
  if (aqi <= 100) return 'Satisfactory'
  if (aqi <= 200) return 'Moderate'
  if (aqi <= 300) return 'Poor'
  if (aqi <= 400) return 'Very Poor'
  return 'Severe'
}