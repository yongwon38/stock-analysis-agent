import { getStockData } from '@/lib/finance';
// import { analyzeStockBatch } from '@/lib/gemini'; // Deprecated
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

    // 1. Gather all stock data first
    const stockDataList = [];
    for (const item of TARGET_STOCKS) {
        const symbol = item.symbol;
        const displayName = item.name;

        try {
            console.log(`Fetching data for ${symbol} (${displayName})...`);
            const stockData = await getStockData(symbol);
            if (displayName) {
                stockData.name = displayName;
            }
            stockDataList.push(stockData);

            // Small delay for Yahoo Finance politeness, not Gemini
            await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
            console.error(`Error fetching ${symbol}:`, error);
        }
    }

    // 2. Perform Analysis (Serial to prevent race condition on JSON file)
    console.log(`Starting serialized analysis for ${stockDataList.length} stocks...`);
    const results = [];

    // Import new AI service
    const { getStockAnalysis } = require('@/lib/ai');

    for (const stock of stockDataList) {
        try {
            console.log(`Analyzing ${stock.symbol}...`);
            // getStockAnalysis checks cache and saves internally.
            const analysis = await getStockAnalysis(stock);

            results.push({
                stock: stock,
                analysis: analysis
            });

            // Small delay to be polite
            await new Promise(resolve => setTimeout(resolve, 2000));

        } catch (e) {
            console.error(`Skipping ${stock.symbol} due to analysis error:`, e);
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
