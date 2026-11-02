/**
 * MapView Component
 * Integrated map with icebergs, predictions, routes, and controls
 */
import React, { useCallback, useMemo, useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { Iceberg, DriftPrediction, Route } from '../../api/client';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

// Fix for default marker icons in leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons
const icebergIcon = L.divIcon({
  className: 'iceberg-marker',
  html: '<div class="iceberg-icon">⛰️</div>',
  iconSize: [30, 30],
  iconAnchor: [15, 15],
});

const shipIcon = L.divIcon({
  className: 'ship-marker',
  html: '<div class="ship-icon">🚢</div>',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const startIcon = L.divIcon({
  className: 'start-marker',
  html: '<div class="start-icon">🏁</div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const endIcon = L.divIcon({
  className: 'end-marker',
  html: '<div class="end-icon">🎯</div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

// Cape Town, Maitri, ice edge markers
const CAPE_TOWN = { lat: -33.9249, lon: 18.4241 };
const MAITRI = { lat: -70.7667, lon: 11.7333 };
const ICE_EDGE = { lat: -60, lon: 20 };

interface MapViewProps {
  icebergs: Iceberg[];
  selectedIceberg: string | null;
  icebergPrediction: DriftPrediction | null;
  routes: Route[];
  selectedRoute: string | null;
  shipPosition: { lat: number; lon: number };
  shipTrail?: Array<{ lat: number; lon: number }>;
  demoStep?: number;
  routePulse?: boolean;
  onIcebergClick: (id: string) => void;
  onRouteSelect: (id: string) => void;
}

// Auto-center map on ship position
function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
}

export const MapView: React.FC<MapViewProps> = ({
  icebergs,
  selectedIceberg,
  icebergPrediction,
  routes,
  selectedRoute,
  shipPosition,
  shipTrail = [],
  demoStep = 0,
  routePulse = false,
  onIcebergClick,
  onRouteSelect,
}) => {

  // Filter icebergs to route bounding box + margin
  const displayedIcebergs = useMemo(() => {
    if (!routes || routes.length === 0) {
      // Show all southern ocean icebergs if no route selected
      return icebergs.filter(ib => {
        const lat = ib.Lat || (ib as any).lat;
        const lon = ib.Lon || (ib as any).lon;
        return lat < -50 && lat > -75 && lon > -20 && lon < 60;
      }).slice(0, 40);
    }

    // Get active route bounds
    const activeRouteObj = routes.find(r => r.id === selectedRoute);
    if (!activeRouteObj) return [];

    const coords = activeRouteObj.coordinates || activeRouteObj.waypoints?.map(w => [w.lat, w.lon]) || [];
    if (coords.length === 0) return [];

    // Calculate bounding box with margin
    const lats = coords.map((c: any) => Array.isArray(c) ? c[0] : c.lat);
    const lons = coords.map((c: any) => Array.isArray(c) ? c[1] : c.lon);
    const minLat = Math.min(...lats) - 5;  // 5 degree margin
    const maxLat = Math.max(...lats) + 5;
    const minLon = Math.min(...lons) - 5;
    const maxLon = Math.max(...lons) + 5;

    // Filter icebergs in bounding box
    const filtered = icebergs.filter(ib => {
      const lat = ib.Lat || (ib as any).lat;
      const lon = ib.Lon || (ib as any).lon;
      return lat >= minLat && lat <= maxLat && lon >= minLon && lon <= maxLon;
    });

    // Sort by distance to route (simplified: distance to route midpoint)
    const midIdx = Math.floor(coords.length / 2);
    const midPoint = coords[midIdx];
    const midLat = Array.isArray(midPoint) ? midPoint[0] : midPoint.lat;
    const midLon = Array.isArray(midPoint) ? midPoint[1] : midPoint.lon;

    const sorted = filtered.sort((a, b) => {
      const aLat = a.Lat || (a as any).lat;
      const aLon = a.Lon || (a as any).lon;
      const bLat = b.Lat || (b as any).lat;
      const bLon = b.Lon || (b as any).lon;
      
      const aDist = Math.sqrt((aLat - midLat) ** 2 + (aLon - midLon) ** 2);
      const bDist = Math.sqrt((bLat - midLat) ** 2 + (bLon - midLon) ** 2);
      return aDist - bDist;
    });

    // Limit to 40 closest icebergs
    return sorted.slice(0, 40);
  }, [icebergs, routes, selectedRoute]);

  // Get selected route object
  const activeRoute = useMemo(() => {
    return routes.find(r => r.id === selectedRoute);
  }, [routes, selectedRoute]);

  // Map center based on ship position
  const mapCenter: [number, number] = [shipPosition.lat, shipPosition.lon];

  return (
    <div className="map-view">
      <MapContainer
        center={mapCenter}
        zoom={4}
        style={{ width: '100%', height: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        
        <MapUpdater center={mapCenter} routes={routes} selectedRoute={selectedRoute} />

        {/* Start marker - Cape Town */}
        <Marker position={[CAPE_TOWN.lat, CAPE_TOWN.lon]} icon={startIcon}>
          <Popup>Cape Town (Start)</Popup>
        </Marker>

        {/* End marker - Maitri Station */}
        <Marker position={[MAITRI.lat, MAITRI.lon]} icon={endIcon}>
          <Popup>
            <div style={{ fontSize: '0.875rem' }}>
              <strong>Maitri Station</strong><br/>
              Destination
            </div>
          </Popup>
        </Marker>

        {/* Ice Edge marker with offset label */}
        <Marker position={[ICE_EDGE.lat, ICE_EDGE.lon]} icon={L.divIcon({
          className: 'ice-edge-marker',
          html: '<div class="ice-edge-icon" style="font-size: 12px; color: #38bdf8;">❄️</div>',
          iconSize: [20, 20],
          iconAnchor: [10, 10],
        })}>
          <Popup>
            <div style={{ fontSize: '0.75rem' }}>
              Ice edge (approx.)
            </div>
          </Popup>
        </Marker>

        {/* Ship trail (thin line from past positions) */}
        {shipTrail && shipTrail.length > 1 && (
          <Polyline
            positions={shipTrail.map(p => [p.lat, p.lon])}
            pathOptions={{ color: '#64748b', weight: 2, opacity: 0.7, dashArray: '5, 5' }}
          />
        )}

        {/* Ship position */}
        <Marker position={[shipPosition.lat, shipPosition.lon]} icon={shipIcon}>
          <Popup>
            <div>
              <strong>R/V Bharati Pioneer</strong><br/>
              Position: {shipPosition.lat.toFixed(3)}°, {shipPosition.lon.toFixed(3)}°
            </div>
          </Popup>
        </Marker>

        {/* Icebergs */}
        {displayedIcebergs.map(iceberg => {
          const id = iceberg.id || iceberg.Iceberg || '';
          const lat = iceberg.Lat || (iceberg as any).lat;
          const lon = iceberg.Lon || (iceberg as any).lon;
          const isSelected = id === selectedIceberg;

          return (
            <Marker
              key={id}
              position={[lat, lon]}
              icon={icebergIcon}
              eventHandlers={{
                click: () => onIcebergClick(id)
              }}
            >
              {isSelected && (
                <Circle
                  center={[lat, lon]}
                  radius={5000}
                  pathOptions={{ color: '#ef4444', weight: 2, fillOpacity: 0.1 }}
                />
              )}
              <Popup>
                <div>
                  <strong>Iceberg {id}</strong><br/>
                  Position: {lat.toFixed(3)}°, {lon.toFixed(3)}°<br/>
                  {iceberg.Length_km && `Size: ${iceberg.Length_km.toFixed(1)} × ${iceberg.Width_km?.toFixed(1)} km`}
                  {isSelected && icebergPrediction && icebergPrediction.method && (
                    <>
                      <br/><br/>
                      <strong>Prediction method:</strong><br/>
                      {icebergPrediction.method === 'track_extrapolation' ? 'Track extrapolation' : 'Current-based fallback'}<br/>
                      {icebergPrediction.velocity_km_h && `Velocity: ${icebergPrediction.velocity_km_h.toFixed(2)} km/h`}
                    </>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Iceberg prediction path (dashed line with uncertainty circles) */}
        {icebergPrediction && icebergPrediction.mean_path && (
          <>
            <Polyline
              positions={icebergPrediction.mean_path.map(p => [p.lat, p.lon])}
              pathOptions={{ color: '#ef4444', dashArray: '5, 10', weight: 2 }}
            />
            {/* Show 24h, 48h, 72h uncertainty circles */}
            {[24, 48, 72].map(hours => {
              const point = icebergPrediction.mean_path.find(p => p.hours === hours);
              const uncertainty = icebergPrediction.uncertainty[`${hours}h`];
              if (!point || !uncertainty) return null;
              
              return (
                <Circle
                  key={hours}
                  center={[point.lat, point.lon]}
                  radius={uncertainty.radius_km * 1000}
                  pathOptions={{ color: '#f97316', weight: 1, fillOpacity: 0.05 }}
                >
                  <Popup>
                    {hours}h prediction<br/>
                    Uncertainty: ±{uncertainty.radius_km.toFixed(1)} km<br/>
                    {icebergPrediction.method && `Method: ${icebergPrediction.method.replace('_', ' ')}`}
                  </Popup>
                </Circle>
              );
            })}
          </>
        )}

        {/* Routes - Step 1: from Cape Town; Later steps: from ship position */}
        {routes.map(route => {
          const isActive = route.id === selectedRoute;
          let coordinates = route.coordinates || route.waypoints?.map(w => [w.lat, w.lon]);
          if (!coordinates || coordinates.length === 0) return null;

          // In step 1 (demoStep === 0), routes start at Cape Town
          // In later steps, routes start at current ship position
          if (demoStep > 0) {
            // Prepend ship position if not already at start
            const firstPoint = coordinates[0];
            const firstLat = Array.isArray(firstPoint) ? firstPoint[0] : firstPoint.lat;
            const firstLon = Array.isArray(firstPoint) ? firstPoint[1] : firstPoint.lon;
            if (Math.abs(firstLat - shipPosition.lat) > 0.1 || Math.abs(firstLon - shipPosition.lon) > 0.1) {
              coordinates = [[shipPosition.lat, shipPosition.lon] as [number, number], ...coordinates as [number, number][]];
            }
          } else {
            // Step 1: Ensure route starts at Cape Town
            const firstPoint = coordinates[0];
            const firstLat = Array.isArray(firstPoint) ? firstPoint[0] : firstPoint.lat;
            const firstLon = Array.isArray(firstPoint) ? firstPoint[1] : firstPoint.lon;
            if (Math.abs(firstLat - CAPE_TOWN.lat) > 0.1 || Math.abs(firstLon - CAPE_TOWN.lon) > 0.1) {
              coordinates = [[CAPE_TOWN.lat, CAPE_TOWN.lon] as [number, number], ...coordinates as [number, number][]];
            }
          }

          // Ensure consistent route colors
          let routeColor = route.color;
          if (route.type === 'safest') routeColor = '#22c55e';  // green
          if (route.type === 'fastest') routeColor = '#eab308';  // yellow
          if (route.type === 'fuel_efficient') routeColor = '#f97316';  // orange

          return (
            <Polyline
              key={route.id}
              positions={coordinates as [number, number][]}
              pathOptions={{
                color: routeColor,
                weight: isActive ? 5 : 3,
                opacity: isActive ? 1 : 0.6,
              }}
              className={routePulse && isActive ? 'route-pulse' : ''}
              eventHandlers={{
                click: () => onRouteSelect(route.id)
              }}
            >
              <Popup>
                <div>
                  <strong>{route.type.replace('_', ' ').toUpperCase()}</strong><br/>
                  Distance: {route.distanceKm.toFixed(0)} km (remaining)<br/>
                  Time: {route.timeDays.toFixed(1)} days (remaining)<br/>
                  Fuel Index: {route.fuelIndex}<br/>
                  Risk: {route.riskPercent}%
                </div>
              </Popup>
            </Polyline>
          );
        })}

        {/* Month slider removed - ocean current arrows not yet implemented */}
      </MapContainer>
    </div>
  );
};
