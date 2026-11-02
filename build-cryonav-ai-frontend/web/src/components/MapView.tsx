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
    return () => {
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
        <div className="row"><span className="dot" style={{ background: '#8fd3ff' }} /> Iceberg (click for drift path)</div>
        <div className="row"><span className="dot" style={{ background: 'rgba(76,201,240,0.3)', border: '1.5px solid #4cc9f0' }} /> Uncertainty circle at +24 / 48 / 72 h</div>
        <div className="row"><span className="line-sw" style={{ borderColor: '#fff' }} /> Selected route (thick); others dashed</div>
        <div className="row"><span className="dot" style={{ background: '#fff', border: '3px solid #4cc9f0' }} /> Ship (approximate position)</div>
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
