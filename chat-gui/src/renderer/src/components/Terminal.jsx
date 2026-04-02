import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Terminal, Play, Trash2, Copy, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config.js';

export default function TerminalView() {
    const navigate = useNavigate();
    const [history, setHistory] = useState([]);
    const [input, setInput] = useState('');
    const [isExecuting, setIsExecuting] = useState(false);
    const [systemInfo, setSystemInfo] = useState(null);
    const bottomRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => {
        fetchSystemInfo();
    }, []);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [history]);

    const fetchSystemInfo = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/terminal/info`);
            const data = await res.json();
            setSystemInfo(data);
        } catch (e) {
            console.error('Failed to get system info:', e);
        }
    };

    const executeCommand = async (e) => {
        e.preventDefault();
        if (!input.trim() || isExecuting) return;

        const cmd = input.trim();
        setInput('');
        setIsExecuting(true);

        setHistory(prev => [...prev, { type: 'command', content: `$ ${cmd}` }]);

        try {
            const res = await fetch(`${API_BASE_URL}/terminal/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    command: cmd,
                    cwd: systemInfo?.cwd || '/home/admin'
                })
            });
            const data = await res.json();
            
            if (data.stdout) {
                setHistory(prev => [...prev, { type: 'output', content: data.stdout }]);
            }
            if (data.stderr) {
                setHistory(prev => [...prev, { type: 'error', content: data.stderr }]);
            }
            if (data.returncode !== 0 && !data.stdout && !data.stderr) {
                setHistory(prev => [...prev, { type: 'error', content: `Command exited with code ${data.returncode}` }]);
            }
        } catch (e) {
            setHistory(prev => [...prev, { type: 'error', content: `Error: ${e.message}` }]);
        }

        setIsExecuting(false);
        fetchSystemInfo();
        inputRef.current?.focus();
    };

    const clearHistory = () => setHistory([]);

    const copyOutput = () => {
        const text = history.map(h => h.content).join('\n');
        navigator.clipboard.writeText(text);
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="w-full h-full flex flex-col bg-[#1a1a2e]"
        >
            <div className="flex items-center justify-between p-4 bg-[#16213e] border-b border-[#0f3460]">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/')}
                        className="p-2 rounded-lg bg-[#0f3460] text-white hover:bg-[#1a1a2e] transition-colors"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div className="flex items-center gap-2">
                        <Terminal size={24} className="text-[#00ff88]" />
                        <span className="text-white font-semibold">Terminal</span>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={copyOutput}
                        className="p-2 rounded-lg bg-[#0f3460] text-white hover:bg-[#1a1a2e] transition-colors"
                        title="Copy output"
                    >
                        <Copy size={18} />
                    </button>
                    <button
                        onClick={clearHistory}
                        className="p-2 rounded-lg bg-[#0f3460] text-white hover:bg-[#1a1a2e] transition-colors"
                        title="Clear"
                    >
                        <Trash2 size={18} />
                    </button>
                    <button
                        onClick={fetchSystemInfo}
                        className="p-2 rounded-lg bg-[#0f3460] text-white hover:bg-[#1a1a2e] transition-colors"
                        title="Refresh"
                    >
                        <RefreshCw size={18} />
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4 font-mono text-sm">
                <div className="text-[#00ff88] mb-2">
                    Viora Terminal v1.0
                </div>
                {systemInfo && (
                    <div className="text-[#888] mb-4 text-xs">
                        {systemInfo.user}@{systemInfo.cwd}
                    </div>
                )}
                
                {history.map((item, i) => (
                    <div key={i} className="mb-1">
                        {item.type === 'command' ? (
                            <div className="text-[#00ff88]">{item.content}</div>
                        ) : item.type === 'error' ? (
                            <div className="text-[#ff6b6b] whitespace-pre-wrap">{item.content}</div>
                        ) : (
                            <div className="text-[#e0e0e0] whitespace-pre-wrap">{item.content}</div>
                        )}
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>

            <form onSubmit={executeCommand} className="p-4 bg-[#16213e] border-t border-[#0f3460]">
                <div className="flex items-center gap-2">
                    <span className="text-[#00ff88] font-mono">$</span>
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Enter command..."
                        disabled={isExecuting}
                        className="flex-1 bg-transparent text-white font-mono outline-none placeholder:text-[#555]"
                        autoFocus
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isExecuting}
                        className="p-2 rounded-lg bg-[#00ff88] text-[#1a1a2e] hover:bg-[#00cc6a] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isExecuting ? (
                            <RefreshCw size={18} className="animate-spin" />
                        ) : (
                            <Play size={18} />
                        )}
                    </button>
                </div>
            </form>
        </motion.div>
    );
}
