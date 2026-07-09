import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Power, Keyboard, Moon, Sun, Volume2, BookOpen, RefreshCw, CheckCircle, AlertCircle, Bell, Brain } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config.js';
import { useKeyboardSettings } from '../contexts/KeyboardContext.jsx';
import { useDarkMode } from '../contexts/DarkModeContext.jsx';
import { useWebSocket } from '../contexts/WebSocketContext.jsx';

export default function Settings() {
    const navigate = useNavigate();
    const { keyboardEnabled, setKeyboardEnabled } = useKeyboardSettings();
    const { isDark, toggleDark } = useDarkMode();
    const { ttsEnabled, setTtsEnabled } = useWebSocket();
    const [knowledgeStatus, setKnowledgeStatus] = useState('idle');
    const [knowledgeProgress, setKnowledgeProgress] = useState({ current: 0, total: 1000 });
    const [updateCheck, setUpdateCheck] = useState(null); // null | 'checking' | 'up_to_date' | 'update_available'
    const pollingRef = useRef(false);
    const mountedRef = useRef(true);

    // Ollama settings
    const [ollamaEnabled, setOllamaEnabled] = useState(false);
    const [ollamaLoading, setOllamaLoading] = useState(false);
    const [activeBrain, setActiveBrain] = useState('Loading...');

    // Fetch Ollama status on mount
    useEffect(() => {
        const fetchOllama = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/settings/ollama`);
                if (res.ok) {
                    const data = await res.json();
                    setOllamaEnabled(data.enabled);
                    setActiveBrain(data.enabled ? 'Ollama (gemma2:2b)' : 'Original (Qwen 1.5B)');
                }
            } catch (e) {
                console.error('Failed to fetch Ollama settings:', e);
                setActiveBrain('Original (Qwen 1.5B)');
            }
        };
        fetchOllama();
    }, []);

    const pollUntilDone = async () => {
        if (pollingRef.current) return;
        pollingRef.current = true;
        try {
            let done = false;
            while (!done && mountedRef.current) {
                await new Promise(resolve => setTimeout(resolve, 2000));
                if (!mountedRef.current) return;
                const resp = await fetch(`${API_BASE_URL}/knowledge`);
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const status = await resp.json();
                setKnowledgeProgress({ current: status.progress || status.entry_count || 0, total: 1000 });
                if (!status.updating) {
                    setKnowledgeStatus(status.entry_count > 0 ? 'success' : 'error');
                    done = true;
                    try {
                        const checkResp = await fetch(`${API_BASE_URL}/knowledge/check`);
                        if (checkResp.ok) setUpdateCheck((await checkResp.json()).status);
                    } catch (e) {
                        console.error('Update check after poll failed:', e);
                    }
                }
            }
        } catch (e) {
            console.error('Polling failed:', e);
            if (mountedRef.current) setKnowledgeStatus('error');
        }
        pollingRef.current = false;
    };

    useEffect(() => {
        mountedRef.current = true;
        (async () => {
            try {
                const resp = await fetch(`${API_BASE_URL}/knowledge`);
                if (resp.ok && mountedRef.current) {
                    const data = await resp.json();
                    if (data.updating) {
                        setKnowledgeStatus('loading');
                        pollUntilDone();
                    } else if (data.entry_count > 0) {
                        setKnowledgeStatus('success');
                        setKnowledgeProgress({ current: data.entry_count, total: data.entry_count });
                    }
                }
            } catch (e) {
                console.error('Initial knowledge fetch failed:', e);
            }
            if (mountedRef.current) setUpdateCheck('checking');
            try {
                const resp = await fetch(`${API_BASE_URL}/knowledge/check`);
                if (resp.ok && mountedRef.current) setUpdateCheck((await resp.json()).status);
                else if (mountedRef.current) setUpdateCheck('up_to_date');
            } catch {
                if (mountedRef.current) setUpdateCheck('up_to_date');
            }
        })();
        return () => { mountedRef.current = false; };
    }, []);

    const handleCloseApp = async () => {
        try {
            await fetch(`${API_BASE_URL}/shutdown`, { method: 'POST' });
        } catch (e) {
            console.error('Failed to notify backend of shutdown:', e);
        }

        if (window.electron && window.electron.quit) {
            window.electron.quit();
        } else {
            window.close();
        }
    };

    const handleKnowledgeUpdate = async () => {
        setKnowledgeStatus('loading');
        setKnowledgeProgress({ current: 0, total: 1000 });
        try {
            const resp = await fetch(`${API_BASE_URL}/knowledge/update`, { method: 'POST' });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            await pollUntilDone();
        } catch (e) {
            console.error('Knowledge update failed:', e);
            setKnowledgeStatus('error');
        }
    };

    const handleOllamaToggle = async () => {
        setOllamaLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/settings/ollama`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: !ollamaEnabled })
            });
            const data = await res.json();
            if (data.status === 'success') {
                setOllamaEnabled(!ollamaEnabled);
                setActiveBrain(!ollamaEnabled ? 'Ollama (gemma2:2b)' : 'Original (Qwen 1.5B)');
                
                // Auto-reload model if backend says so
                if (data.reload_required) {
                    setTimeout(async () => {
                        try {
                            await fetch(`${API_BASE_URL}/settings/ollama/reload`, { method: 'POST' });
                        } catch (e) {
                            console.error('Model reload failed:', e);
                        }
                    }, 1000);
                }
            }
        } catch (e) {
            console.error('Failed to toggle Ollama:', e);
        } finally {
            setOllamaLoading(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="settings-container"
        >
            <div className="ambient-bg" />
            <div className="blob blob-1" />
            <div className="blob blob-2" />

            <div className="settings-header">
                <button
                    onClick={() => navigate('/')}
                    className="header-btn"
                >
                    <ArrowLeft size={20} />
                </button>
                <h1 className="settings-title">Settings</h1>
            </div>

            <div className="settings-content">
                <div className="settings-section">
                    <h2 className="settings-section-title">System Configuration</h2>
                    <p className="settings-section-desc">Manage your preferences</p>
                </div>

                <div className="settings-card">
                    <div className="settings-row">
                        <div className="settings-row-label">
                            <div className="settings-icon">
                                {isDark ? <Moon size={20} /> : <Sun size={20} />}
                            </div>
                            Dark Mode
                        </div>
                        <button
                            type="button"
                            role="switch"
                            aria-checked={isDark}
                            onClick={toggleDark}
                            className={`settings-toggle ${isDark ? 'active' : ''}`}
                        >
                            <span className={`settings-toggle-knob ${isDark ? 'on' : ''}`} />
                        </button>
                    </div>

                    <div className="settings-row">
                        <div className="settings-row-label">
                            <div className="settings-icon">
                                <Keyboard size={20} />
                            </div>
                            Popup keyboard
                        </div>
                        <button
                            type="button"
                            role="switch"
                            aria-checked={keyboardEnabled}
                            onClick={() => setKeyboardEnabled(!keyboardEnabled)}
                            className={`settings-toggle ${keyboardEnabled ? 'active' : ''}`}
                        >
                            <span className={`settings-toggle-knob ${keyboardEnabled ? 'on' : ''}`} />
                        </button>
                    </div>

                    <div className="settings-row">
                        <div className="settings-row-label">
                            <div className="settings-icon">
                                <Volume2 size={20} />
                            </div>
                            Voice output (TTS)
                        </div>
                        <button
                            type="button"
                            role="switch"
                            aria-checked={ttsEnabled}
                            onClick={() => setTtsEnabled(!ttsEnabled)}
                            className={`settings-toggle ${ttsEnabled ? 'active' : ''}`}
                        >
                            <span className={`settings-toggle-knob ${ttsEnabled ? 'on' : ''}`} />
                        </button>
                    </div>

                    {/* Active Brain Indicator */}
                    <div className="settings-row" style={{ marginTop: '8px' }}>
                        <div className="settings-row-label" style={{ flex: 1 }}>
                            <div className="settings-icon">
                                <Brain size={20} />
                            </div>
                            <div>
                                <strong>Active Brain</strong>
                                <span className="settings-desc">{activeBrain}</span>
                            </div>
                        </div>
                        <div style={{ color: 'var(--accent)', fontWeight: 600, fontSize: '13px' }}>
                            {ollamaEnabled ? '🧠 Ollama' : '⚡ Qwen'}
                        </div>
                    </div>

                    {/* Ollama Toggle */}
                    <div className="settings-row">
                        <div className="settings-row-label">
                            <div className="settings-icon">
                                <Brain size={20} />
                            </div>
                            <div>
                                <strong>Ollama Brain (gemma2:2b)</strong>
                                <span className="settings-desc">Switch to local Ollama model instead of Qwen</span>
                            </div>
                        </div>
                        <button
                            type="button"
                            role="switch"
                            aria-checked={ollamaEnabled}
                            onClick={handleOllamaToggle}
                            disabled={ollamaLoading}
                            className={`settings-toggle ${ollamaEnabled ? 'active' : ''}`}
                        >
                            <span className={`settings-toggle-knob ${ollamaEnabled ? 'on' : ''}`} />
                        </button>
                    </div>

                    {ollamaLoading && (
                        <div className="update-badge checking" style={{ marginTop: '8px' }}>
                            <RefreshCw size={14} className="spin-icon" />
                            <span>Switching brain... {ollamaEnabled ? 'Loading Ollama' : 'Loading Qwen'}</span>
                        </div>
                    )}

                    <button
                        onClick={handleCloseApp}
                        className="shutdown-btn"
                    >
                        <Power size={20} />
                        <span>Shutdown</span>
                    </button>

                    <button
                        onClick={handleKnowledgeUpdate}
                        className="knowledge-btn"
                        disabled={knowledgeStatus === 'loading'}
                    >
                        {knowledgeStatus === 'loading' ? (
                            <RefreshCw size={20} className="spin-icon" />
                        ) : knowledgeStatus === 'success' ? (
                            <CheckCircle size={20} />
                        ) : knowledgeStatus === 'error' ? (
                            <AlertCircle size={20} />
                        ) : (
                            <BookOpen size={20} />
                        )}
                        <span>
                            {knowledgeStatus === 'loading'
                                ? `Upgrading... ${knowledgeProgress.current}/${knowledgeProgress.total}`
                                : knowledgeStatus === 'success'
                                    ? `Knowledge Upgraded (${knowledgeProgress.total} topics)`
                                    : knowledgeStatus === 'error'
                                        ? 'Upgrade Failed'
                                        : 'Upgrade Knowledge'}
                        </span>
                    </button>

                    {updateCheck === 'update_available' && (
                        <div className="update-badge">
                            <Bell size={14} />
                            <span>New content available — upgrade above</span>
                        </div>
                    )}
                    {updateCheck === 'up_to_date' && (
                        <div className="update-badge up-to-date">
                            <CheckCircle size={14} />
                            <span>Knowledge is up to date</span>
                        </div>
                    )}
                    {updateCheck === 'checking' && (
                        <div className="update-badge checking">
                            <RefreshCw size={14} className="spin-icon" />
                            <span>Checking for updates...</span>
                        </div>
                    )}
                </div>

                <div className="settings-version">
                    Viora AI v1.0.0
                </div>
            </div>
        </motion.div>
    );
}
