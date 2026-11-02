import { useStore } from '../store/useStore';

export function TopBar() {
  const mode = useStore((s) => s.mode);
  const offline = useStore((s) => s.offline);
  const placeholder = useStore((s) => s.scenario?.placeholder);
  const setMode = useStore((s) => s.setMode);
  const loading = useStore((s) => s.loading);

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
      <div className="badges">
        {mode === 'demo' && <span className="badge scripted">SCRIPTED SCENARIO</span>}
        {mode === 'demo' && placeholder && <span className="badge placeholder">PLACEHOLDER DATA</span>}
        {offline && <span className="badge offline">offline snapshot</span>}
        <span className="badge sim">SIMULATED ALERTS</span>
      </div>
    </header>
  );
}
