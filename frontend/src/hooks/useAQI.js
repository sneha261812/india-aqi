import { useState, useEffect, useCallback } from 'react'
import { getAllCitiesAQI, getCityAQI } from '../api'

/**
 * Hook: all cities AQI with auto-refresh every 5 minutes
 */
export function useAllCitiesAQI(refreshMs = 5 * 60 * 1000) {
  const [data, setData]       = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const fetch = useCallback(async () => {
    try {
      const res = await getAllCitiesAQI()
      setData(res.data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetch()
    const id = setInterval(fetch, refreshMs)
    return () => clearInterval(id)
  }, [fetch, refreshMs])

  return { data, loading, error, refetch: fetch }
}

/**
 * Hook: single city AQI
 */
export function useCityAQI(city) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    if (!city) return
    setLoading(true)
    getCityAQI(city)
      .then(r  => { setData(r.data); setError(null) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [city])

  return { data, loading, error }
}
