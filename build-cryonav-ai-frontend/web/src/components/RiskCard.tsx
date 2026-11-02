import { useStore, currentStep } from '../store/useStore';

export function RiskCard() {
  const risk = useStore((s) => s.risk);
  const mode = useStore((s) => s.mode);
  const busy = useStore((s) => s.busy);
  const step = useStore(currentStep);
  
  // Check if current step has dual risk comparison data
  const riskOriginal = step && 'risk_original' in step ? (step as any).risk_original : null;
  const riskSelected = step && 'risk_selected' in step ? (step as any).risk_selected : null;
  const hasDualRisk = riskOriginal && riskSelected;
  
  if (!risk) {
    return (
      <section className="card">
        <h2>Risk</h2>
        <div className="muted">No risk rating loaded yet.</div>
      </section>
    );
  }
  return (
    <section className={`card risk-card ${risk.level}`} aria-live="polite">
      <h2>
        Risk{' '}
        <span className="pill">{mode === 'demo' ? 'scripted' : 'backend rating'}</span>
      </h2>
      {busy && (
        <div className="muted small" role="status" style={{ marginBottom: 6 }}>
          <span className="spinner" />
          {busy}
        </div>
      )}
      {hasDualRisk ? (
        <>
          <div className="risk-head" style={{ marginBottom: 8 }}>
            <div style={{ fontSize: '0.9em', fontWeight: 600, marginBottom: 4 }}>Original plan:</div>
            <span className={`risk-level lv-${riskOriginal.level}`}>{riskOriginal.level}</span>
            <span className="muted small" style={{ marginLeft: 8 }}>
              (score {riskOriginal.score})
            </span>
          </div>
          <div className="risk-head">
            <div style={{ fontSize: '0.9em', fontWeight: 600, marginBottom: 4 }}>Selected route:</div>
            <span className={`risk-level lv-${riskSelected.level}`}>{riskSelected.level}</span>
            <span className="muted small" style={{ marginLeft: 8 }}>
              (score {riskSelected.score})
            </span>
          </div>
        </>
      ) : (
        <div className="risk-head">
          <span className={`risk-level lv-${risk.level}`}>{risk.level}</span>
          <span className="muted small">Rating level, not a probability.</span>
        </div>
      )}
      {risk.reasons.length > 0 && (
        <ul className="reasons">
          {risk.reasons.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
