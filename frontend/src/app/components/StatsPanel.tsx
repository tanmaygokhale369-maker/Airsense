'use client'

import { CityData, aqiColor, aqiLabel } from '../../lib/api'

export default function StatsPanel({ cities }: { cities: CityData[] }) {
  if (!cities.length) return null

  const avg = Math.round(cities.reduce((s, c) => s + c.aqi, 0) / cities.length)
  const worst = cities.reduce((a, b) => a.aqi > b.aqi ? a : b)
  const best = cities.reduce((a, b) => a.aqi < b.aqi ? a : b)
  const danger = cities.filter(c => c.aqi > 200).length

  const cards = [
    { label: 'National Avg AQI', value: avg, color: aqiColor(avg), sub: aqiLabel(avg) },
    { label: 'Most Polluted', value: worst.name, color: aqiColor(worst.aqi), sub: `AQI ${worst.aqi}` },
    { label: 'Cleanest City', value: best.name, color: aqiColor(best.aqi), sub: `AQI ${best.aqi}` },
    { label: 'Poor Air Cities', value: danger, color: danger > 0 ? '#ef4444' : '#22c55e', sub: 'AQI > 200' },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      {cards.map(card => (
        <div key={card.label}
          className="bg-white dark:bg-gray-900 rounded-2xl p-4 border border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-400 mb-1">{card.label}</p>
          <p className="text-xl font-black" style={{ color: card.color }}>{card.value}</p>
          <p className="text-xs text-gray-400 mt-0.5">{card.sub}</p>
        </div>
      ))}
    </div>
  )
}