/**
 * Design tokens - Read from CSS variables for use in JavaScript/Leaflet
 */

interface Tokens {
  ocean: string;
  antarctica: string;
  land: string;
  landOutline: string;
  oceanLabel: string;
  placeLabel: string;
  antarcticaLabel: string;
  bg: string;
  surface: string;
  surface2: string;
  border: string;
  text: string;
  textMuted: string;
  lineStrong: string;
  lineMid: string;
  lineSoft: string;
  accentCritical: string;
  textOnDark: string;
}

let cachedTokens: Tokens | null = null;

export function readTokens(): Tokens {
  if (cachedTokens) return cachedTokens;
  
  const style = getComputedStyle(document.documentElement);
  const get = (name: string) => style.getPropertyValue(name).trim();
  
  cachedTokens = {
    ocean: get('--ocean'),
    antarctica: get('--antarctica'),
    land: get('--land'),
    landOutline: get('--land-outline'),
    oceanLabel: get('--ocean-label'),
    placeLabel: get('--place-label'),
    antarcticaLabel: get('--antarctica-label'),
    bg: get('--bg'),
    surface: get('--surface'),
    surface2: get('--surface-2'),
    border: get('--border'),
    text: get('--text'),
    textMuted: get('--text-muted'),
    lineStrong: get('--line-strong'),
    lineMid: get('--line-mid'),
    lineSoft: get('--line-soft'),
    accentCritical: get('--accent-critical'),
    textOnDark: get('--text-on-dark'),
  };
  
  return cachedTokens;
}

export function clearTokenCache() {
  cachedTokens = null;
}
