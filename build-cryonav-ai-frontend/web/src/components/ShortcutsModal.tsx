import { useEffect } from 'react';

export function ShortcutsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
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
      <div className="modal shortcuts-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Keyboard Shortcuts</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="modal-body">
          <table className="shortcuts-table">
            <tbody>
              <tr>
                <td><kbd>→</kbd> Right Arrow</td>
                <td>Next step</td>
              </tr>
              <tr>
                <td><kbd>←</kbd> Left Arrow</td>
                <td>Previous step</td>
              </tr>
              <tr>
                <td><kbd>R</kbd></td>
                <td>Restart demo</td>
              </tr>
              <tr>
                <td><kbd>D</kbd></td>
                <td>Toggle dev overlay</td>
              </tr>
              <tr>
                <td><kbd>?</kbd></td>
                <td>Show shortcuts (this dialog)</td>
              </tr>
              <tr>
                <td><kbd>Esc</kbd></td>
                <td>Close dialogs</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
