import { state } from '../state.js';
import { config } from '../config.js';
import {
  calcLevels,
  quarters,
  pinnedSwingsSeries,
  readPivotBreakMemoryFromUi,
  refHighLowFromPivotMemory,
} from '../pivot/math.js';
import { groupPeriods } from '../pivot/periods.js';
import { applySessionBands } from './sessionBands.js';

function clearPool() {
  for (let i = 0; i < state.pool.length; i++) {
    try {
      state.chart.removeSeries(state.pool[i]);
    } catch (e) { /* ignore */ }
  }
  state.pool = [];
}

const W_MAIN = 3;
const W_SEC = 2;
const W_FAINT = 2;

function line(color, width, style, title, excludeFromAutoscale) {
  const LC = state.LightweightCharts;
  const opts = {
    color,
    lineWidth: width,
    lineStyle: style !== undefined ? style : LC.LineStyle.Solid,
    priceLineVisible: false,
    lastValueVisible: !!title,
    title: title || '',
    crosshairMarkerVisible: false,
  };
  if (excludeFromAutoscale) {
    opts.autoscaleInfoProvider = () => null;
  }
  const s = state.chart.addLineSeries(opts);
  state.pool.push(s);
  return s;
}

export function draw() {
  if (!state.chart || !state.LightweightCharts) return;
  clearPool();
  if (!state.allBars.length) return;

  const mode = document.getElementById('pivTf').value;
  const symbol = (document.getElementById('symbol')?.value || config.symbol).trim();
  const showQ = document.getElementById('showQ').checked;
  const showPiv = document.getElementById('showP').checked;
  const showNod = document.getElementById('showNodes').checked;
  const showR2 = document.getElementById('showR2').checked;
  const LC = state.LightweightCharts;
  const LS = LC.LineStyle;

  state.periods = groupPeriods(state.allBars, mode, symbol);

  const sP = showPiv ? line('#58a6ff', W_MAIN, LS.Solid, 'P') : null;
  const sR1 = showPiv ? line('rgba(248,81,73,0.9)', W_SEC, LS.Solid, 'R1') : null;
  const sS1 = showPiv ? line('rgba(63,185,80,0.9)', W_SEC, LS.Solid, 'S1') : null;
  const sR2 = showPiv && showR2 ? line('rgba(248,81,73,0.4)', W_SEC, LS.Solid, 'R2') : null;
  const sS2 = showPiv && showR2 ? line('rgba(63,185,80,0.4)', W_SEC, LS.Solid, 'S2') : null;

  let sQu75;
  let sQu50;
  let sQu25;
  let sQd25;
  let sQd50;
  let sQd75;
  if (showQ) {
    sQu75 = line('rgba(190,150,255,0.9)', W_SEC, LS.Dashed, 'Q75u');
    sQu50 = line('rgba(190,150,255,0.65)', W_SEC, LS.Dashed, 'Q50u');
    sQu25 = line('rgba(190,150,255,0.4)', W_SEC, LS.Dashed, 'Q25u');
    sQd25 = line('rgba(100,200,255,0.4)', W_SEC, LS.Dashed, 'Q25d');
    sQd50 = line('rgba(100,200,255,0.65)', W_SEC, LS.Dashed, 'Q50d');
    sQd75 = line('rgba(100,200,255,0.9)', W_SEC, LS.Dashed, 'Q75d');
  }

  const dP = [];
  const dR1 = [];
  const dS1 = [];
  const dR2 = [];
  const dS2 = [];
  const dQu75 = [];
  const dQu50 = [];
  const dQu25 = [];
  const dQd25 = [];
  const dQd50 = [];
  const dQd75 = [];
  const histP = [];

  const pivotMemory = readPivotBreakMemoryFromUi();

  for (let pi = 1; pi < state.periods.length; pi++) {
    const prev = state.periods[pi - 1];
    const curr = state.periods[pi];
    const lv = calcLevels(prev.high, prev.low, prev.close);
    histP.push(lv.P);
    const { refH, refL } = refHighLowFromPivotMemory(
      state.periods,
      pi,
      pivotMemory
    );

    const { swH, swL } = pinnedSwingsSeries(prev, curr.bars, refH, refL);
    for (let bi = 0; bi < curr.bars.length; bi++) {
      const bar = curr.bars[bi];
      const t = bar.time;

      if (showPiv) {
        dP.push({ time: t, value: lv.P });
        dR1.push({ time: t, value: lv.R1 });
        dS1.push({ time: t, value: lv.S1 });
        if (showR2) {
          dR2.push({ time: t, value: lv.R2 });
          dS2.push({ time: t, value: lv.S2 });
        }
      }
      if (showQ) {
        const q = quarters(lv.P, swH[bi], swL[bi]);
        dQu75.push({ time: t, value: q.u75 });
        dQu50.push({ time: t, value: q.u50 });
        dQu25.push({ time: t, value: q.u25 });
        dQd25.push({ time: t, value: q.d25 });
        dQd50.push({ time: t, value: q.d50 });
        dQd75.push({ time: t, value: q.d75 });
      }
    }
  }

  if (showPiv) {
    sP.setData(dP);
    sR1.setData(dR1);
    sS1.setData(dS1);
    if (showR2) {
      sR2.setData(dR2);
      sS2.setData(dS2);
    }
  }
  if (showQ) {
    sQu75.setData(dQu75);
    sQu50.setData(dQu50);
    sQu25.setData(dQu25);
    sQd25.setData(dQd25);
    sQd50.setData(dQd50);
    sQd75.setData(dQd75);
  }

  if (showNod && histP.length && state.periods.length > 1) {
    const lastBar = state.allBars[state.allBars.length - 1];
    const lastT = lastBar && lastBar.time;
    const firstNodeT = state.periods[1].firstTime;
    /** Cap faint pivot-node series so huge histories do not add thousands of line overlays. */
    const NODE_PIVOT_CAP = 200;
    const nStart = Math.max(0, histP.length - NODE_PIVOT_CAP);
    if (lastT != null) {
      for (let ni = nStart; ni < histP.length; ni++) {
        const pv = histP[ni];
        const startT = state.periods[ni + 1].firstTime;
        if (startT > lastT) continue;
        const seg = [
          { time: startT, value: pv },
          { time: lastT, value: pv },
        ];
        line('rgba(100,80,180,0.3)', W_FAINT, LS.Dotted, '', true).setData(seg);
      }
    }
    const mn = Math.min(...histP);
    const mx = Math.max(...histP);
    if (lastT != null && firstNodeT <= lastT) {
      const envHi = [
        { time: firstNodeT, value: mx },
        { time: lastT, value: mx },
      ];
      const envLo = [
        { time: firstNodeT, value: mn },
        { time: lastT, value: mn },
      ];
      line('rgba(120,100,200,0.12)', W_FAINT, LS.Solid, '', true).setData(envHi);
      line('rgba(120,100,200,0.12)', W_FAINT, LS.Solid, '', true).setData(envLo);
    }
  }

  const barTf = document.getElementById('barTf')?.value || '15m';
  if (state.allBars.length) applySessionBands(state, state.allBars, barTf);
}
