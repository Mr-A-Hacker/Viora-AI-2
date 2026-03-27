import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

const STORAGE_KEY = 'viora_dark_mode';

const DarkModeContext = createContext(null);

function readStored() {
    try {
        const v = localStorage.getItem(STORAGE_KEY);
        if (v === null) {
            return window.matchMedia('(prefers-color-scheme:dark)').matches;
        }
        return v === '1';
    } catch {
        return false;
    }
}

function writeStored(enabled) {
    try {
        localStorage.setItem(STORAGE_KEY, enabled ? '1' : '0');
    } catch (_) {}
}

export function DarkModeProvider({ children }) {
    const [isDark, setIsDark] = useState(readStored);

    useEffect(() => {
        if (isDark) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        writeStored(isDark);
    }, [isDark]);

    const toggleDark = useCallback(() => {
        setIsDark(prev => !prev);
    }, []);

    const value = {
        isDark,
        toggleDark,
    };

    return (
        <DarkModeContext.Provider value={value}>
            {children}
        </DarkModeContext.Provider>
    );
}

export function useDarkMode() {
    const ctx = useContext(DarkModeContext);
    if (!ctx) throw new Error('useDarkMode must be used within DarkModeProvider');
    return ctx;
}