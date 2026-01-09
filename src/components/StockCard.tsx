import { StockData } from '@/lib/finance';
import { MultiAgentAnalysis } from '@/lib/ai';

interface StockCardProps {
    stock: StockData;
    analysis: MultiAgentAnalysis | null;
}

export function StockCard({ stock, analysis }: StockCardProps) {
    if (!analysis) return (
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800 animate-pulse">
            <div className="h-6 bg-slate-800 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-slate-800 rounded w-1/2"></div>
        </div>
    );

    const isPositive = stock.change >= 0;
    const scoreColor = analysis.total_score >= 80 ? 'text-emerald-400' : analysis.total_score >= 40 ? 'text-amber-400' : 'text-rose-400';

    return (
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800 hover:border-slate-700 transition-all shadow-lg">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-2xl font-bold text-white">{stock.name}</h3>
                    <p className="text-sm text-slate-400">{stock.symbol} • {stock.sector || 'Unknown Sector'}</p>
                </div>
                <div className="text-right">
                    <p className="text-xl font-mono text-white">
                        {stock.price.toLocaleString()} {stock.currency}
                    </p>
                    <p className={`text-sm font-mono ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isPositive ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                    </p>
                </div>
            </div>

            {/* AI Analysis Section */}
            <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                    <div className="flex items-center gap-3">
                        <div className={`text-2xl font-black ${analysis.investment_opinion === 'BUY' ? 'text-emerald-400' :
                                analysis.investment_opinion === 'SELL' ? 'text-rose-400' : 'text-amber-400'
                            }`}>
                            {analysis.investment_opinion}
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xs text-slate-400 uppercase tracking-wider">Confidence</span>
                            <span className="text-sm font-semibold text-white">{analysis.confidence_level}</span>
                        </div>
                    </div>

                    <div className="text-right">
                        <div className={`text-2xl font-bold ${scoreColor}`}>
                            {analysis.total_score}<span className="text-sm text-slate-500">/100</span>
                        </div>
                        <span className="text-xs text-slate-400 uppercase tracking-wider">AI Score</span>
                    </div>
                </div>

                {/* Score Breakdown (Mini Bars) */}
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                    <div>
                        <div className="text-slate-500 mb-1">Tech</div>
                        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500" style={{ width: `${analysis.score_breakdown.technical * 10}%` }}></div>
                        </div>
                    </div>
                    <div>
                        <div className="text-slate-500 mb-1">News</div>
                        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-500" style={{ width: `${analysis.score_breakdown.news * 10}%` }}></div>
                        </div>
                    </div>
                    <div>
                        <div className="text-slate-500 mb-1">Industry</div>
                        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500" style={{ width: `${analysis.score_breakdown.industry * 10}%` }}></div>
                        </div>
                    </div>
                    <div>
                        <div className="text-slate-500 mb-1">Market</div>
                        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-teal-500" style={{ width: `${analysis.score_breakdown.market * 10}%` }}></div>
                        </div>
                    </div>
                </div>

                <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700/30">
                    <p className="text-slate-300 text-sm leading-relaxed">
                        {analysis.summary}
                    </p>
                </div>

                <div className="flex justify-between items-center pt-2 border-t border-slate-800">
                    <span className="text-xs text-slate-500">
                        Updated: {new Date(analysis.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="text-xs font-mono text-slate-600 bg-slate-800/50 px-2 py-1 rounded">
                        {analysis.provider === 'Groq' ? '⚡ GPT OSS 120B' : analysis.provider === 'Gemini' ? '✨ Gemini 2.0' : '⚠️ System'}
                    </span>
                </div>
            </div>
        </div>
    );
}
