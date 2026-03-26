/**
 * Shared error message with optional retry. Use after failed fetch or operation.
 */
export default function ErrorMessage({ message, onRetry, className = '' }) {
    return (
        <div
            className={`p-4 bg-red-500/10 border-b border-red-500/30 text-red-400 text-sm font-['Plus_Jakarta_Sans'] flex items-center justify-between gap-3 ${className}`}
            role="alert"
        >
            <span className="flex-1 truncate" title={message}>{message}</span>
            {onRetry && (
                <button
                    type="button"
                    onClick={onRetry}
                    className="ai-btn px-4 py-2 text-sm bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-xl"
                >
                    Retry
                </button>
            )}
        </div>
    );
}
