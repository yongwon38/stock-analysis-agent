import { getStockData } from '@/lib/finance';
import { analyzeStock } from '@/lib/gemini';
import { saveAnalysisResults } from '@/lib/storage';

const TARGET_STOCKS = [
    // Section 1: Market Indices
    { symbol: '^VIX', name: 'Volatility Index' }, // VIX
    { symbol: 'VUG', name: 'Vanguard Growth ETF' }, // Growth
    { symbol: 'VTV', name: 'Vanguard Value ETF' }, // Value
    { symbol: 'HYG', name: 'iShares iBoxx $ High Yield Corporate Bond ETF' }, // High Yield Spread Proxy

    // Section 2: US Market
    { symbol: 'SPY', name: 'S&P 500' },
    { symbol: 'QQQ', name: 'Nasdaq 100' },
    { symbol: 'MAGA', name: 'MAGA ETF' },
    { symbol: 'NVDA', name: 'Nvidia' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.' },

    // Section 3: KR Market
    { symbol: '^KS11', name: 'KOSPI' },
    { symbol: '^KQ11', name: 'KOSDAQ' },
    { symbol: '005930.KS', name: '삼성전자' },
    { symbol: '000660.KS', name: 'SK하이닉스' },
    { symbol: '035420.KS', name: '네이버' }
];

export async function runBatchAnalysis() {
    console.log("Starting batch analysis...");

    // 1. Load existing results for fallback
    let existingResults = [];
    try {
        const fs = require('fs');
        const path = require('path');
        const dbPath = path.join(process.cwd(), 'data', 'analysis_results.json');
        if (fs.existsSync(dbPath)) {
            const data = JSON.parse(fs.readFileSync(dbPath, 'utf8'));
            existingResults = data.results || [];
        }
    } catch (e) {
        console.warn("Could not load existing results for fallback:", e);
    }

    const results = [];

    for (const item of TARGET_STOCKS) {
        const symbol = item.symbol;
        const displayName = item.name;

        try {
            console.log(`Processing ${symbol} (${displayName})...`);
            const stockData = await getStockData(symbol);

            // Override name if provided (especially for KR stocks)
            if (displayName) {
                stockData.name = displayName;
            }

            let analysis = await analyzeStock(stockData);

            // 2. CHECK FOR FALLBACK
            // If recommendation is HOLD and confidence is 0, it likely failed.
            if (analysis.confidence === 0 && analysis.recommendation === 'HOLD' && analysis.summary.includes("failed")) {
                console.warn(`Analysis failed for ${symbol}. checking for fallback...`);
                const previousEntry = existingResults.find((r: any) => r.stock.symbol === symbol);

                if (previousEntry && previousEntry.analysis && previousEntry.analysis.confidence > 0) {
                    console.log(`Using fallback analysis for ${symbol} from ${previousEntry.analysis.analyzedAt}`);
                    analysis = {
                        ...previousEntry.analysis,
                        // We keep the old analysis timestamps and content, 
                        // but ensure the symbol matches just in case.
                        symbol: stockData.symbol
                    };
                }
            }

            results.push({
                stock: stockData,
                analysis: analysis
            });

            // Delay to avoid hitting rate limits too hard (Gemini Free Tier is strictly rate limited)
            // Increased to 10 seconds per user request
            await new Promise(resolve => setTimeout(resolve, 10000));
        } catch (error) {
            console.error(`Error processing ${symbol}:`, error);
            const fs = require('fs');
            // use appendFileSync for simple debugging
            try {
                fs.appendFileSync('debug.log', `Error processing ${symbol}: ${error instanceof Error ? error.message : String(error)}\n`);
            } catch (e) {
                // ignore logging error
            }
        }
    }

    const storedData = {
        lastUpdated: new Date().toISOString(),
        results
    };

    await saveAnalysisResults(storedData);
    console.log("Batch analysis completed and saved.");
    return storedData;
}
