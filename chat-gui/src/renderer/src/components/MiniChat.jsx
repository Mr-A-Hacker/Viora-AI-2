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

    // Auto-scroll to bottom
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
        // Optional: Clear local messages if reset clears backend history
        // But usually backend sends 'session_reset' event which we might listen to?
        // For now, let's manually clear to be responsive
        setMessages([]);
    }, [sendMessage, setMessages]);

    return (
        <div className={`flex flex-col h-full bg-slate-900 border-l border-slate-700 ${className}`}>
            {/* Minimal Header */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 bg-slate-800/50">
                <span className="text-xs font-semibold text-slate-300">Assistant</span>
                <div className="flex items-center space-x-1">
                    <button
                        onClick={reset}
                        className="p-1 hover:bg-slate-700 rounded text-slate-400 hover:text-red-400 transition-colors"
                        title="Clear Chat"
                    >
                        <Trash2 size={14} />
                    </button>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="p-1 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition-colors"
                        >
                            <Minimize2 size={14} />
                        </button>
                    )}
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto min-h-0 bg-slate-900">
                <MessageList
                    messages={messages}
                    streaming={streaming}
                    streamText={streamText}
                />
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-2 border-t border-slate-800 bg-slate-800/30">
                <ChatInput
                    onSend={send}
                    onAbort={abort}
                    streaming={streaming}
                    disabled={connStatus !== 'connected'}
                // We might need to style ChatInput to be more compact via CSS or props
                // But standard is likely fine, just constrained by width.
                />
            </div>
        </div>
    );
}
