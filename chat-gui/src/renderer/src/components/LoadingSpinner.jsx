/**
 * Shared loading indicator. Use when fetching data or waiting for connection.
 */
export default function LoadingSpinner({ label = 'Loading...', className = '' }) {
    return (
        <div
            className={`flex flex-col items-center justify-center gap-4 text-[var(--text)] font-['Plus_Jakarta_Sans'] ${className}`}
            role="status"
            aria-label={label}
        >
            <div
                className="w-12 h-12 border-4 border-[var(--border)] border-t-[var(--ai-color)] rounded-full animate-spin"
                style={{ animationDuration: '0.8s' }}
            />
            {label && <span className="text-sm text-[var(--text-mid)]">{label}</span>}
        </div>
    );
}
