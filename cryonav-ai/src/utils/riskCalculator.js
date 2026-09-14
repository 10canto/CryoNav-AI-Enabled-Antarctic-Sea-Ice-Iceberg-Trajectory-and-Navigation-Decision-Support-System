/**
 * Risk Assessment and Level Logic for CryoNav AI
 */

export const RISK_LEVELS = {
  SAFE: 'SAFE',
  CAUTION: 'CAUTION',
  WARNING: 'WARNING',
  EMERGENCY: 'EMERGENCY',
  // New status strings used by scenario data
  GREEN:  'GREEN',
  YELLOW: 'YELLOW',
  ORANGE: 'ORANGE',
  RED:    'RED',
};

export const RISK_COLORS = {
  SAFE:      '#10b981',
  CAUTION:   '#f59e0b',
  WARNING:   '#f97316',
  EMERGENCY: '#ef4444',
  // New status strings
  GREEN:  '#10b981',
  YELLOW: '#f59e0b',
  ORANGE: '#f97316',
  RED:    '#ef4444',
};

/**
 * Maps numeric risk percentage (0-100) or collision likelihood to risk tier
 */
export function calculateRiskLevel(collisionRiskPercent) {
  if (collisionRiskPercent >= 75) return RISK_LEVELS.EMERGENCY;
  if (collisionRiskPercent >= 40) return RISK_LEVELS.WARNING;
  if (collisionRiskPercent >= 15) return RISK_LEVELS.CAUTION;
  return RISK_LEVELS.SAFE;
}

/**
 * Returns hexadecimal color matching the risk level
 */
export function getRiskColor(level) {
  return RISK_COLORS[level] || RISK_COLORS.SAFE;
}

/**
 * Returns pulsing CSS class name based on risk level
 */
export function getPulseAnimationClass(level) {
  switch (level) {
    case 'RED':
    case RISK_LEVELS.EMERGENCY:
      return 'pulse-rapid';
    case 'ORANGE':
    case RISK_LEVELS.WARNING:
      return 'pulse-fast';
    case 'YELLOW':
    case RISK_LEVELS.CAUTION:
      return 'pulse-normal';
    default:
      return '';
  }
}

/**
 * Formats risk percentage into star rating (1 to 5 stars)
 */
export function getStarRating(riskPercent) {
  if (riskPercent <= 10) return '⭐⭐⭐⭐⭐';
  if (riskPercent <= 25) return '⭐⭐⭐⭐';
  if (riskPercent <= 50) return '⭐⭐⭐';
  if (riskPercent <= 75) return '⭐⭐';
  return '⭐';
}
