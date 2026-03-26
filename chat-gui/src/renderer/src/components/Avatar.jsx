import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Avatar({
    className = "",
    variant = "lg",
    onClick,
    animate = true,
    expression: externalExpression
}) {
    const isSmall = variant === 'sm';
    const isXl = variant === 'xl';
    const scale = isSmall ? 0.4 : (isXl ? 1.3 : 1);

    const [expression, setExpression] = useState('neutral');
    const [blink, setBlink] = useState(false);
    const [glitch, setGlitch] = useState(false);

    useEffect(() => {
        if (externalExpression) {
            setExpression(externalExpression);
        }
    }, [externalExpression]);

    useEffect(() => {
        if (!animate || expression === 'listening') return;
        const interval = setInterval(() => {
            if (Math.random() > 0.7) {
                setBlink(true);
                setTimeout(() => setBlink(false), 150);
            }
        }, 2000);
        return () => clearInterval(interval);
    }, [animate, expression]);

    useEffect(() => {
        if (!animate || (expression !== 'neutral' && expression !== 'idle')) return;
        const interval = setInterval(() => {
            const rand = Math.random();
            if (rand > 0.8) {
                const exprs = ['happy', 'thinking', 'surprised', 'neutral'];
                const nextExpr = exprs[Math.floor(Math.random() * exprs.length)];
                setExpression(nextExpr);
                setTimeout(() => setExpression('neutral'), 2000 + Math.random() * 2000);
            }
        }, 4000);
        return () => clearInterval(interval);
    }, [animate, expression]);

    useEffect(() => {
        if (!animate || expression === 'speaking') return;
        const interval = setInterval(() => {
            if (Math.random() > 0.95) {
                setGlitch(true);
                setTimeout(() => setGlitch(false), 200);
            }
        }, 5000);
        return () => clearInterval(interval);
    }, [animate, expression]);

    const c = {
        primary: 'var(--ai-color)',
        secondary: 'var(--ai-color)',
        accent: 'var(--ai-color)',
        dark: '#1a1b26',
        screen: '#24283b',
        eye: '#00ffff',
        highlight: '#ffffff'
    };

    const containerStyle = {
        width: isSmall ? '48px' : (isXl ? '176px' : '160px'),
        height: isSmall ? '48px' : (isXl ? '176px' : '160px'),
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: onClick ? 'pointer' : 'default',
    };

    const floatVariants = {
        animate: {
            y: [0, -4, 0],
            transition: {
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
            }
        },
        speaking: {
            y: [0, -2, 0],
            transition: {
                duration: 0.2,
                repeat: Infinity,
                ease: "linear"
            }
        }
    };

    const glitchVariants = {
        idle: { x: 0, opacity: 1 },
        glitch: {
            x: [-2, 2, -1, 1, 0],
            opacity: [1, 0.8, 1, 0.9, 1],
            transition: { duration: 0.2 }
        }
    };

    const antennaVariants = {
        animate: {
            rotate: [-5, 5, -5],
            transition: {
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
            }
        },
        listening: {
            scale: [1, 1.3, 1],
            rotate: [-15, 15, -15],
            transition: {
                duration: 0.4,
                repeat: Infinity,
                ease: "easeInOut"
            }
        },
    };
    const effectiveExpression = externalExpression != null && externalExpression !== '' ? externalExpression : expression;
    const isThinking = effectiveExpression === 'thinking' || effectiveExpression === 'processing';

    const getEyeScale = (side) => {
        if (blink) return { scaleY: 0.1 };

        switch (expression) {
            case 'happy':
                return { scaleY: 0.5, translateY: -5, borderRadius: '50%' };
            case 'listening':
                return {
                    scale: [1, 1.1, 1],
                    background: '#ff4444',
                    boxShadow: [
                        '0 0 10px #ff0000',
                        '0 0 25px #ff0000',
                        '0 0 10px #ff0000'
                    ]
                };
            case 'speaking':
                return { scaleY: [1, 0.8, 1] };
            default:
                return { scaleY: 1 };
        }
    };

    return (
        <motion.div
            className={`${className}`}
            style={containerStyle}
            onClick={onClick}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            whileHover={onClick ? { scale: 1.1 } : {}}
            whileTap={onClick ? { scale: 0.95 } : {}}
        >
            <motion.div
                style={{
                    scale: scale,
                    width: '128px',
                    height: '128px',
                    position: 'relative',
                }}
                variants={floatVariants}
                animate={animate ? (expression === 'speaking' ? "speaking" : expression === 'thinking' || expression === 'processing' ? "animate" : "animate") : "initial"}
            >
                <motion.div
                    variants={glitchVariants}
                    animate={glitch ? "glitch" : "idle"}
                    className="relative w-full h-full"
                >
                    <motion.div
                        className="absolute left-1/2 top-0"
                        style={{ x: '-50%', transformOrigin: 'bottom center' }}
                        variants={antennaVariants}
                        animate={animate ? (expression === 'listening' ? "listening" : "animate") : "initial"}
                    >
                        <div className="w-1 h-6 bg-[var(--ai-color)] mx-auto" />
                        <div
                            className={`w-3 h-3 relative -top-1 rounded-full ${
                                effectiveExpression === 'listening' ? 'bg-[#ff0000] animate-pulse duration-75' :
                                isThinking ? 'bg-[#ffff00]' :
                                'bg-[var(--ai-color)] animate-pulse'
                            }`}
                        />
                    </motion.div>

                    <div className="absolute top-6 left-12 right-12 bottom-20 bg-[var(--ai-color)] shadow-lg z-0"
                        style={{
                            left: '24px', right: '24px', top: '24px', bottom: '24px',
                            clipPath: 'polygon(10% 0, 90% 0, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0 90%, 0 10%)'
                        }}>

                        <div className="absolute top-2 left-2 w-4 h-4 bg-white/30 rounded" />
                        <div className="absolute top-2 right-2 w-full h-2 bg-black/10" />
                    </div>

                    <div className="absolute bg-[var(--surface)]"
                        style={{
                            left: '32px', right: '32px', top: '40px', bottom: '40px',
                            boxShadow: 'inset 2px 2px 4px rgba(0,0,0,0.5)',
                            borderRadius: '12px'
                        }}>

                        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full flex justify-center items-center gap-4">
                            {isThinking ? (
                                <>
                                    <motion.div
                                        className="flex items-center justify-center flex-shrink-0"
                                        style={{ width: 24, height: 24, transformOrigin: 'center' }}
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                                    >
                                        <svg width="24" height="24" viewBox="0 0 24 24" className="block">
                                            <circle
                                                cx="12" cy="12" r="10"
                                                fill="none"
                                                stroke="#00ffff"
                                                strokeWidth="3"
                                                strokeLinecap="round"
                                                strokeDasharray="16 50"
                                            />
                                        </svg>
                                    </motion.div>
                                    <motion.div
                                        className="flex items-center justify-center flex-shrink-0"
                                        style={{ width: 24, height: 24, transformOrigin: 'center' }}
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                                    >
                                        <svg width="24" height="24" viewBox="0 0 24 24" className="block">
                                            <circle
                                                cx="12" cy="12" r="10"
                                                fill="none"
                                                stroke="#00ffff"
                                                strokeWidth="3"
                                                strokeLinecap="round"
                                                strokeDasharray="16 50"
                                            />
                                        </svg>
                                    </motion.div>
                                </>
                            ) : (
                                <>
                                    <motion.div
                                        className="w-5 h-8 bg-[#00ffff] shadow-[0_0_10px_#00ffff] rounded-lg"
                                        animate={getEyeScale('left')}
                                        transition={{
                                            type: "spring",
                                            stiffness: 300,
                                            damping: 20,
                                            repeat: expression === 'listening' || expression === 'speaking' ? Infinity : 0
                                        }}
                                    />
                                    <motion.div
                                        className="w-5 h-8 bg-[#00ffff] shadow-[0_0_10px_#00ffff] rounded-lg"
                                        animate={getEyeScale('right')}
                                        transition={{
                                            type: "spring",
                                            stiffness: 300,
                                            damping: 20,
                                            repeat: expression === 'listening' || expression === 'speaking' ? Infinity : 0
                                        }}
                                    />
                                </>
                            )}
                        </div>

                        <motion.div
                            className="absolute bottom-3 left-1/2 transform -translate-x-1/2 bg-[#00ffff] opacity-80 rounded"
                            animate={{
                                height: expression === 'speaking' ? [2, 6, 2, 4, 1] : (expression === 'happy' ? 4 : 2),
                                width: expression === 'happy' ? 24 : 12,
                                opacity: expression === 'neutral' ? 0 : 0.8
                            }}
                            transition={expression === 'speaking' ? {
                                duration: 0.3,
                                repeat: Infinity,
                                ease: "easeInOut"
                            } : {}}
                        />
                    </div>

                    <div className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-12 bg-[var(--border)] rounded-lg shadow-lg" />
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-12 bg-[var(--border)] rounded-lg shadow-lg" />

                </motion.div>

                {!isSmall && animate && (
                    <>
                        <motion.div
                            className="absolute -inset-4 border-2 border-[var(--ai-color)] opacity-20"
                            animate={{
                                rotate: 360,
                                scale: [1, 1.05, 1]
                            }}
                            transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                            style={{ borderRadius: '40%' }}
                        />
                    </>
                )}
            </motion.div>

            {!isSmall && (
                <motion.div
                    className="absolute -bottom-4 w-24 h-4 bg-black/20 rounded-full"
                    animate={{
                        scaleX: [1, 0.8, 1],
                        opacity: [0.3, 0.5, 0.3]
                    }}
                    transition={{
                        duration: 4,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />
            )}
        </motion.div>
    );
}
