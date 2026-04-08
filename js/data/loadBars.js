import { TV_BAR_TF_META } from '../config.js';
import { cacheKey, readCache, writeCache } from './cache.js';
import { fetchTvBars, tvProxyHealthy, getTvProxyBaseUrl } from './tvClient.js';

/**
 * @param {{ symbol: string, barTf: string, onStatus: (s: string) => void }} ctx
 */
export async function loadBars(ctx) {
  const { symbol, barTf, onStatus } = ctx;
  const meta = TV_BAR_TF_META[barTf];
  if (!meta) {
    throw new Error(`Unknown bar timeframe: ${barTf}`);
  }

  const key = cacheKey(symbol, barTf);
  const cached = readCache(key);
  const hadCache = !!(cached?.bars?.length);

  if (hadCache) {
    onStatus(`${cached.bars.length} bars (cached) · refreshing…`);
  } else {
    onStatus('Loading…');
  }

  const healthy = await tvProxyHealthy();
  if (!healthy) {
    if (hadCache) {
      onStatus(`${cached.bars.length} bars (cached · TV server unreachable)`);
      return { bars: cached.bars };
    }
    throw new Error(
      `TV server not reachable at ${getTvProxyBaseUrl()}. Run: python3 server/pivot_tv_proxy.py — then open this app from the same URL (e.g. http://127.0.0.1:8787/).`
    );
  }

  try {
    onStatus(`TV ${barTf}…`);
    const bars = await fetchTvBars({
      ticker: symbol,
      tf: barTf,
      from: new Date(Date.now() - meta.rangeDays * 86400000),
      to: new Date(),
    });
    if (!bars.length) throw new Error('No bars returned from TradingView');
    writeCache(key, bars);
    return { bars };
  } catch (e) {
    if (hadCache) {
      onStatus(`${cached.bars.length} bars (cached · ${e.message})`);
      return { bars: cached.bars };
    }
    throw e;
  }
}
