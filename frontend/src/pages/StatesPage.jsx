import { useEffect, useState } from 'react'
import { getStates } from '../api'
import { getAQIColor, getAQILabel } from '../utils/aqi'
import Spinner from '../components/Spinner'
import AQIBadge from '../components/AQIBadge'
import { BarChart2 } from 'lucide-react'

export default function StatesPage() {
  const [states, setStates]   = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getStates()
      .then(r => setStates(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner text="Loading state data…" />

  const maxAqi = Math.max(...states.map(s => s.avg_aqi), 1)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <BarChart2 className="h-7 w-7 text-orange-500" />
        <div>
          <h1 className="font-display text-2xl font-bold">State AQI Rankings</h1>
          <p className="text-sm text-gray-400">{states.length} states monitored</p>
        </div>
      </div>

      {/* Bar chart / ranking */}
      <div className="card space-y-3">
        {states.map((s, i) => (
          <div key={s.state} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className="w-5 text-right text-xs text-gray-500">{i + 1}</span>
                <span className="font-medium">{s.state}</span>
                <span className="text-xs text-gray-500">{s.city_count} cities</span>
              </div>
              <AQIBadge aqi={s.avg_aqi} size="sm" />
            </div>
            <div className="ml-7 h-2 overflow-hidden rounded-full bg-white/5">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${(s.avg_aqi / maxAqi) * 100}%`,
                  background: getAQIColor(s.avg_aqi),
                }}
              />
            </div>
            {/* City chips */}
            <div className="ml-7 flex flex-wrap gap-1.5">
              {s.cities.slice(0, 6).map(city => (
                <a key={city} href={`/city/${city}`}
                  className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-gray-400 hover:border-orange-500 hover:text-orange-300 transition">
                  {city}
                </a>
              ))}
              {s.cities.length > 6 && (
                <span className="text-xs text-gray-500">+{s.cities.length - 6} more</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
