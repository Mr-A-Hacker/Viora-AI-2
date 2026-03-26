import React from 'react';

export default class ErrorBoundary extends React.Component {
    state = { hasError: false, error: null };

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, info) {
        console.error('ErrorBoundary caught:', error, info);
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: null });
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="w-full h-full flex flex-col items-center justify-center gap-6 p-8 bg-[var(--bg)] text-[var(--text)]">
                    <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center">
                        <span className="text-4xl">⚠️</span>
                    </div>
                    <p className="text-center font-['Syne'] font-semibold text-xl text-[var(--text)]">
                        Something went wrong
                    </p>
                    <p className="text-center text-sm text-[var(--text-mid)] max-w-md">
                        {this.state.error?.message || 'An unexpected error occurred.'}
                    </p>
                    <button
                        type="button"
                        onClick={this.handleRetry}
                        className="ai-btn px-8 py-4 bg-gradient-to-br from-[#7c3aed] to-[#6d28d9] text-white font-['Plus_Jakarta_Sans'] font-medium rounded-2xl shadow-lg shadow-[var(--ai-color)]/30"
                    >
                        Try Again
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}
