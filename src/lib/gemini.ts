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

export async function analyzeStock(data: StockData): Promise<AnalysisResult> {
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

    const prompt = `
    You are a professional financial analyst. Analyze the following stock data for ${data.symbol} (${data.name}).
    
    Context:
    - Current Price: ${data.price} ${data.currency}
    - PE Ratio: ${data.peRatio}
    - EPS: ${data.eps}
    - 1 Year Change: (Calculate from history if needed, or rely on general trend)
    
    Recent News Headlines:
    ${data.news.map(n => `- ${n.title} (${new Date(n.providerPublishTime * 1000).toISOString()})`).join('\n')}
    
    Task:
    - Provide a investment recommendation (BUY, SELL, or HOLD) with a confidence score (0-100).
    - Also perform a sentiment analysis on the news headlines and provide a sentiment score (0-100, where 0 is very negative, 50 neutral, 100 very positive).
    - Summarize your reasoning in markdown, highlighting key positive/negative factors.
    
    Output Format (JSON strictly):
    {
      "recommendation": "BUY" | "SELL" | "HOLD",
      "confidence": number,
      "sentimentScore": number,
      "summary": "markdown string",
      "keyFactors": ["factor 1", "factor 2"],
      "riskFactors": ["risk 1", "risk 2"]
    }
  `;

    try {
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        // Clean up potential markdown code blocks if Gemini wraps the JSON
        const jsonStr = text.replace(/```json/g, '').replace(/```/g, '').trim();
        const analysis = JSON.parse(jsonStr);

        return {
            symbol: data.symbol,
            ...analysis,
            analyzedAt: new Date().toISOString()
        };
    } catch (error) {
        console.error("Gemini analysis failed:", error);
        return {
            symbol: data.symbol,
            recommendation: 'HOLD',
            confidence: 0,
            sentimentScore: 50,
            summary: "Analysis failed due to an error.",
            keyFactors: [],
            riskFactors: [],
            analyzedAt: new Date().toISOString()
        };
    }
}
