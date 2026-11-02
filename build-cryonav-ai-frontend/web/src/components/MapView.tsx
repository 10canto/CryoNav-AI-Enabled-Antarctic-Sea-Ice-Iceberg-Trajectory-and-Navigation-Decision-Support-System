import { useEffect, useRef, useState } from 'react';
import { MapController } from '../map/MapController';
import { useStore } from '../store/useStore';

/**
 * The map container div is rendered once and never re-keyed.
 * MapController is created exactly once (empty dependency array).
 */
export function MapView() {
  const el = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const c = new MapController(el.current!, useStore);
    MapController.current = c;
    
    // Ensure map renders at correct size
    requestAnimationFrame(() => {
      c.map.invalidateSize();
      
      // Dev check: log map container height
      if (import.meta.env.DEV) {
        const height = el.current?.clientHeight || 0;
        if (height < 300) {
          console.warn(`[MapView] Map container height is ${height}px (< 300px). Layout may be broken.`);
        } else {
          console.log(`[MapView] Map container height: ${height}px`);
        }
      }
    });
    
    // Re-invalidate on window resize
    const handleResize = () => {
      c.map.invalidateSize();
    };
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      c.destroy();
      if (MapController.current === c) MapController.current = null;
    };
  }, []);

  return (
    <div className="map-wrap">
      <div ref={el} className="map" />
      <MapOverlays />
    </div>
  );
}

function MapOverlays() {
  const follow = useStore((s) => s.followShip);
  const setFollow = useStore((s) => s.setFollowShip);
  const loading = useStore((s) => s.loading);
  const error = useStore((s) => s.error);
  const mode = useStore((s) => s.mode);
  const init = useStore((s) => s.setMode);
  const [legendOpen, setLegendOpen] = useState(true);

  return (
    <>
      <div className="map-ctl">
        <label>
          <input type="checkbox" checked={follow} onChange={(e) => setFollow(e.target.checked)} />
          Follow ship
        </label>
      </div>
      <div className={`legend ${legendOpen ? 'open' : 'closed'}`} aria-label="Map legend">
        <div className="legend-header" onClick={() => setLegendOpen(!legendOpen)}>
          <span className="legend-title">Map Legend</span>
          <span className="legend-toggle">{legendOpen ? '▼' : '▶'}</span>
        </div>
        {legendOpen && (
          <div className="legend-content">
            <div className="row">
              <span className="line-sample safest" /> Safest route (green)
            </div>
            <div className="row">
              <span className="line-sample fastest" /> Fastest route (yellow)
            </div>
            <div className="row">
              <span className="line-sample fuel" /> Fuel-efficient route (orange)
            </div>
            <div className="row">
              <span className="dot iceberg-marker" /> Iceberg (current position)
            </div>
            <div className="row">
              <span className="dot crossing-marker" /> Predicted crossing point
            </div>
            <div className="row">
              <span className="dot ship-marker" /> Ship (current position)
            </div>
            <div className="row">
              <span className="dot ice-zone" /> Ice zone boundary
            </div>
          </div>
        )}
      </div>
      {loading && (
        <div className="map-msg" role="status">
          <span className="spinner" />
          Loading {mode === 'demo' ? 'scripted scenario' : 'from the backend'}...
        </div>
      )}
      {error && !loading && (
        <div className="map-msg error" role="alert">
          <div>{error}</div>
          <button className="btn primary" onClick={() => void init(mode)}>Try again</button>
        </div>
      )}
    </>
  );
}
