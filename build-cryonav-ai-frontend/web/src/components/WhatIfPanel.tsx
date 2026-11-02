import type { WhatIfOption, WhatIfOutcome } from '../domain/types';
import { currentStep, useStore, type WhatIfRequest } from '../store/useStore';
import { fmtNum } from '../utils/risk';

const NO_OPTIONS: WhatIfOption[] = []; // stable reference for the selector

function Side({ o }: { o: WhatIfOutcome }) {
  return (
    <div className="col">
      <span className={`mini lv-${o.risk_level}`}>
        {o.risk_level} · {fmtNum(o.risk_score)}
      </span>
      {o.distance_km !== undefined && <span>{fmtNum(o.distance_km)} km</span>}
      {o.duration_days !== undefined && <span>{fmtNum(o.duration_days, 1)} days</span>}
      {o.fuel_index !== undefined && <span>Fuel index (relative) {fmtNum(o.fuel_index)}</span>}
    </div>
  );
}

function Cmp({ label, before, after }: { label: string; before: WhatIfOutcome; after: WhatIfOutcome }) {
  return (
    <div className="wi">
      <div className="t">{label}</div>
      <div className="cmp">
        <Side o={before} />
        <span className="arrow" aria-label="becomes">→</span>
        <Side o={after} />
      </div>
    </div>
  );
}

export function WhatIfPanel() {
  const mode = useStore((s) => s.mode);
  const offline = useStore((s) => s.offline);

  if (mode === 'live') return offline ? <OfflineWhatIf /> : <LiveWhatIf />;

  return <DemoWhatIf />;
}

function DemoWhatIf() {
  const options = useStore((s) => currentStep(s)?.whatif ?? NO_OPTIONS);
  return (
    <section className="card">
      <h2>
        What-If <span className="pill pre">precomputed</span>
      </h2>
      {options.length === 0 ? (
        <div className="muted">No What-If options for this step.</div>
      ) : (
        <div className="whatif">
          {options.map((o, i) => (
            <Cmp key={i} label={o.label} before={o.before} after={o.after} />
          ))}
        </div>
      )}
      <div className="muted small" style={{ marginTop: 6 }}>
        Scripted values for the selected route; not recalculated.
      </div>
    </section>
  );
}

function OfflineWhatIf() {
  return (
    <section className="card">
      <h2>What-If</h2>
      <div className="muted">What-If needs the backend. It is unavailable while showing the offline snapshot.</div>
    </section>
  );
}

function LiveWhatIf() {
  const support = useStore((s) => s.whatIfSupport);
  const results = useStore((s) => s.whatIfResults);
  const busy = useStore((s) => s.busy);
  const selectedBerg = useStore((s) => s.selectedIcebergId);
  const run = useStore((s) => s.runWhatIf);

  const opts: Array<{ label: string; req: WhatIfRequest; disabled?: boolean; title?: string }> = [];
  if (support.delay) for (const h of [6, 12, 24]) opts.push({ label: `Delay ${h} h`, req: { kind: 'delay', hours: h } });
  if (support.wind) opts.push({ label: 'Wind +20 km/h', req: { kind: 'wind', deltaKmh: 20 } });
  if (support.moveIceberg)
    opts.push({
      label: 'Move iceberg 15 km north',
      req: { kind: 'moveIceberg', km: 15 },
      disabled: !selectedBerg,
      title: selectedBerg ? `Applies to ${selectedBerg}` : 'Select an iceberg on the map first',
    });

  return (
    <section className="card">
      <h2>
        What-If <span className="pill live">computed by backend</span>
      </h2>
      {opts.length === 0 ? (
        <div className="muted">
          No What-If options are shown: the backend does not declare the inputs needed (delay, wind change, iceberg
          positions), so nothing is invented here.
        </div>
      ) : (
        <>
          <div className="opts">
            {opts.map((o) => (
              <button key={o.label} className="btn" disabled={!!busy || o.disabled} title={o.title} onClick={() => void run(o.req)}>
                {o.label}
              </button>
            ))}
          </div>
          {busy && (
            <div className="muted small" role="status">
              <span className="spinner" />
              {busy}
            </div>
          )}
          {results.length === 0 && !busy && <div className="muted small">Pick an option to re-run the backend with changed inputs.</div>}
          <div className="whatif">
            {results.map((r) => (
              <Cmp key={r.key} label={r.label} before={r.before} after={r.after} />
            ))}
          </div>
        </>
      )}
    </section>
  );
}
