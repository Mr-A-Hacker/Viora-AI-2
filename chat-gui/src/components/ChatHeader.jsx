import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Avatar from './Avatar';

export default function ChatHeader({ connected, onReset }) {
    const navigate = useNavigate();

    return (
        <header className="h-16 min-h-[64px] flex items-center justify-between px-4 bg-slate-50 border-b border-gray-200 z-10">
            <div className="flex items-center gap-3">
                <button
                    onClick={() => navigate('/')}
                    className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-slate-200 text-slate-600 transition-colors"
                    aria-label="Go back"
                >
                    <ArrowLeft size={24} />
                </button>

                <div className="flex items-center gap-3">
                    <Avatar
                        className="shadow-[0_2px_12px_rgba(0,149,255,0.2)] border border-blue-100/50"
                        variant="sm"
                        animate={true}
                    />
                    <div>
                        <div className="text-[17px] font-bold tracking-tight text-slate-900 leading-none mb-0.5">A.D.A</div>
                        <div className="text-[11px] text-slate-500 font-medium leading-none">Advanced Design Assistant</div>
                    </div>
                </div>
            </div>
            <div className="flex gap-2">
                <button
                    className="w-12 h-12 border-none rounded-[10px] bg-gray-200 text-gray-600 text-lg cursor-pointer flex items-center justify-center transition-all duration-150 active:scale-95 active:bg-blue-500 active:text-white"
                    onClick={onReset}
                    aria-label="Reset session"
                    title="Reset session"
                >
                    ↻
                </button>
            </div>
        </header>
    );
}
