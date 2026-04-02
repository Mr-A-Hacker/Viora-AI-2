import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

const API = 'http://127.0.0.1:8000'

export default function Weather() {
  const [weather, setWeather] = useState(null)
  const [location, setLocation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [searching, setSearching] = useState(false)

  /* ── fetch weather by coords ── */
  const fetchWeather = async (lat, lon, label) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API}/weather?lat=${lat}&lon=${lon}`)
      if (!res.ok) throw new Error('Weather fetch failed')
      const data = await res.json()
      setWeather(data)
      setLocation(label || `${lat.toFixed(2)}, ${lon.toFixed(2)}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  /* ── on mount: use browser geolocation ── */
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => fetchWeather(pos.coords.latitude, pos.coords.longitude, null),
        () => fetchWeather(52.52, 13.41, 'Berlin (default)')
      )
    } else {
      fetchWeather(52.52, 13.41, 'Berlin (default)')
    }
  }, [])

  /* ── search a place ── */
  const handleSearch = async (e) => {
    e.preventDefault()
    if (!search.trim()) return
    setSearching(true)
    try {
      const res = await fetch(`${API}/maps/search?q=${encodeURIComponent(search)}`)
      const results = await res.json()
      if (results.length === 0) { setError('Location not found'); return }
      const { lat, lon, display_name } = results[0]
      fetchWeather(lat, lon, display_name.split(',').slice(0, 2).join(', '))
    } catch {
      setError('Search failed')
    } finally {
      setSearching(false)
    }
  }

  /* ── ui ── */
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center py-10 px-4">
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-3xl font-bold mb-6 text-cyan-400"
      >
        🌤️ Weather
      </motion.h1>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex gap-2 mb-8 w-full max-w-md">
        <input
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
          placeholder="Search a city…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button
          type="submit"
          disabled={searching}
          className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 px-4 py-2 rounded-lg font-semibold transition"
        >
          {searching ? '…' : 'Go'}
        </button>
      </form>

      {/* States */}
      {loading && (
        <p className="text-gray-400 animate-pulse">Fetching weather…</p>
      )}

      {error && (
        <p className="text-red-400 bg-red-900/30 px-4 py-2 rounded-lg">{error}</p>
      )}

      {/* Weather card */}
      {weather && !loading && (
        <motion.div
          key={location}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gray-800 rounded-2xl p-8 w-full max-w-md shadow-xl"
        >
          <div className="text-center mb-6">
            <div className="text-7xl mb-2">{weather.emoji}</div>
            <div className="text-5xl font-bold text-cyan-300">
              {Math.round(weather.temperature)}{weather.unit}
            </div>
            <div className="text-gray-400 mt-1">{weather.description}</div>
            {location && (
              <div className="text-gray-500 text-sm mt-2 truncate">{location}</div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 mt-4">
            <Stat label="Feels like" value={`${Math.round(weather.feels_like)}${weather.unit}`} />
            <Stat label="Humidity"   value={`${weather.humidity}%`} />
            <Stat label="Wind"       value={`${weather.wind_speed} mph`} />
            <Stat label="Rain"       value={`${weather.precipitation} mm`} />
          </div>
        </motion.div>
      )}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="bg-gray-700/50 rounded-xl p-3 text-center">
      <div className="text-xs text-gray-400 uppercase tracking-wide">{label}</div>
      <div className="text-lg font-semibold text-white mt-1">{value}</div>
    </div>
  )
}
