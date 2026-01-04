import { TARGET_STOCKS, GROUPS } from '@/lib/consts';
import { getStockData } from '@/lib/finance';
import { getCachedAnalysis } from '@/lib/ai';
import { StockCard } from '@/components/StockCard';
import { RefreshButton } from '@/components/RefreshButton';

export const dynamic = 'force-dynamic'; // Force real-time (no caching of page)

export default async function Dashboard() {
  // 1. Fetch Real-Time Market Data & Cached AI in Parallel
  const results = await Promise.all(
    TARGET_STOCKS.map(async (item) => {
      try {
        // Parallelize Finance and AI Cache lookup
        const [stock, analysis] = await Promise.all([
          getStockData(item.symbol),
          getCachedAnalysis(item.symbol)
        ]);

        // Override name if provided in config
        if (item.name) stock.name = item.name;

        return { stock, analysis };
      } catch (e) {
        console.error(`Failed to load dashboard data for ${item.symbol}:`, e);
        return null;
      }
    })
  );

  const validResults = results.filter(r => r !== null);

  // 2. Group Data
  const indices = validResults.filter(r => GROUPS.INDICES.includes(r!.stock.symbol));
  const usStocks = validResults.filter(r => GROUPS.US.includes(r!.stock.symbol));
  const krStocks = validResults.filter(r => GROUPS.KR.includes(r!.stock.symbol));

  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-7xl mx-auto space-y-12">
        <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              Market Intelligence
            </h1>
            <p className="text-slate-400 mt-2">Real-time Analysis & Semantic Search</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right text-xs text-slate-500 hidden md:block">
              <p>Global Market Status: <span className="text-green-400">OPEN</span></p>
              <p>Data Source: Real-time</p>
            </div>
            <RefreshButton />
          </div>
        </header>

        <section>
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-slate-300">
            <span className="w-1 h-6 bg-blue-500 rounded-full"></span>
            Market Indices
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {indices.map((item) => (
              <StockCard key={item!.stock.symbol} data={item as any} />
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-slate-300">
            <span className="w-1 h-6 bg-purple-500 rounded-full"></span>
            US Market Leaders
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {usStocks.map((item) => (
              <StockCard key={item!.stock.symbol} data={item as any} />
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-slate-300">
            <span className="w-1 h-6 bg-emerald-500 rounded-full"></span>
            Korea Market
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {krStocks.map((item) => (
              <StockCard key={item!.stock.symbol} data={item as any} />
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
