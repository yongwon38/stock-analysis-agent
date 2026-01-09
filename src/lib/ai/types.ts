export interface MultiAgentAnalysis {
    investment_opinion: "BUY" | "SELL" | "HOLD";
    confidence_level: "High" | "Medium" | "Low";
    target_price?: string;
    expected_return_3m?: string;
    total_score: number;
    score_breakdown: {
        technical: number;
        news: number;
        industry: number;
        market: number;
    };
    key_rationale: string[];
    risk_factors: string[];
    summary: string;
    timestamp: string;
    details: {
        price_analysis: PriceAnalysis;
        news_analysis: NewsAnalysis;
        industry_analysis: IndustryAnalysis;
        market_analysis: MarketAnalysis;
    };
    provider?: 'Groq' | 'Gemini' | 'System';
}

export interface PriceAnalysis {
    current_price: number;
    trend: {
        short_term: string;
        medium_term: string;
        trend_strength: string;
    };
    technical_indicators: {
        rsi: number;
        rsi_signal: string;
        macd_signal: string;
    };
    support_resistance: {
        support_levels: number[];
        resistance_levels: number[];
    };
    volatility: string;
    technical_score: number;
    summary: string;
}

export interface NewsAnalysis {
    news_summary: {
        total_count: number;
        positive_count: number;
        neutral_count: number;
        negative_count: number;
    };
    key_news: Array<{
        title: string;
        date: string;
        sentiment: string;
        importance: string;
        category: string;
        impact: string;
    }>;
    overall_sentiment: string;
    sentiment_score: number;
    key_issues: string[];
    expected_impact: string;
}

export interface IndustryAnalysis {
    industry_info: {
        sector: string;
        industry: string;
        growth_trend: string;
        lifecycle_stage: string;
    };
    competitive_position: {
        market_share_rank?: number | string;
        position: string;
        competitive_advantages: string[];
    };
    industry_outlook: {
        outlook_6m: string;
        key_drivers: string[];
        key_risks: string[];
    };
    industry_score: number;
    summary: string;
}

export interface MarketAnalysis {
    market_indices: {
        kospi_trend: string;
        sector_index_trend: string;
    };
    macro_indicators: {
        interest_rate_trend: string;
        currency_trend: string;
    };
    market_sentiment: {
        sentiment: string;
        foreign_flow?: string;
    };
    investment_environment: string;
    market_score: number;
    market_outlook_3m: string;
    summary: string;
}
