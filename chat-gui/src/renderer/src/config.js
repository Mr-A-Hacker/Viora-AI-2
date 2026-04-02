/**
 * Single source of truth for backend API and WebSocket base URLs.
 * Uses window.location.hostname so the GUI works when served from the Pi's IP.
 * Override with VITE_API_HOST and VITE_API_PORT for dev (e.g. remote backend).
 */
const getHost = () => {
    if (typeof window !== 'undefined') {
        const h = window.location.hostname;
        if (h && h !== 'localhost' && h !== '127.0.0.1' && h !== '0.0.0.0') {
            return h;
        }
    }
    return '127.0.0.1';
};

const host = getHost();
const port = '8000';

const base = `${host}:${port}`;
export const API_BASE_URL = `http://${base}`;
export const WS_BASE_URL = `ws://${base}`;

export const API_URL = API_BASE_URL;
export const WS_URL = `${WS_BASE_URL}/ws/voice`;
export const CHAT_WS_URL = `${WS_BASE_URL}/ws/chat`;
