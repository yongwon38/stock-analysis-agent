import { getStockData } from '@/lib/finance';
import { getStockAnalysis } from '@/lib/ai';
import { PriceChart } from '@/components/PriceChart';
import Link from 'next/link';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import { clsx } from 'clsx';

interface PageProps {
    params: Promise<{ symbol: string }>;
}

// Next.js 15+ params are async
export default async function StockPage(props: PageProps) {
    const params = await props.params;
    const { symbol } = params;
    const decodedSymbol = decodeURIComponent(symbol);

    // 1. Fetch Request: Get fresh stock data (Real-time)
    let stock;
    try {
        console.log(`[On-Demand] Fetching live data for ${decodedSymbol}...`);
        stock = await getStockData(decodedSymbol);
    } catch (e) {
        console.error("Failed to load stock data:", e);
        return (
            <div className="min-h-screen flex items-center justify-center text-slate-400 bg-slate-950">
                <div className="text-center">
                    <h2 className="text-xl font-bold text-red-400 mb-2">Stock Not Found</h2>
                    <p>Could not retrieve data for {decodedSymbol}.</p>
                </div>
            </div>
        );
    }

    // 2. AI Request: Check Cache -> analyze via AI -> Save
    // FAIL-SAFE: If AI fails, we still show the page with an "Unavailable" state.
    let analysis;
    try {
        console.log(`[On-Demand] Checking AI analysis for ${decodedSymbol}...`);
        analysis = await getStockAnalysis(stock);
    } catch (e) {
        console.error("AI Analysis Failed (Page will render without it):", e);
        // Create a placeholder "Empty" analysis so the UI doesn't crash
        analysis = {
            investment_opinion: 'HOLD', // Default
            confidence_level: 'Low',
            total_score: 0,
            score_breakdown: { technical: 0, news: 0, industry: 0, market: 0 },
            summary: "AI Analysis is currently unavailable. Please check system status.",
            key_rationale: ["Analysis Unavailable"],
            risk_factors: ["Data only"],
            timestamp: new Date().toISOString(),
            details: {} as any,
            provider: 'System'
        };
    }

    const isPositive = stock.change >= 0;

    return (
        <main className="min-h-screen bg-slate-950 text-white p-8">
            <div className="max-w-5xl mx-auto space-y-8">
                <Link href="/" className="inline-flex items-center text-slate-400 hover:text-white transition-colors">
                    <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
                </Link>

                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-4xl font-bold">{stock.name} <span className="text-2xl text-slate-500 font-normal">({stock.symbol})</span></h1>
                        <div className="flex items-center gap-4 mt-2">
                            <span className="text-3xl font-mono font-bold">{stock.price.toLocaleString()} {stock.currency}</span>
                            <span className={clsx("text-lg font-medium px-2 py-0.5 rounded", isPositive ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400")}>
                                {stock.change > 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                            </span>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className={clsx(
                            "inline-block px-4 py-2 rounded-lg text-xl font-bold mb-2 border",
                            analysis.investment_opinion === 'BUY' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                analysis.investment_opinion === 'SELL' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                    'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                        )}>
                            {analysis.investment_opinion}
                        </div>
                        <p className="text-slate-400 text-sm">Confidence: <span className="text-white font-semibold">{analysis.confidence_level}</span></p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-8">
                        <section>
                            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                                Price History <span className="text-xs font-normal text-slate-500">(1 Year)</span>
                            </h2>
                            <PriceChart data={stock.history} color={isPositive ? '#34d399' : '#f87171'} />
                        </section>

                        <section className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-bold text-purple-400">Multi-Agent Analysis</h2>
                                <div className="text-2xl font-bold text-white">{analysis.total_score}<span className="text-sm text-slate-500">/100</span></div>
                            </div>

                            <div className="prose prose-invert max-w-none text-slate-300 font-light leading-relaxed whitespace-pre-line mb-6">
                                {analysis.summary}
                            </div>

                            {/* Score Breakdown Bars */}
                            <div className="grid grid-cols-4 gap-4 mb-6">
                                {Object.entries(analysis.score_breakdown).map(([key, score]) => (
                                    <div key={key} className="text-center">
                                        <div className="text-xs text-slate-500 uppercase mb-1">{key}</div>
                                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                            <div className="h-full bg-blue-500" style={{ width: `${(score as number) * 10}%` }}></div>
                                        </div>
                                        <div className="text-xs font-mono mt-1 text-slate-300">{score as number}/10</div>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-4 pt-4 border-t border-slate-800 text-right text-xs text-slate-500 font-mono">
                                Analysis Generated: {analysis.timestamp ? new Date(analysis.timestamp).toLocaleString() : 'Just now'} • Provider: <span className="text-slate-400 font-bold">{analysis.provider === 'Groq' ? 'Groq (GPT-OSS-120B)' : analysis.provider === 'Gemini' ? 'Gemini 2.0' : 'System'}</span>
                            </div>
                        </section>
                    </div>

                    <div className="space-y-6">
                        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
                            <h3 className="text-lg font-bold mb-4 text-blue-400">Key Rationale</h3>
                            <ul className="space-y-2">
                                {analysis.key_rationale?.map((factor: string, i: number) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                                        <span className="text-blue-500 mt-1">•</span>
                                        {factor}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
                            <h3 className="text-lg font-bold mb-4 text-orange-400">Risk Factors</h3>
                            <ul className="space-y-2">
                                {analysis.risk_factors?.map((factor: string, i: number) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                                        <span className="text-orange-500 mt-1">•</span>
                                        {factor}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
                            <h3 className="text-lg font-bold mb-4">Latest News</h3>
                            <div className="space-y-4">
                                {stock.news.slice(0, 5).map((news) => (
                                    <a
                                        key={news.uuid}
                                        href={news.link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block group"
                                    >
                                        <h4 className="text-sm font-medium group-hover:text-blue-400 transition-colors line-clamp-2">{news.title}</h4>
                                        <div className="flex justify-between mt-1 text-xs text-slate-500">
                                            <span>{news.publisher}</span>
                                            <span>{new Date(news.providerPublishTime * 1000).toLocaleDateString()}</span>
                                        </div>
                                    </a>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
