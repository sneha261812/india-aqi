import { useState, useEffect } from 'react'
import { getCityForecast } from '../api'

/**
 * Hook: 72-hour Prophet forecast for a city
 */
export function useForecast(city, hours = 72) {
  const [data, setData]       = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    if (!city) return
    setLoading(true)
    getCityForecast(city, hours)
      .then(r  => { setData(r.data.forecast || []); setError(null) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [city, hours])

  return { data, loading, error }
}
