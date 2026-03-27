import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Send, Bot, Sparkles, Loader, Wifi, WifiOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000';

export default function DevAI() {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOffline, setIsOffline] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/devai/status`)
      .then(r => r.json())
      .then(d => setIsOffline(!d.status?.includes('ready')))
      .catch(() => setIsOffline(true));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setMessages(prev => [...prev, { role: 'user', text: trimmed }]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API}/devai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', text: data.response || 'No response' }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Failed to reach Dev AI. Is the backend running?' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  return (
    <div
      className="relative w-full h-full flex flex-col overflow-hidden"
      style={{ background: 'var(--bg)', fontFamily: 'var(--font-body)', color: 'var(--text)' }}
    >
      {/* Ambient background */}
      <div className="ambient-bg" />
      <div className="blob blob-1" />
      <div className="blob blob-2" />

      {/* Header */}
      <div
        className="flex-shrink-0 flex items-center gap-3 px-4 py-3 z-10"
        style={{
          background: 'rgba(250,248,255,.96)',
          backdropFilter: 'blur(14px)',
          borderBottom: '1.5px solid var(--border)',
        }}
      >
        <button
          onClick={() => navigate('/')}
          className="p-2.5 rounded-xl border-2 border-[var(--border)] text-[var(--text-mid)] hover:border-[var(--ai-color)] hover:text-[var(--ai-color)] transition-all duration-200 flex items-center justify-center min-h-[44px] min-w-[44px]"
          aria-label="Back"
        >
          <ArrowLeft size={20} />
        </button>
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
          style={{ background: 'var(--ai-bg)' }}
        >
          <Sparkles size={20} style={{ color: 'var(--ai-color)' }} />
        </div>
        <div>
          <h1 style={{ fontFamily: 'var(--font-head)', fontWeight: 800, color: 'var(--ai-color)', fontSize: '1rem' }}>
            Dev AI
          </h1>
          <p style={{ fontSize: '.68rem', color: 'var(--text-mid)' }} className="flex items-center gap-1">
            {isOffline === false ? (
              <>
                <WifiOff size={10} /> Offline
              </>
            ) : isOffline === true ? (
              <>
                <Wifi size={10} /> Online
              </>
            ) : (
              'Loading...'
            )}
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 flex flex-col gap-4 scroller-ai touch-scroll-y">
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center py-16">
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-20 h-20 rounded-2xl flex items-center justify-center text-4xl"
              style={{ background: 'var(--ai-bg)' }}
            >
              <Bot style={{ color: 'var(--ai-color)' }} size={40} />
            </motion.div>
            <div>
              <h2 style={{ fontFamily: 'var(--font-head)', fontWeight: 800, color: 'var(--ai-color)', fontSize: '1.1rem', marginBottom: 6 }}>
                Dev AI
              </h2>
              <p style={{ color: 'var(--text-mid)', fontSize: '.88rem', maxWidth: 280, lineHeight: 1.6 }}>
                Your offline coding assistant. Ask me anything about coding, debugging, or software engineering.
              </p>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', maxWidth: 380 }}>
              {['Write a Python function', 'Explain this code', 'Debug my script', 'Refactor this code'].map(hint => (
                <button
                  key={hint}
                  onClick={() => send(hint)}
                  className="ai-chip"
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className="max-w-[85%] px-5 py-4 rounded-2xl text-base leading-relaxed"
              style={{
                fontFamily: 'var(--font-body)',
                ...(msg.role === 'user'
                  ? {
                      background: 'linear-gradient(135deg, #7c3aed, #6d28d9)',
                      color: '#fff',
                      borderRadius: '18px 18px 4px 18px',
                      boxShadow: '0 4px 14px rgba(124,58,237,.3)',
                    }
                  : {
                      background: 'var(--surface)',
                      color: 'var(--text)',
                      border: '1.5px solid var(--border)',
                      borderRadius: '18px 18px 18px 4px',
                      boxShadow: '0 2px 12px rgba(0,0,0,.06)',
                    }
                ),
              }}
            >
              <div
                className="text-[11px] uppercase tracking-wider mb-2 opacity-70 font-semibold"
                style={{ color: msg.role === 'user' ? '#fff' : 'var(--ai-color)' }}
              >
                {msg.role === 'user' ? 'You' : 'Dev AI'}
              </div>
              <pre
                className="whitespace-pre-wrap break-words"
                style={{ fontFamily: 'var(--font-body)', fontSize: '.9rem', lineHeight: 1.7 }}
              >
                {msg.text}
              </pre>
            </div>
          </motion.div>
        ))}

        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div
              className="px-5 py-4 rounded-2xl rounded-bl-md"
              style={{
                background: 'var(--surface)',
                border: '1.5px solid var(--border)',
                boxShadow: '0 2px 12px rgba(0,0,0,.06)',
              }}
            >
              <div className="flex items-center gap-3">
                <Loader size={16} style={{ color: 'var(--ai-color)' }} className="animate-spin" />
                <span style={{ color: 'var(--text-mid)', fontSize: '.85rem' }}>Dev AI is thinking...</span>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div
        className="flex-shrink-0 flex items-end gap-3 px-4 py-3 z-10"
        style={{
          background: 'rgba(250,248,255,.96)',
          backdropFilter: 'blur(14px)',
          borderTop: '1.5px solid var(--border)',
        }}
      >
        <div
          className="flex-1 rounded-2xl px-4 py-3 flex items-end border"
          style={{
            background: 'var(--surface)',
            borderColor: 'var(--border)',
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Dev AI something..."
            rows={1}
            className="flex-1 border-none bg-transparent resize-none outline-none"
            style={{
              color: 'var(--text)',
              fontFamily: 'var(--font-body)',
              fontSize: '.95rem',
              lineHeight: 1.5,
              maxHeight: 120,
            }}
            onInput={e => {
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
            }}
          />
        </div>
        <button
          onClick={() => send(input)}
          disabled={!input.trim() || loading}
          className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-2xl cursor-pointer transition-all duration-200 disabled:opacity-40"
          style={{
            background: 'linear-gradient(135deg, #7c3aed, #6d28d9)',
            color: '#fff',
            boxShadow: '0 4px 14px rgba(124,58,237,.3)',
          }}
          aria-label="Send"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
