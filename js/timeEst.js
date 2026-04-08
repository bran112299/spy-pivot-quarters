/** US Eastern (America/New_York) for chart axis + crosshair — honors DST (ET). */

export const CHART_TIME_ZONE = 'America/New_York';

function chartTimeToDate(time) {
  if (typeof time === 'number' && !Number.isNaN(time)) {
    return new Date(time * 1000);
  }
  if (time && typeof time === 'object' && 'year' in time) {
    return new Date(Date.UTC(time.year, time.month - 1, time.day));
  }
  return null;
}

const fmtEt = (d, opts) =>
  new Intl.DateTimeFormat('en-US', { timeZone: CHART_TIME_ZONE, ...opts }).format(d);

/** @param {unknown} time UTCTimestamp or BusinessDay from lightweight-charts */
export function formatCrosshairEt(time) {
  const d = chartTimeToDate(time);
  if (!d) return '';
  return (
    fmtEt(d, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }) + ' ET'
  );
}

export function estTickMarkFormatter(LC) {
  const TM = LC?.TickMarkType;
  return (time, tickMarkType) => {
    const d = chartTimeToDate(time);
    if (!d) return '';
    const year = TM ? tickMarkType === TM.Year : tickMarkType === 0;
    const month = TM ? tickMarkType === TM.Month : tickMarkType === 1;
    const day = TM ? tickMarkType === TM.DayOfMonth : tickMarkType === 2;
    const withSec = TM ? tickMarkType === TM.TimeWithSeconds : tickMarkType === 4;
    if (year) return fmtEt(d, { year: 'numeric' });
    if (month) return fmtEt(d, { month: 'short', year: '2-digit' });
    if (day) return fmtEt(d, { month: 'short', day: 'numeric' });
    if (withSec) {
      return fmtEt(d, { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    }
    return fmtEt(d, { hour: '2-digit', minute: '2-digit', hour12: false });
  };
}

export function estLocalizationAndTimeScale(LC) {
  return {
    localization: {
      locale: 'en-US',
      timeFormatter: (t) => formatCrosshairEt(t),
    },
    timeScale: {
      tickMarkFormatter: estTickMarkFormatter(LC),
    },
  };
}
