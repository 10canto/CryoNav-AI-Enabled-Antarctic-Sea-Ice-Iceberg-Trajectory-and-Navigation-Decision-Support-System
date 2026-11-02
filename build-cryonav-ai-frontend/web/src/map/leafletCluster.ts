import type * as Lt from 'leaflet';
import leaflet from './leafletGlobal';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';

/** Cluster group created through the real Leaflet object that the plugin extended. */
export function createClusterGroup(options: Lt.MarkerClusterGroupOptions): Lt.MarkerClusterGroup {
  return leaflet.markerClusterGroup(options);
}
