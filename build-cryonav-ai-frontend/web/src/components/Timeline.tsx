import { useStore } from '../store/useStore';
import { fmtDate } from '../utils/risk';

const DEFAULT_LABELS = ['Baseline', 'Timing', 'New iceberg', 'Reroute + alert', 'Crisis averted'];

export function Timeline() {
  const mode = useStore((s) => s.mode);
  const offline = useStore((s) => s.offline);
  const loading = useStore((s) => s.loading);
  const setMode = useStore((s) => s.setMode);
  const scenario = useStore((s) => s.scenario);
  const idx = useStore((s) => s.stepIndex);
  const goTo = useStore((s) => s.goToStep);
  const next = useStore((s) => s.next);
  const prev = useStore((s) => s.prev);
  const reset = useStore((s) => s.reset);
  const steps = scenario?.steps ?? [];
  const last = steps.length - 1;

  if (mode === 'live') {
    return (
      <nav className="timeline" aria-label="Live data">
        <div className="steps" style={{ alignItems: 'center' }}>
          <div>
            <strong>{offline ? 'Offline snapshot (placeholder data)' : 'Live snapshot from the backend'}</strong>
            <div className="muted small">
              {offline
                ? 'The backend could not be reached. Data below is a bundled placeholder snapshot.'
                : 'Data is fetched when you press Refresh or interact; nothing updates in the background.'}
            </div>
          </div>
        </div>
        <div className="btns">
          <button className="btn primary" disabled={loading} onClick={() => void setMode('live')}>
            {loading ? 'Loading...' : offline ? 'Retry backend' : 'Refresh'}
          </button>
        </div>
      </nav>
    );
  }

  return (
    <nav className="timeline" aria-label="Scenario steps">
      <div className="steps">
        {steps.map((st, i) => (
          <button
            key={i}
            className={`step${i === idx ? ' active' : ''}${i < idx ? ' done' : ''}`}
            onClick={() => goTo(i)}
            aria-current={i === idx ? 'step' : undefined}
            title={`${st.title} (${fmtDate(st.date)})`}
          >
            <span className="pip">{i + 1}</span>
            <span className="lbl">
              {st.label ?? DEFAULT_LABELS[i] ?? `Step ${i + 1}`}
              <br />
              <span className="muted small">{fmtDate(st.date)}</span>
            </span>
          </button>
        ))}
      </div>
      <div className="btns">
        <button className="btn" onClick={prev} disabled={idx <= 0}>Previous</button>
        <button className="btn primary" onClick={next} disabled={idx >= last}>Next</button>
        <button className="btn" onClick={reset} disabled={steps.length === 0}>Reset</button>
      </div>
    </nav>
  );
}
