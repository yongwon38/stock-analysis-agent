import { GoogleGenerativeAI } from '@google/generative-ai';
import { StockData } from './finance';
import { getAnalysisResults, saveAnalysisResults } from './storage';

// Configuration
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const GROQ_API_KEY = process.env.GROQ_API_KEY;
const CACHE_DURATION_MS = 60 * 60 * 1000; // 1 Hour

// Initialize Gemini
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY || "");

export interface AnalysisResult {
    symbol: string;
    recommendation: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    sentimentScore: number;
    summary: string;
    keyFactors: string[];
    riskFactors: string[];
    analyzedAt: string;
    provider?: 'Gemini' | 'Groq';
}

/**
 * Main Analysis Function (On-Demand + Caching + Multi-Provider)
 */
export async function getStockAnalysis(stock: StockData): Promise<AnalysisResult> {
    // 1. Check Cache
    const cached = await getCachedAnalysis(stock.symbol);
    if (cached) {
        console.log(`[Cache Hit] Using saved analysis for ${stock.symbol} (${cached.analyzedAt})`);
        return cached;
    }

    console.log(`[Cache Miss] Analyzing ${stock.symbol} via AI...`);
    let result: AnalysisResult;

    // 2. Try Primary Provider (Gemini)
    try {
        result = await analyzeWithGemini(stock);
    } catch (geminiError: any) {
        console.warn(`[Gemini Failed] ${geminiError.message}. Switching to Groq...`);

        // 3. Try Secondary Provider (Groq)
        try {
            result = await analyzeWithGroq(stock);
        } catch (groqError: any) {
            console.error(`[Groq Failed] ${groqError.message}`);
            throw new Error(`AI Analysis Failed: Both Gemini and Groq unavailable. (${geminiError.message} / ${groqError.message})`);
        }
    }

    // 4. Save to Cache (Async update)
    // We need to read the latest full DB, update this one item, and save.
    // Ideally this should be optimized, but for <100 stocks JSON file is fine.
    await updateCache(stock, result);

    return result;
}

async function getCachedAnalysis(symbol: string): Promise<AnalysisResult | null> {
    const data = await getAnalysisResults();
    if (!data) return null;

    const item = data.results.find(r => r.stock.symbol === symbol);
    if (!item || !item.analysis) return null;

    const analyzedAt = new Date(item.analysis.analyzedAt).getTime();
    const now = new Date().getTime();

    if (now - analyzedAt < CACHE_DURATION_MS) {
        return item.analysis;
    }
    return null;
}

async function updateCache(stock: StockData, analysis: AnalysisResult) {
    const data = await getAnalysisResults() || { lastUpdated: new Date().toISOString(), results: [] };

    // Remove existing entry for this stock
    const filtered = data.results.filter(r => r.stock.symbol !== stock.symbol);

    filtered.push({
        stock: stock,
        analysis: analysis
    });

    // Sort by symbol or keep insertion order? Let's just save.
    // Wait, let's keep the user-defined order if possible, or just append. 
    // Appending is safer for now.

    const newData = {
        lastUpdated: new Date().toISOString(),
        results: filtered
    };

    await saveAnalysisResults(newData);
}

// --- Providers ---

async function analyzeWithGemini(data: StockData): Promise<AnalysisResult> {
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-lite" });
    const prompt = generatePrompt(data);

    // Simple verification of quota error handling
    try {
        const result = await model.generateContent(prompt);
        const text = (await result.response).text();
        return parseAIResponse(text, data.symbol, 'Gemini');
    } catch (e: any) {
        // Explicitly throw if it's a known error so we fallback
        throw e;
    }
}

async function analyzeWithGroq(data: StockData): Promise<AnalysisResult> {
    if (!GROQ_API_KEY) throw new Error("GROQ_API_KEY not configured");

    const prompt = generatePrompt(data);

    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${GROQ_API_KEY}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            messages: [{ role: "user", content: prompt }],
            model: "llama-3.3-70b-versatile",
            temperature: 0.1
        })
    });

    if (!response.ok) {
        const err = await response.text();
        throw new Error(`Groq API Error: ${response.status} ${err}`);
    }

    const json = await response.json();
    const text = json.choices[0]?.message?.content || "";
    return parseAIResponse(text, data.symbol, 'Groq');
}

// --- Helpers ---

function generatePrompt(data: StockData): string {
    return `
    You are a financial analyst. Analyze the following stock data for ${data.symbol} (${data.name}).
    
    Context:
    - Current Price: ${data.price} ${data.currency}
    - Daily Change: ${data.changePercent.toFixed(2)}%
    - PE Ratio: ${data.peRatio || 'N/A'}
    
    Headlines:
    ${data.news.slice(0, 3).map(n => `- ${n.title}`).join('\n')}
    
    Task:
    Provide a JSON object with investment analysis.
    
    Output Format (JSON Only):
    {
      "recommendation": "BUY" | "SELL" | "HOLD",
      "confidence": number, // 0-100
      "sentimentScore": number, // 0-100
      "summary": "concise markdown summary (max 3 sentences)",
      "keyFactors": ["factor 1", "factor 2"],
      "riskFactors": ["risk 1", "risk 2"]
    }
    `;
}

function parseAIResponse(text: string, symbol: string, provider: 'Gemini' | 'Groq'): AnalysisResult {
    try {
        // Clean markdown code blocks
        const jsonStr = text.replace(/```json/g, '').replace(/```/g, '').trim();
        const data = JSON.parse(jsonStr);

        return {
            symbol,
            recommendation: data.recommendation || 'HOLD',
            confidence: data.confidence || 0,
            sentimentScore: data.sentimentScore || 50,
            summary: data.summary || "No summary provided.",
            keyFactors: data.keyFactors || [],
            riskFactors: data.riskFactors || [],
            analyzedAt: new Date().toISOString(),
            provider
        };
    } catch (e) {
        throw new Error(`Failed to parse AI response from ${provider}: ${text.substring(0, 50)}...`);
    }
}
