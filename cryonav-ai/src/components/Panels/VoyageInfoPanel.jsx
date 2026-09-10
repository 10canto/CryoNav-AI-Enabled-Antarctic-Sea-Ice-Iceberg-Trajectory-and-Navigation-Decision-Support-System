import React from 'react';
import { scenarioMetadata } from '../../services/scenarioData';

const VoyageInfoPanel = ({ scenarioId }) => {
  const data = scenarioMetadata[scenarioId] || scenarioMetadata[0];

  return (
    <div className="voyage-info-panel">
      <div className="panel-header">
        <h4>Voyage Info</h4>
        <span className={`hazard-badge hazard-${data.hazardLevel}`}>
          <span className="hazard-dot"></span>
          {data.hazardLevel} Risk
        </span>
      </div>
      <div className="panel-grid">
        <div className="grid-item">
          <span className="icon">🌤️</span>
          <div className="item-text">
            <span className="label">Weather</span>
            <span className="value">{data.weather}</span>
          </div>
        </div>
        <div className="grid-item">
          <span className="icon">📍</span>
          <div className="item-text">
            <span className="label">Location</span>
            <span className="value">{data.location}</span>
          </div>
        </div>
        <div className="grid-item">
          <span className="icon">🌊</span>
          <div className="item-text">
            <span className="label">Ocean</span>
            <span className="value">{data.ocean}</span>
          </div>
        </div>
        <div className="grid-item">
          <span className="icon">⏱️</span>
          <div className="item-text">
            <span className="label">Departure</span>
            <span className="value">{new Date(data.departureTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoyageInfoPanel;
