import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Mic, Send, Square } from 'lucide-react';
import { useFocusableInput, useKeyboardSettings } from '../contexts/KeyboardContext.jsx';

export default function ChatInput({ onSend, onAbort, onMicPress, isRecording, streaming, disabled }) {
    const [text, setText] = useState('');
    const textareaRef = useRef(null);
    const { onFocus: onKeyboardFocus, onBlur: onKeyboardBlur } = useFocusableInput(true);
    const { syncInputValueRef } = useKeyboardSettings();

    useEffect(() => {
        if (!syncInputValueRef) return;
        const sync = (value) => setText(value ?? '');
        return () => { syncInputValueRef.current = null; };
    }, [syncInputValueRef]);

    const onFocus = useCallback(
        (e) => {
            onKeyboardFocus(e);
            syncInputValueRef.current = (value) => setText(value ?? '');
            const domValue = textareaRef.current?.value;
            if (domValue !== undefined) setText(domValue);
        },
        [onKeyboardFocus, syncInputValueRef]
    );
    const onBlur = useCallback(
        (e) => {
            onKeyboardBlur(e);
            syncInputValueRef.current = null;
        },
        [onKeyboardBlur, syncInputValueRef]
    );

    const handleSend = useCallback(() => {
        const trimmed = text.trim();
        if (!trimmed || streaming || disabled) return;
        onSend(trimmed);
        setText('');
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    }, [text, streaming, disabled, onSend]);

    const handleKeyDown = useCallback(
        (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        },
        [handleSend]
    );

    const handleInput = useCallback((e) => {
        setText(e.target.value);
        const el = e.target;
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }, []);

    return (
        <div className="min-h-[72px] px-4 py-3 bg-[var(--surface)]/80 backdrop-blur-lg border-t border-[var(--border)] flex items-end gap-3 pb-[max(12px,env(safe-area-inset-bottom,12px))]" data-chat-input-bar>
            <div className="flex-1 ai-input bg-[var(--bg)] rounded-2xl px-4 py-3 flex items-end border border-[var(--border)] focus-within:border-[var(--ai-color)] focus-within:shadow-[0_0_0_3px_var(--ai-bg)] transition-all duration-200">
                <textarea
                    ref={textareaRef}
                    className="flex-1 border-none bg-transparent text-[var(--text)] font-['Plus_Jakarta_Sans'] text-base leading-relaxed min-h-[28px] max-h-[120px] resize-none outline-none py-0.5 placeholder:text-[var(--text-light)]"
                    value={text}
                    onChange={handleInput}
                    onKeyDown={handleKeyDown}
                    onFocus={onFocus}
                    onBlur={onBlur}
                    placeholder="Message Viora AI..."
                    rows={1}
                    disabled={disabled}
                    autoComplete="off"
                    autoCorrect="off"
                />
            </div>

            {streaming ? (
                <button
                    className="ai-btn w-12 h-12 rounded-2xl bg-red-500 text-white flex items-center justify-center cursor-pointer hover:bg-red-600 active:scale-95 transition-all duration-200 shadow-lg shadow-red-500/25"
                    onClick={onAbort}
                    aria-label="Stop response"
                >
                    <Square size={18} fill="currentColor" />
                </button>
            ) : (
                <>
                    <button
                        type="button"
                        onClick={onMicPress}
                        aria-label={isRecording ? 'Stop recording' : 'Record voice message'}
                        disabled={disabled}
                        className={`flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-2xl touch-manipulation transition-all duration-200 active:scale-95 border-2 disabled:cursor-not-allowed ${
                            isRecording
                                ? 'bg-red-500 border-red-400 text-white shadow-lg shadow-red-500/25 animate-pulse'
                                : 'bg-transparent border-[var(--border)] text-[var(--text-mid)] hover:border-[#38bdf8] hover:text-[#38bdf8] disabled:opacity-40'
                        }`}
                    >
                        <Mic size={20} />
                    </button>
                    <button
                        type="button"
                        className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-2xl cursor-pointer active:scale-95 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed touch-manipulation bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white shadow-lg shadow-[#7c3aed]/30"
                        onClick={handleSend}
                        disabled={!text.trim() || disabled}
                        aria-label="Send message"
                    >
                        <Send size={18} className="translate-x-0.5" />
                    </button>
                </>
            )}
        </div>
    );
}
