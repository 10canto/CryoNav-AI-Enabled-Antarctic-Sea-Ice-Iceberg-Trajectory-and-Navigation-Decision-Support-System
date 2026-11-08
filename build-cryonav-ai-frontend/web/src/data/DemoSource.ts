import type { Alert, Risk, Route, Scenario } from '../domain/types';
import type { DataSource, RiskParams, RouteParams, ScenarioResult, WhatIfSupport } from './DataSource';

/**
 * Reads /demo/scenario.json once. Every other method answers from that
 * in-memory scenario, so there are zero network calls after the first load.
 */
export class DemoSource implements DataSource {
  readonly kind = 'demo' as const;
  private loading: Promise<Scenario> | null = null;
  private scenario: Scenario | null = null;

  private load(): Promise<Scenario> {
    if (!this.loading) {
      this.loading = fetch('/demo/scenario.json')
        .then((r) => {
          if (!r.ok) throw new Error(`scenario.json: HTTP ${r.status}`);
          return r.json() as Promise<Scenario>;
        })
        .then((s) => {
          if (!s || !Array.isArray(s.steps) || s.steps.length === 0) throw new Error('scenario.json has no steps');
          
          // Ensure all drift predictions have uncertainty_radius_km (default 6.0 km)
          for (const step of s.steps) {
            for (const iceberg of step.icebergs) {
              for (const driftPoint of iceberg.drift_path) {
                if (driftPoint.uncertainty_radius_km === undefined || driftPoint.uncertainty_radius_km === 0) {
                  driftPoint.uncertainty_radius_km = 6.0;
                }
              }
            }
          }
          
          this.scenario = s;
          return s;
        })
        .catch((e) => {
          this.loading = null; // allow a user-initiated retry
          throw e;
        });
    }
    return this.loading;
  }

  async getScenarioSteps(): Promise<ScenarioResult> {
    return { scenario: await this.load(), offline: false };
  }

  private step(i = 0) {
    const s = this.scenario;
    if (!s) throw new Error('Demo scenario not loaded');
    return s.steps[Math.min(Math.max(i, 0), s.steps.length - 1)];
  }

  async predictDrift(iceberg: { id: string }, stepIndex = 0) {
    const found = this.step(stepIndex).icebergs.find((b) => b.id === iceberg.id);
    return { drift_path: found?.drift_path ?? [], method: found?.method };
  }

  async calculateRoutes(p: RouteParams): Promise<Route[]> {
    return this.step(p.stepIndex).routes;
  }

  async getRisk(p: RiskParams): Promise<Risk> {
    return this.step(p.stepIndex).risk;
  }

  async explain(_route: Route, ctx: { stepIndex?: number }): Promise<string> {
    return this.step(ctx.stepIndex).explanation_text;
  }

  async sendAlert(_risk: Risk, _route: Route, opts: { includeFamily: boolean; stepIndex?: number }): Promise<Alert> {
    const a = this.step(opts.stepIndex).alert;
    return a ?? { recipients: [], simulated: true };
  }

  async getWhatIfSupport(): Promise<WhatIfSupport> {
    return { delay: false, wind: false, moveIceberg: false };
  }
}
