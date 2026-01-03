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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.results.map((item) => (
              <StockCard key={item.stock.symbol} data={item} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
