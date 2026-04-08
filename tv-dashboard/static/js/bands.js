import { state, bandColorMap } from './state.js';
import { bandColor, isIntraday, detect24hr } from './utils.js';
import { chart } from './chart.js';

export function clearBands() {
  if (state.bandSeries) {
    try { chart.removeSeries(state.bandSeries); } catch {}
    state.bandSeries = null;
  }
  bandColorMap.clear();
}

export function applyBands(candles) {
  clearBands();
  if (!state.sessionBandsOn || !isIntraday(state.activeTf) || detect24hr(candles)) return;

  state.bandSeries = chart.addHistogramSeries({
    priceScaleId: 'bands',
    priceFormat:  { type: 'price' },
    lastValueVisible: false,
    priceLineVisible: false,
  });
  chart.priceScale('bands').applyOptions({ scaleMargins: { top: 0, bottom: 0 }, visible: false });

  const data = candles.map(c => {
    const color = bandColor(c.time);
    bandColorMap.set(c.time, color);
    return { time: c.time, value: 1, color };
  });
  state.bandSeries.setData(data);
}
