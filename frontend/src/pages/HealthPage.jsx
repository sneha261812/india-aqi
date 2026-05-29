import { useState } from 'react'
import { analyseRisk } from '../api'
import AQIBadge from '../components/AQIBadge'
import { Activity, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

export default function HealthPage() {
  const [form, setForm] = useState({
    aqi: '', age: '', has_asthma: false, has_heart: false,
    pregnant: false, activity: 'normal',
  })
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  function update(key, val) { setForm(f => ({ ...f, [key]: val })) }

  async function submit() {
    if (!form.aqi) { setError('Please enter an AQI value'); return }
    setError('')
    setLoading(true)
    try {
      const res = await analyseRisk({
        aqi:        Number(form.aqi),
        age:        form.age ? Number(form.age) : undefined,
        has_asthma: form.has_asthma,
        has_heart:  form.has_heart,
        pregnant:   form.pregnant,
        activity:   form.activity,
      })
      setResult(res.data)
    } catch (e) {
      setError('Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <div className="flex items-center gap-3">
          <Activity className="h-7 w-7 text-orange-500" />
          <h1 className="font-display text-2xl font-bold">Health Risk Analyzer</h1>
        </div>
        <p className="mt-1 text-sm text-gray-400">
          Get personalised health advice based on current AQI and your profile.
        </p>
      </div>

      <div className="card space-y-5">
        {/* AQI input */}
        <Field label="Current AQI *">
          <input
            type="number" min="0" max="500"
            placeholder="e.g. 185"
            value={form.aqi}
            onChange={e => update('aqi', e.target.value)}
            className="input"
          />
        </Field>

        {/* Age */}
        <Field label="Your Age (optional)">
          <input
            type="number" min="1" max="120"
            placeholder="e.g. 35"
            value={form.age}
            onChange={e => update('age', e.target.value)}
            className="input"
          />
        </Field>

        {/* Activity */}
        <Field label="Planned Activity">
          <select
            value={form.activity}
            onChange={e => update('activity', e.target.value)}
            className="input"
          >
            <option value="indoor">Stay indoors</option>
            <option value="normal">Normal outdoor</option>
            <option value="exercise">Outdoor exercise</option>
          </select>
        </Field>

        {/* Toggles */}
        <div className="grid grid-cols-3 gap-3">
          <Toggle label="Asthma / COPD"  checked={form.has_asthma} onChange={v => update('has_asthma', v)} />
          <Toggle label="Heart condition" checked={form.has_heart}  onChange={v => update('has_heart',  v)} />
          <Toggle label="Pregnant"        checked={form.pregnant}   onChange={v => update('pregnant',   v)} />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button onClick={submit} disabled={loading} className="btn-primary w-full py-3">
          {loading ? 'Analysing…' : 'Analyse My Risk'}
        </button>
      </div>

      {result && <RiskResult data={result} />}
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-gray-300">{label}</label>
      {children}
    </div>
  )
}

function Toggle({ label, checked, onChange }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`rounded-lg border p-3 text-center text-sm transition ${
        checked ? 'border-orange-500 bg-orange-500/10 text-orange-300' : 'border-[var(--border)] text-gray-400'
      }`}
    >
      {label}
    </button>
  )
}

function RiskResult({ data }) {
  const risk = data.risk_level
  const colors = {
    Low: 'text-green-400', 'Low-Moderate': 'text-lime-400',
    Moderate: 'text-yellow-400', High: 'text-orange-400',
    'Very High': 'text-red-400', Critical: 'text-red-300',
  }
  return (
    <div className="card space-y-5">
      <div className="flex flex-wrap items-center gap-4">
        <AQIBadge aqi={data.aqi} size="lg" />
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wide">Risk Level</p>
          <p className={`font-display text-xl font-bold ${colors[risk] ?? 'text-white'}`}>{risk}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <InfoChip icon={data.outdoor_safe     ? <CheckCircle  className="h-4 w-4 text-green-400" /> : <XCircle className="h-4 w-4 text-red-400" />}  label="Outdoor Safe"   value={data.outdoor_safe     ? 'Yes' : 'No'} />
        <InfoChip icon={data.mask_needed      ? <AlertTriangle className="h-4 w-4 text-yellow-400"/> : <CheckCircle className="h-4 w-4 text-green-400" />} label="Mask Needed" value={data.mask_needed      ? 'Yes' : 'No'} />
        <InfoChip icon={data.purifier_advised ? <AlertTriangle className="h-4 w-4 text-orange-400"/>: <CheckCircle className="h-4 w-4 text-green-400" />} label="Purifier"    value={data.purifier_advised ? 'Advised' : 'Optional'} />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-300">Recommendations</h3>
        <ul className="space-y-1.5">
          {data.advice.map((a, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
              <span className="mt-0.5 text-orange-400">•</span> {a}
            </li>
          ))}
        </ul>
      </div>

      {data.sensitive_advice.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-red-300">Special Precautions</h3>
          <ul className="space-y-1.5">
            {data.sensitive_advice.map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-red-200">
                <span className="mt-0.5 text-red-400">⚠</span> {a}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function InfoChip({ icon, label, value }) {
  return (
    <div className="rounded-lg bg-white/5 p-3 text-center">
      <div className="flex justify-center">{icon}</div>
      <p className="mt-1 text-xs text-gray-400">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  )
}
