import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import { getAllCitiesAQI, getAlerts } from '../api'
import { getAQIColor, getAQILabel, timeAgo } from '../utils/aqi'
import Spinner from '../components/Spinner'
import AQIBadge from '../components/AQIBadge'
import { AlertTriangle, TrendingUp, Wind } from 'lucide-react'

// Fix Leaflet default marker icons in Vite
import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const AQI_LEGEND = [
  { label: 'Good',         color: '#00b050' },
  { label: 'Satisfactory', color: '#92d050' },
  { label: 'Moderate',     color: '#f5c518' },
  { label: 'Poor',         color: '#ff9900' },
  { label: 'Very Poor',    color: '#ff4444' },
  { label: 'Severe',       color: '#cc0000' },
]

export default function HomePage() {
  const [cities, setCities]   = useState([])
  const [alerts, setAlerts]   = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    async function load() {
      try {
        const [cRes, aRes] = await Promise.all([getAllCitiesAQI(), getAlerts()])
        setCities(cRes.data)
        setAlerts(aRes.data.slice(0, 5))
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
    const id = setInterval(load, 5 * 60 * 1000)  // refresh every 5 min
    return () => clearInterval(id)
  }, [])

  const sorted = [...cities].sort((a, b) => b.aqi - a.aqi)
  const top10  = sorted.slice(0, 10)
  const avg    = cities.length ? Math.round(cities.reduce((s, c) => s + c.aqi, 0) / cities.length) : null

  if (loading) return <Spinner text="Loading live AQI data…" />

  return (
    <div className="space-y-6">
      {/* Header stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Cities Monitored" value={cities.length} icon={<Wind className="h-5 w-5 text-orange-500"/>} />
        <StatCard label="India Avg AQI"   value={avg}            icon={<TrendingUp className="h-5 w-5 text-blue-400"/>} />
        <StatCard label="Active Alerts"   value={alerts.length}  icon={<AlertTriangle className="h-5 w-5 text-red-400"/>} />
        <StatCard label="Worst City"      value={sorted[0]?.city || '—'} sub={sorted[0] ? `AQI ${sorted[0].aqi}` : ''} icon={<Wind className="h-5 w-5 text-yellow-400"/>} />
      </div>

      {/* Map */}
      <div className="card overflow-hidden p-0">
        <div className="border-b px-5 py-3" style={{ borderColor: 'var(--border)' }}>
          <h2 className="font-display font-semibold">Live India AQI Map</h2>
        </div>
        <MapContainer
          center={[22.5, 80.0]}
          zoom={5}
          style={{ height: '500px', width: '100%' }}
          scrollWheelZoom={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
          {cities.filter(c => c.lat && c.lon).map(city => (
            <CircleMarker
              key={city.city}
              center={[city.lat, city.lon]}
              radius={10}
              pathOptions={{
                fillColor: getAQIColor(city.aqi),
                color:     '#fff',
                weight:    1,
                opacity:   0.9,
                fillOpacity: 0.85,
              }}
              eventHandlers={{ click: () => navigate(`/city/${city.city}`) }}
            >
              <Tooltip>
                <strong>{city.city}</strong><br />
                AQI: {city.aqi} — {getAQILabel(city.aqi)}<br />
                <span style={{ fontSize: '0.75rem', color: '#aaa' }}>{timeAgo(city.timestamp)}</span>
              </Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>

        {/* Legend */}
        <div className="flex flex-wrap gap-3 border-t px-5 py-3" style={{ borderColor: 'var(--border)' }}>
          {AQI_LEGEND.map(l => (
            <div key={l.label} className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-full" style={{ background: l.color }} />
              <span className="text-xs text-gray-400">{l.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Top polluted cities */}
        <div className="card">
          <h2 className="mb-4 font-display font-semibold">Most Polluted Cities</h2>
          <div className="space-y-2">
            {top10.map((c, i) => (
              <button
                key={c.city}
                onClick={() => navigate(`/city/${c.city}`)}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition hover:bg-white/5"
              >
                <span className="w-5 text-center text-xs font-bold text-gray-500">{i + 1}</span>
                <span className="flex-1 text-sm font-medium">{c.city}</span>
                <AQIBadge aqi={c.aqi} size="sm" />
              </button>
            ))}
          </div>
        </div>

        {/* Active alerts */}
        <div className="card">
          <h2 className="mb-4 font-display font-semibold">Recent Alerts</h2>
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-400">No active alerts — air quality looks normal.</p>
          ) : (
            <div className="space-y-3">
              {alerts.map(a => (
                <div key={a.id} className="rounded-lg border border-red-900/40 bg-red-950/20 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 flex-shrink-0 text-red-400" />
                    <span className="text-sm font-medium text-red-300">{a.city}</span>
                    <span className="ml-auto text-xs text-gray-500">{timeAgo(a.timestamp)}</span>
                  </div>
                  <p className="mt-1 text-xs text-gray-400">{a.message}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, sub, icon }) {
  return (
    <div className="card flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">{label}</span>
        {icon}
      </div>
      <span className="font-display text-2xl font-bold">{value ?? '—'}</span>
      {sub && <span className="text-xs text-gray-500">{sub}</span>}
    </div>
  )
}
