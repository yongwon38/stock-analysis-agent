import YahooFinance from 'yahoo-finance2';

const yahooFinance = new YahooFinance({ suppressNotices: ['yahooSurvey'] });

export interface StockData {
    symbol: string;
    price: number;
    change: number;
    changePercent: number;
    currency: string;
    name: string;
    marketCap: number;
    peRatio?: number;
    eps?: number;
    news: NewsItem[];
    history: HistoryItem[];
    financials?: any; // Simplified for now
}

export interface NewsItem {
    uuid: string;
    title: string;
    publisher: string;
    link: string;
    providerPublishTime: number; // Unix timestamp
    type: string;
}

export interface HistoryItem {
    date: string; // ISO date string
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export async function getStockData(symbol: string): Promise<StockData> {
    // 1. Fetch Quote
    const quote = await yahooFinance.quote(symbol);

    // 2. Fetch News (Search) - yahoo-finance2 search might return news
    const searchResult = await yahooFinance.search(symbol, { newsCount: 5 });
    const news = searchResult.news || [];

    // 3. Fetch Historical Data (Last 1 year for context)
    const today = new Date();
    const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());

    const queryOptions = {
        period1: oneYearAgo.toISOString().split('T')[0],
        period2: today.toISOString().split('T')[0],
        interval: '1d' as const
    };

    const history = await yahooFinance.historical(symbol, queryOptions);

    return {
        symbol: quote.symbol,
        name: quote.longName || quote.shortName || symbol,
        price: quote.regularMarketPrice || 0,
        change: quote.regularMarketChange || 0,
        changePercent: quote.regularMarketChangePercent || 0,
        currency: quote.currency || 'USD',
        marketCap: quote.marketCap || 0,
        peRatio: quote.trailingPE,
        eps: quote.epsTrailingTwelveMonths,
        news: news.map((n: any) => ({
            uuid: n.uuid,
            title: n.title,
            publisher: n.publisher,
            link: n.link,
            providerPublishTime: n.providerPublishTime,
            type: n.type,
        })),
        history: history.map((h: any) => ({
            date: h.date instanceof Date ? h.date.toISOString().split('T')[0] : h.date,
            open: h.open,
            high: h.high,
            low: h.low,
            close: h.close,
            volume: h.volume,
        }))
    };
}
