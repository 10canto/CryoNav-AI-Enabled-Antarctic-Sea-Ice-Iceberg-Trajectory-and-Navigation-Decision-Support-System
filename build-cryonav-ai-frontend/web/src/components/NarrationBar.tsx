import { useStore } from '../store/useStore';
import { currentStep } from '../store/useStore';

const DEFAULT_NARRATIONS = [
  'All route options clear through the corridor. Voyage begins.',
  'Iceberg drift brings uncertainty circles closer. Timing becomes a factor.',
  'New detection: ICE-104 crosses the planned path. Risk increases.',
  'West corridor blocked. Rerouting east. Alert prepared.',
  'Ship on eastern arc. Crisis averted. Extra days added.',
];

export function NarrationBar() {
  const step = useStore(currentStep);
  const idx = useStore((s) => s.stepIndex);
  const mode = useStore((s) => s.mode);

  if (mode === 'live') return null;

  const narration = step?.narration ?? DEFAULT_NARRATIONS[idx];

  if (!narration) return null;

  return (
    <div className="narration-bar" role="status">
      <span className="narration-text">{narration}</span>
      {!step?.narration && <span className="narration-badge">default</span>}
    </div>
  );
}
