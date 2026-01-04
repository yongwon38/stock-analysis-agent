import { GoogleGenerativeAI } from '@google/generative-ai';
import { StockData } from './finance';

const apiKey = process.env.GEMINI_API_KEY;

if (!apiKey) {
    console.warn("GEMINI_API_KEY is not set. Gemini features will fail.");
}

const genAI = new GoogleGenerativeAI(apiKey || "");

export interface AnalysisResult {
    symbol: string;
    recommendation: 'BUY' | 'SELL' | 'HOLD';
    confidence: number; // 0-100
    sentimentScore: number; // 0-100 (New Requirement)
    summary: string; // Markdown summary of the reasoning
    keyFactors: string[]; // List of bullet points
    riskFactors: string[];
    analyzedAt: string; // ISO String of when analysis happened
}

// Fallback logic for when AI fails
function getRuleBasedAnalysis(stock: StockData): AnalysisResult {
    let rec: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
    let conf = 50;
    let sentiment = 50;
    let summaryParts = ["**AI Analysis Unavailable (Rate Limit/Error)**: Switching to Technical Fallback."];

    // Simple Rule: 1-Year Trend
    // We don't have explicit 1-year change % in StockData property, so we calculate from price vs closing price of history[0]
    // But data.changePercent is daily. 
    // Let's assume the batch caller might have calculated it, or we rely on daily change for now.
    // Actually, let's use daily change for immediate sentiment.

    if (stock.changePercent > 1.5) {
        rec = 'BUY';
        conf = 65;
        sentiment = 75;
        summaryParts.push(`Stock shows strong daily momentum up ${stock.changePercent.toFixed(2)}%.`);
    } else if (stock.changePercent < -1.5) {
        rec = 'SELL';
        conf = 65;
        sentiment = 25;
        summaryParts.push(`Stock shows significant daily decline of ${stock.changePercent.toFixed(2)}%.`);
    } else {
        summaryParts.push(`Stock is relatively flat (${stock.changePercent.toFixed(2)}%) today.`);
    }

    // PE Ratio check
    if (stock.peRatio) {
        if (stock.peRatio > 50) {
            summaryParts.push("P/E Ratio is high, suggesting premium valuation.");
            if (rec === 'BUY') conf -= 10;
        } else if (stock.peRatio < 15 && stock.peRatio > 0) {
            summaryParts.push("P/E Ratio appears attractive.");
            if (rec === 'SELL') rec = 'HOLD';
        }
    }

    return {
        symbol: stock.symbol,
        recommendation: rec,
        confidence: conf,
        sentimentScore: sentiment,
        summary: summaryParts.join("\n\n"),
        keyFactors: ["Technical Momentum", "Valuation Check"],
        riskFactors: ["Market Volatility", "Data Limited"],
        analyzedAt: new Date().toISOString()
    };
}

export async function analyzeStockBatch(stocks: StockData[]): Promise<AnalysisResult[]> {
    // Try to use 1.5-flash-001 or 2.0-flash if quota permits
    // 2.0-flash gave 429 quota 0. Switch to 2.0-flash-lite as requested.
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-lite" });

    // Optimize payload: Only send necessary fields to save tokens
    const simplifiedData = stocks.map(s => ({
        symbol: s.symbol,
        name: s.name,
        price: s.price,
        currency: s.currency,
        changePercent: s.changePercent,
        pe: s.peRatio,
        headlines: s.news.slice(0, 3).map(n => n.title) // Only top 3 headlines
    }));

    const prompt = `
    You are a financial analyst. Analyze these stocks.
    Input: ${JSON.stringify(simplifiedData)}
    
    Task: Return a JSON ARRAY of objects (one for each input stock) with:
    { "symbol": "...", "recommendation": "BUY/SELL/HOLD", "confidence": 0-100, "sentimentScore": 0-100, "summary": "markdown", "keyFactors": [], "riskFactors": [] }
    
    Keep summaries concise.
    `;

    try {
        console.log(`Sending batch analysis for ${stocks.length} stocks...`);
        const result = await model.generateContent(prompt);
        const text = (await result.response).text();

        const jsonStr = text.replace(/```json/g, '').replace(/```/g, '').trim();
        const resultsArray = JSON.parse(jsonStr);

        // Map results back to ensure order and missing items handling
        return stocks.map(stock => {
            const analysis = resultsArray.find((r: any) => r.symbol === stock.symbol);
            if (analysis) {
                return {
                    symbol: stock.symbol,
                    ...analysis,
                    analyzedAt: new Date().toISOString()
                };
            }
            return getRuleBasedAnalysis(stock);
        });

    } catch (error) {
        console.error("Gemini Batch Analysis Failed:", error);
        // Fallback for ENTIRE batch
        return stocks.map(stock => getRuleBasedAnalysis(stock));
    }
}
