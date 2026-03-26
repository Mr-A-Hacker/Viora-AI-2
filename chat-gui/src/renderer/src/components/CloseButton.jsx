import React from 'react';
import { X } from 'lucide-react';

const CloseButton = () => {
    const handleClose = () => {
        if (window.electron && window.electron.quit) {
            window.electron.quit();
        } else {
            console.log('Close button clicked (Electron API not available)');
            window.close();
        }
    };

    return (
        <button
            onClick={handleClose}
            className="absolute top-4 right-4 z-[9999] w-12 h-12 flex items-center justify-center bg-red-500 hover:bg-red-600 text-white rounded-2xl active:scale-95 transition-all shadow-lg shadow-red-500/25"
            aria-label="Close Application"
            title="Close"
        >
            <X size={20} />
        </button>
    );
};

export default CloseButton;
