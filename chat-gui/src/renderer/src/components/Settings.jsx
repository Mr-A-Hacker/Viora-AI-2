import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Power, Keyboard } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config.js';
import { useKeyboardSettings } from '../contexts/KeyboardContext.jsx';

export default function Settings() {
    const navigate = useNavigate();
    const { keyboardEnabled, setKeyboardEnabled } = useKeyboardSettings();

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
            className="relative w-full h-full max-w-full mx-auto overflow-hidden bg-[var(--bg)] flex flex-col"
        >
            <div className="ambient-bg fixed inset-0 -z-10 overflow-hidden pointer-events-none">
                <div className="blob-1 absolute w-[500px] h-[500px] rounded-full opacity-20 blur-[100px]" />
                <div className="blob-2 absolute w-[400px] h-[400px] rounded-full opacity-15 blur-[80px] top-1/3 right-1/4" />
            </div>

            <div className="flex items-center p-4 bg-[var(--surface)]/80 backdrop-blur-lg border-b border-[var(--border)] z-10">
                <button
                    onClick={() => navigate('/')}
                    className="ai-btn p-2.5 rounded-xl flex items-center justify-center bg-[var(--ai-bg)] text-[var(--ai-color)] hover:bg-[var(--ai-color)] hover:text-white transition-all"
                >
                    <ArrowLeft size={20} />
                </button>
                <h1 className="ml-4 text-lg font-['Syne'] font-bold text-[var(--text)]">Settings</h1>
            </div>

            <div className="flex-1 p-6 flex flex-col items-center justify-center space-y-6">
                <div className="text-center">
                    <h2 className="text-2xl font-['Syne'] font-semibold text-[var(--text)] mb-2">System Configuration</h2>
                    <p className="text-[var(--text-mid)] font-['Plus_Jakarta_Sans'] text-sm">Manage your preferences</p>
                </div>

                <div className="w-full max-w-sm ai-card p-6 space-y-6">
                    <div className="flex items-center justify-between gap-4 py-3">
                        <span className="font-['Plus_Jakarta_Sans'] text-[var(--text)] flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-[var(--ai-bg)] flex items-center justify-center">
                                <Keyboard size={20} className="text-[var(--ai-color)]" />
                            </div>
                            Popup keyboard
                        </span>
                        <button
                            type="button"
                            role="switch"
                            aria-checked={keyboardEnabled}
                            onClick={() => setKeyboardEnabled(!keyboardEnabled)}
                            className={`relative w-14 h-8 rounded-full flex-shrink-0 transition-all duration-300 ${
                                keyboardEnabled
                                    ? 'bg-[var(--ai-color)]'
                                    : 'bg-[var(--border)]'
                            }`}
                        >
                            <span
                                className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow-md transition-transform duration-300 ${
                                    keyboardEnabled ? 'translate-x-7' : 'translate-x-1'
                                }`}
                            />
                        </button>
                    </div>
                    <button
                        onClick={handleCloseApp}
                        className="ai-btn w-full py-4 px-6 bg-red-500 text-white font-['Plus_Jakarta_Sans'] font-semibold text-sm rounded-2xl hover:bg-red-600 active:scale-[0.98] transition-all flex items-center justify-center gap-3 shadow-lg shadow-red-500/25"
                    >
                        <Power size={20} />
                        <span>Shutdown</span>
                    </button>
                </div>

                <div className="text-xs font-['Plus_Jakarta_Sans'] text-[var(--text-light)] mt-auto pt-12">
                    Version 1.0.0
                </div>
            </div>
        </motion.div>
    );
}
