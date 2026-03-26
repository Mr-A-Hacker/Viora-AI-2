import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Clock, Activity, Power, Save } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../contexts/WebSocketContext.jsx';
import { useFocusableInput } from '../contexts/KeyboardContext.jsx';

export default function HeartbeatManager() {
    const navigate = useNavigate();
    const { sendMessage, addEventListener } = useWebSocket();
    const { onFocus: onKeyboardFocus, onBlur: onKeyboardBlur } = useFocusableInput(false);
    const [status, setStatus] = useState({ active: false, schedule: null });
    const [intervalStart, setIntervalStart] = useState(30);

    const checkStatus = () => sendMessage("heartbeat.get", {});

    useEffect(() => {
        checkStatus();

        const removeStatusListener = addEventListener("heartbeat_status", (data) => {
            setStatus(data.status);
            if (data.status.schedule) {
                const match = data.status.schedule.match(/\*\/(\d+)/);
                if (match) {
                    setIntervalStart(parseInt(match[1]));
                }
            }
        });

        const removeUpdateListener = addEventListener("heartbeat_updated", (data) => {
            checkStatus();
        });

        return () => {
            removeStatusListener();
            removeUpdateListener();
        };
    }, [sendMessage, addEventListener]);

    const handleSave = () => {
        sendMessage("heartbeat.set", {
            active: status.active,
            interval: intervalStart
        });
    };

    const toggleActive = () => {
        const newActive = !status.active;
        setStatus({ ...status, active: newActive });
        sendMessage("heartbeat.set", {
            active: newActive,
            interval: intervalStart
        });
    };

    return (
        <div className="w-full h-full mx-auto flex flex-col bg-[var(--bg)] text-[var(--text)] font-['Plus_Jakarta_Sans'] relative overflow-hidden">
            <div className="ambient-bg fixed inset-0 -z-10 overflow-hidden pointer-events-none">
                <div className="blob-1 absolute w-[500px] h-[500px] rounded-full opacity-20 blur-[100px]" />
                <div className="blob-2 absolute w-[400px] h-[400px] rounded-full opacity-15 blur-[80px] top-1/3 right-1/4" />
            </div>

            <div className="flex items-center justify-between p-4 bg-[var(--surface)]/80 backdrop-blur-lg border-b border-[var(--border)] z-10">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/')}
                        className="ai-btn p-2.5 rounded-xl bg-[var(--ai-bg)] text-[var(--ai-color)] hover:bg-[var(--ai-color)] hover:text-white transition-all"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <h1 className="text-lg font-['Syne'] font-bold text-[var(--text)]">Heartbeat</h1>
                </div>
                <div className="flex items-center gap-2">
                    <Activity size={20} className={status.active ? "animate-pulse text-[var(--ai-color)]" : "text-[var(--text-light)]"} />
                </div>
            </div>

            <div className="flex-1 p-6 flex flex-col items-center justify-center relative">

                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="w-full max-w-sm ai-card p-8 relative"
                >
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[var(--ai-bg)] px-4 py-1 text-sm font-medium text-[var(--ai-color)] rounded-full border border-[var(--ai-color)]/20">
                        System Status
                    </div>

                    <div className="flex flex-col items-center text-center mt-4">
                        <div className={`w-24 h-24 rounded-3xl flex items-center justify-center mb-6 transition-all duration-500 ${
                            status.active 
                                ? 'bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white shadow-lg shadow-[var(--ai-color)]/30' 
                                : 'bg-[var(--surface)] text-[var(--text-light)] border border-[var(--border)]'
                        }`}>
                            <Activity size={48} className={status.active ? "animate-bounce" : ""} />
                        </div>

                        <h2 className="text-2xl font-['Syne'] font-bold text-[var(--text)] mb-4">
                            {status.active ? "Online" : "Offline"}
                        </h2>
                        <p className="text-[var(--text-mid)] text-sm mb-8">
                            {status.active
                                ? "Automated system check enabled"
                                : "Automated system check disabled"}
                        </p>

                        <div className="w-full space-y-6">
                            <div className="flex items-center justify-between p-4 bg-[var(--ai-bg)] rounded-2xl">
                                <span className="text-sm font-medium">Active</span>
                                <button
                                    onClick={toggleActive}
                                    className={`w-14 h-8 rounded-full relative transition-all ${
                                        status.active ? 'bg-[var(--ai-color)]' : 'bg-[var(--border)]'
                                    }`}
                                >
                                    <div className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow-md transition-all duration-300 ${
                                        status.active ? 'translate-x-7' : 'translate-x-1'
                                    }`} />
                                </button>
                            </div>

                            <div className={`transition-opacity duration-300 ${status.active ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>
                                <label className="text-sm text-[var(--text-mid)] mb-2 block text-left">
                                    Interval (minutes)
                                </label>
                                <div className="flex gap-3">
                                    <input
                                        type="number"
                                        min="1"
                                        max="1440"
                                        value={intervalStart}
                                        onChange={(e) => setIntervalStart(parseInt(e.target.value))}
                                        onFocus={onKeyboardFocus}
                                        onBlur={onKeyboardBlur}
                                        className="ai-input flex-1 p-3 text-center font-semibold"
                                    />
                                    <button
                                        onClick={handleSave}
                                        className="ai-btn bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white px-5 rounded-2xl shadow-lg shadow-[var(--ai-color)]/30"
                                    >
                                        <Save size={18} />
                                    </button>
                                </div>
                            </div>
                        </div>

                    </div>
                </motion.div>

            </div>
        </div>
    );
}
