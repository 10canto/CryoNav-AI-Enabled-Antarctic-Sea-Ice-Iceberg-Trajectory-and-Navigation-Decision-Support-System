import type { RiskLevel } from '../domain/types';

export const RISK_COLOR: Record<RiskLevel, string> = {
  GREEN: '#2ea043',
  YELLOW: '#d4a72c',
  ORANGE: '#e8772e',
  RED: '#e5484d',
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
