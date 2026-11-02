import { currentStep, useStore } from '../store/useStore';
import { fmtNum } from '../utils/risk';

const LineGlyph = ({ style }: { style: 'solid' | 'dashed' | 'dotted' }) => {
  const patterns = {
    solid: 'M2,6 L18,6',
    dashed: 'M2,6 L6,6 M8,6 L12,6 M14,6 L18,6',
    dotted: 'M2,6 L3,6 M5,6 L6,6 M8,6 L9,6 M11,6 L12,6 M14,6 L15,6 M17,6 L18,6'
  };
  return (
    <svg width="20" height="12" viewBox="0 0 20 12" className="route-line-glyph">
      <path d={patterns[style]} stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  );
};

export function RouteTable() {
  const step = useStore((s) => currentStep(s));
  const selected = useStore((s) => s.selectedRouteId);
  const select = useStore((s) => s.selectRoute);
  const loading = useStore((s) => s.loading);
  const routes = step?.routes ?? [];
  const lineStyles: Array<'solid' | 'dashed' | 'dotted'> = ['solid', 'dashed', 'dotted'];

  if (loading) {
    return (
      <section className="card">
        <h2>Routes</h2>
        <div className="state-msg loading">
          <span className="spinner" />
          Loading routes...
        </div>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>Routes</h2>
      {routes.length === 0 ? (
        <div className="state-msg empty">
          No routes available. Check data source.
        </div>
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
            {routes.map((r, idx) => {
              const isSelected = r.id === selected;
              const lineStyle = isSelected ? 'solid' : lineStyles[(idx % 2) + 1];
              return (
                <tr
                  key={r.id}
                  className={`route-row${isSelected ? ' sel' : ''}`}
                  onClick={() => select(r.id)}
                  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), select(r.id))}
                  tabIndex={0}
                  aria-selected={isSelected}
                >
                  <td>
                    <LineGlyph style={lineStyle} />
                    <span className="rname">{r.name}</span>
                  </td>
                  <td>{fmtNum(r.distance_km)}</td>
                  <td>{fmtNum(r.duration_days, 1)}</td>
                  <td>{fmtNum(r.fuel_index)}</td>
                  <td>{fmtNum(r.risk_score)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      <div className="muted small" style={{ marginTop: 6 }}>
        Fuel index: relative, 100 = lowest in this set. Risk score 0-100, model-defined. Click a row to select.
      </div>
    </section>
  );
}
