import React from 'react';

export default function ConnectionBar({ status, onRetry }) {
    const labels = {
        connected: 'Connected',
        disconnected: 'Disconnected — tap to retry',
        connecting: 'Connecting…',
    };

    const styles = {
        connected: 'bg-green-500/10 text-green-500 border-green-500/30',
        disconnected: 'bg-red-500/10 text-red-500 border-red-500/30',
        connecting: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30',
    };

    const handleClick = () => {
        if (status === 'disconnected' && onRetry) onRetry();
    };

    return (
        <div
            role={status === 'disconnected' && onRetry ? 'button' : undefined}
            tabIndex={status === 'disconnected' && onRetry ? 0 : undefined}
            onClick={handleClick}
            onKeyDown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && status === 'disconnected' && onRetry) onRetry(); }}
            className={`flex items-center justify-center gap-2 py-2 px-4 text-xs font-['Plus_Jakarta_Sans'] font-medium uppercase border rounded-full ${styles[status] || ''} ${status === 'disconnected' && onRetry ? 'cursor-pointer hover:opacity-80' : ''}`}
        >
            <span className={`w-2 h-2 ${status === 'connecting' ? 'animate-pulse' : ''} bg-current rounded-full`} />
            <span>{labels[status] || status}</span>
        </div>
    );
}
