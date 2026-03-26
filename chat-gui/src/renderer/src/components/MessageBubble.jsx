import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function ThoughtBlock({ children }) {
    const [expanded, setExpanded] = useState(true);
    return (
        <div className="thought-container mb-3">
            <div 
                className="thought-header flex items-center gap-2 px-3 py-2 bg-[var(--ai-bg)] rounded-xl cursor-pointer text-sm font-['Plus_Jakarta_Sans'] text-[var(--ai-color)] hover:bg-[var(--ai-color)]/20 transition-colors"
                onClick={() => setExpanded(!expanded)}
            >
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

export default function MessageBubble({ text, role }) {
    const isUser = role === 'user';
    const thinkRegex = /<think>([\s\S]*?)<\/think>/g;
    const thoughts = [];
    let match;
    let mainContent = text;

    while ((match = thinkRegex.exec(text)) !== null) {
        thoughts.push(match[1]);
    }

    mainContent = text.replace(thinkRegex, '').trim();

    return (
        <div className={`flex animate-message-in ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`max-w-[85%] px-5 py-4 text-[15px] leading-relaxed break-words font-['Plus_Jakarta_Sans'] ${
                    isUser
                        ? 'bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white rounded-2xl rounded-br-md shadow-lg shadow-[var(--ai-color)]/20'
                        : 'bg-[var(--surface)] text-[var(--text)] rounded-2xl rounded-bl-md border border-[var(--border)] shadow-sm'
                }`}
            >
                <div className={`text-[11px] uppercase tracking-wider mb-2 opacity-70 font-semibold ${isUser ? 'text-white/80' : 'text-[var(--ai-color)]'}`}>
                    {isUser ? 'You' : 'Viora AI'}
                </div>

                {!isUser && thoughts.length > 0 && (
                    <div className="mb-2">
                        {thoughts.map((thought, idx) => (
                            <ThoughtBlock key={idx}>{thought}</ThoughtBlock>
                        ))}
                    </div>
                )}

                <div className={`markdown-content ${isUser ? 'prose-invert' : ''}`}>
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            a: ({ node, ...props }) => (
                                <a
                                    {...props}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="underline decoration-1 underline-offset-2 text-[var(--ai-color)] hover:bg-[var(--ai-color)] hover:text-white transition-colors rounded px-0.5"
                                />
                            ),
                            code: ({ node, inline, className, children, ...props }) => {
                                const match = /language-(\w+)/.exec(className || '');
                                return !inline ? (
                                    <div className="border border-[var(--border)] my-3 rounded-xl overflow-hidden bg-[var(--bg)]">
                                        <div className="px-4 py-2 text-xs font-medium uppercase bg-[var(--border)]/50 text-[var(--text-mid)] font-['Plus_Jakarta_Sans']">
                                            {match ? match[1] : 'code'}
                                        </div>
                                        <pre className="p-4 overflow-x-auto">
                                            <code className={`font-mono text-sm text-[var(--text)] ${className}`} {...props}>
                                                {children}
                                            </code>
                                        </pre>
                                    </div>
                                ) : (
                                    <code className="font-mono text-sm px-2 py-0.5 bg-[var(--ai-bg)] rounded-md text-[var(--ai-color)]" {...props}>
                                        {children}
                                    </code>
                                );
                            },
                            ul: ({ node, ...props }) => (
                                <ul className="list-disc list-outside ml-5 my-3 space-y-1" {...props} />
                            ),
                            ol: ({ node, ...props }) => (
                                <ol className="list-decimal list-outside ml-5 my-3 space-y-1" {...props} />
                            ),
                            li: ({ node, ...props }) => (
                                <li className="pl-1 marker:text-[var(--ai-color)]" {...props} />
                            ),
                            h1: ({ node, ...props }) => (
                                <h1 className="text-xl font-['Syne'] font-bold mt-4 mb-2 first:mt-0 text-[var(--text)]" {...props} />
                            ),
                            h2: ({ node, ...props }) => (
                                <h2 className="text-lg font-['Syne'] font-semibold mt-3 mb-2 first:mt-0 text-[var(--text)]" {...props} />
                            ),
                            h3: ({ node, ...props }) => (
                                <h3 className="text-base font-semibold mt-2 mb-1 first:mt-0" {...props} />
                            ),
                            p: ({ node, ...props }) => (
                                <p className="mb-3 last:mb-0" {...props} />
                            ),
                            blockquote: ({ node, ...props }) => (
                                <blockquote className="border-l-4 border-[var(--ai-color)]/50 pl-4 py-1 my-3 italic bg-[var(--ai-bg)] rounded-r-xl text-[var(--text-mid)]" {...props} />
                            ),
                            img: ({ node, ...props }) => (
                                <img {...props} className="rounded-xl border border-[var(--border)] max-w-full my-3 shadow-md" />
                            )
                        }}
                    >
                        {mainContent}
                    </ReactMarkdown>
                </div>
            </div>
        </div>
    );
}
