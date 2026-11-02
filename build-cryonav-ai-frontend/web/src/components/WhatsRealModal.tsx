import { useEffect } from 'react';

export function WhatsRealModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  useEffect(() => {
    if (!open) return;
    const handle = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handle);
    return () => window.removeEventListener('keydown', handle);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal whatsreal-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>What's Real?</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="modal-body">
          <div className="whatsreal-columns">
            <div className="whatsreal-col">
              <h3>Real data</h3>
              <ul>
                <li>Iceberg tracking data (647 icebergs)</li>
                <li>Copernicus ocean currents</li>
              </ul>
            </div>
            <div className="whatsreal-col">
              <h3>Simulated or scripted</h3>
              <ul>
                <li>Alert sending</li>
                <li>Scenario timing</li>
                <li>All PLACEHOLDER DATA values</li>
                <li>Seasonal ice model</li>
              </ul>
            </div>
          </div>
          <p className="whatsreal-note">
            Replaced by real exports as they are verified.
          </p>
        </div>
      </div>
    </div>
  );
}
