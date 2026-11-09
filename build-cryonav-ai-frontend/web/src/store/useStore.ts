import { create } from 'zustand';
import { getSource } from '../data';
import type { SourceKind, WhatIfSupport } from '../data/DataSource';
import { filterIcebergsForRoute } from '../domain/geo';
import type { Alert, Iceberg, Risk, Route, Scenario, Step, WhatIfOutcome } from '../domain/types';
import { CAPE_TOWN, ICE_EDGE } from '../map/ports';
import { levelFromScore } from '../utils/risk';

export type Decision = { routeId: string; choice: 'accepted' | 'overridden' } | null;

export type WhatIfRequest =
  | { kind: 'delay'; hours: number }
  | { kind: 'wind'; deltaKmh: number }
  | { kind: 'moveIceberg'; km: number };

export interface WhatIfResult {
  key: string;
  label: string;
  before: WhatIfOutcome;
  after: WhatIfOutcome;
}

export interface AlertStatus {
  state: 'idle' | 'sending' | 'sent' | 'error';
  message: string;
}

const NO_SUPPORT: WhatIfSupport = { delay: false, wind: false, moveIceberg: false };

export interface AppState {
  mode: SourceKind;
  stepIndex: number;
  /** increments on every step navigation; the map uses it to animate */
  navSeq: number;
  scenario: Scenario | null;
  selectedRouteId: string | null;
  selectedIcebergId: string | null;
  risk: Risk | null;
  alert: Alert | null;
  /** true when Live mode fell back to the bundled offline snapshot */
  offline: boolean;
  followShip: boolean;

  // UI state
  loading: boolean;
  /** live: a follow-up request (risk / drift / what-if) is running */
  busy: string | null;
  error: string | null;
  warning: string | null;
  explanation: string;
  decision: Decision;
  preAuthorized: boolean;
  alertOpen: boolean;
  alertStatus: AlertStatus;
  showSeaIce: boolean;

  // live only
  allIcebergs: Iceberg[];
  whatIfSupport: WhatIfSupport;
  whatIfResults: WhatIfResult[];

  // actions
  init: () => Promise<void>;
  setMode: (m: SourceKind) => Promise<void>;
  goToStep: (i: number) => void;
  next: () => void;
  prev: () => void;
  reset: () => void;
  selectRoute: (id: string) => void;
  selectIceberg: (id: string | null) => void;
  setFollowShip: (v: boolean) => void;
  setPreAuthorized: (v: boolean) => void;
  decide: (choice: 'accepted' | 'overridden') => void;
  closeAlert: () => void;
  sendAlert: () => Promise<void>;
  runWhatIf: (req: WhatIfRequest) => Promise<void>;
  toggleSeaIce: () => void;
}

export const currentStep = (s: Pick<AppState, 'scenario' | 'stepIndex'>): Step | null =>
  s.scenario?.steps[s.stepIndex] ?? null;

const errMsg = (e: unknown) => (e instanceof Error ? e.message : String(e));

function stepPatch(step: Step, index: number, seq: number): Partial<AppState> {
  return {
    stepIndex: index,
    navSeq: seq,
    selectedRouteId: step.selected_route_id,
    selectedIcebergId: null,
    risk: step.risk,
    alert: step.alert,
    alertOpen: step.risk.level === 'RED' && step.alert !== null,
    alertStatus: { state: 'idle', message: '' },
    decision: null,
    explanation: step.explanation_text,
    whatIfResults: [],
  };
}

const outcome = (r: Route, level: WhatIfOutcome['risk_level']): WhatIfOutcome => ({
  risk_level: level,
  risk_score: r.risk_score,
  distance_km: r.distance_km,
  duration_days: r.duration_days,
  fuel_index: r.fuel_index,
});

export const useStore = create<AppState>((set, get) => {
  const isLive = () => get().mode === 'live' && !get().offline;

  /** Immutable update of the current step (live mode keeps one step). */
  const patchStep = (patch: Partial<Step>) => {
    const sc = get().scenario;
    if (!sc) return;
    const i = get().stepIndex;
    set({ scenario: { ...sc, steps: sc.steps.map((st, j) => (j === i ? { ...st, ...patch } : st)) } });
  };

  const refreshForRoute = async (routeId: string) => {
    const step = currentStep(get());
    const route = step?.routes.find((r) => r.id === routeId);
    if (!step || !route) return;
    const icebergs = filterIcebergsForRoute(get().allIcebergs, route);
    set({ busy: 'Recalculating risk for the selected route...', warning: null, whatIfResults: [] });
    const src = getSource('live');
    try {
      let risk: Risk;
      try {
        risk = await src.getRisk({ route, icebergs });
      } catch (e) {
        risk = { level: levelFromScore(route.risk_score), reasons: route.reasons };
        set({ warning: `${errMsg(e)} The level shown is derived from the route risk score.` });
      }
      let text = get().explanation;
      try {
        text = (await src.explain(route, { risk })) || text;
      } catch {
        /* keep the previous explanation, but say so */
        text = 'No explanation available from the backend for this route.';
      }
      if (get().selectedRouteId !== routeId) return; // user moved on
      patchStep({
        icebergs,
        risk,
        explanation_text: text,
        selected_route_id: routeId,
        alert: risk.level === 'RED' ? { recipients: ['Mission Control', 'Rescue Coordination Centre'], simulated: true } : null,
      });
      set({
        risk,
        explanation: text,
        alert: get().scenario?.steps[get().stepIndex].alert ?? null,
        alertOpen: risk.level === 'RED',
        alertStatus: { state: 'idle', message: '' },
      });
    } finally {
      set({ busy: null });
    }
  };

  const loadDrift = async (id: string) => {
    const step = currentStep(get());
    const berg = step?.icebergs.find((b) => b.id === id);
    if (!berg) return;
    set({ busy: `Loading drift path for ${id}...`, warning: null });
    try {
      const d = await getSource('live').predictDrift(berg);
      const apply = (b: Iceberg): Iceberg => (b.id === id ? { ...b, drift_path: d.drift_path, method: b.method ?? d.method } : b);
      patchStep({ icebergs: (currentStep(get())?.icebergs ?? []).map(apply) });
      set({ allIcebergs: get().allIcebergs.map(apply) });
    } catch (e) {
      set({ warning: `Drift path for ${id} is unavailable. ${errMsg(e)}` });
    } finally {
      set({ busy: null });
    }
  };

  return {
    mode: 'demo',
    stepIndex: 0,
    navSeq: 0,
    scenario: null,
    selectedRouteId: null,
    selectedIcebergId: null,
    risk: null,
    alert: null,
    offline: false,
    followShip: false,

    loading: false,
    busy: null,
    error: null,
    warning: null,
    explanation: '',
    decision: null,
    preAuthorized: false,
    alertOpen: false,
    alertStatus: { state: 'idle', message: '' },
    showSeaIce: true,

    allIcebergs: [],
    whatIfSupport: NO_SUPPORT,
    whatIfResults: [],

    async init() {
      await get().setMode(get().mode);
    },

    async setMode(mode) {
      set({ mode, loading: true, busy: null, error: null, warning: null });
      try {
        const src = getSource(mode);
        const res = await src.getScenarioSteps();
        let support = NO_SUPPORT;
        if (mode === 'live' && !res.offline) support = await src.getWhatIfSupport().catch(() => NO_SUPPORT);
        // ignore stale responses if the user switched again meanwhile
        if (get().mode !== mode) return;
        set({
          scenario: res.scenario,
          offline: res.offline,
          warning: res.warning ?? null,
          allIcebergs: res.allIcebergs ?? [],
          whatIfSupport: support,
          loading: false,
          ...stepPatch(res.scenario.steps[0], 0, get().navSeq + 1),
        });
      } catch (e) {
        if (get().mode !== mode) return;
        set({ loading: false, error: errMsg(e) });
      }
    },

    goToStep(i) {
      const sc = get().scenario;
      if (!sc) return;
      const idx = Math.min(Math.max(i, 0), sc.steps.length - 1);
      if (idx === get().stepIndex) return;
      set(stepPatch(sc.steps[idx], idx, get().navSeq + 1));
    },
    next() {
      get().goToStep(get().stepIndex + 1);
    },
    prev() {
      get().goToStep(get().stepIndex - 1);
    },
    reset() {
      const sc = get().scenario;
      if (!sc) return;
      // always re-apply step 0 (also clears decision / modal)
      if (get().stepIndex === 0) set(stepPatch(sc.steps[0], 0, get().navSeq + 1));
      else get().goToStep(0);
    },

    selectRoute(id) {
      if (get().selectedRouteId === id) return;
      set({ selectedRouteId: id, decision: null });
      if (isLive()) void refreshForRoute(id);
    },
    selectIceberg(id) {
      set({ selectedIcebergId: id });
      if (!id || !isLive()) return;
      const b = currentStep(get())?.icebergs.find((x) => x.id === id);
      if (b && b.drift_path.length === 0) void loadDrift(id);
    },
    setFollowShip(v) {
      set({ followShip: v });
    },
    setPreAuthorized(v) {
      set({ preAuthorized: v });
    },
    decide(choice) {
      const id = get().selectedRouteId;
      if (id) set({ decision: { routeId: id, choice } });
    },
    closeAlert() {
      set({ alertOpen: false });
    },

    async sendAlert() {
      const { risk, selectedRouteId, preAuthorized } = get();
      const route = currentStep(get())?.routes.find((r) => r.id === selectedRouteId);
      if (!isLive() || !risk || !route) return;
      set({ alertStatus: { state: 'sending', message: 'Sending simulated alert...' } });
      try {
        const a = await getSource('live').sendAlert(risk, route, { includeFamily: preAuthorized });
        set({
          alert: a,
          alertStatus: { state: 'sent', message: `Backend accepted the SIMULATED alert for: ${a.recipients.join(', ')}.` },
        });
      } catch (e) {
        set({ alertStatus: { state: 'error', message: `${errMsg(e)} Nothing was sent (simulation only).` } });
      }
    },

    async runWhatIf(req) {
      const s = get();
      const step = currentStep(s);
      const route = step?.routes.find((r) => r.id === s.selectedRouteId);
      if (!step || !route || !isLive()) return;

      let icebergs = s.allIcebergs;
      let label: string;
      let delayHours: number | undefined;
      let windDeltaKmh: number | undefined;
      if (req.kind === 'delay') {
        delayHours = req.hours;
        label = `Delay departure by ${req.hours} h`;
      } else if (req.kind === 'wind') {
        windDeltaKmh = req.deltaKmh;
        label = `Wind +${req.deltaKmh} km/h`;
      } else {
        const id = s.selectedIcebergId;
        if (!id) {
          set({ warning: 'Select an iceberg on the map first, then run this What-If.' });
          return;
        }
        icebergs = s.allIcebergs.map((b) => (b.id === id ? { ...b, lat: b.lat + req.km / 111.2 } : b));
        label = `${id} moves ${req.km} km north`;
      }

      set({ busy: `Asking the backend: ${label}...`, warning: null });
      try {
        const src = getSource('live');
        const routes = await src.calculateRoutes({ start: CAPE_TOWN, end: ICE_EDGE, icebergs, delayHours, windDeltaKmh });
        const after =
          routes.find((r) => r.id === route.id) ??
          routes.find((r) => r.name === route.name) ??
          [...routes].sort((a, b) => a.risk_score - b.risk_score)[0];
        if (!after) throw new Error('The backend returned no routes for this What-If.');
        const subset = filterIcebergsForRoute(icebergs, after);
        let level = levelFromScore(after.risk_score);
        try {
          level = (await src.getRisk({ route: after, icebergs: subset, delayHours, windDeltaKmh })).level;
        } catch {
          /* level derived from the score */
        }
        const result: WhatIfResult = {
          key: req.kind + ('hours' in req ? req.hours : ''),
          label,
          before: outcome(route, s.risk?.level ?? levelFromScore(route.risk_score)),
          after: outcome(after, level),
        };
        set({ whatIfResults: [result, ...get().whatIfResults.filter((r) => r.key !== result.key)] });
      } catch (e) {
        set({ warning: `What-If could not be computed. ${errMsg(e)}` });
      } finally {
        set({ busy: null });
      }
    },

    toggleSeaIce() {
      set({ showSeaIce: !get().showSeaIce });
    },
  };
});
