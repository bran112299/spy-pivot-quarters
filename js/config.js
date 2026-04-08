/** History window per bar TF (TradingView proxy computes bar count from range). */
export const TV_BAR_TF_META = {
  '3m': { rangeDays: 45 },
  '15m': { rangeDays: 60 },
  '1h': { rangeDays: 730 },
  '1d': { rangeDays: 5 * 365 },
};

export const config = {
  symbol: 'AMEX:SPY',
  tvProxyBaseUrl: 'http://127.0.0.1:8787',
  defaultPivotMode: 'eight_hour',
  defaultBarTf: '15m',
  themeStorageKey: 'pq_theme',
  tvProxyUrlStorageKey: 'pq_tv_proxy_url',
  chartLibSources: [
    'lightweight-charts.standalone.production.js',
    'https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js',
    'https://cdnjs.cloudflare.com/ajax/libs/lightweight-charts/4.1.3/lightweight-charts.standalone.production.js',
    'https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js',
  ],
};

/** Strip exchange prefix for compact labels (e.g. AMEX:SPY → SPY). */
export function shortTickerFromTv(tvSymbol) {
  if (!tvSymbol) return 'SPY';
  const i = tvSymbol.indexOf(':');
  return i >= 0 ? tvSymbol.slice(i + 1) : tvSymbol;
}
