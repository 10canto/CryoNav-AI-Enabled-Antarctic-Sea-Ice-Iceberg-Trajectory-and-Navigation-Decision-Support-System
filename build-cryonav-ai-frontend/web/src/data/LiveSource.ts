import { filterIcebergsForRoute } from '../domain/geo';
import type { Alert, DriftPoint, Iceberg, Risk, Route, Scenario, Step } from '../domain/types';
import { CAPE_TOWN, ICE_EDGE } from '../map/ports';
import { levelFromScore } from '../utils/risk';
import type { DataSource, RiskParams, RouteParams, ScenarioResult, WhatIfSupport } from './DataSource';
import { adaptAlert, adaptDrift, adaptExplain, adaptIcebergs, adaptRisk, adaptRoutes } from './liveAdapter';

export const API_URL: string =
  ((import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000').replace(/\/+$/, '');

const TIMEOUT_MS = 8000;
export const DEFAULT_RECIPIENTS = ['Mission Control', 'Rescue Coordination Centre'];

export class ApiError extends Error {
  constructor(message: string, readonly kind: 'network' | 'http' | 'parse', readonly status?: number) {
    super(message);
  }
}

async function request(path: string, init?: RequestInit): Promise<unknown> {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS); // one-shot request timeout, not polling
  try {
    const res = await fetch(API_URL + path, {
      ...init,
      signal: ctl.signal,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...(init?.headers ?? {}) },
    });
    if (!res.ok) throw new ApiError(`The backend answered ${path} with an error (HTTP ${res.status}).`, 'http', res.status);
    try {
      return await res.json();
    } catch {
      throw new ApiError(`The backend answer for ${path} was not valid JSON.`, 'parse');
    }
  } catch (e) {
    if (e instanceof ApiError) throw e;
    const timedOut = e instanceof DOMException && e.name === 'AbortError';
    throw new ApiError(
      timedOut ? `The backend at ${API_URL} did not answer within ${TIMEOUT_MS / 1000} s.` : `Cannot reach the backend at ${API_URL}.`,
      'network',
    );
  } finally {
    clearTimeout(timer);
  }
}

const post = (path: string, body: unknown) => request(path, { method: 'POST', body: JSON.stringify(body) });

const pt = (p: { lat: number; lon: number }) => ({ lat: p.lat, lon: p.lon });
const bergPayload = (b: Iceberg) => ({ id: b.id, iceberg_id: b.id, lat: b.lat, lon: b.lon, size_m: b.size_m });

interface ApiProps {
  routes: Set<string>;
  risk: Set<string>;
}

export class LiveSource implements DataSource {
  readonly kind = 'live' as const;
  private props: ApiProps | null = null;
  private propsLoad: Promise<void> | null = null;
  private support: WhatIfSupport | null = null;

  // ------------------------------------------------------------------ scenario

  async getScenarioSteps(): Promise<ScenarioResult> {
    try {
      const all = adaptIcebergs(await request('/icebergs'));
      const routes = await this.calculateRoutes({ start: CAPE_TOWN, end: ICE_EDGE, icebergs: all });
      if (routes.length === 0) throw new ApiError('The backend returned no routes.', 'parse');
      const selected = safest(routes);
      const icebergs = filterIcebergsForRoute(all, selected);
      let warning: string | undefined;

      let risk: Risk;
      try {
        risk = await this.getRisk({ route: selected, icebergs });
      } catch {
        risk = { level: levelFromScore(selected.risk_score), reasons: selected.reasons };
        warning = 'The /risk endpoint did not answer; the level is derived from the route risk score.';
      }
      let text = '';
      try {
        text = await this.explain(selected, { risk });
      } catch {
        warning = (warning ? warning + ' ' : '') + 'No explanation available from the backend.';
      }

      const step: Step = {
        title: 'Live snapshot',
        label: 'Live snapshot',
        date: new Date().toISOString().slice(0, 10),
        ship: { lat: selected.waypoints[0].lat, lon: selected.waypoints[0].lon },
        icebergs,
        routes,
        selected_route_id: selected.id,
        risk,
        explanation_text: text || 'The backend provided no explanation text for this route.',
        alert: risk.level === 'RED' ? { recipients: DEFAULT_RECIPIENTS, simulated: true } : null,
        whatif: [], // never hardcoded in live mode
      };
      const scenario: Scenario = { title: 'Live snapshot', steps: [step] };
      return { scenario, offline: false, warning, allIcebergs: all };
    } catch (e) {
      return this.loadOffline(e instanceof Error ? e.message : String(e));
    }
  }

  // ------------------------------------------------------------------ offline snapshot

  private async loadOffline(reason: string): Promise<ScenarioResult> {
    const get = async (f: string): Promise<unknown> => {
      const r = await fetch(`/demo/cache/${f}.json`);
      if (!r.ok) throw new Error(`cache/${f}.json: HTTP ${r.status}`);
      return r.json();
    };
    const [bergsRaw, routesRaw, riskRaw, explainRaw, alertRaw] = await Promise.all([
      get('icebergs'),
      get('routes'),
      get('risk').catch(() => null),
      get('explain').catch(() => null),
      get('alert').catch(() => null),
    ]);
    const all = adaptIcebergs(bergsRaw);
    const routes = adaptRoutes(routesRaw);
    if (routes.length === 0) throw new Error(`${reason} The offline snapshot is also unavailable.`);
    const selected = safest(routes);
    const risk = adaptRisk(riskRaw, selected.risk_score);
    const step: Step = {
      title: 'Offline snapshot',
      label: 'Offline snapshot',
      date: new Date().toISOString().slice(0, 10),
      ship: { lat: selected.waypoints[0].lat, lon: selected.waypoints[0].lon },
      icebergs: filterIcebergsForRoute(all, selected),
      routes,
      selected_route_id: selected.id,
      risk,
      explanation_text: adaptExplain(explainRaw) || 'No explanation in the offline snapshot.',
      alert: risk.level === 'RED' ? adaptAlert(alertRaw, DEFAULT_RECIPIENTS) : null,
      whatif: [],
    };
    return {
      scenario: { title: 'Offline snapshot (placeholder data)', placeholder: true, steps: [step] },
      offline: true,
      allIcebergs: all,
      warning: `${reason} Showing the bundled offline snapshot (placeholder data, not current).`,
    };
  }

  // ------------------------------------------------------------------ endpoints

  async predictDrift(iceberg: Iceberg): Promise<{ drift_path: DriftPoint[]; method?: string }> {
    const raw = await post('/predict-drift', {
      iceberg_id: iceberg.id,
      id: iceberg.id,
      lat: iceberg.lat,
      lon: iceberg.lon,
      hours: 72,
      horizon_hours: 72,
    });
    const d = adaptDrift(raw);
    if (d.drift_path.length === 0) throw new ApiError('The backend returned no drift path for this iceberg.', 'parse');
    return d;
  }

  async calculateRoutes(p: RouteParams): Promise<Route[]> {
    await this.loadProps();
    const body: Record<string, unknown> = {
      start: pt(p.start),
      end: pt(p.end),
      start_lat: p.start.lat,
      start_lon: p.start.lon,
      end_lat: p.end.lat,
      end_lon: p.end.lon,
      icebergs: p.icebergs.map(bergPayload),
    };
    this.addWhatIf(body, this.props?.routes, p.delayHours, p.windDeltaKmh, p.icebergs);
    return adaptRoutes(await post('/calculate-routes', body));
  }

  async getRisk(p: RiskParams): Promise<Risk> {
    await this.loadProps();
    const body: Record<string, unknown> = {
      route_id: p.route.id,
      route: { id: p.route.id, waypoints: p.route.waypoints.map(pt) },
      waypoints: p.route.waypoints.map(pt),
      icebergs: p.icebergs.map(bergPayload),
    };
    this.addWhatIf(body, this.props?.risk, p.delayHours, p.windDeltaKmh, p.icebergs);
    return adaptRisk(await post('/risk', body), p.route.risk_score);
  }

  async explain(route: Route, ctx: { risk: Risk }): Promise<string> {
    return adaptExplain(
      await post('/explain', {
        route_id: route.id,
        route: { id: route.id, name: route.name, waypoints: route.waypoints.map(pt) },
        risk_level: ctx.risk.level,
        reasons: ctx.risk.reasons,
      }),
    );
  }

  async sendAlert(risk: Risk, route: Route, opts: { includeFamily: boolean }): Promise<Alert> {
    const recipients = [...DEFAULT_RECIPIENTS, ...(opts.includeFamily ? ['Family contacts (pre-authorized)'] : [])];
    const raw = await post('/alert', {
      level: risk.level,
      risk_level: risk.level,
      reasons: risk.reasons,
      route_id: route.id,
      recipients,
      include_family: opts.includeFamily,
      simulated: true,
    });
    return adaptAlert(raw, recipients);
  }

  // ------------------------------------------------------------------ What-If capability detection

  /** Reads the FastAPI OpenAPI document once to learn which inputs the endpoints accept. */
  private loadProps(): Promise<void> {
    if (!this.propsLoad) this.propsLoad = this.readOpenApi();
    return this.propsLoad;
  }

  private async readOpenApi(): Promise<void> {
    this.props = { routes: new Set(), risk: new Set() };
    try {
      const doc = (await request('/openapi.json')) as {
        paths?: Record<string, { post?: { requestBody?: { content?: Record<string, { schema?: unknown }> } } }>;
        components?: { schemas?: Record<string, unknown> };
      };
      const resolve = (schema: unknown, depth = 0): Record<string, unknown> => {
        const s = schema as { $ref?: string; properties?: Record<string, unknown>; allOf?: unknown[] } | undefined;
        if (!s || depth > 4) return {};
        if (s.$ref) return resolve(doc.components?.schemas?.[s.$ref.split('/').pop() ?? ''], depth + 1);
        const out: Record<string, unknown> = { ...(s.properties ?? {}) };
        (s.allOf ?? []).forEach((x) => Object.assign(out, resolve(x, depth + 1)));
        return out;
      };
      const read = (path: string) => {
        const content = doc.paths?.[path]?.post?.requestBody?.content;
        const schema = content?.['application/json']?.schema;
        return new Set(Object.keys(resolve(schema)));
      };
      this.props = { routes: read('/calculate-routes'), risk: read('/risk') };
    } catch {
      // no openapi: What-If stays hidden, plain calls still work
    }
  }

  private find(re: RegExp): { routes?: string; risk?: string } {
    const f = (s?: Set<string>) => [...(s ?? [])].find((k) => re.test(k));
    return { routes: f(this.props?.routes), risk: f(this.props?.risk) };
  }

  private addWhatIf(body: Record<string, unknown>, known: Set<string> | undefined, delay?: number, wind?: number, bergs?: Iceberg[]) {
    if (!known) return;
    const key = (re: RegExp) => [...known].find((k) => re.test(k));
    if (delay) {
      const k = key(DELAY_RE);
      if (k) body[k] = delay;
    }
    if (wind) {
      const k = key(WIND_RE);
      if (k) body[k] = wind;
    }
    if (bergs && !known.has('icebergs')) {
      const k = key(/iceberg/i);
      if (k) body[k] = bergs.map(bergPayload);
    }
  }

  async getWhatIfSupport(): Promise<WhatIfSupport> {
    if (this.support) return this.support;
    await this.loadProps();
    const d = this.find(DELAY_RE);
    const w = this.find(WIND_RE);
    const i = this.find(/iceberg/i);
    this.support = { delay: !!(d.routes || d.risk), wind: !!(w.routes || w.risk), moveIceberg: !!(i.routes || i.risk) };
    return this.support;
  }
}

/** Only properties that clearly mean "delay in hours" / "wind change" are used. Anything else stays hidden. */
const DELAY_RE = /delay/i;
const WIND_RE = /wind.*(delta|adjust|extra|offset|bias|add|increase)|(delta|adjust|extra|offset|bias|add|increase).*wind/i;

export function safest(routes: Route[]): Route {
  return [...routes].sort((a, b) => (Number.isFinite(a.risk_score) ? a.risk_score : 1e9) - (Number.isFinite(b.risk_score) ? b.risk_score : 1e9))[0];
}
