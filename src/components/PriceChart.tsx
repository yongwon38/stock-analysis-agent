'use client';

import { HistoryItem } from '@/lib/finance';
import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis
} from 'recharts';

interface PriceChartProps {
    data: HistoryItem[];
    color?: string;
}

export function PriceChart({ data, color = '#3b82f6' }: PriceChartProps) {
    return (
        <div className="h-[400px] w-full bg-slate-900/50 rounded-xl p-4 border border-slate-800">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={color} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                        dataKey="date"
                        stroke="#64748b"
                        tickFormatter={(str) => {
                            const date = new Date(str);
                            return `${date.getMonth() + 1}/${date.getDate()}`;
                        }}
                        minTickGap={30}
                    />
                    <YAxis
                        domain={['auto', 'auto']}
                        stroke="#64748b"
                        tickFormatter={(val) => val.toLocaleString()}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
                        itemStyle={{ color: '#f8fafc' }}
                        formatter={(value: number | undefined) => [value?.toLocaleString() || '', 'Price']}
                        labelFormatter={(label) => new Date(label).toLocaleDateString()}
                    />
                    <Area
                        type="monotone"
                        dataKey="close"
                        stroke={color}
                        fillOpacity={1}
                        fill="url(#colorPrice)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
