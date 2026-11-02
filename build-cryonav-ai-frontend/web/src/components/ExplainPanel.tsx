import { currentStep, useStore } from '../store/useStore';

export function ExplainPanel() {
  const text = useStore((s) => s.explanation);
  const decision = useStore((s) => s.decision);
  const decide = useStore((s) => s.decide);
  const selectedId = useStore((s) => s.selectedRouteId);
  const route = useStore((s) => currentStep(s)?.routes.find((r) => r.id === s.selectedRouteId));

  return (
    <section className="card">
      <h2>Explain</h2>
      <p className="explain-text">{text || 'No explanation available.'}</p>
      <div className="row-btns">
        <button
          className="btn primary"
          disabled={!selectedId}
          aria-pressed={decision?.choice === 'accepted'}
          onClick={() => decide('accepted')}
        >
          Accept Route
        </button>
        <button
          className="btn danger"
          disabled={!selectedId}
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
    </section>
  );
}
