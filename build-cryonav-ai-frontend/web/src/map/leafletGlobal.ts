import * as Lns from 'leaflet';

// leaflet.markercluster is a UMD plugin that extends the *global* L object.
// This module must be fully evaluated BEFORE the plugin is imported (see leafletCluster.ts).
// With bundlers, `import * as L` can be a copy of the real exports, so we take `.default` when present.
const real = ((Lns as unknown as { default?: typeof Lns }).default ?? Lns) as typeof Lns;
(globalThis as unknown as { L: typeof Lns }).L = real;

export default real;
