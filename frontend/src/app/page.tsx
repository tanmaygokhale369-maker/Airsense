'use client'

import { useState, useEffect, useCallback } from 'react'
import { fetchCities, fetchForecast, fetchAnomaly } from '../lib/api'
import type { CityData, AnomalyResult } from '../lib/api'
import CityCard from './components/CityCard'
import ForecastChart from './components/ForecastChart'
import AnomalyAlert from './components/AnomalyAlert'
import HeatmapView from './components/HeatmapView'
import StatsPanel from './components/StatsPanel'

export default function Home() {
  const [cities, setCities] = useState<CityData[]>([])
  const [selected, setSelected] = useState<CityData | null>(null)
  const [forecast, setForecast] = useState<number[]>([])
  const [anomaly, setAnomaly] = useState<AnomalyResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState('')
  const [activeTab, setActiveTab] = useState<'forecast' | 'heatmap'>('forecast')
  const [error, setError] = useState('')

  const selectCity = useCallback(async (city: CityData) => {
    setSelected(city)
    setActiveTab('forecast')
    const recent24h = Array.from({ length: 24 }, () => ({
      aqi: city.aqi + (Math.random() - 0.5) * 20,
      pm25: city.pm25, pm10: city.pm10,
      temperature: city.temperature, wind_speed: city.wind_speed,
    }))
    try {
      const [fc, an] = await Promise.all([
        fetchForecast(city.name, recent24h),
        fetchAnomaly(city),
      ])
      setForecast(fc.forecast_48h || [])
      setAnomaly(an)
    } catch (err) { console.error(err) }
  }, [])

  const loadCities = useCallback(async () => {
    try {
      const data = await fetchCities()
      if (data?.length) {
        setCities(data); setError('')
        setLastUpdate(new Date().toLocaleTimeString())
      } else setError('No data from FastAPI')
    } catch { setError('FastAPI not running on port 8000') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    loadCities()
    const iv = setInterval(loadCities, 30000) // refresh every 30s
    return () => clearInterval(iv)
  }, [loadCities])

  useEffect(() => {
    if (cities.length > 0 && !selected) setSelected(cities[0])
  }, [cities, selected])

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="text-5xl mb-3 animate-spin">🌀</div>
        <p className="text-gray-500">Loading AQI data...</p>
      </div>
    </div>
  )

  if (error) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center p-8 bg-white rounded-2xl shadow max-w-sm">
        <div className="text-4xl mb-3">⚠️</div>
        <h2 className="font-bold text-red-600 mb-2">Backend Not Running</h2>
        <p className="text-sm text-gray-500 mb-3">{error}</p>
        <code className="text-xs bg-gray-100 px-3 py-2 rounded block">cd backend → python main.py</code>
      </div>
    </div>
  )

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-950 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-5">
        <div>
          <h1 className="text-2xl font-black tracking-tight">🌫 AirSense</h1>
          <p className="text-xs text-gray-400 mt-1">Updated {lastUpdate} · refreshes every 30s</p>
        </div>
        <div className="flex items-center gap-2 text-xs bg-green-100 text-green-700 px-3 py-1.5 rounded-full font-semibold">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>LIVE
        </div>
      </div>

      {/* Stats Panel */}
      <StatsPanel cities={cities} />

      {/* Anomaly Alert */}
      {anomaly?.is_anomaly && (<div className="mb-5"><AnomalyAlert result={anomaly} /></div>)}

      {/* City Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {cities.map(city => (
          <CityCard key={city.name} city={city}
            selected={selected?.name === city.name}
            onClick={() => selectCity(city)} />
        ))}
      </div>

      {/* Tab switcher */}
      <div className="flex gap-2 mb-4">
        {(['forecast', 'heatmap'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${activeTab===tab ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900' : 'bg-white dark:bg-gray-800 text-gray-500 border border-gray-200'}`}>
            {tab === 'forecast' ? '📈 48h Forecast' : '🗺 India Heatmap'}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'forecast' && selected && forecast.length > 0 && (
        <ForecastChart forecast={forecast} cityName={selected.name} currentAqi={selected.aqi} />
      )}
      {activeTab === 'heatmap' && <HeatmapView cities={cities} />}
    </main>
  )
}