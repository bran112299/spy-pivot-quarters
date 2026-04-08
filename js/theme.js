import { config } from './config.js';

const root = () => document.documentElement;

export function getStoredTheme() {
  try {
    const t = localStorage.getItem(config.themeStorageKey);
    if (t === 'light' || t === 'dark') return t;
  } catch (e) { /* ignore */ }
  if (typeof matchMedia === 'function' && matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light';
  }
  return 'dark';
}

export function setTheme(mode) {
  const m = mode === 'light' ? 'light' : 'dark';
  root().setAttribute('data-theme', m);
  try {
    localStorage.setItem(config.themeStorageKey, m);
  } catch (e) { /* ignore */ }
  const el = document.getElementById('theme-toggle');
  if (el) el.textContent = m === 'light' ? 'Dark' : 'Light';
}

export function initTheme() {
  setTheme(getStoredTheme());
}

export function toggleTheme() {
  const cur = root().getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  setTheme(cur === 'light' ? 'dark' : 'light');
}

export function cssVar(name, fallback = '') {
  const v = getComputedStyle(root()).getPropertyValue(name).trim();
  return v || fallback;
}
