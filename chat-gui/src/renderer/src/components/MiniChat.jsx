import React, { useCallback, useEffect, useRef } from 'react';
import { X, Minimize2, Trash2 } from 'lucide-react';
import { useWebSocket } from '../contexts/WebSocketContext.jsx';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

export default function MiniChat({ onClose, className }) {
    const {
        connStatus,
        messages,
        setMessages,
        streamText,
        streaming,
        sendMessage
    } = useWebSocket();

    const messagesEndRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, streamText]);

    const send = useCallback(
        (text, images = []) => {
            setMessages((prev) => [...prev, { role: 'user', text }]);
            sendMessage('send', { message: text, images });
        },
        [sendMessage, setMessages]
    );

    const abort = useCallback(() => {
        sendMessage('abort');
    }, [sendMessage]);

    const reset = useCallback(() => {
        sendMessage('reset');
        setMessages([]);
    }, [sendMessage, setMessages]);

    return (
        <div className={`flex flex-col h-full bg-[var(--bg)] text-[var(--text)] font-['Plus_Jakarta_Sans)] ${className}`}>
            <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-lg">
                <span className="text-sm font-['Syne'] font-semibold text-[var(--text)]">Assistant</span>
                <div className="flex items-center gap-4">
                    <button
                        onClick={reset}
                        className="p-2 rounded-xl hover:bg-red-500/10 text-[var(--text-mid)] hover:text-red-500 transition-colors"
                        title="Reset"
                    >
                        <Trash2 size={18} />
                    </button>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="p-2 rounded-xl hover:bg-[var(--ai-bg)] text-[var(--text-mid)] hover:text-[var(--ai-color)] transition-colors"
                        >
                            <Minimize2 size={18} />
                        </button>
                    )}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto min-h-0 bg-[var(--bg)] p-4">
                <MessageList
                    messages={messages}
                    streaming={streaming}
                    streamText={streamText}
                />
                <div ref={messagesEndRef} />
            </div>

            <div className="p-4 border-t border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-lg">
                <ChatInput
                    onSend={send}
                    onAbort={abort}
                    streaming={streaming}
                    disabled={connStatus !== 'connected'}
                />
            </div>
        </div>
    );
}
