import { StockData } from '../finance';
import { getAnalysisResults, saveAnalysisResults } from '../storage';
import { MultiAgentAnalysis, PriceAnalysis, NewsAnalysis, IndustryAnalysis, MarketAnalysis } from './types';
import { generateWithFallback } from './providers';
import { PRICE_AGENT_SYSTEM, NEWS_AGENT_SYSTEM, INDUSTRY_AGENT_SYSTEM, MARKET_AGENT_SYSTEM, AGGREGATOR_AGENT_SYSTEM, generateUserContext } from './prompts';

// Re-export specific legacy keys if needed by debug page (though we moved them to providers)
export { getEffectiveGeminiKey, getEffectiveGroqKey } from './providers';
export type { MultiAgentAnalysis } from './types';

const globalCache = new Map<string, MultiAgentAnalysis>();
const CACHE_DURATION_MS = 24 * 60 * 60 * 1000;

export async function getStockAnalysis(stock: StockData): Promise<MultiAgentAnalysis> {
    // 1. Check Cache
    if (globalCache.has(stock.symbol)) {
        const cached = globalCache.get(stock.symbol);
        if (cached && (Date.now() - new Date(cached.timestamp).getTime() < CACHE_DURATION_MS)) {
            console.log(`[Cache Hit] ${stock.symbol}`);
            return cached;
        }
    }

    // Check File Cache
    const fileCache = await getAnalysisResults();
    if (fileCache) {
        const item = fileCache.results.find((r: any) => r.stock.symbol === stock.symbol);
        if (item && item.analysis && (Date.now() - new Date(item.analysis.timestamp).getTime() < CACHE_DURATION_MS)) {
            // Cast legacy analysis or new analysis?
            // Since we changed the structure efficiently, old cache might be incompatible.
            // Ideally we should version it, but for now we might regenerate if structure lacks 'score_breakdown'.
            if (item.analysis.score_breakdown) {
                return item.analysis as MultiAgentAnalysis;
            }
        }
    }

    console.log(`[Multi-Agent] Starting analysis for ${stock.symbol}...`);
    const userContext = generateUserContext(stock);

    // 2. Parallel Execution of Sub-Agents
    // We add slight delay or standard Promise.all. 
    // Note: Rate Limits on Groq/Gemini might trigger if we do 4 hits instantly.
    // Sequential might be safer for reliability, Parallel for speed.
    // Let's try Parallel first, relying on provider retries (or just standard fetch).

    try {
        const [priceResult, newsResult, industryResult, marketResult] = await Promise.all([
            generateWithFallback(PRICE_AGENT_SYSTEM, userContext),
            generateWithFallback(NEWS_AGENT_SYSTEM, userContext),
            generateWithFallback(INDUSTRY_AGENT_SYSTEM, userContext),
            generateWithFallback(MARKET_AGENT_SYSTEM, userContext)
        ]);

        // 3. Aggregation
        const aggregatorContext = JSON.stringify({
            price_analysis: priceResult,
            news_analysis: newsResult,
            industry_analysis: industryResult,
            market_analysis: marketResult
        });

        const finalDecision = await generateWithFallback(AGGREGATOR_AGENT_SYSTEM, aggregatorContext);

        // 4. Construct Final Object
        const finalAnalysis: MultiAgentAnalysis = {
            ...finalDecision,
            details: {
                price_analysis: priceResult,
                news_analysis: newsResult,
                industry_analysis: industryResult,
                market_analysis: marketResult
            },
            timestamp: new Date().toISOString(),
            provider: 'Groq' // We assume primary succeeded if we are here
        };

        // 5. Update Cache
        globalCache.set(stock.symbol, finalAnalysis);
        // Fire and forget file save
        saveAnalysisResults({
            lastUpdated: new Date().toISOString(),
            results: fileCache ? [...fileCache.results.filter((r: any) => r.stock.symbol !== stock.symbol), { stock, analysis: finalAnalysis }] : [{ stock, analysis: finalAnalysis }]
        }).catch(e => console.warn("File cache save failed", e));

        return finalAnalysis;

    } catch (e: any) {
        console.error(`[Multi-Agent Failed] ${e.message}`);
        // Create a fallback "System" failure analysis
        return {
            investment_opinion: "HOLD",
            confidence_level: "Low",
            total_score: 0,
            score_breakdown: { technical: 0, news: 0, industry: 0, market: 0 },
            key_rationale: ["AI 분석 시스템 오류 발생", "잠시 후 다시 시도해주세요."],
            risk_factors: ["데이터 처리 실패"],
            summary: "시스템 오류로 인해 분석을 완료할 수 없습니다.",
            timestamp: new Date().toISOString(),
            details: {} as any, // Empty details
            provider: 'System'
        };
    }
}

export async function getCachedAnalysis(symbol: string): Promise<MultiAgentAnalysis | null> {
    if (globalCache.has(symbol)) {
        return globalCache.get(symbol) || null;
    }
    // Check file
    const data = await getAnalysisResults();
    if (data) {
        const item = data.results.find((r: any) => r.stock.symbol === symbol);
        // Simple check if it matches new structure (has investment_opinion)
        if (item && item.analysis && item.analysis.investment_opinion) {
            return item.analysis as MultiAgentAnalysis;
        }
    }
    return null;
}
