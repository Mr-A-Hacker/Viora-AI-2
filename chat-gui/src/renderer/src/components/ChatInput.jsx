import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Mic, Send, Square, ImagePlus, X } from 'lucide-react';
import { API_BASE_URL } from '../config.js';
import { useFocusableInput, useKeyboardSettings } from '../contexts/KeyboardContext.jsx';

export default function ChatInput({ onSend, onAbort, onMicPress, isRecording, streaming, disabled }) {
    const [text, setText] = useState('');
    const [images, setImages] = useState([]);
    const [uploading, setUploading] = useState(false);
    const textareaRef = useRef(null);
    const fileInputRef = useRef(null);
    const { onFocus: onKeyboardFocus, onBlur: onKeyboardBlur } = useFocusableInput(true);
    const { syncInputValueRef } = useKeyboardSettings();

    useEffect(() => {
        if (!syncInputValueRef) return;
        syncInputValueRef.current = (value) => setText(value ?? '');
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

    const handleInput = useCallback((e) => {
        setText(e.target.value);
        const el = e.target;
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }, []);

    const handleImageSelect = useCallback(async (e) => {
        const files = Array.from(e.target.files || []);
        if (!files.length) return;
        setUploading(true);
        const uploaded = [];
        for (const file of files) {
            try {
                const form = new FormData();
                form.append('file', file);
                const res = await fetch(`${API_BASE_URL}/vision/upload`, { method: 'POST', body: form });
                const data = await res.json();
                uploaded.push(data);
            } catch (err) {
                console.error('Upload failed:', err);
            }
        }
        setImages((prev) => [...prev, ...uploaded]);
        setUploading(false);
        if (fileInputRef.current) fileInputRef.current.value = '';
    }, []);

    const removeImage = useCallback((index) => {
        setImages((prev) => prev.filter((_, i) => i !== index));
    }, []);

    const handleSend = useCallback(() => {
        const trimmed = text.trim();
        if ((!trimmed && !images.length) || streaming || disabled) return;
        onSend(trimmed, images.map((img) => img.filename));
        setText('');
        setImages([]);
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    }, [text, images, streaming, disabled, onSend]);

    const handleKeyDown = useCallback(
        (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        },
        [handleSend]
    );

    return (
        <div className="min-h-[72px] px-4 py-3 bg-[var(--surface)]/80 backdrop-blur-lg border-t border-[var(--border)] flex flex-col items-end gap-3 pb-[max(12px,env(safe-area-inset-bottom,12px))]" data-chat-input-bar>
            {images.length > 0 && (
                <div className="flex flex-wrap gap-2 w-full">
                    {images.map((img, i) => (
                        <div key={i} className="relative group">
                            <img src={`${API_BASE_URL}/vision/uploads/${img.filename}`} alt="" className="w-16 h-16 rounded-xl object-cover border border-[var(--border)]" />
                            <button onClick={() => removeImage(i)} className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"><X size={12} /></button>
                        </div>
                    ))}
                    {uploading && <div className="w-16 h-16 rounded-xl bg-[var(--bg)] border border-[var(--border)] flex items-center justify-center text-[var(--text-light)] text-xs">...</div>}
                </div>
            )}
            <div className="flex items-end gap-3 w-full">
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
            <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/webp,image/gif" multiple className="hidden" onChange={handleImageSelect} />
            <button type="button" onClick={() => fileInputRef.current?.click()} disabled={disabled || streaming}
                className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-2xl touch-manipulation transition-all duration-200 active:scale-95 border-2 disabled:cursor-not-allowed disabled:opacity-40 bg-[var(--surface)] border-[var(--border)] text-[var(--text-mid)] hover:border-[var(--ai-color)] hover:text-[var(--ai-color)]"
                aria-label="Attach image"><ImagePlus size={20} /></button>

            <button
                type="button"
                onClick={onMicPress}
                aria-label={isRecording ? 'Stop recording' : 'Record voice message'}
                disabled={disabled || streaming}
                className={`flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-2xl touch-manipulation transition-all duration-200 active:scale-95 border-2 disabled:cursor-not-allowed disabled:opacity-40 ${
                    isRecording
                        ? 'bg-red-500 border-red-400 text-white shadow-lg shadow-red-500/25 animate-pulse'
                        : 'bg-[var(--surface)] border-[var(--ai-color)] text-[var(--ai-color)] hover:bg-[var(--ai-color)] hover:text-white'
                }`}
            >
                <Mic size={20} />
            </button>
            {streaming ? (
                <button
                    className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-2xl bg-red-500 text-white cursor-pointer hover:bg-red-600 active:scale-95 transition-all duration-200 shadow-lg shadow-red-500/25"
                    onClick={onAbort}
                    aria-label="Stop response"
                >
                    <Square size={18} fill="currentColor" />
                </button>
            ) : (
                <button
                    type="button"
                    className="flex-shrink-0 flex items-center justify-center gap-1.5 w-auto px-4 h-12 rounded-2xl cursor-pointer active:scale-95 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed touch-manipulation bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white shadow-lg shadow-[#7c3aed]/30"
                    onClick={handleSend}
                    disabled={!text.trim() || disabled}
                    aria-label="Send message"
                >
                    <span className="text-sm font-semibold">Send</span>
                    <Send size={16} />
                </button>
            )}
        </div>
        </div>
    );
}