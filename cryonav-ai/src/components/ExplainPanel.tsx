/**
 * Explainable AI Panel Component
 * Shows plain-language route explanation with accept/override controls
 */
import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import type { RouteExplanation } from '../api/client';
import './ExplainPanel.css';

interface ExplainPanelProps {
  routeId: string | null;
}

export const ExplainPanel: React.FC<ExplainPanelProps> = ({ routeId }) => {
  const [explanation, setExplanation] = useState<RouteExplanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [choice, setChoice] = useState<'accepted' | 'overridden' | null>(null);

  useEffect(() => {
    if (routeId) {
      loadExplanation(routeId);
      setChoice(null);
    }
  }, [routeId]);

  const loadExplanation = async (id: string) => {
    setLoading(true);
    try {
      const data = await apiClient.explainRoute(id);
      setExplanation(data);
    } catch (error) {
      console.error('Failed to load explanation:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = () => {
    setChoice('accepted');
    console.log('Route accepted:', routeId);
  };

  const handleOverride = () => {
    setChoice('overridden');
    console.log('Route overridden by user:', routeId);
  };

  if (!routeId) {
    return (
      <div className="explain-panel">
        <div className="explain-placeholder">
          Select a route to see explanation
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="explain-panel">
        <div className="explain-loading">Loading explanation...</div>
      </div>
    );
  }

  if (!explanation) return null;

  return (
    <div className="explain-panel">
      <h3 className="explain-title">Why This Route?</h3>
      
      <div className="explain-summary">{explanation.summary}</div>
      
      <div className="explain-section">
        <h4>Key Factors</h4>
        <ul className="explain-reasons">
          {explanation.reasons.map((reason, idx) => (
            <li key={idx}>{reason}</li>
          ))}
        </ul>
      </div>
      
      <div className="explain-section">
        <h4>Trade-offs</h4>
        <div className="trade-offs-grid">
          <div className="trade-off">
            <span className="trade-off-label">Extra Distance</span>
            <span className="trade-off-value">
              {explanation.trade_offs.extra_distance_km > 0 ? '+' : ''}
              {explanation.trade_offs.extra_distance_km.toFixed(1)} km
            </span>
          </div>
          <div className="trade-off">
            <span className="trade-off-label">Extra Time</span>
            <span className="trade-off-value">
              {explanation.trade_offs.extra_time_hours > 0 ? '+' : ''}
              {explanation.trade_offs.extra_time_hours.toFixed(1)} hrs
            </span>
          </div>
          <div className="trade-off">
            <span className="trade-off-label">Fuel Impact</span>
            <span className="trade-off-value">
              {explanation.trade_offs.extra_fuel_percent > 0 ? '+' : ''}
              {explanation.trade_offs.extra_fuel_percent}%
            </span>
          </div>
          <div className="trade-off">
            <span className="trade-off-label">Risk Reduction</span>
            <span className="trade-off-value highlight">
              {explanation.trade_offs.risk_reduction_percent}%
            </span>
          </div>
        </div>
      </div>
      
      <div className="explain-section">
        <h4>Data Sources</h4>
        <ul className="data-sources">
          {explanation.data_sources.map((source, idx) => (
            <li key={idx}>{source}</li>
          ))}
        </ul>
      </div>
      
      {!choice && (
        <div className="explain-actions">
          <button className="btn-accept" onClick={handleAccept}>
            ✓ Accept Route
          </button>
          <button className="btn-override" onClick={handleOverride}>
            ✕ Override
          </button>
        </div>
      )}
      
      {choice && (
        <div className={`choice-badge ${choice}`}>
          {choice === 'accepted' ? '✓ Route Accepted' : '✕ Route Overridden by User'}
        </div>
      )}
    </div>
  );
};
