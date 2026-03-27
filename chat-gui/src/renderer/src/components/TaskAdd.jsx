import React, { useEffect, useState, useRef, useCallback } from 'react';
import { ArrowLeft, MessageSquare, AlarmClock } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useWebSocket } from '../contexts/WebSocketContext.jsx';
import { useFocusableInput, useKeyboardSettings } from '../contexts/KeyboardContext.jsx';
import VirtualKeyboard from './VirtualKeyboard.jsx';

function jobToFormState(job) {
    if (!job) return { taskType: 'task', name: '', description: '', scheduleType: 'every', intervalValue: 30, intervalUnit: 'minutes', targetDate: '', agentMessage: '' };
    const s = job.schedule || {};
    const payload = job.payload || {};
    const taskType = payload?.taskType || 'task';
    let scheduleType = 'every';
    let intervalValue = 30;
    let intervalUnit = 'minutes';
    let targetDate = '';
    if (s.kind === 'at' && s.atMs != null) {
        scheduleType = 'at';
        const d = new Date(s.atMs);
        targetDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}T${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
    } else if (s.kind === 'every' && s.everyMs != null) {
        const ms = s.everyMs;
        const days = ms / (1000 * 60 * 60 * 24);
        const hours = ms / (1000 * 60 * 60);
        const mins = ms / (1000 * 60);
        if (days >= 1 && Math.abs(days - Math.round(days)) < 0.01) {
            intervalValue = Math.round(days);
            intervalUnit = 'days';
        } else if (hours >= 1 && Math.abs(hours - Math.round(hours)) < 0.01) {
            intervalValue = Math.round(hours);
            intervalUnit = 'hours';
        } else {
            intervalValue = Math.max(1, Math.round(mins));
            intervalUnit = 'minutes';
        }
    }
    const agentMessage = (payload && (payload.message || payload.text)) || '';
    return { taskType, name: job.name || '', description: job.description || '', scheduleType, intervalValue, intervalUnit, targetDate, agentMessage };
}

export default function TaskAdd() {
    const navigate = useNavigate();
    const location = useLocation();
    const editJob = location.state?.job;
    const isEdit = !!editJob;
    const initial = jobToFormState(editJob);

    useEffect(() => {
        if (location.pathname === '/tasks/edit' && !editJob) {
            navigate('/tasks', { replace: true });
        }
    }, [location.pathname, editJob, navigate]);
    const formRef = useRef(null);
    const scrollContainerRef = useRef(null);
    const dragScrollRef = useRef(null);
    const { sendMessage, addEventListener } = useWebSocket();
    const { onFocus: onKeyboardFocus, onBlur: onKeyboardBlur } = useFocusableInput(false);
    const { keyboardEnabled, focusState, setFocusState, focusedElementRef, syncInputValueRef } = useKeyboardSettings();
    const showInlineKeyboard = keyboardEnabled && !!focusState;

    const scrollFocusedIntoView = useCallback((el) => {
        if (!el) return;
        const timer = setTimeout(() => {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 150);
        return () => clearTimeout(timer);
    }, []);

    const bindKeyboardSync = (setState) => ({
        onFocus: (e) => {
            onKeyboardFocus(e);
            syncInputValueRef.current = (v) => setState(v ?? '');
            scrollFocusedIntoView(e.target);
        },
        onBlur: (e) => {
            onKeyboardBlur(e);
            syncInputValueRef.current = null;
        },
    });
    const bindKeyboardSyncNumber = (setState) => ({
        onFocus: (e) => {
            onKeyboardFocus(e);
            syncInputValueRef.current = (v) => setState(Math.max(1, parseInt(String(v), 10) || 1));
            scrollFocusedIntoView(e.target);
        },
        onBlur: (e) => {
            onKeyboardBlur(e);
            syncInputValueRef.current = null;
        },
    });

    const [taskType, setTaskType] = useState(initial.taskType);
    const [name, setName] = useState(initial.name);
    const [description, setDescription] = useState(initial.description);
    const [scheduleType, setScheduleType] = useState(initial.taskType === 'alarm' ? 'at' : initial.scheduleType);
    const [intervalValue, setIntervalValue] = useState(initial.intervalValue);
    const [intervalUnit, setIntervalUnit] = useState(initial.intervalUnit);
    const [targetDate, setTargetDate] = useState(initial.targetDate);
    const [agentMessage, setAgentMessage] = useState(initial.agentMessage);

    const handleTaskTypeChange = (newType) => {
        setTaskType(newType);
        if (newType === 'alarm') {
            setScheduleType('at');
        }
    };

    const setTodayNow = () => {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        setTargetDate(`${year}-${month}-${day}T${hours}:${minutes}`);
    };

    useEffect(() => {
        const removeAdded = addEventListener('task_added', (data) => {
            if (data.result) navigate('/tasks', { replace: true });
        });
        const removeUpdated = addEventListener('task_updated', (data) => {
            if (data.result) navigate('/tasks', { replace: true });
        });
        return () => {
            removeAdded();
            removeUpdated();
        };
    }, [addEventListener, navigate]);

    const handleSubmit = (e) => {
        e.preventDefault();
        let schedule = null;
        if (scheduleType === 'every') {
            let ms = intervalValue * 1000 * 60;
            if (intervalUnit === 'hours') ms *= 60;
            if (intervalUnit === 'days') ms *= 60 * 24;
            schedule = { kind: 'every', everyMs: ms };
        } else if (scheduleType === 'at') {
            schedule = { kind: 'at', atMs: new Date(targetDate).getTime() };
        }
        const payload = agentMessage ? { kind: 'agentTurn', message: agentMessage, taskType } : { taskType };
        if (Object.keys(payload).length === 0 && !confirm('No agent message provided. Save anyway?')) return;
        if (isEdit) {
            sendMessage('task.update', { id: editJob.id, name, description, schedule, payload });
        } else {
            sendMessage('task.add', { name, description, schedule, payload });
        }
    };

    const handleFormKeyDown = useCallback((e) => {
        if (e.key !== 'Enter') return;
        const target = e.target;
        if (target?.tagName !== 'INPUT' && target?.tagName !== 'TEXTAREA') return;
        if (target?.type === 'datetime-local') return;
        e.preventDefault();
        formRef.current?.requestSubmit();
    }, []);

    const closeKeyboard = useCallback(() => {
        setFocusState(null);
        focusedElementRef.current = null;
    }, [setFocusState, focusedElementRef]);

    const handleAreaPointerDown = useCallback(
        (e) => {
            if (!focusState) return;
            const target = e.target;
            if (target?.closest?.('[data-virtual-keyboard]')) return;
            if (target?.closest?.('[data-task-form]')) return;
            if (target?.closest?.('[data-task-scroll]')) return;
            closeKeyboard();
        },
        [focusState, closeKeyboard]
    );

    const onScrollAreaPointerDown = useCallback((e) => {
        if (e.target.closest?.('button, a, input, select, textarea, [role="button"]')) return;
        const el = scrollContainerRef.current;
        if (!el || el.scrollHeight <= el.clientHeight) return;
        dragScrollRef.current = { clientY: e.clientY, scrollTop: el.scrollTop };
        el.setPointerCapture(e.pointerId);
    }, []);
    const onScrollAreaPointerMove = useCallback((e) => {
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
    const onScrollAreaPointerUp = useCallback((e) => {
        if (dragScrollRef.current) {
            scrollContainerRef.current?.releasePointerCapture(e.pointerId);
            dragScrollRef.current = null;
        }
    }, []);

    return (
        <div
            className="w-full h-full flex flex-col bg-[var(--bg)] text-[var(--text)] font-['Plus_Jakarta_Sans'] overflow-hidden min-h-0"
            onPointerDown={handleAreaPointerDown}
        >
            <div className="ambient-bg fixed inset-0 -z-10 overflow-hidden pointer-events-none">
                <div className="blob-1 absolute w-[500px] h-[500px] rounded-full opacity-20 blur-[100px]" />
                <div className="blob-2 absolute w-[400px] h-[400px] rounded-full opacity-15 blur-[80px] bottom-1/3 right-1/4" />
            </div>

            <header className="flex-shrink-0 flex items-center justify-between px-4 py-4 bg-[var(--surface)]/80 backdrop-blur-lg border-b border-[var(--border)] z-10">
                <button
                    type="button"
                    onClick={() => navigate('/tasks')}
                    className="ai-btn p-2.5 rounded-xl min-h-[44px] min-w-[44px] bg-[var(--ai-bg)] text-[var(--ai-color)] hover:bg-[var(--ai-color)] hover:text-white transition-all"
                    aria-label="Back to tasks"
                >
                    <ArrowLeft size={20} />
                </button>
                <h1 className="text-lg font-['Syne'] font-bold text-[var(--text)]">{isEdit ? 'Edit Task' : 'New Task'}</h1>
                <div className="w-10" />
            </header>

            <div
                ref={scrollContainerRef}
                data-task-scroll
                className="flex-1 min-h-0 overflow-y-auto p-4"
                onPointerDown={onScrollAreaPointerDown}
                onPointerMove={onScrollAreaPointerMove}
                onPointerUp={onScrollAreaPointerUp}
                onPointerCancel={onScrollAreaPointerUp}
                onPointerLeave={onScrollAreaPointerUp}
            >
                <div className="ai-card p-6" data-task-form>
                    <form ref={formRef} onSubmit={handleSubmit} onKeyDown={handleFormKeyDown} className="space-y-6">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-[var(--text-mid)]">Name</label>
                            <input
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                {...bindKeyboardSync(setName)}
                                className="ai-input w-full p-4 min-h-[48px] text-base"
                                placeholder="Task name..."
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-[var(--text-mid)]">Description (optional)</label>
                            <input
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                {...bindKeyboardSync(setDescription)}
                                className="ai-input w-full p-4 min-h-[48px] text-base"
                                placeholder="Optional description..."
                            />
                        </div>
                        <div className="space-y-3">
                            <label className="block text-sm font-medium text-[var(--text-mid)]">Task Type</label>
                            <div className="flex bg-[var(--bg)] p-1.5 rounded-2xl gap-1">
                                <button
                                    type="button"
                                    onClick={() => handleTaskTypeChange('task')}
                                    className={`flex-1 py-3.5 text-center text-sm font-medium min-h-[48px] rounded-xl transition-all ${
                                        taskType === 'task' 
                                            ? 'bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white shadow-lg shadow-[var(--ai-color)]/20' 
                                            : 'text-[var(--text-mid)] hover:bg-[var(--ai-bg)]'
                                    }`}
                                >
                                    Task
                                </button>
                                <button
                                    type="button"
                                    onClick={() => handleTaskTypeChange('alarm')}
                                    className={`flex-1 py-3.5 text-center text-sm font-medium min-h-[48px] rounded-xl transition-all flex items-center justify-center gap-2 ${
                                        taskType === 'alarm' 
                                            ? 'bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white shadow-lg shadow-[var(--ai-color)]/20' 
                                            : 'text-[var(--text-mid)] hover:bg-[var(--ai-bg)]'
                                    }`}
                                >
                                    <AlarmClock size={16} /> Alarm
                                </button>
                            </div>
                        </div>
                        {taskType === 'alarm' ? (
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-[var(--text-mid)]">Alarm Time</label>
                                <div className="flex gap-2">
                                    <input
                                        type="datetime-local"
                                        value={targetDate}
                                        onChange={(e) => setTargetDate(e.target.value)}
                                        {...bindKeyboardSync(setTargetDate)}
                                        className="ai-input flex-1 min-h-[48px] text-base p-4"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={setTodayNow}
                                        className="ai-btn px-4 min-h-[48px] text-sm bg-[var(--ai-bg)] text-[var(--ai-color)] border border-[var(--ai-color)] hover:bg-[var(--ai-color)] hover:text-white"
                                    >
                                        Today
                                    </button>
                                </div>
                            </div>
                        ) : taskType !== 'alarm' && (
                            <div className="space-y-3">
                                <label className="block text-sm font-medium text-[var(--text-mid)]">Schedule Type</label>
                                <div className="flex bg-[var(--bg)] p-1.5 rounded-2xl gap-1">
                                    <button
                                        type="button"
                                        onClick={() => setScheduleType('every')}
                                        className={`flex-1 py-3.5 text-center text-sm font-medium min-h-[48px] rounded-xl transition-all ${
                                            scheduleType === 'every' 
                                                ? 'bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white shadow-lg shadow-[var(--ai-color)]/20' 
                                                : 'text-[var(--text-mid)] hover:bg-[var(--ai-bg)]'
                                        }`}
                                    >
                                        Interval
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setScheduleType('at')}
                                        className={`flex-1 py-3.5 text-center text-sm font-medium min-h-[48px] rounded-xl transition-all ${
                                            scheduleType === 'at' 
                                                ? 'bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white shadow-lg shadow-[var(--ai-color)]/20' 
                                                : 'text-[var(--text-mid)] hover:bg-[var(--ai-bg)]'
                                        }`}
                                    >
                                        Date & Time
                                    </button>
                                </div>
                            </div>
                        )}
                        {taskType !== 'alarm' && scheduleType === 'every' && (
                            <div className="flex flex-col sm:flex-row gap-4">
                                <div className="flex-1 space-y-2">
                                    <label className="block text-sm font-medium text-[var(--text-mid)]">Interval</label>
                                    <input
                                        type="number"
                                        min="1"
                                        value={intervalValue}
                                        onChange={(e) => setIntervalValue(parseInt(e.target.value) || 1)}
                                        {...bindKeyboardSyncNumber(setIntervalValue)}
                                        className="ai-input w-full min-h-[48px] text-base p-4"
                                    />
                                </div>
                                <div className="flex-1 space-y-2">
                                    <label className="block text-sm font-medium text-[var(--text-mid)]">Unit</label>
                                    <select
                                        value={intervalUnit}
                                        onChange={(e) => setIntervalUnit(e.target.value)}
                                        className="ai-input w-full min-h-[48px] text-base p-4"
                                    >
                                        <option value="minutes">Minutes</option>
                                        <option value="hours">Hours</option>
                                        <option value="days">Days</option>
                                    </select>
                                </div>
                            </div>
                        )}
                        {scheduleType === 'at' && taskType !== 'alarm' && (
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-[var(--text-mid)]">Date & Time</label>
                                <div className="flex gap-2">
                                    <input
                                        type="datetime-local"
                                        value={targetDate}
                                        onChange={(e) => setTargetDate(e.target.value)}
                                        {...bindKeyboardSync(setTargetDate)}
                                        className="ai-input flex-1 min-h-[48px] text-base p-4"
                                        required={scheduleType === 'at'}
                                    />
                                    <button
                                        type="button"
                                        onClick={setTodayNow}
                                        className="ai-btn px-4 min-h-[48px] text-sm bg-[var(--ai-bg)] text-[var(--ai-color)] border border-[var(--ai-color)] hover:bg-[var(--ai-color)] hover:text-white"
                                    >
                                        Today
                                    </button>
                                </div>
                            </div>
                        )}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-[var(--text-mid)] flex items-center gap-2">
                                {taskType === 'alarm' ? <AlarmClock size={16} /> : <MessageSquare size={16} />} 
                                {taskType === 'alarm' ? 'Alarm Message' : 'Agent Instruction'}
                            </label>
                            <textarea
                                value={agentMessage}
                                onChange={(e) => setAgentMessage(e.target.value)}
                                {...bindKeyboardSync(setAgentMessage)}
                                className="ai-input w-full p-4 bg-[var(--bg)] border border-[var(--border)] text-[var(--text)] text-base focus:border-[var(--ai-color)] outline-none min-h-[100px] resize-none"
                                placeholder={taskType === 'alarm' ? 'What should the AI say when the alarm goes off...' : 'Instructions for agent...'}
                                required
                            />
                        </div>
                        <div className="flex flex-col-reverse sm:flex-row gap-3 pt-2">
                            <button
                                type="button"
                                onClick={() => navigate('/tasks')}
                                className="ai-btn flex-1 py-4 min-h-[52px] text-sm bg-[var(--surface)] text-[var(--text)] border border-[var(--border)]"
                            >
                                Cancel
                            </button>
                            <button type="submit" className="ai-btn flex-1 py-4 min-h-[52px] text-sm bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white shadow-lg shadow-[var(--ai-color)]/30">
                                {isEdit ? 'Save Task' : 'Add Task'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <VirtualKeyboard visible={showInlineKeyboard} mode="inline" focusedElementRef={focusedElementRef} syncInputValueRef={syncInputValueRef} />
        </div>
    );
}
