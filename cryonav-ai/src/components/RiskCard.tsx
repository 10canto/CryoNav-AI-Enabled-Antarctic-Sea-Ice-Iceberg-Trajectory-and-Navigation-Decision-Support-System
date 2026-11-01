/**
 * Risk Level Card Component
 * Color-coded risk indicator with pulsing animation for RED level
 */
import React from 'react';
import type { RiskAssessment } from '../types/api';
import './RiskCard.css';

interface RiskCardProps {
  risk: RiskAssessment | null;
  loading?: boolean;
}

export const RiskCard: React.FC<RiskCardProps> = ({ risk, loading }) => {
  if (loading) {
    return (
      <div className="risk-card">
        <div className="risk-loading">Assessing risk...</div>
      </div>
    );
  }

  if (!risk) {
    return (
      <div className="risk-card">
        <div className="risk-level risk-unknown">
          <div className="risk-indicator">?</div>
          <div className="risk-text">
            <div className="risk-title">Risk Assessment Unavailable</div>
          </div>
        </div>
      </div>
    );
  }

  const levelClass = `risk-${risk.level.toLowerCase()}`;
  const isPulsing = risk.level === 'RED';  // Only pulse for RED

  return (
    <div className={`risk-card ${levelClass}`}>
      <div className={`risk-level ${isPulsing ? 'pulsing' : ''}`}>
        <div className="risk-indicator">{risk.level}</div>
        <div className="risk-text">
          <div className="risk-title">Navigation Risk</div>
          <div className="risk-distance">{risk.distance_km.toFixed(1)} km to nearest iceberg</div>
        </div>
      </div>
      
      <div className="risk-reasons">
        {risk.reasons.map((reason, idx) => (
          <div key={idx} className="risk-reason">{reason}</div>
        ))}
      </div>
      
      <div className="risk-timestamp">
        Updated: {new Date(risk.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
};
