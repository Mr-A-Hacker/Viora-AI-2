import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, Settings, Camera, Image as GalleryIcon, Code, Map, Bot, Cloud, MapPin, Search, Gamepad2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Avatar from './Avatar';
import { useWebSocket } from '../contexts/WebSocketContext.jsx';
import { useRef, useState, useEffect } from 'react';

const AI_COLOR = '#7c3aed';
const AI_BG    = 'rgba(124, 58, 237, .12)';
const AI_SEND  = 'linear-gradient(135deg, #7c3aed, #6d28d9)';

const MenuButton = ({ icon: Icon, label, onClick, color }) => (
  <motion.button
    whileHover={{ scale: 1.05, y: -2 }}
    whileTap={{ scale: 0.95 }}
    onClick={onClick}
    style={{
      width: '100%',
      minHeight: 100,
      flex: 1,
      minWidth: 0,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 10,
      border: '1.5px solid var(--border)',
      borderRadius: 20,
      background: 'var(--surface)',
      color: color,
      cursor: 'pointer',
      fontFamily: 'var(--font-body)',
      transition: 'all .2s',
      boxShadow: '0 2px 12px rgba(0,0,0,.06)',
    }}
  >
    <Icon size={36} />
    <span style={{ fontSize: '.75rem', fontWeight: 600, letterSpacing: '.04em' }}>{label}</span>
  </motion.button>
);

export default function Home() {
  const navigate = useNavigate();
  const {
    toggleVoice,
    startVosk,
    stopVosk,
    isRecording,
    isVoskRecording,
    voiceStatus,
    voskText,
    voiceStreamText,
    isVoiceStreaming
  } = useWebSocket();

  const [showBubble, setShowBubble] = useState(false);
  const bubbleTimeoutRef = useRef(null);

  useEffect(() => {
    const active = isVoiceStreaming || voiceStatus === 'speaking';
    if (active) {
      if (bubbleTimeoutRef.current) clearTimeout(bubbleTimeoutRef.current);
      setShowBubble(true);
    } else if (showBubble) {
      bubbleTimeoutRef.current = setTimeout(() => {
        setShowBubble(false);
      }, 1000);
    }
    return () => {
      if (bubbleTimeoutRef.current) clearTimeout(bubbleTimeoutRef.current);
    };
  }, [isVoiceStreaming, voiceStatus, showBubble]);

  const displayVoiceText = voiceStreamText.trim();

  // Weather modal state
  const [showWeatherModal, setShowWeatherModal] = useState(false);
  const [weatherData, setWeatherData] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError] = useState(null);
  const [locationInput, setLocationInput] = useState('');

  // Games modal state
  const [showGamesModal, setShowGamesModal] = useState(false);
  const [gamesList, setGamesList] = useState([]);
  const [gamesLoading, setGamesLoading] = useState(false);

  const fetchGames = async () => {
    setGamesLoading(true);
    try {
      const resp = await fetch('http://localhost:8000/games');
      const data = await resp.json();
      setGamesList(data.games || []);
    } catch (err) {
      console.error('Failed to load games:', err);
    } finally {
      setGamesLoading(false);
    }
  };

  const launchGame = async (game) => {
    try {
      await fetch('http://localhost:8000/games/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_id: game.id, executable: game.executable })
      });
    } catch (err) {
      console.error('Failed to launch game:', err);
    }
  };

  const handleGamesClick = () => {
    setShowGamesModal(true);
    fetchGames();
  };

  const fetchWeather = async (city = null) => {
    setWeatherLoading(true);
    setWeatherError(null);
    try {
      let url = 'http://localhost:8000/weather';
      if (city) {
        url += `?city=${encodeURIComponent(city)}`;
      } else if (navigator.geolocation) {
        // Use geolocation for "My location"
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
        });
        url += `?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`;
      }
      const resp = await fetch(url);
      const data = await resp.json();
      if (data.error) {
        setWeatherError(data.error);
      } else {
        setWeatherData(data);
      }
    } catch (err) {
      setWeatherError(err.message || 'Failed to fetch weather');
    } finally {
      setWeatherLoading(false);
    }
  };

  const handleWeatherClick = () => {
    setShowWeatherModal(true);
    setWeatherData(null);
    setWeatherError(null);
    setLocationInput('');
    // Auto-fetch for "My location" by default
    fetchWeather();
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (locationInput.trim()) {
      fetchWeather(locationInput.trim());
    }
  };

  const handleMyLocation = () => {
    setLocationInput('');
    fetchWeather();
  };

  const pressTimer = useRef(null);
  const [isHoldMode, setIsHoldMode] = useState(false);

  const handleMouseDown = () => {
    console.log('[Voice] Mouse down, starting timer...');
    setIsHoldMode(false);
    pressTimer.current = setTimeout(() => {
      console.log('[Voice] Long press detected, starting Vosk...');
      setIsHoldMode(true);
      startVosk();
    }, 400);
  };

  const handleMouseUp = () => {
    console.log('[Voice] Mouse up, isHoldMode:', isHoldMode);
    if (pressTimer.current) {
      clearTimeout(pressTimer.current);
      pressTimer.current = null;
    }
    if (isHoldMode) {
      console.log('[Voice] Stopping Vosk...');
      stopVosk();
      setIsHoldMode(false);
    } else {
      console.log('[Voice] Toggle voice (short press)...');
      toggleVoice();
    }
  };

  const handleMouseLeave = () => {
    if (isHoldMode) {
      stopVosk();
      setIsHoldMode(false);
    }
    if (pressTimer.current) {
      clearTimeout(pressTimer.current);
      pressTimer.current = null;
    }
  };

  return (
    <div
      className="relative w-full h-full overflow-hidden flex flex-col items-center justify-center"
      style={{
        background: 'var(--bg)',
        fontFamily: 'var(--font-body)',
        color: 'var(--text)',
      }}
    >
      {/* Ambient background */}
      <div className="ambient-bg" />
      <div className="blob blob-1" />
      <div className="blob blob-2" />

      {/* Settings button top left */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => navigate('/settings')}
        style={{
          position: 'absolute',
          top: 16,
          left: 16,
          zIndex: 30,
          width: 44,
          height: 44,
          borderRadius: 14,
          border: '1.5px solid var(--border)',
          background: 'rgba(255,255,255,.9)',
          backdropFilter: 'blur(10px)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: AI_COLOR,
          boxShadow: '0 2px 12px rgba(0,0,0,.08)',
          transition: 'all .2s',
        }}
        aria-label="Settings"
      >
        <Settings size={22} />
      </motion.button>

      {/* Avatar name + status */}
      <div
        className="flex flex-col items-center gap-2 mb-6 z-10"
        style={{ animation: 'fadeUp .4s ease both' }}
      >
        <h1
          style={{
            fontFamily: 'var(--font-head)',
            fontWeight: 800,
            color: AI_COLOR,
            fontSize: 'clamp(1.1rem, 4vw, 1.5rem)',
            letterSpacing: '-.02em',
          }}
        >
          VIORA AI
        </h1>
        <span
          style={{
            fontSize: 'clamp(.6rem, 1.8vw, .7rem)',
            fontWeight: 600,
            color: 'var(--text-mid)',
            letterSpacing: '.08em',
            textTransform: 'uppercase',
          }}
        >
          SYSTEMS ONLINE
        </span>
      </div>

      {/* Avatar */}
      <div
        className={`mb-10 relative ${showBubble ? 'z-20' : 'z-10'}`}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        style={{ animation: 'fadeUp .4s ease both .1s' }}
      >
        <Avatar
          variant="xl"
          animate={true}
          expression={voiceStatus}
          className={`cursor-pointer transition-all duration-300 ${isRecording ? 'scale-110' : 'hover:scale-105'}`}
        />

        {/* Vosk Transcription Overlay */}
        <AnimatePresence>
          {isVoskRecording && voskText && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8 }}
              style={{
                position: 'absolute',
                left: 90,
                top: 60,
                width: 200,
                background: 'rgba(30, 16, 48, .92)',
                backdropFilter: 'blur(12px)',
                padding: 12,
                borderRadius: 14,
                border: '1.5px solid rgba(124,58,237,.4)',
                boxShadow: '0 8px 24px rgba(0,0,0,.3)',
                zIndex: 50,
              }}
            >
              <p
                style={{
                  color: '#c084fc',
                  fontSize: '.78rem',
                  lineHeight: 1.6,
                  wordBreak: 'break-word',
                  whiteSpace: 'pre-wrap',
                  maxHeight: 120,
                  overflowY: 'auto',
                }}
              >
                {voskText}
              </p>
              <div
                style={{
                  position: 'absolute',
                  left: -8,
                  top: -2,
                  width: 0,
                  height: 0,
                  borderRight: '10px solid rgba(124,58,237,.4)',
                  borderBottom: '10px solid transparent',
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* AI Response Bubble */}
        <AnimatePresence>
          {showBubble && displayVoiceText && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="response-bubble"
            >
              <div className="response-bubble-arrow" />
              <p>{displayVoiceText}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Main Menu Grid - 5 buttons */}
      <div
        className="grid gap-3 z-10 w-full max-w-[460px] px-4"
        style={{
          gridTemplateColumns: 'repeat(3, 1fr)',
          gridTemplateRows: 'repeat(2, 1fr)',
          animation: 'fadeUp .4s ease both .2s',
        }}
      >
        <MenuButton icon={MessageCircle} label="CHAT" onClick={() => navigate('/chat')} color={AI_COLOR} />
        <MenuButton icon={Camera} label="VISION" onClick={() => navigate('/camera')} color="#38bdf8" />
        <MenuButton icon={Code} label="AGENT" onClick={() => navigate('/tasks')} color="#f7768e" />
        <MenuButton icon={GalleryIcon} label="GALLERY" onClick={() => navigate('/gallery')} color="var(--text-mid)" />
        <MenuButton icon={Cloud} label="WEATHER" onClick={handleWeatherClick} color="#38bdf8" />
        <MenuButton icon={Gamepad2} label="GAMES" onClick={handleGamesClick} color="#f472b6" />
        <MenuButton
          icon={Map}
          label="MAPS"
          onClick={async () => { await fetch('http://localhost:8000/maps/open', { method: 'POST' }); }}
          color="#9ece6a"
        />
        <MenuButton
          icon={Bot}
          label="DEV AI"
          onClick={() => navigate('/devai')}
          color="#f97316"
        />
      </div>

      {/* Weather Modal */}
      <AnimatePresence>
        {showWeatherModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              padding: 20,
            }}
            onClick={() => setShowWeatherModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              style={{
                background: 'var(--surface)',
                borderRadius: 24,
                padding: 24,
                maxWidth: 400,
                width: '100%',
                border: '1.5px solid var(--border)',
                boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)' }}>Weather</h2>
                <button
                  onClick={() => setShowWeatherModal(false)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-mid)', fontSize: '1.5rem' }}
                >
                  ×
                </button>
              </div>

              <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <input
                  type="text"
                  value={locationInput}
                  onChange={(e) => setLocationInput(e.target.value)}
                  placeholder="Search city..."
                  style={{
                    flex: 1,
                    padding: '12px 16px',
                    borderRadius: 12,
                    border: '1.5px solid var(--border)',
                    background: 'var(--bg)',
                    color: 'var(--text)',
                    fontSize: '1rem',
                    outline: 'none',
                  }}
                />
                <button
                  type="submit"
                  style={{
                    padding: 12,
                    borderRadius: 12,
                    border: 'none',
                    background: AI_COLOR,
                    color: 'white',
                    cursor: 'pointer',
                  }}
                >
                  <Search size={20} />
                </button>
              </form>

              <button
                onClick={handleMyLocation}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  width: '100%',
                  padding: 12,
                  marginBottom: 16,
                  borderRadius: 12,
                  border: '1.5px solid var(--border)',
                  background: 'var(--bg)',
                  color: 'var(--text)',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                }}
              >
                <MapPin size={18} />
                Use My Location
              </button>

              {weatherLoading && (
                <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-mid)' }}>
                  Loading weather...
                </div>
              )}

              {weatherError && (
                <div style={{ textAlign: 'center', padding: 16, color: '#f7768e', background: 'rgba(247,118,142,0.1)', borderRadius: 12 }}>
                  {weatherError}
                </div>
              )}

              {weatherData && (
                <div style={{ textAlign: 'center', padding: 20, background: 'var(--bg)', borderRadius: 16 }}>
                  <div style={{ fontSize: '3rem', marginBottom: 8 }}>{weatherData.emoji}</div>
                  <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text)' }}>
                    {weatherData.temperature}{weatherData.unit}
                  </div>
                  <div style={{ fontSize: '1.1rem', color: 'var(--text-mid)', marginTop: 4 }}>
                    {weatherData.description}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: AI_COLOR, marginTop: 8, fontWeight: 600 }}>
                    {weatherData.location}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 16, fontSize: '0.85rem', color: 'var(--text-mid)' }}>
                    <span>💧 {weatherData.humidity}%</span>
                    <span>💨 {weatherData.wind_speed} mph</span>
                  </div>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Games Modal */}
      <AnimatePresence>
        {showGamesModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              padding: 20,
            }}
            onClick={() => setShowGamesModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              style={{
                background: 'var(--surface)',
                borderRadius: 24,
                padding: 24,
                maxWidth: 500,
                width: '100%',
                maxHeight: '80vh',
                border: '1.5px solid var(--border)',
                boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)' }}>Games</h2>
                <button
                  onClick={() => setShowGamesModal(false)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-mid)', fontSize: '1.5rem' }}
                >
                  ×
                </button>
              </div>

              {gamesLoading && (
                <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-mid)' }}>
                  Loading games...
                </div>
              )}

              {!gamesLoading && gamesList.length === 0 && (
                <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-mid)' }}>
                  No games found. Add games to /opt or /usr/games
                </div>
              )}

              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', 
                gap: 12,
                overflowY: 'auto',
                paddingBottom: 16,
              }}>
                {gamesList.map((game) => (
                  <motion.button
                    key={game.id}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => launchGame(game)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 8,
                      padding: 12,
                      borderRadius: 16,
                      border: '1.5px solid var(--border)',
                      background: 'var(--bg)',
                      cursor: 'pointer',
                      minHeight: 90,
                    }}
                  >
                    <span style={{ fontSize: '2rem' }}>{game.icon}</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text)', fontWeight: 500, textAlign: 'center', lineHeight: 1.2 }}>
                      {game.name}
                    </span>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
