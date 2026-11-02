# CryoNav AI - web frontend

Vite + React + TypeScript. Map: Leaflet used imperatively (no react-leaflet), optional `leaflet.markercluster`. State: zustand.
Package manager: npm (the repo already has a `package-lock.json`).

## Run

```bash
cd web
npm install
npm run dev        # http://localhost:5173  (Demo mode works with the backend OFF)
npm run build      # type-checks, then writes web/dist
npm run preview    # serves the production build
```

Live mode talks to the FastAPI backend. Copy `.env.example` to `.env` to change the URL:

```bash
cp .env.example .env     # VITE_API_URL=http://localhost:8000
```

## Modes

- **Demo**: reads `public/demo/scenario.json` once, then makes zero network calls. 4 scripted steps (GREEN, YELLOW, ORANGE, RED). The file is currently PLACEHOLDER data (`"placeholder": true`). Schema: `docs/demo_scenario_schema.md`. Regenerate the filler with `node scripts/gen-placeholder.mjs`.
- **Live**: calls `/icebergs`, `/calculate-routes`, `/risk`, `/explain`, `/predict-drift` (on iceberg click), `/alert` (button in the alert modal). Requests only happen on user actions (switching to Live, Refresh, selecting a route / iceberg, What-If, Send simulated alert). If the backend is down or answers badly, the app loads `public/demo/cache/*.json` automatically and shows the "offline snapshot" badge.

## Layout of `src/`

```
domain/types.ts        domain types (Iceberg, Route, Step, ...)
domain/geo.ts          distance + route bounding-box iceberg filter
data/DataSource.ts     interface
data/DemoSource.ts     scenario.json only
data/LiveSource.ts     backend calls, offline fallback, What-If capability detection
data/liveAdapter.ts    backend response shapes -> domain types (edit here if the API differs)
store/useStore.ts      zustand store
map/MapController.ts   plain class owning the single Leaflet map (subscribes to the store outside React)
components/            panels, timeline, alert modal
dev/DevOverlay.tsx     dev-only checks (import.meta.env.DEV)
```

## Dev checks (only in `npm run dev`)

An overlay (top-left) shows FPS, network requests since a baseline, and Leaflet map instances created. The button
"Run 4-step demo check" resets the scenario, steps through all 4 steps and prints PASS/FAIL for 0 requests and 1 map.
The overlay is not part of the production build.

## Land layer

`public/data/land.geojson` is Natural Earth 110m land (public domain). If it is missing the map still works with an empty land layer. To re-download:

```bash
curl -L -o public/data/land.geojson \
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson
```

## Notes

- StrictMode is off on purpose (its dev double-mount would create a second Leaflet map).
- Sea-ice, currents, alerts and the Demo scenario are simplified / simulated; the UI labels them as such.
- The repository root also contains a thin wrapper (`src/main.tsx`, `src/App.tsx`, `public/`) that re-exports this app so a root `npm run build` produces the same UI in `dist/`. The source of truth is `web/`. After changing anything in `web/public/`, copy it: `cp -r web/public/. public/`.
