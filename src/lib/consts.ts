export const TARGET_STOCKS = [
    // Section 1: Market Indices
    { symbol: '^VIX', name: 'Volatility Index', type: 'INDEX' },
    { symbol: 'VUG', name: 'Vanguard Growth ETF', type: 'ETF' },
    { symbol: 'VTV', name: 'Vanguard Value ETF', type: 'ETF' },
    { symbol: 'HYG', name: 'High Yield Corp Bond', type: 'ETF' },

    // Section 2: US Market
    { symbol: 'SPY', name: 'S&P 500', type: 'US' },
    { symbol: 'QQQ', name: 'Nasdaq 100', type: 'US' },
    { symbol: 'MAGA', name: 'MAGA ETF', type: 'US' },
    { symbol: 'NVDA', name: 'Nvidia', type: 'US' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', type: 'US' },

    // Section 3: KR Market
    { symbol: '^KS11', name: 'KOSPI', type: 'KR' },
    { symbol: '^KQ11', name: 'KOSDAQ', type: 'KR' },
    { symbol: '005930.KS', name: '삼성전자', type: 'KR' },
    { symbol: '000660.KS', name: 'SK하이닉스', type: 'KR' },
    { symbol: '035420.KS', name: '네이버', type: 'KR' }
];

export const GROUPS = {
    INDICES: ['^VIX', 'VUG', 'VTV', 'HYG'],
    US: ['SPY', 'QQQ', 'MAGA', 'NVDA', 'GOOGL'],
    KR: ['^KS11', '^KQ11', '005930.KS', '000660.KS', '035420.KS']
};
