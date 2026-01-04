import YahooFinance from 'yahoo-finance2';
import { getStockNews } from './news';

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

// Keep local interface or import? Let's keep local to avoid breaking other files, 
// but we need to make sure the data matches. 
// Actually, let's just use 'any' mapping or align the interfaces.
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
    const { regularMarketPrice, currency, exchange } = quote;

    // Determine Region for news
    const isKR = symbol.endsWith('.KS') || symbol.endsWith('.KQ') || exchange === 'KSE' || exchange === 'KOE';

    // 2. Fetch News (Localized)
    const news = await getStockNews(symbol, isKR ? 'KR' : 'US');

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
        price: regularMarketPrice || 0,
        change: quote.regularMarketChange || 0,
        changePercent: quote.regularMarketChangePercent || 0,
        currency: currency || 'USD',
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
