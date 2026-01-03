'use client';

import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';

export function RefreshButton() {
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleRefresh = async () => {
        setLoading(true);
        try {
            await fetch('/api/analyze');
            router.refresh();
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
        >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
    );
}
