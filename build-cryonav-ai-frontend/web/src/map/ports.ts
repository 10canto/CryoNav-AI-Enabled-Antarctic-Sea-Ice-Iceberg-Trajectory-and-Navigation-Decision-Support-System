import type { LatLon } from '../domain/types';

export const CAPE_TOWN: LatLon = { lat: -33.92, lon: 18.43 };
/** Approximate ice-edge unloading point. Not a surveyed position. */
export const ICE_EDGE: LatLon = { lat: -70.3, lon: 11.7 };
/** Maitri station (India), about 80 km inland of the ice shelf edge. */
export const MAITRI: LatLon = { lat: -70.77, lon: 11.73 };

export interface PortSpec {
  id: string;
  name: string;
  pos: LatLon;
  color: string;
  note: string;
  tooltipDir: 'left' | 'right' | 'top' | 'bottom';
}

export const PORTS: PortSpec[] = [
  { id: 'cape-town', name: 'Cape Town', pos: CAPE_TOWN, color: '#4cc9f0', note: 'Departure port', tooltipDir: 'right' },
  {
    id: 'ice-edge',
    name: 'Ice edge (approx.)',
    pos: ICE_EDGE,
    color: '#ffd166',
    note: 'Approximate unloading point at the ice edge. Position is indicative only.',
    tooltipDir: 'left',
  },
  {
    id: 'maitri',
    name: 'Maitri',
    pos: MAITRI,
    color: '#f78fb3',
    note: 'Maitri station: inland, overland haul from ice edge',
    tooltipDir: 'right',
  },
];
