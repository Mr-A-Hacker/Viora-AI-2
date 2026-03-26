import React, { useState } from 'react';
import { Pencil, Trash2, Check, X, Plus, ArrowLeft } from 'lucide-react';
import { useWebSocket } from '../contexts/WebSocketContext.jsx';
import { useFocusableInput } from '../contexts/KeyboardContext.jsx';

export default function ChatSidebar({ isOpen, onClose }) {
    const { onFocus: onKeyboardFocus, onBlur: onKeyboardBlur } = useFocusableInput(false);
    const {
        conversations,
        currentConvId,
        setCurrentConvId,
        createConversation,
        deleteConversation,
        renameConversation,
        lastApiError,
        clearApiError,
    } = useWebSocket();

    const [editingId, setEditingId] = useState(null);
    const [editTitle, setEditTitle] = useState('');

    const handleNewChat = async () => {
        const conv = await createConversation();
        if (conv) {
            setCurrentConvId(conv.id);
            onClose();
        }
    };

    const startEditing = (e, conv) => {
        e.stopPropagation();
        setEditingId(conv.id);
        setEditTitle(conv.title || "Untitled Chat");
    };

    const cancelEditing = (e) => {
        e.stopPropagation();
        setEditingId(null);
        setEditTitle('');
    };

    const saveRename = async (e, id) => {
        e.stopPropagation();
        if (editTitle.strip()) {
            await renameConversation(id, editTitle.strip());
        }
        setEditingId(null);
        setEditTitle('');
    };

    return (
        <>
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
                    onClick={onClose}
                />
            )}

            <aside
                className={`fixed top-0 right-0 bottom-0 z-50 bg-[var(--surface)] backdrop-blur-lg border-l border-[var(--border)] transition-transform duration-300 ease-out ${isOpen ? 'translate-x-0' : 'translate-x-full'} w-80 max-w-[85vw] flex flex-col shadow-2xl`}
            >
                <div className="p-4 border-b border-[var(--border)] flex items-center gap-3">
                    <button
                        onClick={onClose}
                        className="p-2.5 rounded-xl border-2 border-[var(--border)] text-[var(--text-mid)] hover:border-[var(--ai-color)] hover:text-[var(--ai-color)] transition-all duration-200 flex items-center justify-center min-h-[44px] min-w-[44px]"
                        aria-label="Close sidebar"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <span style={{ fontFamily: 'var(--font-head)', fontWeight: 800, color: 'var(--ai-color)', fontSize: '1rem' }}>
                        Conversations
                    </span>
                    <div className="flex-1" />
                    <button
                        onClick={onClose}
                        className="p-2 rounded-xl text-[var(--text-light)] hover:text-[var(--text)] hover:bg-[var(--border)] transition-all duration-200"
                        aria-label="Close"
                    >
                        <X size={18} />
                    </button>
                </div>

                <div className="px-4 pb-3">
                    {lastApiError && (
                        <div className="flex items-center justify-between gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">
                            <span className="flex-1 truncate" title={lastApiError}>{lastApiError}</span>
                            <button type="button" onClick={clearApiError} className="shrink-0 p-1 hover:bg-red-500/20 rounded-lg" aria-label="Dismiss"><X size={14} /></button>
                        </div>
                    )}
                    <button
                        onClick={handleNewChat}
                        className="ai-btn w-full py-3 min-h-[44px] bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white font-medium text-sm flex items-center justify-center gap-2 rounded-2xl shadow-lg shadow-[var(--ai-color)]/20"
                    >
                        <Plus size={18} /> New Chat
                    </button>
                </div>

                <div className="flex-1 min-h-0 overflow-y-auto p-3 flex flex-col gap-2">
                    {conversations.map(conv => (
                        <div
                            key={conv.id}
                            className={`p-3 min-h-[48px] border border-[var(--border)] rounded-2xl cursor-pointer hover:bg-[var(--ai-bg)] relative group flex items-center justify-between gap-2 transition-all duration-200 ${
                                currentConvId === conv.id 
                                    ? 'bg-[var(--ai-bg)] border-[var(--ai-color)]' 
                                    : 'hover:border-[var(--text-light)]'
                            }`}
                            onClick={() => { setCurrentConvId(conv.id); }}
                        >
                            {editingId === conv.id ? (
                                <div className="flex items-center gap-2 w-full" onClick={e => e.stopPropagation()}>
                                    <input
                                        type="text"
                                        className="ai-input bg-[var(--bg)] text-sm px-3 py-2 w-full rounded-xl"
                                        value={editTitle}
                                        onChange={e => setEditTitle(e.target.value)}
                                        onFocus={onKeyboardFocus}
                                        onBlur={onKeyboardBlur}
                                        onKeyDown={e => {
                                            if (e.key === 'Enter') saveRename(e, conv.id);
                                            if (e.key === 'Escape') cancelEditing(e);
                                        }}
                                        autoFocus
                                    />
                                    <button onClick={e => saveRename(e, conv.id)} className="p-2 rounded-xl hover:bg-green-500/20 text-green-500 transition-colors">
                                        <Check size={16} />
                                    </button>
                                    <button onClick={e => cancelEditing(e)} className="p-2 rounded-xl hover:bg-red-500/20 text-red-500 transition-colors">
                                        <X size={16} />
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <div className="text-sm truncate flex-1 text-[var(--text)]">{conv.title || "Untitled Chat"}</div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={(e) => startEditing(e, conv)}
                                            className="p-2 rounded-xl hover:bg-[var(--ai-bg)] text-[var(--ai-color)] transition-colors"
                                            title="Rename"
                                        >
                                            <Pencil size={16} />
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }}
                                            className="p-2 rounded-xl hover:bg-red-500/20 text-red-500 transition-colors"
                                            title="Delete"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            </aside>
        </>
    );
}
