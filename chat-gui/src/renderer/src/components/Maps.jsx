import { useState } from 'react'
import { motion } from 'framer-motion'

const API = 'http://localhost:8000'

export default function Maps() {
  const [loading, setLoading] = useState(false)
  const [status, setStatus]   = useState(null)
  const [search, setSearch]   = useState('')
  const [results, setResults] = useState([])
  const [searchError, setSearchError] = useState(null)

  const launchMaps = async (query) => {
    setLoading(true)
    setStatus(null)
    try {
      const res  = await fetch(`${API}/maps/open`, { method: 'POST' })
      const data = await res.json()
      setStatus({ ok: true, msg: data.msg || 'Organic Maps opened!' })
    } catch {
      setStatus({ ok: false, msg: 'Failed to launch Organic Maps. Is the backend running?' })
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!search.trim()) return
    setLoading(true)
    setSearchError(null)
    setResults([])
    try {
      const res  = await fetch(`${API}/maps/search?q=${encodeURIComponent(search)}`)
      const data = await res.json()
      if (!Array.isArray(data) || data.length === 0) setSearchError('No results found')
      else setResults(data)
    } catch {
      setSearchError('Search failed — is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const selectResult = (r) => {
    setSearch(r.display_name.split(',').slice(0, 2).join(', '))
    setResults([])
  }

  const aiColor = '#7c3aed'
  const aiBg    = 'rgba(124,58,237,.12)'
  const aiSend  = 'linear-gradient(135deg,#7c3aed,#6d28d9)'

  return (
    <div className="relative min-h-screen w-full overflow-hidden"
      style={{
        background: '#faf8ff',
        fontFamily: "'Plus Jakarta Sans', sans-serif",
        color: '#1e1030',
      }}
    >
      {/* Ambient background */}
      <div className="fixed inset-0 pointer-events-none" style={{
        background: `
          radial-gradient(ellipse 60% 50% at 10% 20%, rgba(124,58,237,.09) 0%, transparent 70%),
          radial-gradient(ellipse 50% 60% at 90% 10%, rgba(236,72,153,.07) 0%, transparent 70%),
          radial-gradient(ellipse 70% 40% at 60% 90%, rgba(249,115,22,.06) 0%, transparent 70%)
        `,
        zIndex: 0,
      }} />
      <div className="fixed blob" style={{
        width: 240, height: 240, borderRadius: '50%', filter: 'blur(50px)',
        background: '#c084fc', top: -50, right: '4%', opacity: .18, zIndex: 0,
      }} />
      <div className="fixed blob" style={{
        width: 160, height: 160, borderRadius: '50%', filter: 'blur(50px)',
        background: '#fb923c', bottom: '4%', left: -35, opacity: .18, zIndex: 0,
        animation: 'blobFloat 12s ease-in-out infinite alternate',
        animationDelay: '-4s',
      }} />

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');
        @keyframes dotPulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.4); } }
        @keyframes blobFloat { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(14px,22px) scale(1.07); } }
        @keyframes logoPulse { 0%,100% { box-shadow: 0 4px 14px rgba(124,58,237,.35); } 50% { box-shadow: 0 4px 22px rgba(236,72,153,.5); } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
      `}</style>

      {/* App shell */}
      <div className="relative z-10 flex flex-col min-h-screen" style={{ padding: 'env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)' }}>

        {/* Header */}
        <header style={{
          display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px',
          borderBottom: '1.5px solid #ede9f8', flexShrink: 0,
          background: 'rgba(250,248,255,.96)',
          backdropFilter: 'blur(14px)', minHeight: 56,
        }}>
          <button
            onClick={() => history.back()}
            style={{
              width: 34, height: 34, borderRadius: 10, flexShrink: 0, border: '1.5px solid #ede9f8',
              background: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: '.9rem', color: '#6b5b8e',
              transition: 'all .2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = aiColor; e.currentTarget.style.color = aiColor; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = '#ede9f8'; e.currentTarget.style.color = '#6b5b8e'; }}
          >
            ←
          </button>

          <div style={{
            width: 34, height: 34, borderRadius: 10, flexShrink: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center', fontSize: '1.15rem',
            background: aiBg, animation: 'logoPulse 3s ease-in-out infinite',
          }}>
            🗺️
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{
              fontFamily: "'Syne', sans-serif", fontWeight: 800, color: aiColor,
              fontSize: 'clamp(.85rem, 2.8vw, 1rem)',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>
              Maps
            </div>
            <div style={{
              fontSize: 'clamp(.62rem, 1.8vw, .7rem)', color: '#6b5b8e', marginTop: 1,
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>
              Organic Maps · Offline Navigation
            </div>
          </div>

          <div style={{
            display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0,
            padding: '4px 10px', borderRadius: 20,
            fontSize: 'clamp(.6rem, 1.6vw, .68rem)', fontWeight: 600,
            background: aiBg, color: aiColor,
            border: '1.5px solid rgba(124,58,237,.28)',
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: aiColor, display: 'inline-block', animation: 'dotPulse 2s ease-in-out infinite' }} />
            Ready
          </div>
        </header>

        {/* Main content */}
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', gap: 28, padding: '24px 16px',
          animation: 'fadeUp .4s ease both',
        }}>

          {/* Orb icon */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            style={{
              width: 'clamp(70px, 18vw, 90px)', height: 'clamp(70px, 18vw, 90px)',
              borderRadius: 20, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 'clamp(2rem, 6vw, 2.8rem)',
              background: aiBg,
              boxShadow: '0 6px 28px rgba(0,0,0,.1)',
              border: '2px solid rgba(124,58,237,.2)',
            }}
          >
            🗺️
          </motion.div>

          {/* Title */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            style={{ textAlign: 'center' }}
          >
            <h2 style={{
              fontFamily: "'Syne', sans-serif", fontWeight: 800, color: aiColor,
              fontSize: 'clamp(1.2rem, 5vw, 1.6rem)',
            }}>
              Organic Maps
            </h2>
            <p style={{
              fontSize: 'clamp(.78rem, 2.2vw, .9rem)', color: '#6b5b8e',
              maxWidth: 300, lineHeight: 1.65, marginTop: 8,
            }}>
              Beautiful offline maps powered by OpenStreetMap. No internet required.
            </p>
          </motion.div>

          {/* Search bar */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            style={{ width: '100%', maxWidth: 420, position: 'relative' }}
          >
            <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8 }}>
              <input
                value={search}
                onChange={e => { setSearch(e.target.value); setResults([]); }}
                placeholder="Search a place…"
                style={{
                  flex: 1, padding: '11px 16px', borderRadius: 14,
                  border: '1.5px solid #ede9f8', background: '#fff',
                  color: '#1e1030', fontFamily: "'Plus Jakarta Sans', sans-serif",
                  fontSize: 'clamp(.84rem, 2.2vw, .9rem)', outline: 'none',
                  transition: 'border-color .2s',
                }}
                onFocus={e => e.target.style.borderColor = aiColor}
                onBlur={e => e.target.style.borderColor = '#ede9f8'}
              />
              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: '11px 18px', borderRadius: 14, border: 'none',
                  background: aiSend, color: '#fff', fontWeight: 700,
                  fontSize: '.88rem', cursor: 'pointer',
                  fontFamily: "'Plus Jakarta Sans', sans-serif",
                  transition: 'transform .18s, opacity .2s',
                  opacity: loading ? .6 : 1,
                }}
                onMouseEnter={e => { if (!loading) e.currentTarget.style.transform = 'scale(1.04)'; }}
                onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
              >
                {loading ? '…' : '🔍'}
              </button>
            </form>

            {results.length > 0 && (
              <ul style={{
                position: 'absolute', top: '100%', left: 0, right: 0,
                background: '#fff', border: '1.5px solid #ede9f8',
                borderRadius: 14, marginTop: 6, zIndex: 50,
                overflow: 'hidden', boxShadow: '0 8px 24px rgba(0,0,0,.1)',
                maxHeight: 240, overflowY: 'auto',
              }}>
                {results.map((r, i) => (
                  <li
                    key={i}
                    onClick={() => selectResult(r)}
                    style={{
                      padding: '10px 16px', cursor: 'pointer', fontSize: '.82rem',
                      color: '#1e1030', borderBottom: i < results.length - 1 ? '1px solid #ede9f8' : 'none',
                      transition: 'background .15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = '#f5f3ff'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    {r.display_name}
                  </li>
                ))}
              </ul>
            )}

            {searchError && (
              <p style={{ color: '#dc2626', fontSize: '.78rem', marginTop: 6, fontWeight: 500 }}>
                {searchError}
              </p>
            )}
          </motion.div>

          {/* Launch button */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
            style={{ width: '100%', maxWidth: 420 }}
          >
            <button
              onClick={() => launchMaps(search)}
              disabled={loading}
              style={{
                width: '100%', padding: '15px 32px', borderRadius: 16, border: 'none',
                background: aiSend, color: '#fff',
                fontFamily: "'Syne', sans-serif", fontWeight: 800,
                fontSize: 'clamp(.95rem, 2.5vw, 1.05rem)',
                cursor: loading ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 20px rgba(124,58,237,.35)',
                transition: 'transform .18s, box-shadow .2s, opacity .2s',
                opacity: loading ? .7 : 1,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
              }}
              onMouseEnter={e => { if (!loading) { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 28px rgba(124,58,237,.45)'; } }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(124,58,237,.35)'; }}
            >
              {loading ? (
                <>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#fff', display: 'inline-block', animation: 'dotPulse 1.2s ease-in-out infinite' }} />
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#fff', display: 'inline-block', animation: 'dotPulse 1.2s ease-in-out infinite .18s' }} />
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#fff', display: 'inline-block', animation: 'dotPulse 1.2s ease-in-out infinite .36s' }} />
                </>
              ) : (
                <>🚀 Open Organic Maps</>
              )}
            </button>
          </motion.div>

          {/* Status message */}
          {status && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              style={{
                padding: '10px 16px', borderRadius: 12,
                background: status.ok ? 'rgba(16,185,129,.1)' : 'rgba(244,63,94,.1)',
                border: `1.5px solid ${status.ok ? 'rgba(16,185,129,.3)' : 'rgba(244,63,94,.3)'}`,
                color: status.ok ? '#059669' : '#e11d48',
                fontSize: '.82rem', fontWeight: 600, maxWidth: 420, textAlign: 'center',
              }}
            >
              {status.msg}
            </motion.div>
          )}

          {/* Feature chips */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            style={{
              display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center',
              maxWidth: 420,
            }}
          >
            {['Offline Maps', 'Satellite View', 'Turn-by-Turn Nav', 'No Tracking'].map(chip => (
              <span
                key={chip}
                style={{
                  padding: '6px 12px', borderRadius: 20, fontSize: '.75rem',
                  fontWeight: 500, color: '#6b5b8e',
                  border: '1.5px solid #ede9f8', background: '#fff',
                  fontFamily: "'Plus Jakarta Sans', sans-serif",
                }}
              >
                {chip}
              </span>
            ))}
          </motion.div>
        </div>
      </div>
    </div>
  )
}
