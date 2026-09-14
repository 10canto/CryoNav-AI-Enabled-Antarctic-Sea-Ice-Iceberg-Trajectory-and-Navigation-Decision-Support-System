const ExplanationPanel = ({ explanation, onAcceptRoute, onKeepCurrent }) => {
  const text = explanation?.text || explanation || 'No explanation available';
  const headline = explanation?.headline;
  const confidence = explanation?.confidence;

  return (
    <div className="explanation-panel">
      <div className="ai-reasoning-title">AI reasoning</div>
      {headline && (
        <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#0f172a' }}>{headline}</div>
      )}
      <div className="explanation-body">
        <p>{text}</p>
        {confidence != null && (
          <p style={{ marginTop: '8px', color: '#0284c7', fontWeight: 700 }}>Confidence {confidence}%</p>
        )}
      </div>
      {explanation?.actions && (
        <div className="explanation-actions">
          <button className="btn-action btn-accept" onClick={onAcceptRoute}>✓ Accept Route A (Recommended)</button>
          <button className="btn-action btn-reject" onClick={onKeepCurrent}>✗ Keep Current Route</button>
        </div>
      )}
    </div>
  );
};

export default ExplanationPanel;
