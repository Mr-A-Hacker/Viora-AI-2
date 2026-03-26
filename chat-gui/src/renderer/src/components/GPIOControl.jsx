import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { ArrowLeft, RefreshCw, Zap, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from './LoadingSpinner';

const GPIOControl = () => {
    const { sendMessage, addEventListener, connStatus } = useWebSocket();
    const isConnected = connStatus === 'connected';
    const navigate = useNavigate();
    const [pins, setPins] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedPin, setSelectedPin] = useState(null);

    useEffect(() => {
        if (isConnected) {
            sendMessage('gpio.get_all');
            setLoading(false);
        }

        const handleGpioState = (data) => {
            if (data.pins) {
                setPins(data.pins);
                if (selectedPin) {
                    const updated = data.pins.find(p => p.pin === selectedPin.pin);
                    if (updated) setSelectedPin(updated);
                }
            }
        };

        const unsubscribeState = addEventListener('gpio_state', handleGpioState);

        return () => {
            unsubscribeState();
        };
    }, [isConnected, sendMessage, addEventListener, selectedPin]);

    const handlePinClick = (pin) => {
        if (pin.type === 'gpio' && !pin.restricted) {
            setSelectedPin(pin);
        } else {
            setSelectedPin(null);
        }
    };

    const toggleMode = () => {
        if (!selectedPin || !isConnected) return;
        const newMode = selectedPin.mode === 'output' ? 'input' : 'output';
        sendMessage('gpio.set_mode', {
            bcm: selectedPin.bcm,
            mode: newMode
        });
    };

    const toggleValue = () => {
        if (!selectedPin || selectedPin.mode !== 'output' || !isConnected) return;
        const newValue = selectedPin.value === 1 ? 0 : 1;
        sendMessage('gpio.write', {
            bcm: selectedPin.bcm,
            value: newValue
        });
    };

    const getPinColor = (pin) => {
        if (pin.type === 'power') {
            if (pin.name.includes("5V")) return "bg-red-500 rounded-lg shadow-lg";
            return "bg-orange-500 rounded-lg shadow-lg";
        }
        if (pin.type === 'ground') return "bg-[var(--text)] rounded-lg";

        if (pin.mode === 'output') {
            return pin.value === 1
                ? "bg-green-500 rounded-lg animate-pulse shadow-lg shadow-green-500/50"
                : "bg-green-900/80 rounded-lg";
        }
        if (pin.mode === 'input') {
            return pin.value === 1
                ? "bg-blue-500 rounded-lg shadow-lg shadow-blue-500/50"
                : "bg-blue-900/80 rounded-lg";
        }

        return "bg-slate-700 rounded-lg";
    };

    const leftColumn = pins.filter((_, i) => i % 2 === 0);
    const rightColumn = pins.filter((_, i) => i % 2 !== 0);

    return (
        <div className="h-full flex flex-col bg-[var(--bg)] overflow-hidden relative text-[var(--text)] font-['Plus_Jakarta_Sans']">
            <div className="ambient-bg fixed inset-0 -z-10 overflow-hidden pointer-events-none">
                <div className="blob-1 absolute w-[500px] h-[500px] rounded-full opacity-20 blur-[100px]" />
                <div className="blob-2 absolute w-[400px] h-[400px] rounded-full opacity-15 blur-[80px] bottom-1/3 left-1/4" />
            </div>

            <div className="flex items-center justify-between p-4 z-10 bg-[var(--surface)]/80 backdrop-blur-lg border-b border-[var(--border)]">
                <button
                    onClick={() => navigate('/')}
                    className="ai-btn p-2.5 rounded-xl flex items-center justify-center bg-[var(--ai-bg)] text-[var(--ai-color)] hover:bg-[var(--ai-color)] hover:text-white transition-all"
                >
                    <ArrowLeft size={20} />
                </button>
                <div className="flex items-center gap-2 text-[var(--ai-color)]">
                    <Activity size={20} />
                    <h1 className="text-lg font-['Syne'] font-bold">GPIO Control</h1>
                </div>
                <div className="w-10" />
            </div>

            <div className="flex-1 flex gap-4 overflow-hidden z-10 h-full p-4 pt-4">

                <div className="flex-1 flex items-center justify-center h-full min-h-0 overflow-y-auto pb-20">
                    {loading && pins.length === 0 ? (
                        <LoadingSpinner label="Connecting..." className="h-full" />
                    ) : (
                    <div className="ai-card p-6 relative">
                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[var(--ai-bg)] px-4 py-1 text-xs font-medium text-[var(--ai-color)] rounded-full border border-[var(--ai-color)]/20 uppercase tracking-wider">
                            Raspberry Pi Header
                        </div>

                        <div className="flex gap-8 mt-4">
                            <div className="flex flex-col gap-3">
                                {leftColumn.map(pin => (
                                    <div key={pin.pin} className="flex items-center justify-end gap-3 h-9">
                                        <span className={`text-sm ${pin.type === 'gpio' ? 'text-[var(--text)]' : 'text-[var(--text-light)]'}`}>
                                            {pin.name}
                                        </span>
                                        <button
                                            onClick={() => handlePinClick(pin)}
                                            className={`w-5 h-5 transition-all duration-150 ${getPinColor(pin)} ${selectedPin?.pin === pin.pin ? 'ring-2 ring-[var(--ai-color)] scale-125' : ''}`}
                                        />
                                        <span className="text-xs text-[var(--text-light)] w-4 text-center">{pin.pin}</span>
                                    </div>
                                ))}
                            </div>

                            <div className="flex flex-col gap-3">
                                {rightColumn.map(pin => (
                                    <div key={pin.pin} className="flex items-center justify-start gap-3 h-9">
                                        <span className="text-xs text-[var(--text-light)] w-4 text-center">{pin.pin}</span>
                                        <button
                                            onClick={() => handlePinClick(pin)}
                                            className={`w-5 h-5 transition-all duration-150 ${getPinColor(pin)} ${selectedPin?.pin === pin.pin ? 'ring-2 ring-[var(--ai-color)] scale-125' : ''}`}
                                        />
                                        <span className={`text-sm ${pin.type === 'gpio' ? 'text-[var(--text)]' : 'text-[var(--text-light)]'}`}>
                                            {pin.name}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                    )}
                </div>

                <div className="w-52 ai-card p-4 flex flex-col gap-4 h-fit self-center">
                    <h2 className="text-sm font-['Syne'] font-semibold text-[var(--text-mid)] uppercase tracking-wider border-b border-[var(--border)] pb-2 mb-1">
                        Pin Config
                    </h2>

                    {selectedPin ? (
                        <div className="flex flex-col gap-4">
                            <div>
                                <div className="text-lg font-bold text-[var(--ai-color)]">{selectedPin.name.replace('GPIO ', 'GP-')}</div>
                                <div className="text-xs text-[var(--text-light)] mt-0.5">BCM: {selectedPin.bcm}</div>
                            </div>

                            <div className="space-y-1">
                                <div className="text-xs text-[var(--text-light)] uppercase">Mode</div>
                                <div className={`text-base font-bold ${
                                    selectedPin.mode === 'output' ? 'text-green-400' : 
                                    selectedPin.mode === 'input' ? 'text-blue-400' : 'text-[var(--text-light)]'
                                }`}>
                                    {selectedPin.mode ? selectedPin.mode.charAt(0).toUpperCase() + selectedPin.mode.slice(1) : 'Unknown'}
                                </div>
                            </div>

                            <div className="space-y-1">
                                <div className="text-xs text-[var(--text-light)] uppercase">State</div>
                                <div className="flex items-center gap-2">
                                    <div className={`w-3 h-3 ${selectedPin.value ? 'bg-green-500 shadow-lg shadow-green-500/50' : 'bg-[var(--text-light)]'} rounded`} />
                                    <div className="text-base font-bold">{selectedPin.value === 1 ? 'HIGH' : 'LOW'}</div>
                                </div>
                            </div>

                            <hr className="border-[var(--border)]" />

                            <div className="flex flex-col gap-2">
                                <button
                                    onClick={toggleMode}
                                    className="ai-btn bg-[var(--surface)] text-[var(--text)] text-sm py-2.5 rounded-xl border border-[var(--border)]"
                                >
                                    Set {selectedPin.mode === 'output' ? 'Input' : 'Output'}
                                </button>

                                {selectedPin.mode === 'output' && (
                                    <button
                                        onClick={toggleValue}
                                        className={`ai-btn text-sm py-2.5 font-bold rounded-xl ${
                                            selectedPin.value
                                                ? 'bg-red-500 text-white shadow-lg shadow-red-500/25'
                                                : 'bg-green-500 text-white shadow-lg shadow-green-500/25'
                                        }`}
                                    >
                                        Turn {selectedPin.value ? 'Off' : 'On'}
                                    </button>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-8 text-center text-[var(--text-light)] gap-2">
                            <Zap size={24} className="opacity-30" />
                            <span className="text-xs">Select a pin<br />to edit</span>
                        </div>
                    )}
                </div>
            </div>

            <div className="absolute bottom-4 left-0 w-full flex justify-center gap-6 text-[10px] text-[var(--text-light)] uppercase tracking-wider font-medium z-10 bg-[var(--surface)]/80 backdrop-blur-lg py-3 border-t border-[var(--border)]">
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-orange-500 rounded" /> Power</div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-[var(--text)] rounded" /> GND</div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-green-500 rounded" /> Output</div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-blue-500 rounded" /> Input</div>
            </div>
        </div>
    );
};

export default GPIOControl;
