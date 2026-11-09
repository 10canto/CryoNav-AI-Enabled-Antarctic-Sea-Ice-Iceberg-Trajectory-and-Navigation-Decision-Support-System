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
  private selectedDate: string = "2020-08-15";

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
        fillOpacity: 0.7,
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

  setSeason(date: string) {
    this.selectedDate = date;
  }

  getSelectedDate(): string {
    return this.selectedDate;
  }

  destroy() {
    this.iceGroup.clearLayers();
    this.iceGroup.remove();
  }
}

/**
 * Load real sea-ice concentration data from Copernicus Marine
 * Real data: Copernicus Marine GLORYS12 reanalysis via A-AMAR pipeline
 */
export async function loadRealSeaIceData(selectedDate: string): Promise<IceCell[]> {
  const targetDate = selectedDate;
  
  try {
    const response = await fetch('/data/seaice_grid.json');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data: Array<{ lat: number; lon: number; date: string; concentration: number | null }> = await response.json();
    
    // Filter to target date and skip null/NaN/undefined concentrations (land/ice-shelf cells)
    const cells: IceCell[] = data
      .filter(row => row.date === targetDate)
      .filter(row => row.concentration != null && !isNaN(row.concentration))
      .map(row => ({
        lat: row.lat,
        lon: row.lon,
        concentration: row.concentration as number
      }));
    
    return cells;
  } catch (error) {
    console.error('Failed to load sea-ice data:', error);
    return [];
  }
}
