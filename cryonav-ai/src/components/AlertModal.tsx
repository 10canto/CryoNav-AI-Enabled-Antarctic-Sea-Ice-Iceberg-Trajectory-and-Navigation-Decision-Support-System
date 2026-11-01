/**
 * Alert Modal Component
 * Shows simulated satellite alert for RED risk situations
 */
import React from 'react';
import './AlertModal.css';

interface AlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  recipients: string[];
  familyAuthorized: boolean;
}

export const AlertModal: React.FC<AlertModalProps> = ({
  isOpen,
  onClose,
  recipients,
  familyAuthorized
}) => {
  if (!isOpen) return null;

  const displayRecipients = familyAuthorized
    ? recipients
    : recipients.filter(r => !r.toLowerCase().includes('family'));

  return (
    <div className="alert-modal-overlay" onClick={onClose}>
      <div className="alert-modal" onClick={(e) => e.stopPropagation()}>
        <div className="alert-header">
          <h2>🚨 CRITICAL ALERT</h2>
          <span className="simulated-badge">SIMULATED</span>
        </div>

        <div className="alert-content">
          <p className="alert-message">
            HIGH RISK navigation situation detected. Satellite alert has been sent to:
          </p>

          <ul className="alert-recipients">
            {displayRecipients.map((recipient, idx) => (
              <li key={idx}>✓ {recipient}</li>
            ))}
          </ul>

          <div className="alert-details">
            <div className="alert-detail">
              <strong>Delivery Method:</strong> Satellite (Iridium)
            </div>
            <div className="alert-detail">
              <strong>Transmission Time:</strong> 2.3 seconds
            </div>
            <div className="alert-detail">
              <strong>Status:</strong> Delivered (Simulated)
            </div>
          </div>

          <div className="alert-note">
            <strong>Note:</strong> This is a demonstration. No actual alerts were sent.
          </div>
        </div>

        <div className="alert-actions">
          <button className="btn-acknowledge" onClick={onClose}>
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
};
