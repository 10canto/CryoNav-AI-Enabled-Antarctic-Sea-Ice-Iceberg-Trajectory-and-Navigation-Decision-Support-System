import type { Alert, DriftPoint, Iceberg, LatLon, Risk, Route, Scenario } from '../domain/types';

export type SourceKind = 'demo' | 'live';

export interface ScenarioResult {
  scenario: Scenario;
  /** Live only: every iceberg the backend knows; the step holds the filtered subset. */
  allIcebergs?: Iceberg[];
  /** true when the data came from the bundled offline snapshot instead of the backend. */
  offline: boolean;
  /** Friendly message when something degraded. */
  warning?: string;
}

export interface RouteParams {
  start: LatLon;
  end: LatLon;
  icebergs: Iceberg[];
  /** What-If inputs. Only sent when the backend declares support. */
  delayHours?: number;
  windDeltaKmh?: number;
  /** Demo source only: which scripted step to answer for. */
  stepIndex?: number;
}

export interface RiskParams {
  route: Route;
  icebergs: Iceberg[];
  delayHours?: number;
  windDeltaKmh?: number;
  stepIndex?: number;
}

export type WhatIfKind = 'delay' | 'wind' | 'moveIceberg';

/** Which What-If inputs the data source can compute for real. */
export interface WhatIfSupport {
  delay: boolean;
  wind: boolean;
  moveIceberg: boolean;
}

export interface DataSource {
  readonly kind: SourceKind;
  /** Whole scenario (demo: 4 scripted steps; live: one snapshot step). */
  getScenarioSteps(): Promise<ScenarioResult>;
  predictDrift(iceberg: Iceberg, stepIndex?: number): Promise<{ drift_path: DriftPoint[]; method?: string }>;
  calculateRoutes(params: RouteParams): Promise<Route[]>;
  getRisk(params: RiskParams): Promise<Risk>;
  explain(route: Route, ctx: { risk: Risk; stepIndex?: number }): Promise<string>;
  sendAlert(risk: Risk, route: Route, opts: { includeFamily: boolean; stepIndex?: number }): Promise<Alert>;
  /** Demo: nothing (options are precomputed in the scenario). Live: detected from the backend. */
  getWhatIfSupport(): Promise<WhatIfSupport>;
}
