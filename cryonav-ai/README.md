# CryoNav AI - Antarctic Ship Navigation Dashboard
### Indian Antarctic Expedition (Chennai Port ➔ Maitri Research Station)

**CryoNav AI** is an advanced AI-powered maritime navigation dashboard prototype designed for ice-strengthened polar research vessels traversing the treacherous Indian Ocean and Southern Ocean corridor to India's **Maitri Research Station** (Queen Maud Land, East Antarctica).

CryoNav AI continuously fuses satellite-detected sea ice concentration zones, radar-tracked tabular iceberg drift vectors, high-latitude katabatic wind fields, and bathymetric chokepoints to dynamically calculate and evaluate 3 comparative polar routes.

---

## Expedition Profile

| Parameter | Specification |
|---|---|
| **Departure Point** | Chennai Port, India (`13.0827°N, 80.2707°E`) |
| **Destination** | Maitri Research Station, Antarctica (`70.7644°S, 11.7386°E`) |
| **Vessel Class** | Ice-strengthened Polar Research Vessel (Polar Class 1A / PC5) |
| **Total Distance** | 10,500 – 12,750 km (~5,670 – 6,880 nautical miles) |
| **Voyage Duration** | 28 – 36 days (672 – 864 hours) |
| **Transit Oceans** | Bay of Bengal ➔ Central Indian Ocean ➔ Roaring Forties (40°S) ➔ Furious Fifties (50°S) ➔ Screaming Sixties (60°S) ➔ Lazarev Ice Shelf |
| **Operational Corridor** | Coordinates `[13.08°N, 80.27°E]` down to `[70.76°S, 11.74°E]` |

---

## 3 Realistic Navigation Routes

### 1. Route A - Safest (Ice-Avoidance Priority)
* **Visual Representation**: Solid Emerald Green Polyline (`#10b981`, width 4px)
* **Total Distance**: ~12,200 – 12,750 km
* **Voyage Duration**: 34 – 36 days (816 – 864 hrs)
* **Fuel Consumption**: ~185,000 – 198,000 Liters
* **Calculated Risk**: 12% – 18% (5-Star Rating ★★★★★)
* **Maritime Strategy**:
  - Conservative eastward trajectory in the Southern Ocean, keeping clear of treacherous **Iceberg Alley** (40°E to 60°E) and Prince Edward Island sub-Antarctic drift zones.
  - Approaches the Princess Astrid Coast and Lazarev Ice Shelf from an eastern waypoint (22°E to 26°E) through consolidated leads with minimum pressure ridges.
  - Serves as the designated safe convoy corridor during heavy ice conditions.

### 2. Route B - Fastest (Direct Southern Great-Circle Track)
* **Visual Representation**: Dashed Amber Polyline (`#f59e0b`, width 3px)
* **Total Distance**: ~10,500 – 11,300 km
* **Voyage Duration**: 28 – 30.5 days (672 – 732 hrs)
* **Fuel Consumption**: ~168,000 – 182,000 Liters
* **Calculated Risk**: 38% – 61% (Normal) / **98% (Blocked in Calving Event)**
* **Maritime Strategy**:
  - Cuts straight across the Southern Indian Ocean basin, minimizing nautical miles.
  - Crosses directly through the hazardous 40°E–50°E iceberg drift stream and heavy swell zones of the Furious Fifties.
  - Faster when open leads exist, but highly vulnerable to tabular iceberg collisions and pack ice compression.

### 3. Route C - Fuel-Saver (Current & Wind Assisted)
* **Visual Representation**: Dotted Orange Polyline (`#f97316`, width 2px)
* **Total Distance**: ~11,200 – 11,500 km
* **Voyage Duration**: 31 – 32 days (744 – 768 hrs)
* **Fuel Consumption**: ~152,000 – 158,000 Liters (Lowest fuel burn)
* **Calculated Risk**: 23% – 32% (4-Star Rating ★★★★☆)
* **Maritime Strategy**:
  - Exploits prevailing westerly circumpolar currents and favorable trailing wind components in the 40°S–48°S latitudes.
  - Reduces engine load by 18% compared to direct routing while maintaining adequate safety margins from major ice fields.

---

## 4 Operational Scenarios

CryoNav AI features an interactive simulation engine modeling four critical phases of the polar expedition:

### Scenario 0: Baseline Departure & Nominal Transit
- **Vessel Position**: `[-35.0°S, 65.0°E]` (Entering the Roaring Forties)
- **Condition**: SAFE (Green). Open ocean, ice concentration 18%, benign weather.
- **AI Recommendation**: Route A (Safest) recommended as baseline passage plan.

### Scenario 1: Tabular Iceberg Detection in Iceberg Alley
- **Vessel Position**: `[-54.0°S, 36.0°E]` (Furious Fifties approach)
- **Hazard**: Radar and satellite detection of giant tabular iceberg `ICE-TAB-2024-01` (2.5 km × 1.8 km) drifting NW at 1.2 knots directly across Route B.
- **Condition**: CAUTION (Yellow). Route B risk spikes to 52%.
- **AI Recommendation**: Divert to Route A (Safest) to maintain an 85+ km safety clearance.

### Scenario 2: Gale-Force Southern Ocean Cyclone Skirting
- **Vessel Position**: `[-52.0°S, 24.0°E]`
- **Hazard**: Deep sub-polar cyclone generating 52-knot winds, 11-meter waves, and freezing spray between 50°S–58°S.
- **Condition**: WARNING (Orange, sound pulse). Route B forced into heavy swell and dangerous ice compression.
- **AI Recommendation**: Route A eastward offset maintains vessel on the navigable semi-circle of the storm system with minimal risk (15%).

### Scenario 3: Catastrophic Lazarev Ice Shelf Calving & Escort Reroute
- **Vessel Position**: `[-68.5°S, 22.0°E]` (Icebreaker Escort Rendezvous)
- **Hazard**: Massive collapse of Lazarev Ice Shelf barrier generating multi-kilometer tabular melange blocks (`CALVING-BLOCK-ALPHA`, `BETA`, `GAMMA`) blocking standard southern entry channels.
- **Condition**: EMERGENCY (Red strobe modal, 3-beep alarm, satellite dispatch alert).
- **AI Recommendation**: Routes B and C marked `[BLOCKED - IMPASSABLE]`. Dynamic reroute via Route A eastward corridor with Russian/Indian icebreaker escort convoy for final 150 km ice penetration.

---

## Maritime Constraints & Polar Code Considerations

1. **IMO Polar Code (Polar Class 1A)**:
   - Operating limit in consolidated ice: up to 1.0m first-year ice without icebreaker escort.
   - Requires minimum 10 nautical mile buffer from fast-ice edges under katabatic wind conditions.
2. **Iceberg Alley (40°E to 60°E)**:
   - Concentration of calved Antarctic icebergs drifting northwestward under the influence of the Antarctic Coastal Current and ACC.
3. **Katabatic Wind Surges**:
   - Severe down-slope winds off the Antarctic ice sheet can reach hurricane force (60+ knots) within 30 minutes, compressing pack ice against vessels.

---

## Quick Start

### Installation & Launch
```bash
npm install
npm run dev
# dev server runs on port 3000
```

### Backend Integration
- Connects automatically to FastAPI backend at `http://localhost:8000`.
- If offline, the built-in **Simulation Engine** handles all telemetry seamlessly for demonstrations.

---

## Key Architecture & Technology Stack
- **React 18** with **Vite**
- **Tailwind CSS** with **Professional Polish** tactical maritime design system
- **Leaflet & React-Leaflet** with custom SVG projection markers, sector presets, and uncertainty cones
- **Web Audio API** for synthesized marine emergency alarms
