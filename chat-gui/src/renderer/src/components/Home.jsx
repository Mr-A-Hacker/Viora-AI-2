import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, Settings, Camera, Image as GalleryIcon, Code, Map, Bot } from 'lucide-react';
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
    </div>
  );
}
