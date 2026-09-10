import React, { useEffect } from 'react';

export function Notification({ notifications = [], onDismiss }) {
  useEffect(() => {
    if (!notifications.length) return;
    const timers = notifications.map((notif) =>
      setTimeout(() => {
        if (onDismiss) onDismiss(notif.id);
      }, notif.duration || 5000),
    );
    return () => timers.forEach((t) => clearTimeout(t));
  }, [notifications, onDismiss]);

  if (!notifications.length) return null;

  return (
    <div className="toast-container">
      {notifications.map((n) => (
        <div key={n.id} className={`toast-item ${n.type || 'info'}`}>
          <p>{n.message}</p>
          <button type="button" className="toast-close-btn" onClick={() => onDismiss && onDismiss(n.id)}>
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

export default Notification;
