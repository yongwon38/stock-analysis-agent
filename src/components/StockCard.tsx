import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import Link from 'next/link';
import { StockData } from '@/lib/finance';
import { AnalysisResult } from '@/lib/gemini';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface StockCardProps {
    data: {
        stock: StockData;
        analysis: AnalysisResult;
    };
}

export function StockCard({ data }: StockCardProps) {
    const { stock, analysis } = data;
    const isPositive = stock.change >= 0;

    const sentimentColor =
        analysis.sentimentScore >= 70 ? 'text-emerald-400' :
            analysis.sentimentScore >= 40 ? 'text-yellow-400' : 'text-red-400';

    const recommendationColor =
        analysis.recommendation === 'BUY' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
            analysis.recommendation === 'SELL' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';

    return (
        <Link href={`/stock/${encodeURIComponent(stock.symbol)}`} className="group relative block bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-600 transition-all duration-300 shadow-lg hover:shadow-xl hover:shadow-blue-500/5">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-xl font-bold">{stock.symbol}</h3>
                    <p className="text-sm text-slate-400 truncate max-w-[150px]">{stock.name}</p>
                </div>
                <div className={twMerge("px-3 py-1 rounded-full text-xs font-bold border", recommendationColor)}>
                    {analysis.recommendation}
                </div>
            </div>

            <div className="mb-6">
                <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold">{stock.price.toLocaleString()}</span>
                    <span className="text-xs text-slate-500">{stock.currency}</span>
                </div>
                <div className={clsx("flex items-center gap-1 text-sm font-medium", isPositive ? "text-emerald-400" : "text-red-400")}>
                    {isPositive ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
                    <span>{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)</span>
                </div>
            </div>

            <div className="space-y-3 border-t border-slate-800 pt-4">
                <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-500">AI Confidence</span>
                    <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-blue-500 rounded-full"
                                style={{ width: `${analysis.confidence}%` }}
                            />
                        </div>
                        <span className="font-mono text-blue-400">{analysis.confidence}%</span>
                    </div>
                </div>

                <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-500">News Sentiment</span>
                    <span className={twMerge("font-mono font-bold", sentimentColor)}>
                        {analysis.sentimentScore}/100
                    </span>
                </div>
            </div>

            {/* Hidden detail overlay or link could go here */}
            <div className="mt-4 pt-4 border-t border-slate-800">
                <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">
                    {analysis.summary}
                </p>
            </div>
        </Link>
    );
}
