import { fmtTick, fmtDateEST } from './utils.js';

export const chartEl = document.getElementById('chart');

export const chart = LightweightCharts.createChart(chartEl, {
  layout: { background: { color: '#0d1117' }, textColor: '#8b949e' },
  grid:   { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
  crosshair: {
    mode: LightweightCharts.CrosshairMode.Normal,
    vertLine: { color: '#444c56', labelBackgroundColor: '#161b22' },
    horzLine: { color: '#444c56', labelBackgroundColor: '#161b22' },
  },
  rightPriceScale: { borderColor: '#30363d' },
  timeScale: {
    borderColor: '#30363d',
    timeVisible: true,
    secondsVisible: false,
    tickMarkFormatter: fmtTick,
  },
  localization: { timeFormatter: fmtDateEST },
  width:  chartEl.parentElement.clientWidth,
  height: chartEl.parentElement.clientHeight,
});

new ResizeObserver(() => chart.applyOptions({
  width:  chartEl.parentElement.clientWidth,
  height: chartEl.parentElement.clientHeight,
})).observe(chartEl.parentElement);

export const candleSeries = chart.addCandlestickSeries({
  upColor: '#3fb950', downColor: '#f85149',
  borderUpColor: '#3fb950', borderDownColor: '#f85149',
  wickUpColor:   '#3fb950', wickDownColor:   '#f85149',
  lastValueVisible: true, priceLineVisible: true,
});

// ── Theme switching ───────────────────────────────────────────────
const CHART_THEMES = {
  dark: {
    layout: { background: { color: '#0d1117' }, textColor: '#8b949e' },
    grid:   { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
    crosshair: {
      vertLine: { color: '#444c56', labelBackgroundColor: '#161b22' },
      horzLine: { color: '#444c56', labelBackgroundColor: '#161b22' },
    },
    rightPriceScale: { borderColor: '#30363d' },
    timeScale: { borderColor: '#30363d' },
  },
  light: {
    layout: { background: { color: '#f2eee8' }, textColor: '#746b61' },
    grid:   { vertLines: { color: '#ded9d2' }, horzLines: { color: '#ded9d2' } },
    crosshair: {
      vertLine: { color: '#bbb3a9', labelBackgroundColor: '#e9e4dd' },
      horzLine: { color: '#bbb3a9', labelBackgroundColor: '#e9e4dd' },
    },
    rightPriceScale: { borderColor: '#cfc9c2' },
    timeScale: { borderColor: '#cfc9c2' },
  },
};

const CANDLE_THEMES = {
  dark:  { upColor: '#3fb950', downColor: '#f85149', borderUpColor: '#3fb950', borderDownColor: '#f85149', wickUpColor: '#3fb950', wickDownColor: '#f85149' },
  light: { upColor: '#c046af', downColor: '#07aeb6', borderUpColor: '#c046af', borderDownColor: '#07aeb6', wickUpColor: '#c046af', wickDownColor: '#07aeb6' },
};

export function applyChartTheme(theme) {
  chart.applyOptions(CHART_THEMES[theme]);
}

/** Solid crosshair lines while measure tool is active. */
export function applyCrosshairForMeasure(active) {
  const theme = document.documentElement.dataset.theme || 'dark';
  const cx = CHART_THEMES[theme]?.crosshair || CHART_THEMES.dark.crosshair;
  const style = active ? LightweightCharts.LineStyle.Solid : LightweightCharts.LineStyle.Dashed;
  chart.applyOptions({
    crosshair: {
      vertLine: { ...cx.vertLine, style, width: 1 },
      horzLine: { ...cx.horzLine, style, width: 1 },
    },
  });
}

export function applyCandleTheme(theme) {
  candleSeries.applyOptions(CANDLE_THEMES[theme]);
}
