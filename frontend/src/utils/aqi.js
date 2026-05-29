/**
 * India National AQI scale helpers
 */

export const AQI_BANDS = [
  { min: 0,   max: 50,  label: 'Good',         color: '#00b050', bg: 'bg-green-600',  text: 'text-green-400'  },
  { min: 51,  max: 100, label: 'Satisfactory',  color: '#92d050', bg: 'bg-lime-500',   text: 'text-lime-400'   },
  { min: 101, max: 200, label: 'Moderate',      color: '#f5c518', bg: 'bg-yellow-500', text: 'text-yellow-400' },
  { min: 201, max: 300, label: 'Poor',          color: '#ff9900', bg: 'bg-orange-500', text: 'text-orange-400' },
  { min: 301, max: 400, label: 'Very Poor',     color: '#ff4444', bg: 'bg-red-600',    text: 'text-red-400'    },
  { min: 401, max: 999, label: 'Severe',        color: '#cc0000', bg: 'bg-red-900',    text: 'text-red-300'    },
]

export function getAQIBand(aqi) {
  return AQI_BANDS.find(b => aqi >= b.min && aqi <= b.max) || AQI_BANDS[AQI_BANDS.length - 1]
}

export function getAQIColor(aqi) {
  return getAQIBand(aqi).color
}

export function getAQILabel(aqi) {
  return getAQIBand(aqi).label
}

/** Format timestamp to readable string */
export function fmtTime(iso) {
  return new Date(iso).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true,
  })
}

/** Short relative time */
export function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1)  return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}
