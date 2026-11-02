import { currentStep, useStore } from '../store/useStore';

export function ExplainPanel() {
  const text = useStore((s) => s.explanation);
  const decision = useStore((s) => s.decision);
  const decide = useStore((s) => s.decide);
  const selectedId = useStore((s) => s.selectedRouteId);
  const route = useStore((s) => currentStep(s)?.routes.find((r) => r.id === s.selectedRouteId));
  const loading = useStore((s) => s.loading);
  const busy = useStore((s) => s.busy);

  if (loading) {
    return (
      <section className="card">
        <h2>Explain</h2>
        <div className="state-msg loading">
          <span className="spinner" />
          Loading...
        </div>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>Explain</h2>
      {busy ? (
        <div className="state-msg loading">
          <span className="spinner" />
          {busy}
        </div>
      ) : (
        <>
          <p className="explain-text">{text || 'No explanation available. Select a route to see details.'}</p>
          <div className="row-btns">
            <button
              className="btn primary"
              disabled={!selectedId || !!busy}
              aria-pressed={decision?.choice === 'accepted'}
              onClick={() => decide('accepted')}
            >
              Accept Route
            </button>
            <button
              className="btn danger"
              disabled={!selectedId || !!busy}
              aria-pressed={decision?.choice === 'overridden'}
              onClick={() => decide('overridden')}
            >
              Override
            </button>
          </div>
          {decision && (
            <div className="decision" role="status">
              {decision.choice === 'accepted' ? 'Accepted' : 'Overridden'}: {route?.name ?? decision.routeId}. Stored in this
              session only; nothing is sent.
            </div>
          )}
        </>
      )}
    </section>
  );
}
