import { currentStep, useStore } from '../store/useStore';
import { fmtNum } from '../utils/risk';

export function RouteTable() {
  const step = useStore((s) => currentStep(s));
  const selected = useStore((s) => s.selectedRouteId);
  const select = useStore((s) => s.selectRoute);
  const routes = step?.routes ?? [];

  return (
    <section className="card">
      <h2>Routes</h2>
      {routes.length === 0 ? (
        <div className="muted">No routes available.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Route</th>
              <th>km</th>
              <th>Days</th>
              <th title="Relative index: 100 = lowest fuel use among these routes">Fuel index (relative)</th>
              <th>Risk score</th>
            </tr>
          </thead>
          <tbody>
            {routes.map((r) => (
              <tr
                key={r.id}
                className={`route-row${r.id === selected ? ' sel' : ''}`}
                onClick={() => select(r.id)}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), select(r.id))}
                tabIndex={0}
                aria-selected={r.id === selected}
              >
                <td>
                  <span className="sw" style={{ background: r.color }} />
                  <span className="rname">{r.name}</span>
                </td>
                <td>{fmtNum(r.distance_km)}</td>
                <td>{fmtNum(r.duration_days, 1)}</td>
                <td>{fmtNum(r.fuel_index)}</td>
                <td>{fmtNum(r.risk_score)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="muted small" style={{ marginTop: 6 }}>
        Fuel index: relative, 100 = lowest in this set. Risk score 0-100, model-defined. Click a row to select.
      </div>
    </section>
  );
}
