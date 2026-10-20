// src/components/ForecastChart.tsx
"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid,
         Tooltip, ResponsiveContainer, ReferenceLine } from "recharts"
import { aqiColor } from '../../lib/api'

interface Props { forecast: number[]; cityName: string; currentAqi: number }

export default function ForecastChart({ forecast, cityName, currentAqi }: Props) {
  const data = forecast.map((aqi, i) => ({
    hour: i === 0 ? "Now" : i % 6 === 0 ? `+${i}h` : "",
    aqi: Math.round(aqi),
    fill: aqiColor(aqi)
  }))

  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-700">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="font-bold text-base">48h Forecast — {cityName}</h2>
          <p className="text-xs text-gray-400 mt-0.5">LSTM Neural Network prediction</p>
        </div>
        <div className="text-right text-sm">
          <div className="font-bold" style={{ color: aqiColor(currentAqi) }}>
            Current: {currentAqi}
          </div>
          <div className="text-gray-400 text-xs">AQI</div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
          <YAxis domain={[0, 500]} tick={{ fontSize: 10 }} />
          <Tooltip formatter={(v) => [v, "AQI"]} />
          <ReferenceLine y={100} stroke="#eab308" strokeDasharray="4 4"
            label={{ value:"Moderate", fontSize:9, fill:"#eab308" }} />
          <ReferenceLine y={200} stroke="#ef4444" strokeDasharray="4 4"
            label={{ value:"Poor", fontSize:9, fill:"#ef4444" }} />
          <Line type="monotone" dataKey="aqi"
            stroke={aqiColor(currentAqi)} strokeWidth={2.5}
            dot={false} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}