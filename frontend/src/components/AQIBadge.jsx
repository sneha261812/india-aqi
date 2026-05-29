import { getAQIBand } from '../utils/aqi'

export default function AQIBadge({ aqi, size = 'md' }) {
  const band = getAQIBand(aqi)
  const sizes = {
    sm:  'text-xs px-2 py-0.5',
    md:  'text-sm px-3 py-1',
    lg:  'text-base px-4 py-1.5',
    xl:  'text-2xl px-5 py-2 font-extrabold',
  }
  return (
    <span
      className={`inline-block rounded-full font-bold uppercase tracking-wider text-black ${sizes[size] ?? sizes.md}`}
      style={{ backgroundColor: band.color }}
    >
      {aqi} — {band.label}
    </span>
  )
}
