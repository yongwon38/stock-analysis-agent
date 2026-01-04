import YahooFinance from 'yahoo-finance2';
import Parser from 'rss-parser';

const yahooFinance = new YahooFinance({ suppressNotices: ['yahooSurvey'] });
const parser = new Parser();

export interface NewsItem {
    title: string;
    link: string;
    publisher: string;
    providerPublishTime: number; // Unix timestamp
    uuid: string;
}

export async function getStockNews(symbol: string, region: 'US' | 'KR' = 'US'): Promise<NewsItem[]> {
    // 1. Korean Stocks: Use Google News RSS (Korean)
    if (region === 'KR' || symbol.endsWith('.KS') || symbol.endsWith('.KQ')) {
        try {
            return await fetchGoogleNewsKR(symbol);
        } catch (e) {
            console.warn(`[News] Google RSS failed for ${symbol}, falling back to Yahoo.`);
        }
    }

    // 2. US Stocks / Fallback: Use Yahoo Finance
    try {
        const result = await yahooFinance.search(symbol, { newsCount: 5 });
        return result.news.map((n: any) => ({
            title: n.title,
            link: n.link,
            publisher: n.publisher,
            providerPublishTime: n.providerPublishTime,
            uuid: n.uuid
        }));
    } catch (e) {
        console.error(`[News] Yahoo Finance failed for ${symbol}:`, e);
        return [];
    }
}

async function fetchGoogleNewsKR(symbol: string): Promise<NewsItem[]> {
    // Clean symbol for search (e.g., "005930.KS" -> "005930" or Name if possible)
    // Actually search by Symbol is often okay, but Name is better. 
    // For now, let's use the symbol, or if we had the name passed in, that would be ideal.
    // Lacking name here, we'll try Symbol.

    // Better strategy: Just query the symbol directly.
    const query = encodeURIComponent(symbol);
    const rssUrl = `https://news.google.com/rss/search?q=${query}&hl=ko&gl=KR&ceid=KR:ko`;

    const feed = await parser.parseURL(rssUrl);

    return feed.items.slice(0, 5).map(item => ({
        title: item.title || 'No Title',
        link: item.link || '#',
        publisher: item.creator || item.source || 'Google News',
        providerPublishTime: item.pubDate ? new Date(item.pubDate).getTime() / 1000 : Date.now() / 1000,
        uuid: item.guid || item.link || String(Math.random())
    }));
}
