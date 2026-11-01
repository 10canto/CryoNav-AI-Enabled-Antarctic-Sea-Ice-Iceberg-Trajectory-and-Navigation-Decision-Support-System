# CryoNav AI - Demo Instructions for 5-Minute Judge Presentation

## Quick Start (Demo Mode - Recommended for Presentation)

```bash
# Terminal 1: Frontend Only (No backend needed!)
cd cryonav-ai
npm run dev

# Open: http://localhost:3001
# Click "Start Scripted Demo" button
# Navigate with "Next Step →" button
```

**Why Demo Mode:**
- ✅ Works 100% offline
- ✅ Frozen data (reliable, repeatable)
- ✅ Perfect risk escalation: GREEN → YELLOW → ORANGE → RED
- ✅ No backend dependencies
- ✅ Always works during presentation

## Normal Mode (Live Backend)

```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd cryonav-ai
npm run dev

# Open: http://localhost:3001
```

**Features in Normal Mode:**
- Real-time iceberg data
- Live route calculations
- What-If analysis with real backend
- Automatic offline fallback if backend crashes

## Demo Presentation Flow (5 Minutes)

### Minute 0-1: Introduction
```
"CryoNav AI is an Antarctic navigation decision support system
using track extrapolation and physics-based drift prediction."
```
- Show normal mode briefly
- Point out route options (safest/fastest/fuel-efficient)

### Minute 1: Start Demo
```
"Let me show you a scripted crisis scenario."
```
- Click **"Start Scripted Demo"**
- **Step 1 (GREEN):** "Departure from Cape Town, all systems nominal"
- Show 3 route options, point out consistent colors

### Minute 2: Risk Escalation Begins
```
"24 hours in, we detect iceberg A81 drifting toward our route."
```
- Click **"Next Step →"**
- **Step 2 (YELLOW):** Risk card turns yellow
- Click an iceberg marker
- Show drift prediction with 24h/48h/72h uncertainty circles
- Point out "Track extrapolation" method in popup

### Minute 3: Crisis
```
"48 hours in: Critical situation. New iceberg detected ahead."
```
- Click **"Next Step →"**
- **Step 3 (ORANGE then RED):** Risk card turns RED and pulses
- Alert modal appears automatically
- Show explanation panel with route trade-offs
- Point out: "System recommends reroute with +12 km distance but 85% risk reduction"

### Minute 4: What-If Analysis
```
"What if we had delayed departure by 24 hours?"
```
- Scroll to What-If panel (if backend is online)
- Click **"Delay 24 hours"**
- Show live recalculation
- Point out: "System shows ORANGE → GREEN with waiting"

### Minute 5: Resolution
```
"Crisis averted. We rerouted successfully."
```
- Click **"Next Step →"**
- **Step 4 (GREEN):** Risk returns to green
- Show final route on map
- Conclude: "Track extrapolation with current-based fallback provides
  reliable drift prediction for Antarctic navigation."

## Key Points to Mention

1. **Hybrid Prediction Model**
   - Primary: Track extrapolation (when ≥2 recent positions available)
   - Fallback: Current-based physics model
   - Error measured on real BYU iceberg data: 2.19 km mean at 24h

2. **Data Sources**
   - BYU Antarctic Iceberg Tracking Database (real positions)
   - Copernicus Marine Service ocean currents (monthly Oct 2025-Aug 2026)
   - Calibrated uncertainty from 75th percentile validation

3. **Safety Features**
   - 3 route types with different risk/time/fuel trade-offs
   - Visual risk assessment (GREEN/YELLOW/ORANGE/RED)
   - Automatic satellite alerts on RED risk
   - What-If analysis for contingency planning

4. **Production-Ready Features**
   - Offline fallback (works without backend)
   - Scripted demo mode (reliable for presentations)
   - Explainable AI (plain-language route explanations)
   - Projector-friendly fonts (14px minimum)

## Troubleshooting During Demo

| Issue | Quick Fix |
|-------|-----------|
| Backend offline | Use demo mode (works without backend) |
| Demo not loading | Verify `public/demo/scenario.json` exists |
| Map blank | Press F5 to reload |
| Routes not showing | Click "Reset" then restart demo |
| Fonts too small | Check browser zoom is 100% |

## Files Checklist

Before presentation, verify these files exist:
```bash
cd cryonav-ai/public/demo
ls -la

# Should show:
# scenario.json (27KB) - Frozen demo scenario
# cache/snapshot.json (2KB) - Offline fallback
# cache/predictions.json (5.5KB) - Cached predictions
```

## Emergency Backup Plan

If frontend crashes during demo:
1. Open browser to: http://localhost:3001
2. Press F5 to hard reload
3. Click "Start Scripted Demo" again
4. Continue from last step shown

If nothing works:
1. Show static route map SVGs in repo root:
   - `route_map_scenario_0.svg` through `route_map_scenario_3.svg`
2. Use these to explain the concept manually

## After Demo

To regenerate demo scenario with fresh backend data:
```bash
cd backend
python scripts/export_demo.py
```

To build for deployment:
```bash
cd cryonav-ai
npm run build
# Output: dist/ folder ready to serve
```

## Contact & Support

- Frontend: React + TypeScript + Leaflet
- Backend: FastAPI + Python
- Demo: 100% offline capable
- Repository: Check README.md for full documentation

**Good luck with your presentation! 🚢🧊**
