import { getAnalysisResults } from '@/lib/storage';
import { StockCard } from '@/components/StockCard';
import { RefreshButton } from '@/components/RefreshButton';

export const revalidate = 0; // Disable cache for realtime-ish updates

export default async function Home() {
  const data = await getAnalysisResults();

  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="flex justify-between items-center border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
              Market Intelligence Agent
            </h1>
            <p className="text-slate-400 mt-2">
              AI-Powered Stock Analysis & Sentiment Tracking
            </p>
          </div>
          <div className="text-right">
            <RefreshButton />
            <p className="text-xs text-slate-500 mt-1">
              Last Updated: {data?.lastUpdated ? new Date(data.lastUpdated).toLocaleString() : 'Never'}
            </p>
          </div>
        </header>

        {!data ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-500 animate-pulse">
            <p>No analysis data found. Click Refresh to start.</p>
          </div>
        ) : (
          <div className="space-y-12">
            {/* Section 1: Market Indices */}
            <section>
              <h2 className="text-2xl font-bold mb-4 text-purple-400 border-b border-purple-500/20 pb-2">Market Indices</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {data.results.filter(r => ['^VIX', 'VUG', 'VTV', 'HYG'].includes(r.stock.symbol)).map((item) => (
                  <StockCard key={item.stock.symbol} data={item} />
                ))}
              </div>
            </section>

            {/* Section 2: US Market */}
            <section>
              <h2 className="text-2xl font-bold mb-4 text-blue-400 border-b border-blue-500/20 pb-2">US Market Leaders</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.results.filter(r => ['SPY', 'QQQ', 'MAGA', 'NVDA', 'GOOGL'].includes(r.stock.symbol)).map((item) => (
                  <StockCard key={item.stock.symbol} data={item} />
                ))}
              </div>
            </section>

            {/* Section 3: Korean Market */}
            <section>
              <h2 className="text-2xl font-bold mb-4 text-emerald-400 border-b border-emerald-500/20 pb-2">Korean Market</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.results.filter(r => ['^KS11', '^KQ11', '005930.KS', '000660.KS', '035420.KS'].includes(r.stock.symbol)).map((item) => (
                  <StockCard key={item.stock.symbol} data={item} />
                ))}
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
