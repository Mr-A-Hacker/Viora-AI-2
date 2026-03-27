import { ArrowLeft, Menu, Moon, Sun } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useDarkMode } from '../contexts/DarkModeContext.jsx';

export default function ChatHeader({ connected, onToggleSidebar, onCloseKeyboard }) {
    const navigate = useNavigate();
    const { isDark, toggleDark } = useDarkMode();

    const handleBack = () => {
        onCloseKeyboard?.();
        navigate('/');
    };

    return (
        <header className="chat-header">
            <div className="flex justify-start">
                <button
                    onClick={handleBack}
                    className="header-btn"
                    aria-label="Go back"
                >
                    <ArrowLeft size={20} />
                </button>
            </div>
            <div className="flex flex-col items-center justify-center text-center">
                <div className="ai-name">Viora AI</div>
                <div className="text-xs text-[var(--text-light)] font-['Plus_Jakarta_Sans'] leading-none">
                    {connected ? 'Ready to assist' : 'Connecting...'}
                </div>
            </div>
            <div className="flex justify-end gap-2">
                <button
                    onClick={toggleDark}
                    className="header-btn dark-toggle"
                    aria-label="Toggle dark mode"
                >
                    {isDark ? <Sun size={18} /> : <Moon size={18} />}
                </button>
                <button
                    onClick={onToggleSidebar}
                    className="header-btn"
                    aria-label="Toggle sidebar"
                >
                    <Menu size={20} />
                </button>
            </div>
        </header>
    );
}
