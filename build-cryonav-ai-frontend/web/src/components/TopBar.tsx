import { useStore } from '../store/useStore';
import { MapController } from '../map/MapController';

export function TopBar({ onOpenShortcuts, onOpenWhatsReal }: { onOpenShortcuts: () => void; onOpenWhatsReal: () => void }) {
  const mode = useStore((s) => s.mode);
  const offline = useStore((s) => s.offline);
  const placeholder = useStore((s) => s.scenario?.placeholder);
  const setMode = useStore((s) => s.setMode);
  const loading = useStore((s) => s.loading);
  const showSeaIce = useStore((s) => s.showSeaIce);
  const toggleSeaIce = useStore((s) => s.toggleSeaIce);

  const handleSeasonChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const date = e.target.value;
    MapController.current?.setSeaIceSeason(date);
  };

  return (
    <header className="topbar">
      <h1>CryoNav AI - Cape Town to Maitri</h1>
      <div className="seg" role="group" aria-label="Data mode">
        <button aria-pressed={mode === 'demo'} disabled={loading} onClick={() => mode !== 'demo' && void setMode('demo')}>
          Demo
        </button>
        <button aria-pressed={mode === 'live'} disabled={loading} onClick={() => mode !== 'live' && void setMode('live')}>
          Live
        </button>
      </div>
      <div className="spacer" />
      <button className="header-btn" onClick={onOpenWhatsReal} title="What's real?">
        What's real?
      </button>
      <button className="shortcut-hint" onClick={onOpenShortcuts} title="Keyboard shortcuts">
        ? shortcuts
      </button>
      <button 
        className={`ice-toggle-btn ${showSeaIce ? 'active' : ''}`}
        onClick={toggleSeaIce}
        title={`Sea-ice overlay: ${showSeaIce ? 'ON' : 'OFF'}`}
      >
        🧊 Ice
      </button>
      {showSeaIce && (
        <div className="ice-season-selector">
          <label className="season-label">Ice Season</label>
          <select className="season-select" onChange={handleSeasonChange} defaultValue="2020-08-15">
            <option value="2020-01-15">Summer (Jan)</option>
            <option value="2020-05-15">Autumn (May)</option>
            <option value="2020-08-15">Winter (Aug)</option>
          </select>
        </div>
      )}
      <div className="badges">
        {mode === 'demo' && <span className="badge scripted">SCRIPTED SCENARIO</span>}
        {mode === 'demo' && placeholder && <span className="badge placeholder">PLACEHOLDER DATA</span>}
        {offline && <span className="badge offline">offline snapshot</span>}
        <span className="badge sim">SIMULATED ALERTS</span>
      </div>
      {showSeaIce && (
        <div className="sea-ice-legend">
          <div className="legend-title">Sea-ice concentration</div>
          <div className="legend-scale">
            <div className="legend-item">
              <div className="legend-color" style={{ background: 'rgb(0, 105, 148)' }}></div>
              <span>0%</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: 'rgb(128, 180, 202)' }}></div>
              <span>50%</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: 'rgb(255, 255, 255)' }}></div>
              <span>100%</span>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
