import type { Map as LeafletMap } from 'leaflet';
import L from 'leaflet';

export interface IceCell {
  lat: number;
  lon: number;
  concentration: number; // 0-100%
}

export class SeaIceLayer {
  private map: LeafletMap;
  private iceGroup: L.LayerGroup;
  private visible: boolean = true;

  constructor(map: LeafletMap) {
    this.map = map;
    this.iceGroup = L.layerGroup();
    
    // Create dedicated sea-ice pane below uncertainty circles (380) and routes (450)
    if (!this.map.getPane('seaice')) {
      const pane = this.map.createPane('seaice');
      pane.style.zIndex = '300';
    }
    
    this.iceGroup.addTo(this.map);
  }

  /**
   * Update the ice layer with new concentration data
   */
  update(cells: IceCell[]) {
    this.iceGroup.clearLayers();
    
    for (const cell of cells) {
      const color = this.getColorForConcentration(cell.concentration);
      const size = 2.0; // 2° resolution
      
      const bounds: L.LatLngBoundsExpression = [
        [cell.lat - size / 2, cell.lon - size / 2],
        [cell.lat + size / 2, cell.lon + size / 2]
      ];
      
      const rect = L.rectangle(bounds, {
        color: color,
        weight: 0,
        fillColor: color,
        fillOpacity: 0.4,
        pane: 'seaice',
        interactive: false
      });
      
      this.iceGroup.addLayer(rect);
    }
  }

  /**
   * Color scale: dark blue (0%) → light blue (30-50%) → white (100%)
   */
  private getColorForConcentration(concentration: number): string {
    const pct = Math.max(0, Math.min(100, concentration)) / 100;
    
    // Dark blue at 0%, white at 100%
    const r = Math.round(0 + pct * 255);
    const g = Math.round(105 + pct * 150);
    const b = Math.round(148 + pct * 107);
    
    return `rgb(${r}, ${g}, ${b})`;
  }

  show() {
    if (!this.visible) {
      this.iceGroup.addTo(this.map);
      this.visible = true;
    }
  }

  hide() {
    if (this.visible) {
      this.iceGroup.remove();
      this.visible = false;
    }
  }

  isVisible(): boolean {
    return this.visible;
  }

  destroy() {
    this.iceGroup.clearLayers();
    this.iceGroup.remove();
  }
}

/**
 * Generate placeholder sea-ice concentration data based on latitude
 * PLACEHOLDER DATA - to be replaced with real sea-ice grids
 */
export function generatePlaceholderIceData(stepIndex: number): IceCell[] {
  const cells: IceCell[] = [];
  
  // Seasonal variation: 0-based step index affects ice extent
  const seasonalShift = (stepIndex % 4) * 5; // 0, 5, 10, 15% variation
  
  // Grid resolution: 2° x 2°
  const resolution = 2.0;
  
  // Antarctic region: -75° to -50° latitude, -180° to 180° longitude
  for (let lat = -75; lat <= -50; lat += resolution) {
    for (let lon = -180; lon <= 180; lon += resolution) {
      let concentration = 0;
      
      if (lat < -65) {
        // Pack ice zone: 60-90% ice
        concentration = 60 + Math.random() * 30 + seasonalShift;
      } else if (lat >= -65 && lat < -60) {
        // Marginal ice zone: 20-60% ice
        concentration = 20 + Math.random() * 40 + seasonalShift * 0.5;
      } else {
        // Open ocean: 0-20% ice
        concentration = Math.random() * 20;
      }
      
      // Clamp to 0-100%
      concentration = Math.max(0, Math.min(100, concentration));
      
      cells.push({ lat, lon, concentration });
    }
  }
  
  return cells;
}
