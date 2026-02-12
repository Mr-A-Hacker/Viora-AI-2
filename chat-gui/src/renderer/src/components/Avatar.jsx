import React from 'react';
import { motion } from 'framer-motion';

export default function Avatar({
    className = "",
    variant = "lg", // 'sm' | 'lg'
    onClick,
    animate = true
}) {
    // Defines size constants for each variant
    const styles = {
        sm: {
            size: "w-9 h-9",
            gapConfig: "gap-1 mt-1",
            eyeGap: "gap-1.5",
            eyeSize: "w-2 h-2",
            mouthSize: "w-3 h-0.5 border-b-[1.5px]"
        },
        lg: {
            // Reduced from w-48 h-48 to w-32 h-32 as requested
            size: "w-32 h-32",
            gapConfig: "gap-3 mt-3", // Scaled down from gap-5 mt-4
            eyeGap: "gap-5",          // Scaled down from gap-8
            eyeSize: "w-6 h-6",       // Scaled down from w-10 h-10
            mouthSize: "w-4 h-2 border-b-[2px]" // Scaled down
        }
    };

    const currentStyle = styles[variant] || styles.lg;

    // Allow overriding width/height via className if needed, but default to variant size
    const containerClasses = `relative bg-white rounded-[40px] flex items-center justify-center ${currentStyle.size} shadow-[0_8px_40px_rgba(0,149,255,0.15)] border border-blue-100 ${onClick ? 'cursor-pointer' : ''} ${className}`;

    // Eye animation variants
    const eyeVariants = {
        blink: {
            scaleY: [1, 0.1, 1],
            transition: {
                duration: 0.25, // Slightly slower for better visibility
                repeat: Infinity,
                repeatDelay: 3.5 // Blink every ~3.5s
            }
        },
        static: {
            scaleY: 1
        }
    };

    return (
        <motion.div
            className={containerClasses}
            onClick={onClick}
            whileHover={onClick ? { scale: 1.05, boxShadow: "0 12px 50px rgba(0,149,255,0.2)" } : {}}
            whileTap={onClick ? { scale: 0.95 } : {}}
            initial={animate ? { opacity: 0, scale: 0.5 } : {}}
            animate={animate ? { opacity: 1, scale: 1 } : {}}
            transition={{ duration: 0.5 }}
        >
            {/* Face Container */}
            <div className={`flex flex-col items-center justify-center ${currentStyle.gapConfig}`}>
                {/* Eyes */}
                <div className={`flex ${currentStyle.eyeGap}`}>
                    <motion.div
                        className={`${currentStyle.eyeSize} bg-cyan-400 rounded-full shadow-[0_0_15px_rgba(34,211,238,0.6)]`}
                        variants={eyeVariants}
                        animate={animate ? "blink" : "static"}
                    />
                    <motion.div
                        className={`${currentStyle.eyeSize} bg-cyan-400 rounded-full shadow-[0_0_15px_rgba(34,211,238,0.6)]`}
                        variants={eyeVariants}
                        animate={animate ? "blink" : "static"}
                    />
                </div>

                {/* Mouth */}
                <div className={`${currentStyle.mouthSize} border-slate-700/30 rounded-full`} />
            </div>
        </motion.div>
    );
}
