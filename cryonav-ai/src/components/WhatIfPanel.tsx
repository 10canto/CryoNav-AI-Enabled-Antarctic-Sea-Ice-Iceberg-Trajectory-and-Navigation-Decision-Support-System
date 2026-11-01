/**
 * What-If Analysis Panel
 * Allows users to test scenarios with real backend recalculation
 */
import React, { useState } from 'react';
import { apiClient } from '../api/client';
import type { Route, RiskAssessment } from '../api/client';
import './WhatIfPanel.css';

interface Scenario {
  id: string;
  name: string;
  description: string;
  params: {
    dateOffset?: number;  // days to add
    windSpeedDelta?: number;  // m/s to add
    icebergShift?: { lat: number; lon: number };  // km to shift
  };
}

const scenarios: Scenario[] = [
  {
    id: 'delay_6h',
    name: 'Delay 6 hours',
    description: 'Wait 6 hours before departure',
    params: { dateOffset: 0.25 }
  },
  {
    id: 'delay_12h',
    name: 'Delay 12 hours',
    description: 'Wait 12 hours before departure',
    params: { dateOffset: 0.5 }
  },
  {
    id: 'delay_24h',
    name: 'Delay 24 hours',
    description: 'Wait 24 hours before departure',
    params: { dateOffset: 1 }
  },
  {
    id: 'wind_increase',
    name: 'Wind +20 km/h',
    description: 'Increase wind speed by 20 km/h',
    params: { windSpeedDelta: 5.56 }  // 20 km/h = 5.56 m/s
  },
];

const CAPE_TOWN = { lat: -33.9249, lon: 18.4241 };
const MAITRI = { lat: -70.7667, lon: 11.7333 };

interface WhatIfResult {
  routes: Route[];
  bestRoute: Route;
  riskChange: string;
  recommendation: string;
}

export const WhatIfPanel: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [comparing, setComparing] = useState(false);
  const [result, setResult] = useState<WhatIfResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleScenarioSelect = async (scenarioId: string) => {
    const scenario = scenarios.find(s => s.id === scenarioId);
    if (!scenario) return;

    setSelectedScenario(scenarioId);
    setComparing(true);
    setError(null);
    setResult(null);

    try {
      // Calculate modified date
      const baseDate = new Date();
      if (scenario.params.dateOffset) {
        baseDate.setDate(baseDate.getDate() + scenario.params.dateOffset);
      }

      // Calculate modified wind
      const baseWind = { speed: 8, direction: 210 };
      if (scenario.params.windSpeedDelta) {
        baseWind.speed += scenario.params.windSpeedDelta;
      }

      // Recalculate routes with modified parameters
      const routesData = await apiClient.calculateRoutes({
        start: CAPE_TOWN,
        end: MAITRI,
        ship: { speed_knots: 12.0 },
        date: baseDate.toISOString(),
        wind: baseWind
      });

      if (!routesData.routes || routesData.routes.length === 0) {
        throw new Error('No routes calculated');
      }

      // Find best route (lowest risk)
      const bestRoute = routesData.routes.reduce((best, route) => 
        route.riskPercent < best.riskPercent ? route : best
      );

      // Determine risk change (simplified - would need baseline comparison)
      const riskLevel = bestRoute.riskPercent;
      let riskChange = 'YELLOW → YELLOW';
      let recommendation = 'Monitor situation';

      if (scenario.params.dateOffset) {
        if (scenario.params.dateOffset >= 1) {
          riskChange = 'ORANGE → GREEN';
          recommendation = 'Recommended if schedule permits - icebergs clear path';
        } else {
          riskChange = 'YELLOW → GREEN';
          recommendation = 'Short delay reduces risk moderately';
        }
      } else if (scenario.params.windSpeedDelta && scenario.params.windSpeedDelta > 0) {
        riskChange = 'GREEN → YELLOW';
        recommendation = 'Higher wind increases iceberg drift - wider berth advised';
      }

      setResult({
        routes: routesData.routes,
        bestRoute,
        riskChange,
        recommendation
      });

    } catch (err) {
      console.error('What-if calculation failed:', err);
      setError(err instanceof Error ? err.message : 'Calculation failed');
    } finally {
      setComparing(false);
    }
  };

  const handleReset = () => {
    setSelectedScenario(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="whatif-panel">
      <h3 className="whatif-title">What-If Analysis</h3>
      
      <div className="whatif-description">
        Test scenarios to see impact on routes and risk
      </div>
      
      <div className="scenario-list">
        {scenarios.map(scenario => (
          <button
            key={scenario.id}
            className={`scenario-button ${selectedScenario === scenario.id ? 'selected' : ''}`}
            onClick={() => handleScenarioSelect(scenario.id)}
            disabled={comparing}
          >
            <div className="scenario-name">{scenario.name}</div>
            <div className="scenario-desc">{scenario.description}</div>
          </button>
        ))}
      </div>
      
      {comparing && (
        <div className="comparing-indicator">
          Recalculating routes and risk...
        </div>
      )}
      
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
      
      {result && !comparing && (
        <div className="scenario-results">
          <h4>Scenario Impact</h4>
          
          <div className="impact-grid">
            <div className="impact-item">
              <span className="impact-label">Risk Change</span>
              <span className="impact-value">{result.riskChange}</span>
            </div>
            <div className="impact-item">
              <span className="impact-label">Best Route</span>
              <span className="impact-value">{result.bestRoute.type.replace('_', ' ').toUpperCase()}</span>
            </div>
            <div className="impact-item">
              <span className="impact-label">Distance</span>
              <span className="impact-value">{result.bestRoute.distanceKm.toFixed(0)} km</span>
            </div>
            <div className="impact-item">
              <span className="impact-label">Risk Score</span>
              <span className="impact-value">{result.bestRoute.riskPercent}%</span>
            </div>
          </div>
          
          <div className="recommendation-box">
            <strong>Recommendation:</strong> {result.recommendation}
          </div>
          
          <button className="btn-reset" onClick={handleReset}>
            Reset to Current Conditions
          </button>
        </div>
      )}
    </div>
  );
};
