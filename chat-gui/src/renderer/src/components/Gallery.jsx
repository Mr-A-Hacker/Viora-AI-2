import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, X, ChevronLeft, ChevronRight, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config.js';
import { apiFetch } from '../apiClient.js';
import { useFocusableInput } from '../contexts/KeyboardContext.jsx';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

export default function Gallery() {
    const { onFocus: onKeyboardFocus, onBlur: onKeyboardBlur } = useFocusableInput(false);
    const navigate = useNavigate();
    const [images, setImages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedImageIndex, setSelectedImageIndex] = useState(null);
    const [showChatModal, setShowChatModal] = useState(false);
    const [chatPrompt, setChatPrompt] = useState('');

    useEffect(() => {
        fetchImages();
    }, []);

    const fetchImages = async () => {
        setError(null);
        try {
            const data = await apiFetch('/gallery/images');
            if (data.status === 'success') {
                setImages(data.images || []);
            }
        } catch (err) {
            setError(err?.message || 'Failed to load images');
            console.error('Failed to load images:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleImageClick = (index) => {
        setSelectedImageIndex(index);
    };

    const closeImage = () => {
        setSelectedImageIndex(null);
        setShowChatModal(false);
        setChatPrompt('');
    };

    const handleDelete = async (e) => {
        e.stopPropagation();
        if (selectedImageIndex === null) return;

        const img = images[selectedImageIndex];
        if (!confirm('Are you sure you want to delete this image?')) return;

        try {
            setError(null);
            const data = await apiFetch(`/gallery/images/${img.filename}`, { method: 'DELETE' });
            if (data.status === 'success') {
                const newImages = images.filter((_, i) => i !== selectedImageIndex);
                setImages(newImages);
                if (newImages.length === 0) {
                    closeImage();
                } else if (selectedImageIndex >= newImages.length) {
                    setSelectedImageIndex(newImages.length - 1);
                }
            } else {
                setError(data.message || 'Failed to delete image');
            }
        } catch (err) {
            setError(err?.message || 'Error deleting image');
            console.error('Error deleting image:', err);
        }
    };

    const handleChatClick = (e) => {
        e.stopPropagation();
        setShowChatModal(true);
    };

    const handleSendToChat = () => {
        if (!chatPrompt.trim()) return;

        const img = images[selectedImageIndex];
        navigate('/chat', {
            state: {
                prompt: chatPrompt,
                image: img.filename
            }
        });
    };

    const handleNext = (e) => {
        e && e.stopPropagation();
        if (selectedImageIndex !== null && selectedImageIndex < images.length - 1) {
            setSelectedImageIndex(selectedImageIndex + 1);
        }
    };

    const handlePrev = (e) => {
        e && e.stopPropagation();
        if (selectedImageIndex !== null && selectedImageIndex > 0) {
            setSelectedImageIndex(selectedImageIndex - 1);
        }
    };

    const swipeConfidenceThreshold = 10000;
    const swipePower = (offset, velocity) => {
        return Math.abs(offset) * velocity;
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="relative w-full h-full max-w-full mx-auto overflow-hidden bg-[var(--bg)] flex flex-col"
        >
            <div className="ambient-bg fixed inset-0 -z-10 overflow-hidden pointer-events-none">
                <div className="blob-1 absolute w-[500px] h-[500px] rounded-full opacity-20 blur-[100px]" />
                <div className="blob-2 absolute w-[400px] h-[400px] rounded-full opacity-15 blur-[80px] bottom-1/4 right-1/3" />
            </div>

            <div className="p-4 z-10 flex justify-between items-center bg-[var(--surface)]/80 backdrop-blur-lg border-b border-[var(--border)]">
                <button
                    onClick={() => navigate('/')}
                    className="p-2.5 rounded-xl min-h-[44px] min-w-[44px] border-2 border-[var(--border)] text-[var(--text-mid)] hover:border-[var(--ai-color)] hover:text-[var(--ai-color)] transition-all duration-200 flex items-center justify-center"
                >
                    <ArrowLeft size={20} />
                </button>
                <h1 className="text-lg font-['Syne'] font-bold text-[var(--text)]">Gallery</h1>
                <div className="w-10" />
            </div>

            {error && (
                <ErrorMessage message={error} onRetry={() => { setError(null); fetchImages(); }} />
            )}

            <div className="flex-1 min-h-0 overflow-y-auto p-4">
                {loading ? (
                    <LoadingSpinner label="Loading..." className="h-full" />
                ) : images.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-[var(--text-mid)] font-['Plus_Jakarta_Sans'] text-base">
                        <p>No images found</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-3 gap-3">
                        {images.map((img, index) => (
                            <div
                                key={img.filename}
                                onClick={() => handleImageClick(index)}
                                className="aspect-[9/16] bg-[var(--surface)] border border-[var(--border)] rounded-2xl relative cursor-pointer hover:border-[var(--ai-color)] hover:shadow-lg hover:shadow-[var(--ai-color)]/10 transition-all duration-200 overflow-hidden"
                            >
                                <img
                                    src={`${API_BASE_URL}${img.url}`}
                                    alt={img.filename}
                                    className="w-full h-full object-cover rounded-2xl"
                                    loading="lazy"
                                />
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <AnimatePresence>
                {selectedImageIndex !== null && images[selectedImageIndex] && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 z-50 bg-black/90 backdrop-blur-sm flex flex-col"
                        onClick={closeImage}
                    >
                        <div className="absolute top-4 left-4 right-4 z-50 flex justify-between">
                            <button
                                onClick={closeImage}
                                className="ai-btn p-3 rounded-2xl bg-red-500 hover:bg-red-600 text-white transition-all shadow-lg shadow-red-500/25"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <div className="absolute bottom-6 left-6 z-50">
                            <button
                                onClick={handleChatClick}
                                className="ai-btn flex items-center gap-2 bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white px-5 py-3 rounded-2xl shadow-lg shadow-[var(--ai-color)]/30"
                            >
                                <MessageSquare size={18} />
                                Chat
                            </button>
                        </div>

                        <div className="absolute bottom-6 right-6 z-50">
                            <button
                                onClick={handleDelete}
                                className="ai-btn bg-red-500 text-white px-5 py-3 rounded-2xl hover:bg-red-600 transition-all shadow-lg shadow-red-500/25"
                            >
                                Delete
                            </button>
                        </div>

                        <div className="flex-1 flex items-center justify-center relative w-full h-full p-8">
                            {selectedImageIndex > 0 && (
                                <button
                                    onClick={handlePrev}
                                    className="absolute left-4 z-40 ai-btn p-3 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 transition-all"
                                >
                                    <ChevronLeft size={24} />
                                </button>
                            )}
                            {selectedImageIndex < images.length - 1 && (
                                <button
                                    onClick={handleNext}
                                    className="absolute right-4 z-40 ai-btn p-3 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 transition-all"
                                >
                                    <ChevronRight size={24} />
                                </button>
                            )}

                            <motion.img
                                key={images[selectedImageIndex].filename}
                                src={`${API_BASE_URL}${images[selectedImageIndex].url}`}
                                alt={images[selectedImageIndex].filename}
                                className="max-w-full max-h-full object-contain rounded-3xl bg-[var(--surface)] shadow-2xl"
                                initial={{ x: 100, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                exit={{ x: -100, opacity: 0 }}
                                drag="x"
                                dragConstraints={{ left: 0, right: 0 }}
                                dragElastic={0.2}
                                onDragEnd={(e, { offset, velocity }) => {
                                    const swipe = swipePower(offset.x, velocity.x);

                                    if (swipe < -swipeConfidenceThreshold) {
                                        handleNext();
                                    } else if (swipe > swipeConfidenceThreshold) {
                                        handlePrev();
                                    }
                                }}
                                onClick={(e) => e.stopPropagation()}
                            />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {showChatModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 z-[60] bg-black/80 backdrop-blur-sm flex items-center justify-center p-6"
                        onClick={() => setShowChatModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.9, y: 20 }}
                            className="ai-card p-6 w-full max-w-sm"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h3 className="text-base font-['Syne'] font-semibold text-[var(--text)] mb-4">Query Image</h3>
                            <textarea
                                className="ai-input w-full h-32 p-4 resize-none"
                                placeholder="What would you like to know about this image?"
                                value={chatPrompt}
                                onChange={(e) => setChatPrompt(e.target.value)}
                                onFocus={onKeyboardFocus}
                                onBlur={onKeyboardBlur}
                                autoFocus
                            />
                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    onClick={() => setShowChatModal(false)}
                                    className="ai-btn bg-[var(--surface)] text-[var(--text)] px-5 py-3 rounded-xl border border-[var(--border)]"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSendToChat}
                                    disabled={!chatPrompt.trim()}
                                    className="ai-btn bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white px-5 py-3 rounded-xl disabled:opacity-50 shadow-lg shadow-[var(--ai-color)]/30"
                                >
                                    Send
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
