import { getStockData } from '@/lib/finance';
import { analyzeStock } from '@/lib/gemini';
import { saveAnalysisResults } from '@/lib/storage';

const TARGET_STOCKS = [
    'AAPL', // Apple
    'TSLA', // Tesla
    '005930.KS', // Samsung Electronics (KR)
    '035420.KS', // NAVER (KR)
    'MSFT', // Microsoft
    'NVDA' // Nvidia
];

export async function runBatchAnalysis() {
    console.log("Starting batch analysis...");
    const results = [];

    for (const symbol of TARGET_STOCKS) {
        try {
            console.log(`Processing ${symbol}...`);
            const stockData = await getStockData(symbol);
            const analysis = await analyzeStock(stockData);

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
