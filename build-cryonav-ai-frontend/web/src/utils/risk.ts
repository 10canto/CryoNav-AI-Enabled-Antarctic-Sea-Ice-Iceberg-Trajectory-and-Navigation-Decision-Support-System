import type { RiskLevel } from '../domain/types';

// Risk colors are now in CSS (tokens.css) and applied via className
// This map is kept for legacy compatibility but styling uses CSS variables
export const RISK_COLOR: Record<RiskLevel, string> = {
  GREEN: 'var(--surface)', // outline only
  YELLOW: 'var(--surface-2)', // light fill
  ORANGE: 'var(--text-muted)', // grey fill
  RED: 'var(--accent-critical)', // critical fill with pulse
};

/** Fallback mapping from a 0-100 score (or 0-1) to a level. */
export function levelFromScore(score: number): RiskLevel {
  const s = score <= 1 ? score * 100 : score;
  if (s < 25) return 'GREEN';
  if (s < 50) return 'YELLOW';
  if (s < 75) return 'ORANGE';
  return 'RED';
}

export function fmtDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
}

/** Formats a number, or "-" when the backend did not provide it (NaN / undefined). */
export function fmtNum(n: number | undefined, digits = 0): string {
  if (n === undefined || !Number.isFinite(n)) return '-';
  return digits === 0 ? Math.round(n).toLocaleString('en-US') : n.toFixed(digits);
}
