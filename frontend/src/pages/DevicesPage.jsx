import { useState } from 'react'
import { getDevices } from '../api'
import { Cpu, ExternalLink, CheckCircle } from 'lucide-react'

export default function DevicesPage() {
  const [form, setForm] = useState({
    room_sqft: '', aqi: '', budget_inr: '', smart_only: false,
  })
  const [devices, setDevices] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  function update(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function submit() {
    if (!form.room_sqft || !form.aqi) { setError('Room size and AQI are required'); return }
    setError('')
    setLoading(true)
    try {
      const res = await getDevices({
        room_sqft:  Number(form.room_sqft),
        aqi:        Number(form.aqi),
        budget_inr: form.budget_inr ? Number(form.budget_inr) : undefined,
        smart_only: form.smart_only,
      })
      setDevices(res.data.devices)
    } catch {
      setError('Failed to get recommendations. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Cpu className="h-7 w-7 text-orange-500" />
        <div>
          <h1 className="font-display text-2xl font-bold">Air Purifier Finder</h1>
          <p className="text-sm text-gray-400">Matched to your room size and AQI</p>
        </div>
      </div>

      <div className="card space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="field-label">Room Size (sq ft) *</label>
            <input type="number" placeholder="e.g. 250" value={form.room_sqft}
              onChange={e => update('room_sqft', e.target.value)} className="input" />
          </div>
          <div>
            <label className="field-label">Current AQI *</label>
            <input type="number" placeholder="e.g. 200" value={form.aqi}
              onChange={e => update('aqi', e.target.value)} className="input" />
          </div>
          <div>
            <label className="field-label">Max Budget (₹) — optional</label>
            <input type="number" placeholder="e.g. 20000" value={form.budget_inr}
              onChange={e => update('budget_inr', e.target.value)} className="input" />
          </div>
          <div className="flex flex-col justify-end">
            <button
              onClick={() => update('smart_only', !form.smart_only)}
              className={`rounded-lg border px-4 py-3 text-sm transition ${
                form.smart_only ? 'border-orange-500 bg-orange-500/10 text-orange-300' : 'border-[var(--border)] text-gray-400'
              }`}
            >
              {form.smart_only ? '✓ Smart / WiFi only' : 'Smart / WiFi only'}
            </button>
          </div>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
        <button onClick={submit} disabled={loading} className="btn-primary w-full py-3">
          {loading ? 'Finding best purifiers…' : 'Find Purifiers'}
        </button>
      </div>

      {devices !== null && (
        devices.length === 0
          ? <p className="text-sm text-gray-400 text-center py-8">No devices match your criteria. Try relaxing the budget or room size.</p>
          : <div className="space-y-4">
              <h2 className="font-display font-semibold">Top Recommendations</h2>
              {devices.map((d, i) => <DeviceCard key={d.id} device={d} rank={i + 1} />)}
            </div>
      )}
    </div>
  )
}

function DeviceCard({ device: d, rank }) {
  return (
    <div className="card space-y-4">
      <div className="flex items-start gap-3">
        <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-orange-500/10 font-display font-bold text-orange-400">
          {rank}
        </span>
        <div className="flex-1">
          <h3 className="font-display font-semibold">{d.name}</h3>
          <p className="text-2xl font-bold text-orange-400 mt-1">₹{d.price_inr.toLocaleString('en-IN')}</p>
        </div>
        <a href={d.buy_url} target="_blank" rel="noopener noreferrer"
          className="btn-ghost flex items-center gap-1.5">
          Buy <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <Spec label="CADR" value={`${d.cadr_m3h} m³/h`} />
        <Spec label="Room Size" value={`${d.room_size_sqft[0]}–${d.room_size_sqft[1]} sq ft`} />
        <Spec label="HEPA Filter"         value={d.hepa             ? '✓ Yes' : '✗ No'} />
        <Spec label="Activated Carbon"    value={d.activated_carbon ? '✓ Yes' : '✗ No'} />
      </div>

      <div className="flex flex-wrap gap-2">
        {d.best_for.map(tag => (
          <span key={tag} className="rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs text-gray-400">
            {tag}
          </span>
        ))}
        {d.smart && (
          <span className="flex items-center gap-1 rounded-full bg-blue-500/10 px-2.5 py-0.5 text-xs text-blue-400">
            <CheckCircle className="h-3 w-3" /> Smart / WiFi
          </span>
        )}
      </div>
    </div>
  )
}

function Spec({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="font-medium text-sm">{value}</p>
    </div>
  )
}
