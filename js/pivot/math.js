export function calcLevels(H, L, C) {
  const P = (H + L + C) / 3;
  return {
    P,
    R1: 2 * P - L,
    S1: 2 * P - H,
    R2: P + (H - L),
    S2: P - (H - L),
  };
}

export function quarters(P, swH, swL) {
  const up = swH - P;
  const down = P - swL;
  return {
    u75: P + 0.75 * up,
    u50: P + 0.5 * up,
    u25: P + 0.25 * up,
    d25: P - 0.25 * down,
    d50: P - 0.5 * down,
    d75: P - 0.75 * down,
  };
}

/**
 * Swing reference: anchor on the **most recent** completed pivot (`periods[pi-1]`).
 * Older pivots in the lookback only move the pin if they are **more extreme** —
 * higher high or lower low — never a milder old level pulling the reference inward.
 *
 * `memory` = how many prior buckets may contribute (always includes the latest);
 * memory 1 → latest only.
 *
 * @param {object[]} periods from groupPeriods (chronological)
 * @param {number} pi index of the **current** bucket
 * @param {number} memory count of prior pivots in the window (minimum 1)
 */
export function refHighLowFromPivotMemory(periods, pi, memory) {
  const m = Math.max(1, Math.floor(memory || 1));
  const prev = periods[pi - 1];
  if (!prev) {
    const fb = periods[0] || { high: 0, low: 0 };
    return { refH: fb.high, refL: fb.low };
  }

  let refH = prev.high;
  let refL = prev.low;
  const oldest = Math.max(0, pi - m);

  for (let j = pi - 2; j >= oldest; j--) {
    const p = periods[j];
    if (p.high > refH) refH = p.high;
    if (p.low < refL) refL = p.low;
  }

  return { refH, refL };
}

/**
 * Classic pinned swings: stick to ref H/L until broken, then running period extreme.
 *
 * @param {object} prevPeriod unused except for backward compat callers (pass curr’s prev)
 * @param {object[]} currBars bars in current bucket
 * @param {{ refHigh: number, refLow: number, timeCutoff?: number|null, endIndex?: number|null }} opts
 */
export function pinnedSwingsSimulate(prevPeriod, currBars, opts) {
  const refHigh = opts.refHigh;
  const refLow = opts.refLow;
  const timeCutoff = opts.timeCutoff != null ? opts.timeCutoff : null;
  const endIndex = opts.endIndex != null ? opts.endIndex : null;

  let releasedHigh = false;
  let releasedLow = false;
  let runningHi = -Infinity;
  let runningLo = Infinity;
  const n = currBars.length;
  for (let i = 0; i < n; i++) {
    if (endIndex != null && i > endIndex) break;
    const b = currBars[i];
    if (timeCutoff != null && b.time > timeCutoff) break;
    if (b.high > runningHi) runningHi = b.high;
    if (b.low < runningLo) runningLo = b.low;
    if (!releasedHigh && b.high > refHigh) releasedHigh = true;
    if (!releasedLow && b.low < refLow) releasedLow = true;
  }
  return {
    swH: releasedHigh ? runningHi : refHigh,
    swL: releasedLow ? runningLo : refLow,
  };
}

/** @param {number} refHigh @param {number} refLow */
export function pinnedSwingsThroughTime(prevPeriod, currBars, timeCutoff, refHigh, refLow) {
  return pinnedSwingsSimulate(prevPeriod, currBars, {
    timeCutoff,
    refHigh,
    refLow,
  });
}

/** @param {number} refHigh @param {number} refLow */
export function pinnedSwingsThroughIndex(prevPeriod, currBars, endIndex, refHigh, refLow) {
  return pinnedSwingsSimulate(prevPeriod, currBars, {
    endIndex,
    refHigh,
    refLow,
  });
}

/**
 * Same swing semantics as calling pinnedSwingsThroughIndex for every endIndex, but O(n) per bucket.
 *
 * @returns {{ swH: number[], swL: number[] }} parallel to currBars indices
 */
export function pinnedSwingsSeries(prevPeriod, currBars, refHigh, refLow) {
  const n = currBars.length;
  const swH = new Array(n);
  const swL = new Array(n);
  let releasedHigh = false;
  let releasedLow = false;
  let runningHi = -Infinity;
  let runningLo = Infinity;
  for (let i = 0; i < n; i++) {
    const b = currBars[i];
    if (b.high > runningHi) runningHi = b.high;
    if (b.low < runningLo) runningLo = b.low;
    if (!releasedHigh && b.high > refHigh) releasedHigh = true;
    if (!releasedLow && b.low < refLow) releasedLow = true;
    swH[i] = releasedHigh ? runningHi : refHigh;
    swL[i] = releasedLow ? runningLo : refLow;
  }
  return { swH, swL };
}

/**
 * #pivotBreakMemory — how many **prior pivot buckets** define swing ref (max H, min L).
 * Minimum 1 (= only the immediate prior bucket, same as old default pin).
 */
export function readPivotBreakMemoryFromUi() {
  const el =
    typeof document !== 'undefined' && document.getElementById('pivotBreakMemory');
  if (!el) return 1;
  const fromNum =
    typeof el.valueAsNumber === 'number' && Number.isFinite(el.valueAsNumber)
      ? Math.trunc(el.valueAsNumber)
      : NaN;
  const v = Number.isFinite(fromNum)
    ? fromNum
    : parseInt(String(el.value ?? '1').trim(), 10);
  if (!Number.isFinite(v) || v < 1) return 1;
  return Math.min(20, v);
}
