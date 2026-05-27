import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Power, Keyboard, Moon, Sun, Volume2, BookOpen, RefreshCw, CheckCircle, AlertCircle, Bell } from 'lucide-react';
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

    const pollUntilDone = async () => {
        if (pollingRef.current) return;
        pollingRef.current = true;
        try {
            let done = false;
            while (!done) {
                await new Promise(resolve => setTimeout(resolve, 2000));
                const resp = await fetch(`${API_BASE_URL}/knowledge`);
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const status = await resp.json();
                setKnowledgeProgress({ current: status.progress || status.entry_count || 0, total: 1000 });
                if (!status.updating) {
                    setKnowledgeStatus(status.entry_count > 0 ? 'success' : 'error');
                    done = true;
                    // Re-check update status after completion
                    try {
                        const checkResp = await fetch(`${API_BASE_URL}/knowledge/check`);
                        if (checkResp.ok) setUpdateCheck((await checkResp.json()).status);
                    } catch {}
                }
            }
        } catch (e) {
            console.error('Polling failed:', e);
            setKnowledgeStatus('error');
        }
        pollingRef.current = false;
    };

    useEffect(() => {
        (async () => {
            try {
                const resp = await fetch(`${API_BASE_URL}/knowledge`);
                if (resp.ok) {
                    const data = await resp.json();
                    if (data.updating) {
                        setKnowledgeStatus('loading');
                        pollUntilDone();
                    } else if (data.entry_count > 0) {
                        setKnowledgeStatus('success');
                        setKnowledgeProgress({ current: data.entry_count, total: data.entry_count });
                    }
                }
            } catch {}
            setUpdateCheck('checking');
            try {
                const resp = await fetch(`${API_BASE_URL}/knowledge/check`);
                if (resp.ok) setUpdateCheck((await resp.json()).status);
                else setUpdateCheck('up_to_date');
            } catch {
                setUpdateCheck('up_to_date');
            }
        })().catch(() => {});
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
