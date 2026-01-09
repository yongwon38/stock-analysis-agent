import { StockData } from '@/lib/finance';
import { MultiAgentAnalysis } from '@/lib/ai';

interface StockCardProps {
    stock: StockData;
    analysis: MultiAgentAnalysis | null;
}

export function StockCard({ stock, analysis }: StockCardProps) {
    // Determine status for UI
    const isPositive = stock.change >= 0;
    const hasAnalysis = !!analysis;

    // Derived values for Analysis (safe access)
    const score = analysis?.total_score || 0;
    const scoreColor = score >= 80 ? 'text-emerald-400' : score >= 40 ? 'text-amber-400' : 'text-rose-400';
    const opinion = analysis?.investment_opinion || 'NEUTRAL';
    const confidence = analysis?.confidence_level || 'Low';

    return (
        <a href={`/stock/${stock.symbol}`} className="block bg-slate-900 rounded-xl p-6 border border-slate-800 hover:border-slate-600 transition-all shadow-lg hover:shadow-blue-500/10 group">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors">{stock.name}</h3>
                    <p className="text-sm text-slate-400">{stock.symbol} • {stock.sector || 'Unknown'}</p>
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
            {hasAnalysis && analysis ? (
                <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                        <div className="flex items-center gap-3">
                            <div className={`text-2xl font-black ${opinion === 'BUY' ? 'text-emerald-400' :
                                opinion === 'SELL' ? 'text-rose-400' : 'text-amber-400'
                                }`}>
                                {opinion}
                            </div>
                            <div className="flex flex-col">
                                <span className="text-xs text-slate-400 uppercase tracking-wider">Confidence</span>
                                <span className="text-sm font-semibold text-white">{confidence}</span>
                            </div>
                        </div>

                        <div className="text-right">
                            <div className={`text-2xl font-bold ${scoreColor}`}>
                                {score}<span className="text-sm text-slate-500">/100</span>
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
                            <div className="text-slate-500 mb-1">Ind.</div>
                            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full bg-purple-500" style={{ width: `${analysis.score_breakdown.industry * 10}%` }}></div>
                            </div>
                        </div>
                        <div>
                            <div className="text-slate-500 mb-1">Mkt.</div>
                            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full bg-teal-500" style={{ width: `${analysis.score_breakdown.market * 10}%` }}></div>
                            </div>
                        </div>
                    </div>

                    <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/30">
                        <p className="text-slate-300 text-sm leading-relaxed line-clamp-2">
                            {analysis.summary}
                        </p>
                    </div>

                    <div className="flex justify-between items-center pt-2 border-t border-slate-800">
                        <span className="text-xs text-slate-500">
                            {new Date(analysis.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="text-xs font-mono text-slate-600 bg-slate-800/50 px-2 py-1 rounded">
                            {analysis.provider === 'Groq' ? '⚡ GPT OSS' : 'System'}
                        </span>
                    </div>
                </div>
            ) : (
                <div className="mt-4 pt-4 border-t border-slate-800 text-center">
                    <span className="text-sm font-medium text-blue-400 group-hover:text-blue-300 flex items-center justify-center gap-2">
                        ✨ Click to Analyze with AI Agent
                    </span>
                </div>
            )}
        </a>
    );
}
