import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Filler, Tooltip, Legend
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import { getCityAQI, getCityHistory, getCityForecast } from '../api'
import { getAQIColor, getAQILabel, fmtTime } from '../utils/aqi'
import AQIBadge from '../components/AQIBadge'
import Spinner from '../components/Spinner'
import { ArrowLeft, Thermometer, Wind, Droplets } from 'lucide-react'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Filler, Tooltip, Legend)

const CHART_OPTS = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { color: '#6b7280', maxTicksLimit: 8 }, grid: { color: '#1f2937' } },
    y: { ticks: { color: '#6b7280' }, grid: { color: '#1f2937' } },
  },
}

export default function CityPage() {
  const { name }    = useParams()
  const [current, setCurrent]   = useState(null)
  const [history, setHistory]   = useState([])
  const [forecast, setForecast] = useState([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [cRes, hRes, fRes] = await Promise.all([
          getCityAQI(name),
          getCityHistory(name, 7),
          getCityForecast(name, 72),
        ])
        setCurrent(cRes.data)
        setHistory(hRes.data.data || [])
        setForecast(fRes.data.forecast || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [name])

  if (loading) return <Spinner text={`Loading data for ${name}…`} />

  const histLabels = history.map(r => fmtTime(r.timestamp))
  const histData   = history.map(r => r.aqi)

  const forecastLabels = forecast.filter((_, i) => i % 3 === 0).map(r => fmtTime(r.timestamp))
  const forecastYhat   = forecast.filter((_, i) => i % 3 === 0).map(r => r.aqi)
  const forecastLower  = forecast.filter((_, i) => i % 3 === 0).map(r => r.lower)
  const forecastUpper  = forecast.filter((_, i) => i % 3 === 0).map(r => r.upper)

  const pollutants = current
    ? [
        { label: 'PM2.5', value: current.pm25, unit: 'µg/m³' },
        { label: 'PM10',  value: current.pm10,  unit: 'µg/m³' },
        { label: 'NO₂',   value: current.no2,   unit: 'ppb'  },
        { label: 'SO₂',   value: current.so2,   unit: 'ppb'  },
        { label: 'CO',    value: current.co,    unit: 'ppm'  },
        { label: 'O₃',    value: current.o3,    unit: 'ppb'  },
      ].filter(p => p.value !== null && p.value !== undefined)
    : []

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <div>
        <Link to="/" className="mb-3 flex items-center gap-1 text-sm text-gray-400 hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Back to map
        </Link>
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <h1 className="font-display text-3xl font-bold">{name}</h1>
            <p className="text-sm text-gray-400">{current?.station}</p>
          </div>
          {current && <AQIBadge aqi={current.aqi} size="xl" />}
        </div>
      </div>

      {/* Weather strip */}
      {current && (
        <div className="card grid grid-cols-2 gap-4 sm:grid-cols-4">
          <WeatherItem icon={<Thermometer />} label="Temp"      value={current.temperature ? `${current.temperature}°C` : '—'} />
          <WeatherItem icon={<Wind />}        label="Wind"      value={current.windspeed    ? `${current.windspeed} km/h`  : '—'} />
          <WeatherItem icon={<Droplets />}    label="Humidity"  value={current.humidity     ? `${current.humidity}%`       : '—'} />
          <WeatherItem icon={<Wind />}        label="Source"    value={current.source?.toUpperCase() || '—'} />
        </div>
      )}

      {/* Pollutant breakdown */}
      {pollutants.length > 0 && (
        <div className="card">
          <h2 className="mb-4 font-display font-semibold">Pollutant Breakdown</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {pollutants.map(p => (
              <div key={p.label} className="rounded-lg bg-white/5 p-3 text-center">
                <p className="text-xs text-gray-400">{p.label}</p>
                <p className="mt-1 font-display text-xl font-bold">{Number(p.value).toFixed(1)}</p>
                <p className="text-xs text-gray-500">{p.unit}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7-day history chart */}
      <div className="card">
        <h2 className="mb-4 font-display font-semibold">7-Day AQI History</h2>
        <Line
          data={{
            labels: histLabels,
            datasets: [{
              data:            histData,
              borderColor:     '#f97316',
              backgroundColor: 'rgba(249,115,22,0.1)',
              borderWidth:     2,
              fill:            true,
              tension:         0.4,
              pointRadius:     2,
            }],
          }}
          options={CHART_OPTS}
        />
      </div>

      {/* 72-hour forecast chart */}
      {forecastYhat.length > 0 && (
        <div className="card">
          <h2 className="mb-4 font-display font-semibold">72-Hour Forecast</h2>
          <Line
            data={{
              labels: forecastLabels,
              datasets: [
                {
                  label:           'Forecast AQI',
                  data:            forecastYhat,
                  borderColor:     '#3b82f6',
                  backgroundColor: 'rgba(59,130,246,0.08)',
                  borderWidth:     2,
                  fill:            false,
                  tension:         0.4,
                  pointRadius:     2,
                },
                {
                  label:           'Upper bound',
                  data:            forecastUpper,
                  borderColor:     'rgba(59,130,246,0.2)',
                  borderWidth:     1,
                  fill:            '+1',
                  backgroundColor: 'rgba(59,130,246,0.06)',
                  pointRadius:     0,
                  tension:         0.4,
                },
                {
                  label:           'Lower bound',
                  data:            forecastLower,
                  borderColor:     'rgba(59,130,246,0.2)',
                  borderWidth:     1,
                  fill:            false,
                  pointRadius:     0,
                  tension:         0.4,
                },
              ],
            }}
            options={{ ...CHART_OPTS, plugins: { legend: { display: true, labels: { color: '#9ca3af' } } } }}
          />
        </div>
      )}
    </div>
  )
}

function WeatherItem({ icon, label, value }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-gray-400">{icon}</span>
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="font-medium">{value}</p>
      </div>
    </div>
  )
}
