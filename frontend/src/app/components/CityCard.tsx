'use client'

import { CityData, aqiColor, aqiLabel } from '../../lib/api'
interface Props {
  city: CityData
  selected: boolean // ← must match page.tsx prop name
  onClick: () => void
}

export default function CityCard({ city, selected, onClick }: Props) {
  const color = aqiColor(city.aqi)
  const label = aqiLabel(city.aqi)

  return (
    <div
      onClick={onClick}
      style={{ borderColor: selected ? color : undefined, background: selected ? `${color}15` : undefined }}
      className={`cursor-pointer rounded-2xl p-4 border transition-all hover:shadow-md ${ selected ? 'border-2 shadow-lg scale-105' : 'border border-gray-200 dark:border-gray-700' }`}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-bold text-sm">{city.name}</h3>
          <p className="text-xs text-gray-400">{city.lat.toFixed(1)}°N</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-black" style={{ color }}>{city.aqi}</div>
          <div className="text-xs font-semibold px-2 py-0.5 rounded-full mt-0.5"
              style={{ background:`${color}20`, color }}>{label}</div>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-1 text-xs">
        {([
          ['PM2.5', city.pm25, 'µg'],
          ['PM10', city.pm10, 'µg'],
          ['NO₂', city.no2, 'µg'],
          ['SO₂', city.so2, 'µg'],
          ['Wind', city.wind_speed, 'km'],
          ['Temp', city.temperature, '°C'],
        ] as [string, number, string][]).map(([k, v, u]) => (
          <div key={k} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-1.5 text-center">
            <div className="text-gray-400 text-[9px]">{k}</div>
            <div className="font-bold text-[10px]">{v.toFixed(1)}{u}</div>
          </div>
        ))}
      </div>
      <div className="flex gap-2 mt-2 text-xs text-gray-400">
        <span>💧{city.humidity}%</span>
        <span>💨{city.wind_speed}km/h</span>
      </div>
    </div>
  )
}