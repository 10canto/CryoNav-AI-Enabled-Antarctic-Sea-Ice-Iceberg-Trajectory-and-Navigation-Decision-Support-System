import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { createClusterGroup } from './leafletCluster';
import type { Iceberg, Route, Step } from '../domain/types';
import { currentStep, type AppState, type useStore } from '../store/useStore';
import { PORTS } from './ports';

type Store = typeof useStore;
type IcebergLayer = L.LayerGroup | L.MarkerClusterGroup;

const CLUSTER_THRESHOLD = 40;
const SHIP_ANIM_MS = 1500;
const CAMERA_S = 0.8;
const DRIFT_HOURS = [24, 48, 72];

const ll = (p: { lat: number; lon: number }): L.LatLngTuple => [p.lat, p.lon];

/**
 * Owns the single Leaflet map. Created once from a React effect, driven by
 * store.subscribe outside React. All layers are keyed by id and diffed.
 */
export class MapController {
  /** total instances ever created / currently alive (dev checks) */
  static created = 0;
  static alive = 0;
  /** the live instance, for dev checks */
  static current: MapController | null = null;

  readonly map: L.Map;
  private unsub: (() => void) | null = null;
  private destroyed = false;

  private landLayer: L.GeoJSON | null = null;
  private portLayers = new Map<string, L.CircleMarker>();

  private routeGroup = L.layerGroup();
  private routeLines = new Map<string, { line: L.Polyline; sig: string }>();
  private halo: L.Polyline;

  private icebergLayer: IcebergLayer = L.layerGroup();
  private icebergMarkers = new Map<string, L.CircleMarker>();
  private icebergData = new Map<string, Iceberg>();
  private clustered = false;

  private driftGroup = L.layerGroup();
  private driftLayers = new Map<string, L.Path | L.CircleMarker>();
  private predictionMarker: L.CircleMarker | null = null;

  private ship: L.Marker;
  private raf = 0;
  private idleWaiters: Array<() => void> = [];

  private prevState: AppState | null = null;
  private prevSelectedRoute: L.LatLng[] | null = null;
  private lastStepRef: Step | null = null;
  private alertAcknowledged = false;

  constructor(container: HTMLElement, private store: Store) {
    MapController.created += 1;
    MapController.alive += 1;

    this.map = L.map(container, {
      preferCanvas: true,
      zoomAnimation: true,
      zoomControl: true,
      attributionControl: true,
      minZoom: 2,
      maxZoom: 12, // required by markercluster when there is no tile layer
      zoomSnap: 0.25,
    });
    this.map.attributionControl.setPrefix(false);
    this.map.attributionControl.addAttribution('Land: Natural Earth (public domain). No tile server.');

    // Initial view: Cape Town to Antarctica
    this.map.fitBounds(
      [
        [-75, -2],
        [-31, 28],
      ],
      { padding: [10, 10], animate: false },
    );

    this.halo = L.polyline([], { weight: 11, opacity: 0.28, interactive: false }).addTo(this.map);
    this.routeGroup.addTo(this.map);
    this.driftGroup.addTo(this.map);
    this.icebergLayer.addTo(this.map);
    this.addPorts();

    this.ship = L.marker([-33.92, 18.43], {
      icon: L.divIcon({ className: 'ship-marker', html: '<div class="ship-icon"></div>', iconSize: [26, 26], iconAnchor: [13, 13] }),
      zIndexOffset: 1000,
      keyboard: false,
    })
      .bindTooltip('Ship (approximate position)', { direction: 'top', offset: [0, -10] })
      .addTo(this.map);

    this.map.on('click', () => this.store.getState().selectIceberg(null));

    void this.loadLand();
    this.unsub = this.store.subscribe((s, p) => this.sync(s, p));
    this.sync(this.store.getState(), null);
  }

  destroy() {
    if (this.destroyed) return;
    this.destroyed = true;
    this.unsub?.();
    cancelAnimationFrame(this.raf);
    this.map.remove();
    MapController.alive -= 1;
    this.flushIdle();
  }

  /** Resolves when the ship animation (if any) has finished. */
  whenIdle(): Promise<void> {
    if (!this.raf) return Promise.resolve();
    return new Promise((res) => this.idleWaiters.push(res));
  }

  // ---------------------------------------------------------------- static layers

  private async loadLand() {
    try {
      const r = await fetch('/data/land.geojson');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const gj = await r.json();
      if (this.destroyed) return;
      this.landLayer = L.geoJSON(gj, {
        interactive: false,
        style: { color: '#4a6a94', weight: 1, fillColor: '#1d3558', fillOpacity: 1 },
      }).addTo(this.map);
      this.landLayer.bringToBack();
    } catch (e) {
      console.warn('[map] land.geojson unavailable, continuing with an empty land layer', e);
    }
  }

  private addPorts() {
    for (const p of PORTS) {
      const m = L.circleMarker(ll(p.pos), {
        radius: 7,
        color: '#0a1428',
        weight: 2,
        fillColor: p.color,
        fillOpacity: 1,
      })
        .bindTooltip(p.name, { permanent: true, direction: p.tooltipDir, className: 'port-label', offset: p.tooltipDir === 'left' ? [-8, 0] : [8, 0] })
        .bindPopup(`<strong>${p.name}</strong><br/>${p.note}`)
        .addTo(this.map);
      this.portLayers.set(p.id, m);
    }
    const edge = PORTS.find((p) => p.id === 'ice-edge')!;
    const maitri = PORTS.find((p) => p.id === 'maitri')!;
    L.polyline([ll(edge.pos), ll(maitri.pos)], {
      color: '#f78fb3',
      weight: 2,
      dashArray: '4 6',
      interactive: false,
    })
      .bindTooltip('overland haul', { sticky: true })
      .addTo(this.map);
  }

  // ---------------------------------------------------------------- store sync

  private sync(s: AppState, p: AppState | null) {
    if (this.destroyed) return;
    const step = currentStep(s);
    const prev = this.prevState ?? p;
    this.prevState = s;
    if (!step) return;

    const stepChanged = step !== this.lastStepRef;
    const navigated = !prev || s.navSeq !== prev.navSeq;
    const first = this.lastStepRef === null;

    if (stepChanged || navigated) {
      this.lastStepRef = step;
      this.syncRoutes(step.routes, s.selectedRouteId);
      this.syncIcebergs(step.icebergs);
      this.syncPredictedCrossing(step);
      if (navigated) this.onNavigate(step, first);
    } else if (s.selectedRouteId !== prev.selectedRouteId) {
      this.styleRoutes(s.selectedRouteId);
    }
    if (stepChanged || navigated || s.selectedIcebergId !== prev?.selectedIcebergId) {
      this.drawDrift(step, s.selectedIcebergId);
      this.styleIcebergs(s.selectedIcebergId);
    }
    if (prev && s.followShip && !prev.followShip) {
      this.map.panTo(this.ship.getLatLng(), { animate: true, duration: CAMERA_S });
    }
    
    // Handle alert acknowledgment for route pulse
    if (prev && prev.alertOpen && !s.alertOpen && !this.alertAcknowledged) {
      this.alertAcknowledged = true;
      this.pulseSelectedRoute(s.selectedRouteId);
    }
  }

  /** Step navigation: animate the ship and move the camera ONCE. */
  private onNavigate(step: Step, first: boolean) {
    // Reset alert acknowledged flag on navigation
    this.alertAcknowledged = false;
    
    const target = L.latLng(step.ship.lat, step.ship.lon);
    const selected = step.routes.find((r) => r.id === step.selected_route_id);
    const newLine = selected ? selected.waypoints.map((w) => L.latLng(w.lat, w.lon)) : null;

    if (first) {
      this.ship.setLatLng(target);
      this.fitStep(step, false);
    } else {
      const follow = this.store.getState().followShip;
      const path = this.shipPath(this.ship.getLatLng(), target, this.prevSelectedRoute);
      this.animateShip(path, () => {
        if (this.store.getState().followShip) this.map.panTo(target, { animate: true, duration: CAMERA_S });
      });
      if (!follow) this.fitStep(step, true);
    }
    this.prevSelectedRoute = newLine;
  }

  /** ONE camera move per step. */
  private fitStep(step: Step, animate: boolean) {
    const pts: L.LatLngTuple[] = [ll(step.ship)];
    const sel = step.routes.find((r) => r.id === step.selected_route_id);
    sel?.waypoints.forEach((w) => pts.push([w.lat, w.lon]));
    step.icebergs.forEach((b) => pts.push([b.lat, b.lon]));
    const b = L.latLngBounds(pts);
    if (!b.isValid()) return;
    this.map.fitBounds(b.pad(0.12), { animate, duration: CAMERA_S, padding: [20, 20], maxZoom: 6 });
  }

  // ---------------------------------------------------------------- ship

  /** Path along the previous route from old to new position when possible, else straight. */
  private shipPath(from: L.LatLng, to: L.LatLng, line: L.LatLng[] | null): L.LatLng[] {
    if (line && line.length > 1) {
      const nearest = (pt: L.LatLng) => {
        let bi = 0;
        let bd = Infinity;
        line.forEach((v, i) => {
          const d = this.map.distance(v, pt);
          if (d < bd) {
            bd = d;
            bi = i;
          }
        });
        return { bi, bd };
      };
      const a = nearest(from);
      const b = nearest(to);
      if (a.bd < 40000 && b.bd < 40000 && b.bi > a.bi) {
        return [from, ...line.slice(a.bi + 1, b.bi), to];
      }
    }
    return [from, to];
  }

  private animateShip(path: L.LatLng[], onDone: () => void) {
    cancelAnimationFrame(this.raf);
    const seg: number[] = [0];
    for (let i = 1; i < path.length; i++) seg.push(seg[i - 1] + this.map.distance(path[i - 1], path[i]));
    const total = seg[seg.length - 1];
    if (total < 1) {
      this.ship.setLatLng(path[path.length - 1]);
      this.raf = 0;
      onDone();
      this.flushIdle();
      return;
    }
    const t0 = performance.now();
    let k = 1;
    const frame = (now: number) => {
      const u = Math.min(1, (now - t0) / SHIP_ANIM_MS);
      const e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; // ease in-out
      const d = e * total;
      while (k < seg.length - 1 && seg[k] < d) k++;
      const span = seg[k] - seg[k - 1] || 1;
      const f = Math.min(1, Math.max(0, (d - seg[k - 1]) / span));
      const a = path[k - 1];
      const b = path[k];
      this.ship.setLatLng([a.lat + (b.lat - a.lat) * f, a.lng + (b.lng - a.lng) * f]);
      if (u < 1) {
        this.raf = requestAnimationFrame(frame);
      } else {
        this.ship.setLatLng(path[path.length - 1]);
        this.raf = 0;
        onDone();
        this.flushIdle();
      }
    };
    this.raf = requestAnimationFrame(frame);
  }

  private flushIdle() {
    const w = this.idleWaiters;
    this.idleWaiters = [];
    w.forEach((f) => f());
  }

  // ---------------------------------------------------------------- routes

  private syncRoutes(routes: Route[], selectedId: string | null) {
    const seen = new Set<string>();
    for (const r of routes) {
      seen.add(r.id);
      const latlngs = r.waypoints.map((w) => ll(w));
      const sig = latlngs.map((p) => p.join(',')).join(';');
      const have = this.routeLines.get(r.id);
      if (!have) {
        const line = L.polyline(latlngs, { color: r.color, weight: 3, opacity: 0.6, lineJoin: 'round' })
          .bindTooltip(r.name, { sticky: true })
          .on('click', (ev) => {
            L.DomEvent.stopPropagation(ev);
            this.store.getState().selectRoute(r.id);
          })
          .addTo(this.routeGroup);
        this.routeLines.set(r.id, { line, sig });
      } else {
        if (have.sig !== sig) {
          have.line.setLatLngs(latlngs);
          have.sig = sig;
        }
        have.line.setStyle({ color: r.color });
        have.line.setTooltipContent(r.name);
      }
    }
    for (const [id, v] of this.routeLines) {
      if (!seen.has(id)) {
        this.routeGroup.removeLayer(v.line);
        this.routeLines.delete(id);
      }
    }
    this.currentRoutes = routes;
    this.styleRoutes(selectedId);
  }

  private currentRoutes: Route[] = [];

  private styleRoutes(selectedId: string | null) {
    for (const r of this.currentRoutes) {
      const v = this.routeLines.get(r.id);
      if (!v) continue;
      const sel = r.id === selectedId;
      v.line.setStyle({ weight: sel ? 5 : 3, opacity: sel ? 1 : 0.55, dashArray: sel ? undefined : '8 6' });
      if (sel) {
        v.line.bringToFront();
        this.halo.setLatLngs(v.line.getLatLngs() as L.LatLng[]);
        this.halo.setStyle({ color: r.color });
      }
    }
    if (!this.currentRoutes.some((r) => r.id === selectedId)) this.halo.setLatLngs([]);
  }

  // ---------------------------------------------------------------- icebergs

  private makeIcebergLayer(clustered: boolean): IcebergLayer {
    return clustered
      ? createClusterGroup({ showCoverageOnHover: false, maxClusterRadius: 45, chunkedLoading: false })
      : L.layerGroup();
  }

  private syncIcebergs(list: Iceberg[]) {
    const wantCluster = list.length > CLUSTER_THRESHOLD;
    if (wantCluster !== this.clustered) {
      // container type flips: rebuild markers into the new container
      this.map.removeLayer(this.icebergLayer);
      this.icebergMarkers.clear();
      this.icebergLayer = this.makeIcebergLayer(wantCluster);
      this.icebergLayer.addTo(this.map);
      this.clustered = wantCluster;
    }
    const seen = new Set<string>();
    this.icebergData.clear();
    for (const b of list) {
      seen.add(b.id);
      this.icebergData.set(b.id, b);
      const radius = 5 + Math.min(7, (b.size_m ?? 200) / 150);
      const have = this.icebergMarkers.get(b.id);
      if (!have) {
        const m = L.circleMarker(ll(b), {
          radius,
          color: '#e8f6ff',
          weight: 1.5,
          fillColor: '#8fd3ff',
          fillOpacity: 0.85,
          bubblingMouseEvents: false,
        })
          .bindPopup(() => this.popupFor(b.id), { closeButton: true })
          .on('click', () => this.store.getState().selectIceberg(b.id));
        m.addTo(this.icebergLayer);
        this.icebergMarkers.set(b.id, m);
      } else {
        const cur = have.getLatLng();
        if (cur.lat !== b.lat || cur.lng !== b.lon) have.setLatLng(ll(b));
        have.setRadius(radius);
      }
    }
    for (const [id, m] of this.icebergMarkers) {
      if (!seen.has(id)) {
        this.icebergLayer.removeLayer(m);
        this.icebergMarkers.delete(id);
      }
    }
  }

  private styleIcebergs(selectedId: string | null) {
    for (const [id, m] of this.icebergMarkers) {
      const sel = id === selectedId;
      m.setStyle({ color: sel ? '#ffffff' : '#e8f6ff', weight: sel ? 3 : 1.5, fillColor: sel ? '#4cc9f0' : '#8fd3ff' });
      if (sel) m.bringToFront();
    }
  }

  private popupFor(id: string): HTMLElement {
    const b = this.icebergData.get(id);
    const el = document.createElement('div');
    el.className = 'berg-popup';
    const h = document.createElement('strong');
    h.textContent = id;
    el.appendChild(h);
    const add = (t: string) => {
      const d = document.createElement('div');
      d.textContent = t;
      el.appendChild(d);
    };
    if (b) {
      if (b.size_m) add(`Size: approx. ${Math.round(b.size_m)} m`);
      add(b.method ? `Drift method: ${b.method}` : 'Drift method: not reported');
      add(b.drift_path.length ? 'Drift path and uncertainty circles shown' : 'Loading drift path...');
    }
    return el;
  }

  // ---------------------------------------------------------------- drift

  private drawDrift(step: Step, icebergId: string | null) {
    const wanted = new Map<string, () => L.Path | L.CircleMarker>();
    const b = icebergId ? step.icebergs.find((x) => x.id === icebergId) : undefined;
    if (b && b.drift_path.length) {
      const pts = [...b.drift_path].sort((x, y) => x.hours - y.hours);
      wanted.set(`${b.id}:path`, () =>
        L.polyline([ll(b), ...pts.map(ll)], { color: '#4cc9f0', weight: 2.5, dashArray: '6 5', interactive: false }),
      );
      // one uncertainty circle per 24 / 48 / 72 h (nearest available point if the backend uses other hours)
      const marks = new Set(DRIFT_HOURS.map((h) => pts.reduce((best, q) => (Math.abs(q.hours - h) < Math.abs(best.hours - h) ? q : best), pts[0])));
      for (const pt of marks) {
        const hasRadius = pt.uncertainty_radius_km > 0;
        if (hasRadius) wanted.set(`${b.id}:circle:${pt.hours}`, () =>
          L.circle(ll(pt), {
            radius: pt.uncertainty_radius_km * 1000,
            color: '#4cc9f0',
            weight: 1.5,
            fillColor: '#4cc9f0',
            fillOpacity: 0.12 + (pt.hours / 72) * 0.06,
            interactive: false,
          }).bindTooltip(`+${pt.hours} h, uncertainty radius ${pt.uncertainty_radius_km} km`, { sticky: true }),
        );
        wanted.set(`${b.id}:dot:${pt.hours}`, () =>
          L.circleMarker(ll(pt), { radius: 3, color: '#4cc9f0', fillColor: '#fff', fillOpacity: 1, weight: 1.5 }).bindTooltip(`+${pt.hours} h`, {
            permanent: true,
            direction: 'top',
            className: 'drift-label',
            offset: [0, -4],
          }),
        );
      }
    }
    for (const [id, layer] of this.driftLayers) {
      if (!wanted.has(id)) {
        this.driftGroup.removeLayer(layer);
        this.driftLayers.delete(id);
      }
    }
    for (const [id, make] of wanted) {
      // drift geometry for a given id+step is immutable, so replace when step changes
      const old = this.driftLayers.get(id);
      if (old) this.driftGroup.removeLayer(old);
      const layer = make();
      this.driftGroup.addLayer(layer);
      this.driftLayers.set(id, layer);
    }
  }

  // ---------------------------------------------------------------- predicted crossing marker

  private syncPredictedCrossing(step: Step) {
    const crossing = (step as any).predicted_crossing;
    if (crossing && crossing.lat && crossing.lon && crossing.label) {
      if (!this.predictionMarker) {
        this.predictionMarker = L.circleMarker([crossing.lat, crossing.lon], {
          radius: 10,
          color: '#da3633',
          weight: 3,
          fillColor: '#da3633',
          fillOpacity: 0.3,
        })
          .bindTooltip(crossing.label, { permanent: true, direction: 'top', className: 'prediction-label', offset: [0, -12] })
          .addTo(this.map);
      } else {
        this.predictionMarker.setLatLng([crossing.lat, crossing.lon]);
        this.predictionMarker.setTooltipContent(crossing.label);
      }
    } else if (this.predictionMarker) {
      this.map.removeLayer(this.predictionMarker);
      this.predictionMarker = null;
    }
  }

  // ---------------------------------------------------------------- route pulse animation

  private pulseSelectedRoute(routeId: string | null) {
    if (!routeId) return;
    const routeObj = this.routeLines.get(routeId);
    if (!routeObj) return;
    
    const line = routeObj.line;
    const originalOpacity = line.options.opacity ?? 1;
    const originalWeight = line.options.weight ?? 5;
    
    // Pulse animation: 1 second
    const duration = 1000;
    const startTime = performance.now();
    
    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);
      
      // Ease in-out for smooth animation
      const eased = progress < 0.5 
        ? 2 * progress * progress 
        : 1 - Math.pow(-2 * progress + 2, 2) / 2;
      
      // Pulse: increase then decrease weight and opacity
      const pulse = Math.sin(eased * Math.PI);
      line.setStyle({
        weight: originalWeight + pulse * 3,
        opacity: originalOpacity + pulse * 0.2
      });
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        // Reset to original style
        line.setStyle({ weight: originalWeight, opacity: originalOpacity });
      }
    };
    
    requestAnimationFrame(animate);
  }
}
