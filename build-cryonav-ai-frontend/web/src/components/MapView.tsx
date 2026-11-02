import { useEffect, useRef } from 'react';
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

  return (
    <>
      <div className="map-ctl">
        <label>
          <input type="checkbox" checked={follow} onChange={(e) => setFollow(e.target.checked)} />
          Follow ship
        </label>
      </div>
      <div className="legend" aria-label="Map legend">
        <div className="row"><span className="dot" style={{ background: 'white', border: '2px solid var(--line-mid)' }} /> Iceberg (white with dark outline)</div>
        <div className="row"><span className="dot" style={{ background: 'rgba(255,255,255,0.1)', border: '1.5px solid var(--line-mid)' }} /> Uncertainty circle (+24/48/72h)</div>
        <div className="row"><span className="line-sw" style={{ borderColor: 'var(--line-strong)', background: 'white' }} /> Route: white casing + color line (4px solid selected, 2px dashed/dotted others)</div>
        <div className="row"><span className="dot" style={{ background: 'var(--line-strong)', border: '2px solid white' }} /> Ship (black triangle, white outline)</div>
        <div className="row"><span className="dot" style={{ background: 'var(--line-strong)', border: '2px solid white', borderRadius: 0 }} /> Port (black square, white outline)</div>
        <div className="row"><span style={{ fontSize: '10px', fontWeight: 600 }}>🟩🟨🟧🟥</span> Risk meter: GREEN outline, YELLOW light, ORANGE grey, RED critical with pulse</div>
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
