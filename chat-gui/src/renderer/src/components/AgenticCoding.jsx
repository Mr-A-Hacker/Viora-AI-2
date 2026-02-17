import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, RefreshCw, ExternalLink, MessageSquare, Play, ChevronDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import MiniChat from './MiniChat';

const API_URL = 'http://localhost:8000';

export default function AgenticCoding() {
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState('');
    const [iframeKey, setIframeKey] = useState(0);
    const [isChatOpen, setIsChatOpen] = useState(false);

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const response = await fetch(`${API_URL}/workspace/projects`);
            const data = await response.json();
            if (data.status === 'success') {
                setProjects(data.projects);
                if (data.projects.length > 0 && !selectedProject) {
                    setSelectedProject(data.projects[0]);
                }
            }
        } catch (error) {
            console.error('Error fetching projects:', error);
        }
    };

    const handleRefreshPreview = () => {
        setIframeKey(prev => prev + 1);
    };

    const handleOpenInNewTab = () => {
        if (selectedProject) {
            window.open(`${API_URL}/apps/${selectedProject}/index.html`, '_blank');
        }
    };

    const previewUrl = selectedProject
        ? `${API_URL}/apps/${selectedProject}/index.html`
        : 'about:blank';

    return (
        <div className="relative w-full h-full bg-slate-900 text-white overflow-hidden">

            {/* Fullscreen Preview Layer */}
            <div className="absolute inset-0 z-0 bg-white">
                {selectedProject ? (
                    <iframe
                        key={iframeKey}
                        src={previewUrl}
                        className="w-full h-full border-0 block"
                        title="App Preview"
                        sandbox="allow-scripts allow-same-origin allow-forms"
                    />
                ) : (
                    <div className="flex items-center justify-center h-full bg-slate-100 text-slate-500">
                        <p>Select a project to start.</p>
                    </div>
                )}
            </div>

            {/* Top Toolbar (Floating / Transparent) */}
            <div className="absolute top-0 left-0 right-0 z-20 p-2 flex items-center justify-between pointer-events-none">
                {/* Left Controls */}
                <div className="flex items-center space-x-2 pointer-events-auto bg-slate-900/80 backdrop-blur-md p-1 rounded-xl border border-slate-700/50 shadow-lg">
                    <button
                        onClick={() => navigate('/')}
                        className="p-2 hover:bg-white/10 rounded-lg transition-colors text-white"
                    >
                        <ArrowLeft size={18} />
                    </button>

                    <div className="h-4 w-px bg-white/20 mx-1" />

                    <select
                        value={selectedProject}
                        onChange={(e) => setSelectedProject(e.target.value)}
                        className="bg-transparent border-none text-sm focus:outline-none text-white font-medium max-w-[150px]"
                    >
                        <option value="" disabled className="text-black">Select Project</option>
                        {projects.map(p => (
                            <option key={p} value={p} className="text-black">{p}</option>
                        ))}
                    </select>
                    <button onClick={fetchProjects} className="p-1 hover:text-blue-400 text-slate-300">
                        <RefreshCw size={14} />
                    </button>
                </div>

                {/* Right Controls */}
                <div className="flex items-center space-x-2 pointer-events-auto bg-slate-900/80 backdrop-blur-md p-1 rounded-xl border border-slate-700/50 shadow-lg">
                    <button
                        onClick={handleRefreshPreview}
                        className="p-2 hover:bg-white/10 rounded-lg transition-colors text-white"
                        title="Refresh Preview"
                    >
                        <Play size={18} />
                    </button>
                    <button
                        onClick={handleOpenInNewTab}
                        className="p-2 hover:bg-white/10 rounded-lg transition-colors text-white"
                        title="Open in New Tab"
                    >
                        <ExternalLink size={18} />
                    </button>
                    <div className="h-4 w-px bg-white/20 mx-1" />
                    <button
                        onClick={() => setIsChatOpen(!isChatOpen)}
                        className={`p-2 rounded-lg transition-colors border ${isChatOpen ? 'bg-blue-600 border-blue-500 text-white' : 'hover:bg-white/10 border-transparent text-slate-300'}`}
                        title="Toggle Chat"
                    >
                        <MessageSquare size={18} />
                    </button>
                </div>
            </div>

            {/* Chat Overlay (Drawer) */}
            <AnimatePresence>
                {isChatOpen && (
                    <motion.div
                        initial={{ y: '100%', opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: '100%', opacity: 0 }}
                        transition={{ type: "spring", damping: 25, stiffness: 200 }}
                        className="absolute bottom-4 right-4 w-[350px] h-[500px] bg-slate-900/95 backdrop-blur-xl border border-slate-700 shadow-2xl rounded-2xl z-30 flex flex-col overflow-hidden"
                    >
                        <MiniChat
                            onClose={() => setIsChatOpen(false)}
                            className="w-full h-full"
                        />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
