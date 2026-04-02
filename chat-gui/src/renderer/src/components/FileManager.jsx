import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Folder, File, ChevronRight, Home, Trash2, FilePlus, FolderPlus, Edit3, ArrowUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config.js';

const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
};

export default function FileManager() {
    const navigate = useNavigate();
    const [currentPath, setCurrentPath] = useState('');
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [basePath, setBasePath] = useState('');
    const [showNewDialog, setShowNewDialog] = useState(false);
    const [newName, setNewName] = useState('');
    const [newIsDir, setNewIsDir] = useState(false);
    const [renameItem, setRenameItem] = useState(null);
    const [renameName, setRenameName] = useState('');

    useEffect(() => {
        loadDirectory('');
    }, []);

    const loadDirectory = async (path) => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/files/list?path=${encodeURIComponent(path)}`);
            const data = await res.json();
            setItems(data.items || []);
            setBasePath(data.base || '');
            setCurrentPath(data.path || '');
        } catch (e) {
            console.error('Failed to load directory:', e);
        }
        setLoading(false);
    };

    const navigateTo = (item) => {
        if (item.is_dir) {
            loadDirectory(item.path);
        }
    };

    const goUp = () => {
        const parts = currentPath.split('/').filter(Boolean);
        parts.pop();
        loadDirectory(parts.join('/'));
    };

    const goHome = () => {
        loadDirectory('');
    };

    const handleCreate = async () => {
        if (!newName.trim()) return;
        try {
            const res = await fetch(`${API_BASE_URL}/files/create?path=${encodeURIComponent(currentPath ? currentPath + '/' + newName : newName)}&is_dir=${newIsDir}`, {
                method: 'POST'
            });
            if (res.ok) {
                setShowNewDialog(false);
                setNewName('');
                loadDirectory(currentPath);
            }
        } catch (e) {
            console.error('Create failed:', e);
        }
    };

    const handleDelete = async (item) => {
        if (!confirm(`Delete ${item.name}?`)) return;
        try {
            const res = await fetch(`${API_BASE_URL}/files/delete?path=${encodeURIComponent(item.path)}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                loadDirectory(currentPath);
            }
        } catch (e) {
            console.error('Delete failed:', e);
        }
    };

    const handleRename = async () => {
        if (!renameItem || !renameName.trim()) return;
        try {
            const res = await fetch(`${API_BASE_URL}/files/rename?old_path=${encodeURIComponent(renameItem.path)}&new_name=${encodeURIComponent(renameName)}`, {
                method: 'POST'
            });
            if (res.ok) {
                setRenameItem(null);
                setRenameName('');
                loadDirectory(currentPath);
            }
        } catch (e) {
            console.error('Rename failed:', e);
        }
    };

    const getBreadcrumbs = () => {
        const parts = currentPath.split('/').filter(Boolean);
        return [{ name: 'Home', path: '' }, ...parts.map((p, i) => ({
            name: p,
            path: parts.slice(0, i + 1).join('/')
        }))];
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="w-full h-full flex flex-col bg-[var(--bg)]"
        >
            <div className="flex items-center justify-between p-4 bg-[var(--surface)] border-b border-[var(--border)]">
                <div className="flex items-center gap-3">
                    <button onClick={() => navigate('/')} className="p-2 rounded-lg bg-[var(--ai-bg)] text-[var(--ai-color)]">
                        <ArrowLeft size={20} />
                    </button>
                    <h2 className="text-lg font-semibold">File Manager</h2>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={goUp} className="p-2 rounded-lg hover:bg-[var(--bg)]" title="Go up">
                        <ArrowUp size={20} />
                    </button>
                    <button onClick={goHome} className="p-2 rounded-lg hover:bg-[var(--bg)]" title="Home">
                        <Home size={20} />
                    </button>
                    <button onClick={() => { setNewIsDir(false); setShowNewDialog(true); }} className="p-2 rounded-lg hover:bg-[var(--bg)]" title="New file">
                        <FilePlus size={20} />
                    </button>
                    <button onClick={() => { setNewIsDir(true); setShowNewDialog(true); }} className="p-2 rounded-lg hover:bg-[var(--bg)]" title="New folder">
                        <FolderPlus size={20} />
                    </button>
                </div>
            </div>

            <div className="flex items-center gap-1 px-4 py-2 bg-[var(--surface)] border-b border-[var(--border)] text-sm overflow-x-auto">
                {getBreadcrumbs().map((crumb, i) => (
                    <React.Fragment key={i}>
                        {i > 0 && <ChevronRight size={14} className="text-[var(--text-light)]" />}
                        <button
                            onClick={() => loadDirectory(crumb.path)}
                            className={`hover:text-[var(--ai-color)] ${i === getBreadcrumbs().length - 1 ? 'text-[var(--text)] font-medium' : 'text-[var(--text-light)]'}`}
                        >
                            {crumb.name}
                        </button>
                    </React.Fragment>
                ))}
            </div>

            <div className="flex-1 overflow-auto">
                {loading ? (
                    <div className="flex items-center justify-center h-full">Loading...</div>
                ) : items.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-[var(--text-light)]">
                        <Folder size={48} className="mb-2 opacity-50" />
                        <p>Empty folder</p>
                    </div>
                ) : (
                    <div className="divide-y divide-[var(--border)]">
                        {items.map((item) => (
                            <div
                                key={item.path}
                                className="flex items-center justify-between px-4 py-3 hover:bg-[var(--bg)] cursor-pointer"
                                onClick={() => navigateTo(item)}
                            >
                                <div className="flex items-center gap-3">
                                    {item.is_dir ? (
                                        <Folder size={24} className="text-[#fbbf24]" />
                                    ) : (
                                        <File size={24} className="text-[var(--text-light)]" />
                                    )}
                                    <div>
                                        <div className="font-medium">{item.name}</div>
                                        {item.is_dir ? (
                                            <div className="text-xs text-[var(--text-light)]">Folder</div>
                                        ) : (
                                            <div className="text-xs text-[var(--text-light)]">{formatSize(item.size)}</div>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="text-xs text-[var(--text-light)] mr-2">{formatDate(item.modified)}</div>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); setRenameItem(item); setRenameName(item.name); }}
                                        className="p-1.5 rounded hover:bg-[var(--bg)]"
                                    >
                                        <Edit3 size={16} />
                                    </button>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleDelete(item); }}
                                        className="p-1.5 rounded hover:bg-red-50 text-red-500"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {showNewDialog && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowNewDialog(false)}>
                    <div className="bg-[var(--surface)] rounded-2xl p-6 w-80 shadow-xl" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold mb-4">Create {newIsDir ? 'Folder' : 'File'}</h3>
                        <input
                            type="text"
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            placeholder={`Enter ${newIsDir ? 'folder' : 'file'} name...`}
                            className="w-full px-4 py-2 rounded-xl border border-[var(--border)] bg-[var(--bg)] outline-none focus:border-[var(--ai-color)] mb-4"
                            autoFocus
                        />
                        <div className="flex gap-2">
                            <button onClick={() => setShowNewDialog(false)} className="flex-1 px-4 py-2 rounded-xl border border-[var(--border)]">Cancel</button>
                            <button onClick={handleCreate} className="flex-1 px-4 py-2 rounded-xl bg-[var(--ai-color)] text-white">Create</button>
                        </div>
                    </div>
                </div>
            )}

            {renameItem && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setRenameItem(null)}>
                    <div className="bg-[var(--surface)] rounded-2xl p-6 w-80 shadow-xl" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold mb-4">Rename</h3>
                        <input
                            type="text"
                            value={renameName}
                            onChange={(e) => setRenameName(e.target.value)}
                            className="w-full px-4 py-2 rounded-xl border border-[var(--border)] bg-[var(--bg)] outline-none focus:border-[var(--ai-color)] mb-4"
                            autoFocus
                        />
                        <div className="flex gap-2">
                            <button onClick={() => setRenameItem(null)} className="flex-1 px-4 py-2 rounded-xl border border-[var(--border)]">Cancel</button>
                            <button onClick={handleRename} className="flex-1 px-4 py-2 rounded-xl bg-[var(--ai-color)] text-white">Rename</button>
                        </div>
                    </div>
                </div>
            )}
        </motion.div>
    );
}
