import { useEffect, useRef, useState } from 'react';
import { MapController } from '../map/MapController';
import { useStore } from '../store/useStore';

/**
 * DEV-ONLY checks (rendered only when import.meta.env.DEV):
 *  - network requests since baseline (PerformanceObserver on resource entries)
 *  - Leaflet map instances created / alive
 *  - FPS (requestAnimationFrame counter)
 *  - "Run 4-step demo check": reset, step through all steps, report.
 * No setInterval / polling: everything is event driven.
 */
interface Result {
  requests: number;
  maps: number;
  fpsMin: number;
  fpsAvg: number;
  steps: number;
}

export default function DevOverlay() {
  const fpsEl = useRef<HTMLSpanElement>(null);
  const samples = useRef<number[] | null>(null);
  const baseline = useRef(performance.getEntriesByType('resource').length);
  const [net, setNet] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const [running, setRunning] = useState(false);
  const mode = useStore((s) => s.mode);

  // network counter, event driven
  useEffect(() => {
    const obs = new PerformanceObserver(() => setNet(performance.getEntriesByType('resource').length - baseline.current));
    obs.observe({ type: 'resource', buffered: false });
    return () => obs.disconnect();
  }, []);

  // FPS counter, rAF based, DOM text updated twice per second
  useEffect(() => {
    let raf = 0;
    let frames = 0;
    let t0 = performance.now();
    const loop = (now: number) => {
      frames++;
      if (now - t0 >= 500) {
        const fps = (frames * 1000) / (now - t0);
        if (fpsEl.current) fpsEl.current.textContent = fps.toFixed(0);
        samples.current?.push(fps);
        frames = 0;
        t0 = now;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  const resetCounter = () => {
    baseline.current = performance.getEntriesByType('resource').length;
    setNet(0);
  };

  const run = async () => {
    const st = useStore.getState();
    if (st.mode !== 'demo' || !st.scenario) return;
    setRunning(true);
    setResult(null);
    st.reset();
    await MapController.current?.whenIdle();
    resetCounter();
    samples.current = [];
    const n = st.scenario.steps.length;
    for (let i = 1; i < n; i++) {
      useStore.getState().next();
      await MapController.current?.whenIdle();
      await new Promise((r) => setTimeout(r, 650)); // let the camera move finish and be sampled
    }
    const s = samples.current ?? [];
    samples.current = null;
    const requests = performance.getEntriesByType('resource').length - baseline.current;
    setResult({
      requests,
      maps: MapController.created,
      fpsMin: s.length ? Math.min(...s) : 0,
      fpsAvg: s.length ? s.reduce((a, b) => a + b, 0) / s.length : 0,
      steps: n,
    });
    setRunning(false);
  };

  const mapsOk = MapController.created === 1;
  return (
    <div className="dev" aria-label="Dev checks">
      <div><b>DEV CHECKS</b> (not in production build)</div>
      <div>FPS: <span ref={fpsEl}>-</span></div>
      <div>
        Network requests since baseline:{' '}
        <span className={net === 0 ? 'ok' : 'bad'}>{net}</span>
      </div>
      <div>
        Map instances created: <span className={mapsOk ? 'ok' : 'bad'}>{MapController.created}</span> (alive {MapController.alive})
      </div>
      <button onClick={resetCounter}>Reset counter</button>
      <button onClick={() => void run()} disabled={running || mode !== 'demo'}>
        {running ? 'Running...' : 'Run 4-step demo check'}
      </button>
      {result && (
        <div style={{ marginTop: 4 }}>
          <div className={result.requests === 0 ? 'ok' : 'bad'}>
            {result.requests === 0 ? 'PASS' : 'FAIL'} requests during {result.steps - 1} step moves: {result.requests}
          </div>
          <div className={result.maps === 1 ? 'ok' : 'bad'}>{result.maps === 1 ? 'PASS' : 'FAIL'} map instances: {result.maps}</div>
          <div>FPS during run: min {result.fpsMin.toFixed(0)}, avg {result.fpsAvg.toFixed(0)}</div>
        </div>
      )}
    </div>
  );
}
