import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, Play, Film, FolderOpen, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { API_BASE_URL } from '../config.js'

export default function VideoPlayer() {
    const navigate = useNavigate()
    const [videos, setVideos] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [playing, setPlaying] = useState(null)
    const videoRef = useRef(null)

    useEffect(() => {
        fetch(`${API_BASE_URL}/videos/list`)
            .then(r => r.json())
            .then(data => {
                setVideos(data.videos || [])
                setLoading(false)
            })
            .catch(e => {
                setError(e.message)
                setLoading(false)
            })
    }, [])

    const playVideo = (name) => {
        setPlaying(name)
    }

    const closePlayer = () => {
        setPlaying(null)
        if (videoRef.current) {
            videoRef.current.pause()
            videoRef.current.src = ''
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="relative w-full h-full overflow-hidden bg-black flex flex-col"
        >
            <div className="absolute top-0 left-0 right-0 z-50 p-4 flex items-center gap-3 bg-gradient-to-b from-black/80 to-transparent pointer-events-none">
                <button
                    onClick={() => navigate('/')}
                    className="pointer-events-auto p-2 rounded-xl flex items-center justify-center bg-black/40 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 transition-all"
                >
                    <ArrowLeft size={22} />
                </button>
                <span className="text-white font-bold text-lg font-['Syne']">Videos</span>
                <span className="text-white/50 text-sm ml-auto">{videos.length} files</span>
            </div>

            <div className="flex-1 overflow-y-auto pt-20 pb-4 px-4">
                {loading && (
                    <div className="flex items-center justify-center h-48">
                        <div className="text-white/50 animate-pulse">Loading videos...</div>
                    </div>
                )}

                {error && (
                    <div className="flex flex-col items-center justify-center h-48 text-center">
                        <FolderOpen size={48} className="text-red-400 mb-3" />
                        <div className="text-red-400">{error}</div>
                    </div>
                )}

                {!loading && !error && videos.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-48 text-center">
                        <Film size={48} className="text-white/20 mb-3" />
                        <div className="text-white/40">No videos found in ~/Downloads</div>
                    </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                    {videos.map((v, i) => (
                        <motion.button
                            key={v.name}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.03 }}
                            onClick={() => playVideo(v.name)}
                            className="bg-white/5 hover:bg-white/10 rounded-xl p-3 text-left border border-white/10 transition-all active:scale-95"
                        >
                            <div className="w-full aspect-video bg-black/40 rounded-lg mb-2 flex items-center justify-center">
                                <Play size={32} className="text-white/30" />
                            </div>
                            <div className="text-white text-sm font-medium truncate">{v.name}</div>
                            <div className="text-white/40 text-xs mt-1">{v.size_mb} MB</div>
                        </motion.button>
                    ))}
                </div>
            </div>

            <AnimatePresence>
                {playing && (
                    <motion.div
                        initial={{ opacity: 0, y: '100%' }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: '100%' }}
                        className="absolute inset-0 z-50 bg-black flex flex-col"
                    >
                        <div className="absolute top-0 left-0 right-0 z-10 p-4 flex items-center bg-gradient-to-b from-black/80 to-transparent">
                            <button
                                onClick={closePlayer}
                                className="p-2 rounded-xl bg-black/40 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 transition-all"
                            >
                                <ArrowLeft size={22} />
                            </button>
                            <span className="text-white text-sm ml-3 truncate">{playing}</span>
                        </div>

                        <video
                            ref={videoRef}
                            controls
                            autoPlay
                            className="w-full h-full object-contain"
                            src={`${API_BASE_URL}/videos/stream/${encodeURIComponent(playing)}`}
                        >
                            Your browser does not support the video tag.
                        </video>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    )
}
