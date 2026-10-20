// src/components/AnomalyAlert.tsx
"use client"

import { AnomalyResult } from "@/lib/api"

const SEV_STYLES: Record<string, string> = {
  CRITICAL: "bg-red-50 border-red-400 text-red-800 dark:bg-red-900/20 dark:text-red-300",
  WARNING: "bg-orange-50 border-orange-400 text-orange-800 dark:bg-orange-900/20 dark:text-orange-300",
  WATCH: "bg-yellow-50 border-yellow-400 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300",
  NORMAL: "bg-green-50 border-green-400 text-green-800 dark:bg-green-900/20 dark:text-green-300",
}
const SEV_ICON: Record<string, string> = {
  CRITICAL: "🚨", WARNING: "⚠️", WATCH: "👀", NORMAL: "✅"
}

export default function AnomalyAlert({ result }: { result: AnomalyResult | null }) {
  if (!result) return null
  const style = SEV_STYLES[result.severity] || SEV_STYLES.NORMAL
  const icon = SEV_ICON[result.severity] || "✅"
  return (
    <div className={`rounded-2xl border-l-4 p-4 ${style}`}>
      <div className="flex items-center gap-2 font-bold text-sm mb-1">
        <span>{icon}</span>
        <span>{result.severity} — {result.city}</span>
      </div>
      <p className="text-xs opacity-80">
        Anomaly score: {result.anomaly_score.toFixed(3)}
         · {result.is_anomaly ? "Spike detected" : "All readings normal"}
      </p>
    </div>
  )
}
