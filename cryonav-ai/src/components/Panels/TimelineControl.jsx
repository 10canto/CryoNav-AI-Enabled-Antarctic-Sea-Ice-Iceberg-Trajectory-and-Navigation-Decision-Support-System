import { useEffect, useState } from 'react';
import { DEMO_CONFIG } from '../../config';

const SCENARIO_LABELS = [
  'Baseline transit',
  'Tabular iceberg',
  'Southern cyclone',
  'Ice-shelf calving',
];

const TimelineControl = ({
  scenario,
  nextScenario,
  prevScenario,
  resetScenario,
  isTransitioning,
  missionTime,
}) => {
  const [autoPlay, setAutoPlay] = useState(false);

  useEffect(() => {
    if (!autoPlay) return;
    const interval = setInterval(() => {
      nextScenario();
    }, DEMO_CONFIG.AUTO_ADVANCE_INTERVAL || 30000);
    return () => clearInterval(interval);
  }, [autoPlay, nextScenario]);

  useEffect(() => {
    if (scenario >= 3) setAutoPlay(false);
  }, [scenario]);

  return (
    <div className="timeline-card">
      <div className="timeline-info">
        <div className="time-row">
          <span>Mission clock</span>
          <span className="clock-val">{missionTime || '—'}</span>
        </div>
        <div className="scenario-badge-row">
          <span>
            Scenario {scenario} of 3 · {SCENARIO_LABELS[scenario]}
          </span>
          <div className="scenario-progress-blocks">
            {[0, 1, 2, 3].map((step) => (
              <div key={step} className={`progress-block ${step <= scenario ? 'filled' : ''}`} />
            ))}
          </div>
        </div>
      </div>

      <div className="timeline-buttons">
        <button className="btn-timeline" onClick={prevScenario} disabled={isTransitioning || scenario === 0}>
          ◀ Prev
        </button>
        <button className="btn-timeline" onClick={nextScenario} disabled={isTransitioning || scenario === 3}>
          {isTransitioning ? 'Loading…' : 'Next ▶'}
        </button>
        <button className="btn-timeline" onClick={resetScenario} disabled={isTransitioning}>
          Reset
        </button>
        <button
          className={`btn-timeline btn-autoplay ${autoPlay ? 'active' : ''}`}
          onClick={() => setAutoPlay((v) => !v)}
          disabled={scenario === 3}
        >
          {autoPlay ? 'Pause' : 'Auto-Play'}
        </button>
      </div>
    </div>
  );
};

export default TimelineControl;
