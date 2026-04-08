export const state = {
  activeTf:       '8h',
  chartData:      [],
  liveES:         null,
  liveTimer:      null,
  settleTimer:    null,
  bandSeries:     null,
  sessionBandsOn: false,
  gridOn:         false,
  planets: {
    enabled: true,
    selected: ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'],
    orbDeg: 1.0,
    /** Longitudes + measure cards: geocentric vs heliocentric (hotkey h). */
    helio: false,
  },
  measure: {
    on: false,
    draftTs0: null,
  },
  /** { id, ts0, ts1, color, data, planets } data = span API JSON or null while loading */
  measurements: [],
};

export const memCache         = {};
export const bandColorMap     = new Map();

export const TF_MINS = {
  '1m': 1, '3m': 3, '15m': 15, '1h': 60, '4h': 240,
  '8h': 480, '1d': 1440, '1w': 10080, '1M': 43200,
};

export function cacheKey(ticker, tf, from, to) {
  return `${ticker.toUpperCase()}|${tf}|${from}|${to}`;
}
