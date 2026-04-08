import { state } from '../state.js';
import { shortTickerFromTv } from '../config.js';
import { formatCrosshairEt } from '../timeEst.js';
import { calcLevels, quarters, pinnedSwingsThroughTime } from '../pivot/math.js';
import { getPivotKey } from '../pivot/periods.js';

export function hideFibDots() {
  const hi = document.getElementById('fib-dot-hi');
  const lo = document.getElementById('fib-dot-lo');
  if (hi) hi.style.display = 'none';
  if (lo) lo.style.display = 'none';
}

export function onCrosshair(param) {
  const sym = (document.getElementById('symbol')?.value || 'AMEX:SPY').trim();
  const shortSym = shortTickerFromTv(sym);

  const pl = document.getElementById('price-label');
  const bar = param && param.seriesData && param.seriesData.get(state.candleSeries);
  const tsEt =
    param && param.time != null ? formatCrosshairEt(param.time) : '';
  if (bar && bar.close != null && pl) {
    pl.textContent = tsEt
      ? `${shortSym} ${bar.close.toFixed(2)} · ${tsEt}`
      : `${shortSym} ${bar.close.toFixed(2)}`;
  } else if (pl && tsEt) {
    pl.textContent = `${shortSym} — · ${tsEt}`;
  }

  if (!param || !param.time || !state.periods.length) {
    hideFibDots();
    return;
  }

  const mode = document.getElementById('pivTf').value;
  const key = getPivotKey(param.time, mode);
  let idx = -1;
  for (let i = 0; i < state.periods.length; i++) {
    if (state.periods[i].key === key) {
      idx = i;
      break;
    }
  }
  if (idx < 1) {
    hideFibDots();
    return;
  }

  const prev = state.periods[idx - 1];
  const curr = state.periods[idx];
  const lv = calcLevels(prev.high, prev.low, prev.close);

  const ps = pinnedSwingsThroughTime(prev, curr.bars, param.time);
  const { swH, swL } = ps;

  const q = quarters(lv.P, swH, swL);
  const f = (v) => v.toFixed(2);

  document.getElementById('iP').textContent = f(lv.P);
  document.getElementById('iR1').textContent = f(lv.R1);
  document.getElementById('iS1').textContent = f(lv.S1);
  document.getElementById('iSH').textContent = f(swH);
  document.getElementById('iSL').textContent = f(swL);
  document.getElementById('iQ75u').textContent = f(q.u75);
  document.getElementById('iQ50u').textContent = f(q.u50);
  document.getElementById('iQ25u').textContent = f(q.u25);
  document.getElementById('iQ25d').textContent = f(q.d25);
  document.getElementById('iQ50d').textContent = f(q.d50);
  document.getElementById('iQ75d').textContent = f(q.d75);

  const x = state.chart.timeScale().timeToCoordinate(param.time);
  const yHi = state.candleSeries.priceToCoordinate(swH);
  const yLo = state.candleSeries.priceToCoordinate(swL);
  const dotHi = document.getElementById('fib-dot-hi');
  const dotLo = document.getElementById('fib-dot-lo');
  if (x == null || yHi == null || yLo == null || !dotHi || !dotLo) {
    hideFibDots();
    return;
  }
  dotHi.style.display = 'block';
  dotLo.style.display = 'block';
  dotHi.style.left = `${x}px`;
  dotHi.style.top = `${yHi}px`;
  dotLo.style.left = `${x}px`;
  dotLo.style.top = `${yLo}px`;
}
