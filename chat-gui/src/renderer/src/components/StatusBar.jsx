import React, { useState, useEffect } from 'react';
import { Activity, Thermometer, Cpu, Clock } from 'lucide-react';
import { apiFetch } from '../apiClient.js';

const StatusBar = () => {
    const [stats, setStats] = useState({
        time: '--:--:--',
        cpu_percent: 0,
        memory_percent: 0,
        temperature: 0
    });

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await apiFetch('/system/stats');
                setStats(data);
            } catch (error) {
                console.error('Failed to fetch system stats:', error);
            }
        };

        fetchStats();
        const interval = setInterval(fetchStats, 2000);

        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (value, type) => {
        if (type === 'temp') {
            if (value > 80) return 'text-red-500';
            if (value > 60) return 'text-yellow-500';
            return 'text-green-500';
        }
        if (value > 80) return 'text-red-500';
        if (value > 50) return 'text-yellow-500';
        return 'text-green-500';
    };

    return (
        <div className="w-full h-10 bg-[var(--surface)] border-b border-[var(--border)] z-50 flex items-center justify-between px-4 text-sm font-['Plus_Jakarta_Sans'] select-none backdrop-blur-md">
            <div className="flex items-center gap-2 text-[var(--ai-color)]">
                <Clock size={14} />
                <span>{stats.time}</span>
            </div>

            <div className="flex items-center gap-5">
                <div className="flex items-center gap-1.5 text-[var(--text-mid)]">
                    <Cpu size={12} className="text-[var(--text-light)]" />
                    <span>CPU</span>
                    <span className={`font-semibold ${getStatusColor(stats.cpu_percent, 'usage')}`}>
                        {Math.round(stats.cpu_percent)}%
                    </span>
                </div>

                <div className="flex items-center gap-1.5 text-[var(--text-mid)]">
                    <Activity size={12} className="text-[var(--text-light)]" />
                    <span>RAM</span>
                    <span className={`font-semibold ${getStatusColor(stats.memory_percent, 'usage')}`}>
                        {Math.round(stats.memory_percent)}%
                    </span>
                </div>

                <div className="flex items-center gap-1.5 text-[var(--text-mid)]">
                    <Thermometer size={12} className="text-[var(--text-light)]" />
                    <span>TEMP</span>
                    <span className={`font-semibold ${getStatusColor(stats.temperature, 'temp')}`}>
                        {Math.round(stats.temperature)}°
                    </span>
                </div>
            </div>
        </div>
    );
};

export default StatusBar;
