import { config } from '../config.js';
import { state } from '../state.js';
import { cssVar } from '../theme.js';
import { estLocalizationAndTimeScale } from '../timeEst.js';

export function applyPriceAxisVisibility(visible) {
  if (!state.chart) return;
  state.chart.priceScale('right').applyOptions({ visible: !!visible });
}

export function applyChartTheme() {
  if (!state.chart || !state.candleSeries) return;
  const LC = state.LightweightCharts;
  const est = estLocalizationAndTimeScale(LC);
  state.chart.applyOptions({
    layout: {
      background: { color: cssVar('--chart-bg', '#0b0e14') },
      textColor: cssVar('--chart-text', '#8b949e'),
    },
    grid: {
      vertLines: { visible: false },
      horzLines: { visible: false },
    },
    crosshair: { mode: LC.CrosshairMode.Normal },
    rightPriceScale: { borderColor: cssVar('--chart-border', '#1c2230') },
    localization: est.localization,
    timeScale: {
      borderColor: cssVar('--chart-border', '#1c2230'),
      timeVisible: true,
      secondsVisible: false,
      ...est.timeScale,
    },
  });
  const up = cssVar('--candle-up', '#3fb950');
  const down = cssVar('--candle-down', '#f85149');
  state.candleSeries.applyOptions({
    upColor: up,
    downColor: down,
    borderUpColor: up,
    borderDownColor: down,
    wickUpColor: up,
    wickDownColor: down,
  });
}

export function initChartAfterLibLoaded(onCrosshair) {
  const LC = state.LightweightCharts;
  const el = document.getElementById('chart');
  if (!el) throw new Error('#chart missing');

  const est = estLocalizationAndTimeScale(LC);
  state.chart = LC.createChart(el, {
    layout: {
      background: { color: cssVar('--chart-bg', '#0b0e14') },
      textColor: cssVar('--chart-text', '#8b949e'),
    },
    grid: {
      vertLines: { visible: false },
      horzLines: { visible: false },
    },
    crosshair: { mode: LC.CrosshairMode.Normal },
    rightPriceScale: { borderColor: cssVar('--chart-border', '#1c2230') },
    localization: est.localization,
    timeScale: {
      borderColor: cssVar('--chart-border', '#1c2230'),
      timeVisible: true,
      secondsVisible: false,
      ...est.timeScale,
    },
    handleScroll: true,
    handleScale: true,
  });

  state.bandSeries = state.chart.addHistogramSeries({
    priceScaleId: 'bands',
    priceFormat: { type: 'price', precision: 1, minMove: 0.1 },
    lastValueVisible: false,
    priceLineVisible: false,
    base: 0,
    autoscaleInfoProvider: () => ({
      priceRange: { minValue: 0, maxValue: 1 },
    }),
  });
  state.chart.priceScale('bands').applyOptions({
    scaleMargins: { top: 0, bottom: 0 },
    visible: false,
  });

  const up = cssVar('--candle-up', '#3fb950');
  const down = cssVar('--candle-down', '#f85149');
  state.candleSeries = state.chart.addCandlestickSeries({
    upColor: up,
    downColor: down,
    borderUpColor: up,
    borderDownColor: down,
    wickUpColor: up,
    wickDownColor: down,
  });

  state.pool = [];
  state.chart.subscribeCrosshairMove(onCrosshair);
}

export function loadChartLibrary(i, onLoaded) {
  if (i >= config.chartLibSources.length) {
    const st = document.getElementById('status');
    if (st) st.textContent = 'Failed to load chart library';
    return;
  }
  const src = config.chartLibSources[i];
  const s = document.createElement('script');
  s.src = src;
  s.onload = () => {
    state.LightweightCharts = window.LightweightCharts;
    onLoaded();
  };
  s.onerror = () => loadChartLibrary(i + 1, onLoaded);
  document.head.appendChild(s);
}
