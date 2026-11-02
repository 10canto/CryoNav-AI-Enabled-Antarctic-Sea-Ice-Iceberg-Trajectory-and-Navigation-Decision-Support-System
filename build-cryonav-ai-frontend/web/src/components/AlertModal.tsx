import { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';

const isFamily = (r: string) => /family/i.test(r);

export function AlertModal() {
  const open = useStore((s) => s.alertOpen);
  const alert = useStore((s) => s.alert);
  const pre = useStore((s) => s.preAuthorized);
  const setPre = useStore((s) => s.setPreAuthorized);
  const close = useStore((s) => s.closeAlert);
  const mode = useStore((s) => s.mode);
  const offline = useStore((s) => s.offline);
  const status = useStore((s) => s.alertStatus);
  const send = useStore((s) => s.sendAlert);
  const btn = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) btn.current?.focus();
  }, [open]);

  if (!open || !alert) return null;

  // Family is listed ONLY when the pre-authorized toggle is on.
  const base = alert.recipients.filter((r) => !isFamily(r));
  const recipients = base.length ? [...base] : ['Mission Control', 'Rescue Coordination Centre'];
  if (pre) recipients.push('Family contacts (pre-authorized)');
  const canSend = mode === 'live' && !offline;

  return (
    <div className="backdrop" role="presentation">
      <div className="modal" role="alertdialog" aria-modal="true" aria-labelledby="alert-title">
        <h2 id="alert-title">
          RED risk alert <span className="sim-badge">SIMULATED</span>
        </h2>
        <p className="muted" style={{ margin: '0 0 8px' }}>
          This is a simulation. No real message is sent. Recipients that would be notified:
        </p>
        <ul>
          {recipients.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
        <label className="toggle">
          <input type="checkbox" checked={pre} onChange={(e) => setPre(e.target.checked)} />
          Pre-authorized: also notify family contacts
        </label>
        {status.state !== 'idle' && (
          <div className={status.state === 'error' ? 'notice' : 'decision'} role="status">
            {status.state === 'sending' && <span className="spinner" />}
            {status.message}
          </div>
        )}
        <div className="actions">
          {canSend && (
            <button className="btn" disabled={status.state === 'sending'} onClick={() => void send()}>
              Send simulated alert
            </button>
          )}
          <button ref={btn} className="btn primary" onClick={close}>
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
}
