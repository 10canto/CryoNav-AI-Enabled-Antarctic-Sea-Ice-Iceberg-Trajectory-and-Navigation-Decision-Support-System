import React from 'react';
import { Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import { formatCoordinates } from '../../utils/mapHelpers.js';

/**
 * Creates custom blue boat Leaflet icon with vessel heading orientation
 */
function createShipIcon(heading = 210) {
  const size = 36;
  const svgHtml = `
    <div style="width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center; position: relative;">
      <!-- Pulse radar ring -->
      <div style="position: absolute; width: 100%; height: 100%; border-radius: 50%; background: rgba(0, 212, 255, 0.25); animation: pulseNormal 2s infinite;"></div>
      <!-- Ship Icon SVG rotated to heading -->
      <div style="transform: rotate(${heading}deg); transform-origin: center; display: flex; align-items: center; justify-content: center; filter: drop-shadow(0 2px 5px rgba(0,0,0,0.6));">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="#00d4ff" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="12,2 19,21 12,17 5,21" />
        </svg>
      </div>
    </div>
  `;

  return L.divIcon({
    html: svgHtml,
    className: 'ship-marker-icon',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

/**
 * Ship Marker Component
 * Visualizes vessel position, forward proximity radar zone, and navigational telemetry
 */
export function ShipMarker({
  position = [-65.0, -64.0],
  vesselName = 'R/V Polar Pioneer (IMO 9482103)',
  heading = 210,
  speedKnots = 12.4,
}) {
  if (!position) return null;

  const shipIcon = createShipIcon(heading);

  return (
    <>
      {/* 5 km Forward Proximity Safety Zone */}
      <Circle
        center={position}
        radius={5000}
        pathOptions={{
          color: '#00d4ff',
          fillColor: '#00d4ff',
          fillOpacity: 0.06,
          weight: 1,
          dashArray: '4, 4',
        }}
      />

      {/* Ship Marker */}
      <Marker position={position} icon={shipIcon}>
        <Popup>
          <div style={{ minWidth: '180px', color: '#1e293b', fontSize: '0.8rem', lineHeight: '1.4' }}>
            <div style={{ fontWeight: 800, color: '#0284c7', borderBottom: '1px solid #e2e8f0', paddingBottom: '4px', marginBottom: '6px' }}>
              🚢 {vesselName}
            </div>
            <div>
              <strong>Coordinates:</strong> {formatCoordinates(position)}
            </div>
            <div>
              <strong>Heading:</strong> {heading}° (SSW)
            </div>
            <div>
              <strong>Speed:</strong> {speedKnots} knots
            </div>
            <div>
              <strong>Ice Class:</strong> Polar Class 4 (PC4)
            </div>
            <div style={{ marginTop: '4px', color: '#10b981', fontWeight: 700 }}>
              ● Systems Nominal / AIS Active
            </div>
          </div>
        </Popup>
      </Marker>
    </>
  );
}

export default ShipMarker;
