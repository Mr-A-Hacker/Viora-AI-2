import { ArrowLeft, Menu } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ChatHeader({ connected, onToggleSidebar, onCloseKeyboard }) {
    const navigate = useNavigate();

    const handleBack = () => {
        onCloseKeyboard?.();
        navigate('/');
    };

    return (
        <header className="h-16 min-h-[64px] grid grid-cols-3 items-center px-4 bg-[var(--surface)]/80 backdrop-blur-lg border-b border-[var(--border)] z-10">
            <div className="flex justify-start">
                <button
                    onClick={handleBack}
                    className="p-2.5 rounded-xl flex items-center justify-center min-h-[44px] min-w-[44px] border-2 border-[var(--border)] text-[var(--text-mid)] hover:border-[var(--ai-color)] hover:text-[var(--ai-color)] transition-all duration-200"
                    aria-label="Go back"
                >
                    <ArrowLeft size={20} />
                </button>
            </div>
            <div className="flex flex-col items-center justify-center text-center">
                <div className="text-lg font-['Syne'] font-bold tracking-tight text-[var(--text)] leading-none mb-1">Viora AI</div>
                <div className="text-xs text-[var(--text-light)] font-['Plus_Jakarta_Sans'] leading-none">
                    {connected ? 'Ready to assist' : 'Connecting...'}
                </div>
            </div>
            <div className="flex justify-end">
                <button
                    onClick={onToggleSidebar}
                    className="p-2.5 rounded-xl flex items-center justify-center min-h-[44px] min-w-[44px] border-2 border-[var(--border)] text-[var(--text-mid)] hover:border-[#38bdf8] hover:text-[#38bdf8] transition-all duration-200"
                    aria-label="Toggle sidebar"
                >
                    <Menu size={20} />
                </button>
            </div>
        </header>
    );
}
