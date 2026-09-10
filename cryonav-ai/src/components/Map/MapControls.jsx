import React from 'react';
import { useMap } from 'react-leaflet';
import { MAP_CENTER, MAP_ZOOM } from '../../config.js';

export function MapControls({ layerVisibility, onToggleLayer }) {
  const map = useMap();

  return (
    <>
      <div className="map-overlay-top">
        <div className="map-layer-bar">
          {['ice', 'routes', 'wind', 'icebergs'].map((key) => (
            <button
              key={key}
              type="button"
              className={`map-layer-btn ${layerVisibility[key] ? 'active' : ''}`}
              onClick={() => onToggleLayer(key)}
            >
              {key === 'ice' ? 'Ice Chart' : key.charAt(0).toUpperCase() + key.slice(1)}
            </button>
          ))}
        </div>
        <div className="map-layer-bar">
          <span className="map-sector-label">Sector</span>
          <button type="button" className="map-layer-btn" onClick={() => map.setView([-32.0, 48.0], 3, { animate: true })}>
            Full Voyage
          </button>
          <button type="button" className="map-layer-btn" onClick={() => map.setView([-57.5, 42.0], 5, { animate: true })}>
            Iceberg Alley
          </button>
          <button type="button" className="map-layer-btn" onClick={() => map.setView([-68.5, 14.0], 6, { animate: true })}>
            Maitri Base
          </button>
        </div>
      </div>

      <div className="map-controls-panel">
        <button type="button" className="map-control-btn" onClick={() => map.zoomIn()} title="Zoom In" aria-label="Zoom In">
          +
        </button>
        <button type="button" className="map-control-btn" onClick={() => map.zoomOut()} title="Zoom Out" aria-label="Zoom Out">
          −
        </button>
        <button
          type="button"
          className="map-control-btn"
          onClick={() => map.setView(MAP_CENTER, MAP_ZOOM, { animate: true })}
          title="Reset View"
          aria-label="Reset View"
        >
          ⟲
        </button>
      </div>
    </>
  );
}

export default MapControls;
