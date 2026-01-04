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
            symbol: stock.symbol,
            recommendation: 'HOLD', // Default
            confidence: 0,
            sentimentScore: 50,
            summary: "AI Analysis is currently unavailable due to API configuration or rate limits. Please verify your API Keys in Vercel Settings.",
            keyFactors: ["Analysis Unavailable"],
            riskFactors: ["Data only"],
            analyzedAt: new Date().toISOString(),
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
                            analysis.recommendation === 'BUY' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                analysis.recommendation === 'SELL' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                    'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                        )}>
                            {analysis.recommendation}
                        </div>
                        <p className="text-slate-400 text-sm">Review Confidence: {analysis.confidence}%</p>
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
                            <h2 className="text-xl font-bold mb-4 text-purple-400">AI Analysis Summary</h2>
                            <div className="prose prose-invert max-w-none text-slate-300 font-light leading-relaxed whitespace-pre-line">
                                {analysis.summary}
                            </div>
                            <div className="mt-4 pt-4 border-t border-slate-800 text-right text-xs text-slate-500 font-mono">
                                Analysis Generated: {analysis.analyzedAt ? new Date(analysis.analyzedAt).toLocaleString() : 'Just now'} • Model: <span className="text-slate-400 font-bold">{analysis.provider === 'Groq' ? 'Llama-3.3-70b (via Groq)' : 'Gemini 2.0 Flash'}</span>
                            </div>
                        </section>
                    </div>

                    <div className="space-y-6">
                        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
                            <h3 className="text-lg font-bold mb-4 text-blue-400">Key Factors</h3>
                            <ul className="space-y-2">
                                {analysis.keyFactors?.map((factor, i) => (
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
                                {analysis.riskFactors?.map((factor, i) => (
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
