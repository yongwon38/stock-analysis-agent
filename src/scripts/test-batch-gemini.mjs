import { GoogleGenerativeAI } from '@google/generative-ai';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const apiKey = process.env.GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(apiKey || "");

async function testBatch() {
    // Try a specific version that usually works
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro-latest" });

    const stocks = [
        { symbol: "AAPL", name: "Apple", price: 230, changePercent: 12.5, news: ["Apple launches new Vision Pro", "Stock hits all time high"] },
        { symbol: "TSLA", name: "Tesla", price: 180, changePercent: -5.2, news: ["Robotaxi event delayed", "Elon Musk tweets"] },
        { symbol: "005930.KS", name: "Samsung Electronics", price: 75000, changePercent: -2.0, news: ["Chip demand slows", "New Galaxy S25 rumors"] }
    ];

    const prompt = `
  You are a professional financial analyst. Analyze the following list of stocks data.
  
  Input Data (JSON):
  ${JSON.stringify(stocks, null, 2)}
  
  Task:
  For EACH stock in the list, provide:
  1. Recommendation (BUY, SELL, HOLD)
  2. Confidence Score (0-100)
  3. Sentiment Score based on news (0-100)
  4. Summary of reasoning
  
  Output Format:
  Strictly return a JSON ARRAY of objects. Each object must contain:
  {
      "symbol": "STOCK_SYMBOL",
      "recommendation": "BUY" | "SELL" | "HOLD",
      "confidence": number,
      "sentimentScore": number,
      "summary": "string",
      "keyFactors": ["string", "string"],
      "riskFactors": ["string", "string"]
  }
  `;

    try {
        console.log("Sending batch request...");
        // For testing, force failure to test fallback if needed, or try real model
        const result = await model.generateContent(prompt);
        const text = (await result.response).text();
        console.log("Success (Gemini):", text.substring(0, 100));
    } catch (e) {
        console.warn("Batch failed or Rate Limited. Executing Rule-Based Fallback...", e.message.split('\n')[0]);

        const fallbackResults = stocks.map(stock => {
            let rec = 'HOLD';
            let conf = 50;
            let summary = "AI Unavailable. ";

            if (stock.changePercent > 3) {
                rec = 'BUY';
                conf = 70;
                summary += "Strong upward momentum detected.";
            } else if (stock.changePercent < -3) {
                rec = 'SELL';
                conf = 60;
                summary += "Negative trend detected.";
            } else {
                summary += "Market movement is neutral.";
            }

            return {
                symbol: stock.symbol,
                recommendation: rec,
                confidence: conf,
                sentimentScore: 50,
                summary: summary,
                keyFactors: ["Technical Trend"],
                riskFactors: ["Market Volatility"],
                analyzedAt: new Date().toISOString()
            };
        });

        console.log("Fallback Generated Items:", fallbackResults.length);
        console.log(JSON.stringify(fallbackResults[0], null, 2));
    }
}

testBatch();
