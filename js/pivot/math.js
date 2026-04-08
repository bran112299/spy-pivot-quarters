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
 * Pin swH/swL to prior period H/L until broken above/below; then running period swing.
 */
export function pinnedSwingsThroughTime(prevPeriod, currBars, timeCutoff) {
  let releasedHigh = false;
  let releasedLow = false;
  let runningHi = -Infinity;
  let runningLo = Infinity;
  for (let i = 0; i < currBars.length; i++) {
    const b = currBars[i];
    if (timeCutoff != null && b.time > timeCutoff) break;
    if (b.high > runningHi) runningHi = b.high;
    if (b.low < runningLo) runningLo = b.low;
    if (!releasedHigh && b.high > prevPeriod.high) releasedHigh = true;
    if (!releasedLow && b.low < prevPeriod.low) releasedLow = true;
  }
  const swH = releasedHigh ? runningHi : prevPeriod.high;
  const swL = releasedLow ? runningLo : prevPeriod.low;
  return { swH, swL };
}
