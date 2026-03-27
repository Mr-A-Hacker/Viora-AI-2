import React, { useEffect, useState, useRef, useCallback } from 'react';
// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';
import { ArrowLeft, Plus, Trash2, Clock, Zap, Pencil, AlarmClock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../contexts/WebSocketContext.jsx';

const formatSchedule = (schedule, isAlarm) => {
    if (!schedule || typeof schedule !== 'object') return 'No schedule';
    if (schedule.kind === 'every') {
        const ms = schedule.everyMs;
        const days = ms / (1000 * 60 * 60 * 24);
        if (days >= 1 && Number.isInteger(days)) return `Every ${days} day${days > 1 ? 's' : ''}`;
        const hours = ms / (1000 * 60 * 60);
        if (hours >= 1 && Number.isInteger(hours)) return `Every ${hours} hour${hours > 1 ? 's' : ''}`;
        const mins = ms / (1000 * 60);
        return `Every ${Math.round(mins)} minute${Math.round(mins) !== 1 ? 's' : ''}`;
    }
    if (schedule.kind === 'at') {
        const date = new Date(schedule.atMs);
        const dateStr = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        const timeStr = date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit', hour12: true });
        if (isAlarm) {
            return `Alarm: ${timeStr}`;
        }
        return `At ${dateStr} ${timeStr}`;
    }
    return 'Scheduled';
};

export default function TaskManager() {
    const navigate = useNavigate();
    const scrollContainerRef = useRef(null);
    const dragScrollRef = useRef(null);
    const { sendMessage, addEventListener } = useWebSocket();
    const [jobs, setJobs] = useState([]);

    const onScrollPointerDown = useCallback((e) => {
        if (e.target.closest?.('button, a, input, select, textarea, [role="button"]')) return;
        const el = scrollContainerRef.current;
        if (!el || el.scrollHeight <= el.clientHeight) return;
        dragScrollRef.current = { clientY: e.clientY, scrollTop: el.scrollTop };
        el.setPointerCapture(e.pointerId);
    }, []);
    const onScrollPointerMove = useCallback((e) => {
        const state = dragScrollRef.current;
        if (!state) return;
        const el = scrollContainerRef.current;
        if (!el) return;
        const deltaY = e.clientY - state.clientY;
        const newTop = Math.max(0, Math.min(el.scrollHeight - el.clientHeight, state.scrollTop - deltaY));
        el.scrollTop = newTop;
        state.scrollTop = newTop;
        state.clientY = e.clientY;
        e.preventDefault();
    }, []);
    const onScrollPointerUp = useCallback((e) => {
        if (dragScrollRef.current) {
            scrollContainerRef.current?.releasePointerCapture(e.pointerId);
            dragScrollRef.current = null;
        }
    }, []);

    useEffect(() => {
        sendMessage('task.list', {});

        const removeList = addEventListener('task_list', (data) => {
            setJobs(data.jobs || []);
        });
        const removeRemoved = addEventListener('task_removed', () => {
            sendMessage('task.list', {});
        });
        const removeUpdated = addEventListener('task_updated', () => {
            sendMessage('task.list', {});
        });

        return () => {
            removeList();
            removeRemoved();
            removeUpdated();
        };
    }, [sendMessage, addEventListener]);

    const handleEditJob = (job) => {
        navigate('/tasks/edit', { state: { job } });
    };

    const handleRemoveJob = (id) => {
        if (confirm('Delete this scheduled task?')) {
            sendMessage('task.remove', { id });
        }
    };

    return (
        <div className="w-full h-full mx-auto flex flex-col bg-[var(--bg)] text-[var(--text)] font-['Plus_Jakarta_Sans'] overflow-hidden min-h-0">
            <div className="ambient-bg fixed inset-0 -z-10 overflow-hidden pointer-events-none">
                <div className="blob-1 absolute w-[500px] h-[500px] rounded-full opacity-20 blur-[100px]" />
                <div className="blob-2 absolute w-[400px] h-[400px] rounded-full opacity-15 blur-[80px] top-1/3 right-1/4" />
            </div>

            <div className="flex-shrink-0 flex items-center justify-between px-4 py-4 bg-[var(--surface)]/80 backdrop-blur-lg border-b border-[var(--border)] z-10">
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={() => navigate('/')}
                        className="p-2.5 rounded-xl min-h-[44px] min-w-[44px] border-2 border-[var(--border)] text-[var(--text-mid)] hover:border-[var(--ai-color)] hover:text-[var(--ai-color)] transition-all duration-200 flex items-center justify-center"
                        aria-label="Back"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <h1 className="text-lg font-['Syne'] font-bold text-[var(--text)]">Tasks</h1>
                </div>
                <button
                    type="button"
                    onClick={() => navigate('/tasks/add')}
                    className="ai-btn p-2.5 rounded-xl min-h-[44px] min-w-[44px] bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white transition-all shadow-lg shadow-[var(--ai-color)]/30"
                    aria-label="New task"
                >
                    <Plus size={20} />
                </button>
            </div>

            <div
                ref={scrollContainerRef}
                className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4"
                onPointerDown={onScrollPointerDown}
                onPointerMove={onScrollPointerMove}
                onPointerUp={onScrollPointerUp}
                onPointerCancel={onScrollPointerUp}
                onPointerLeave={onScrollPointerUp}
            >
                {jobs.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 text-[var(--text-light)]">
                        <div className="w-16 h-16 rounded-full bg-[var(--ai-bg)] flex items-center justify-center mb-4">
                            <Clock size={32} className="text-[var(--ai-color)] opacity-50" />
                        </div>
                        <p className="text-base font-medium">No active tasks</p>
                    </div>
                ) : (
                    jobs.map((job) => (
                        <motion.div
                            key={job.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="ai-card p-5 group"
                        >
                            <div className="flex justify-between items-start gap-3 mb-4">
                                <div className="min-w-0 flex-1">
                                    <h3 className="font-['Syne'] font-semibold text-[var(--text)] text-base mb-1 flex items-center gap-2">
                                        {job.name}
                                        {job.payload?.taskType === 'alarm' && (
                                            <AlarmClock size={16} className="text-orange-500" />
                                        )}
                                    </h3>
                                    {job.description && (
                                        <p className="text-sm text-[var(--text-mid)]">{job.description}</p>
                                    )}
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        type="button"
                                        onClick={() => handleEditJob(job)}
                                        className="p-2.5 rounded-xl min-h-[44px] min-w-[44px] flex items-center justify-center text-[var(--ai-color)] hover:bg-[var(--ai-bg)] border border-transparent hover:border-[var(--ai-color)] transition-all"
                                        aria-label="Edit task"
                                    >
                                        <Pencil size={18} />
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveJob(job.id)}
                                        className="p-2.5 rounded-xl min-h-[44px] min-w-[44px] flex items-center justify-center text-red-500 hover:bg-red-500/10 border border-transparent hover:border-red-500 transition-all"
                                        aria-label="Delete task"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </div>
                            </div>

                            <div className="flex flex-col gap-3">
                                <div className="flex items-center text-sm text-[var(--text-mid)]">
                                    <div className="w-8 flex justify-center mr-2 opacity-70">
                                        {job.payload?.taskType === 'alarm' ? <AlarmClock size={16} className="text-orange-500" /> : <Clock size={16} />}
                                    </div>
                                    <span className={`font-medium px-3 py-1.5 rounded-xl ${job.payload?.taskType === 'alarm' ? 'bg-orange-500/10 text-orange-500' : 'bg-[var(--ai-bg)] text-[var(--ai-color)]'}`}>
                                        {formatSchedule(job.schedule, job.payload?.taskType === 'alarm')}
                                    </span>
                                </div>

                                {job.payload && (job.payload.message || job.payload.text) && (
                                    <div className="flex items-start text-sm text-[var(--text-mid)]">
                                        <div className="w-8 flex justify-center mr-2 opacity-70 mt-0.5">
                                            {job.payload.taskType === 'alarm' ? <AlarmClock size={16} className="text-orange-500" /> : <Zap size={16} />}
                                        </div>
                                        <div className={`flex-1 p-3 rounded-xl text-sm ${job.payload.taskType === 'alarm' ? 'bg-orange-500/10 text-orange-400' : 'bg-[var(--ai-bg)] text-[var(--ai-color)]'}`}>
                                            {job.payload.text || job.payload.message}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    );
}
