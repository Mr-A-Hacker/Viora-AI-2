import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Power, Keyboard, Moon, Sun } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config.js';
import { useKeyboardSettings } from '../contexts/KeyboardContext.jsx';
import { useDarkMode } from '../contexts/DarkModeContext.jsx';

export default function Settings() {
    const navigate = useNavigate();
    const { keyboardEnabled, setKeyboardEnabled } = useKeyboardSettings();
    const { isDark, toggleDark } = useDarkMode();

    const handleCloseApp = async () => {
        try {
            await fetch(`${API_BASE_URL}/shutdown`, { method: 'POST' });
        } catch (e) {
            console.error('Failed to notify backend of shutdown:', e);
        }

        if (window.electron && window.electron.quit) {
            window.electron.quit();
        } else {
            console.log('Close button clicked (Electron API not available)');
            window.close();
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

                    <button
                        onClick={handleCloseApp}
                        className="shutdown-btn"
                    >
                        <Power size={20} />
                        <span>Shutdown</span>
                    </button>
                </div>

                <div className="settings-version">
                    Viora AI v1.0.0
                </div>
            </div>
        </motion.div>
    );
}
