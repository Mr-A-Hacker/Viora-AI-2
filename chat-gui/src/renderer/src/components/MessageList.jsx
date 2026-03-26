import React, { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble';

function ThoughtBlock({ children }) {
    const [expanded, setExpanded] = useState(true);
    return (
        <div className="thought-container">
            <div className="thought-header flex items-center gap-2 px-3 py-2 bg-[var(--ai-bg)] rounded-xl cursor-pointer text-sm font-['Plus_Jakarta_Sans'] text-[var(--ai-color)] hover:bg-[var(--ai-color)]/20 transition-colors" onClick={() => setExpanded(!expanded)}>
                <span className="text-xs uppercase tracking-wider">Thinking</span>
                <span className={`transition-transform duration-200 ${expanded ? 'rotate-0' : '-rotate-90'}`}>▼</span>
            </div>
            {expanded && (
                <div className="thought-content px-3 py-2 text-sm text-[var(--text-mid)] font-['Plus_Jakarta_Sans']">
                    {children}
                </div>
            )}
        </div>
    );
}

export default function MessageList({ messages, streaming, streamText }) {
    const bottomRef = useRef(null);
    const scrollContainerRef = useRef(null);
    const dragScrollRef = useRef(null);

    const onPointerDown = (e) => {
        if (e.target.closest?.('button, a, input, select, textarea, [role="button"]')) return;
        const el = scrollContainerRef.current;
        if (!el || el.scrollHeight <= el.clientHeight) return;
        dragScrollRef.current = { clientY: e.clientY, scrollTop: el.scrollTop };
        el.setPointerCapture(e.pointerId);
    };
    const onPointerMove = (e) => {
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
    };
    const onPointerUp = (e) => {
        if (dragScrollRef.current) {
            scrollContainerRef.current?.releasePointerCapture(e.pointerId);
            dragScrollRef.current = null;
        }
    };

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamText]);

    const thinkRegex = /<think>([\s\S]*?)(?:<\/think>|$)/;
    const match = streamText.match(thinkRegex);
    let thoughtText = '';
    let hasCompleteThink = false;
    let mainContent = streamText;

    if (match) {
        thoughtText = match[1];
        hasCompleteThink = streamText.includes('</think>');
        if (hasCompleteThink) {
            mainContent = streamText.replace(/<think>[\s\S]*?<\/think>/, '').trim();
        } else {
            mainContent = '';
        }
    }

    const isEmpty = messages.length === 0 && !streaming;

    return (
        <div
            ref={scrollContainerRef}
            className="flex-1 min-h-0 overflow-x-hidden p-4 flex flex-col gap-4"
            data-chat-messages
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
            onPointerLeave={onPointerUp}
        >
            {isEmpty && (
                <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center p-10">
                    <div className="w-20 h-20 rounded-full bg-[var(--ai-bg)] flex items-center justify-center">
                        <span className="text-4xl">✨</span>
                    </div>
                    <div className="text-xl font-['Syne'] font-semibold text-[var(--text)]">Start a conversation</div>
                    <div className="text-sm text-[var(--text-light)] font-['Plus_Jakarta_Sans']">
                        Ask me anything!
                    </div>
                </div>
            )}

            {messages.map((msg, i) => (
                <MessageBubble key={i} role={msg.role} text={msg.text} />
            ))}

            {streaming && streamText && (
                <div className="flex justify-start animate-message-in">
                    <div className="max-w-[85%] px-5 py-4 text-[15px] leading-relaxed break-words font-['Plus_Jakarta_Sans'] bg-[var(--surface)] text-[var(--text)] rounded-2xl rounded-bl-md border border-[var(--border)] shadow-sm">
                        <div className="text-[11px] uppercase tracking-wider mb-2 opacity-70 text-[var(--ai-color)] font-semibold">
                            Viora AI
                        </div>

                        {thoughtText && (
                            <ThoughtBlock>{thoughtText}{!hasCompleteThink && <span className="animate-pulse">▊</span>}</ThoughtBlock>
                        )}

                        <div className="markdown-content">
                            {mainContent} {(!thoughtText || hasCompleteThink) && <span className="animate-pulse">▊</span>}
                        </div>
                    </div>
                </div>
            )}

            {streaming && !streamText && (
                <div className="flex justify-start animate-message-in">
                    <div className="flex gap-2 px-5 py-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-sm">
                        <div className="w-2.5 h-2.5 bg-[var(--ai-color)] rounded-full animate-bounce [animation-delay:0s]" />
                        <div className="w-2.5 h-2.5 bg-[var(--ai-color)] rounded-full animate-bounce [animation-delay:0.15s]" />
                        <div className="w-2.5 h-2.5 bg-[var(--ai-color)] rounded-full animate-bounce [animation-delay:0.3s]" />
                    </div>
                </div>
            )}

            <div ref={bottomRef} />
        </div>
    );
}
