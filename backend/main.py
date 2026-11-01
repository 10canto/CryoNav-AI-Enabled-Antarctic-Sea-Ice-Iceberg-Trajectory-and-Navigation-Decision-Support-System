"""
CryoNav AI Backend API
FastAPI server for iceberg prediction, routing, and risk assessment
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import json
import sys
from pathlib import Path

# Add parent directory to path to import hybrid_predictor
sys.path.append(str(Path(__file__).parent))
from hybrid_predictor import HybridPredictor
from routing import RoutingEngine, ShipConfig

app = FastAPI(title="CryoNav AI API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictors
hybrid_predictor = HybridPredictor()
routing_engine = RoutingEngine()

# Load iceberg data
ICEBERG_DATA_PATH = Path(__file__).parent / "test_icebergs.json"  # Use test data for demo

def load_icebergs():
    """Load current iceberg data"""
    if ICEBERG_DATA_PATH.exists():
        try:
            with open(ICEBERG_DATA_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {ICEBERG_DATA_PATH}")
            return []
    print(f"Warning: Iceberg data file not found at {ICEBERG_DATA_PATH}")
    return []

@app.get("/")
async def root():
    return {
        "service": "CryoNav AI API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            "/icebergs",
            "/predict-drift",
            "/ocean-currents",
            "/calculate-routes",
            "/risk",
            "/alert",
            "/explain"
        ]
    }

@app.get("/icebergs")
async def get_icebergs():
    """Get current iceberg positions"""
    icebergs = load_icebergs()
    return {"icebergs": icebergs, "count": len(icebergs)}

@app.get("/predict-drift")
async def predict_drift(
    iceberg_id: str = Query(..., description="Iceberg ID"),
    hours: int = Query(72, description="Prediction horizon in hours"),
    wind_speed: Optional[float] = Query(None, description="Wind speed in m/s"),
    wind_dir: Optional[float] = Query(None, description="Wind direction in degrees"),
    model: str = Query("hybrid", description="Model type: hybrid, physics, or lstm")
):
    """Predict iceberg drift trajectory"""
    
    # Find iceberg
    icebergs = load_icebergs()
    iceberg = next((ib for ib in icebergs if ib.get('id') == iceberg_id or ib.get('Iceberg') == iceberg_id), None)
    
    if not iceberg:
        raise HTTPException(status_code=404, detail=f"Iceberg {iceberg_id} not found")
    
    lat = iceberg.get('Lat') or iceberg.get('lat')
    lon = iceberg.get('Lon') or iceberg.get('lon')
    
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Iceberg position not available")
    
    # Use current date
    current_date = datetime.now()
    
    # Check if iceberg has recent track (mock data - in production, load from database)
    recent_positions = iceberg.get('recent_track', None)
    
    if model == "hybrid" or model == "track":
        # Use hybrid predictor (track extrapolation with current-based fallback)
        result = hybrid_predictor.predict_drift(
            lat=lat,
            lon=lon,
            date=current_date,
            hours=hours,
            recent_positions=recent_positions,
            wind_speed=wind_speed,
            wind_direction=wind_dir
        )
        return result
    elif model == "lstm":
        # LSTM not implemented for demo
        return {
            "error": "LSTM model not available in demo",
            "fallback": "hybrid",
            **hybrid_predictor.predict_drift(lat=lat, lon=lon, date=current_date, hours=hours, recent_positions=recent_positions)
        }
    else:
        # Legacy physics-only
        from physics_predictor import PhysicsPredictor
        physics_predictor = PhysicsPredictor()
        result = physics_predictor.predict_drift(lat=lat, lon=lon, date=current_date, hours=hours, wind_speed=wind_speed, wind_direction=wind_dir)
        result['method'] = 'physics_only_legacy'
        return result

@app.get("/ocean-currents")
async def get_ocean_currents(
    region: str = Query("southern_ocean", description="Region name"),
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """Get ocean current vectors for a region (downsampled)"""
    
    data_dir = Path(__file__).parent.parent / "iceberg-trajectory-ml" / "data" / "ocean_currents_yearly"
    json_path = data_dir / f"ocean_currents_{region}_2025.json"
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"Region {region} not found")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Get month index from date
    if date:
        try:
            dt = datetime.fromisoformat(date)
            month_idx = (dt.month - 10) if dt.year == 2025 else (dt.month + 2)
            month_idx = max(0, min(month_idx, len(data['data']) - 1))
        except:
            month_idx = 0
    else:
        month_idx = 0
    
    month_data = data['data'][month_idx]
    currents = month_data.get('currents', [])
    
    # Downsample to max 2000 vectors
    if len(currents) > 2000:
        step = len(currents) // 2000
        currents = currents[::step]
    
    return {
        "region": region,
        "date": month_data.get('date'),
        "currents": currents[:2000],
        "count": len(currents)
    }

class RouteRequestBody(BaseModel):
    start: Dict[str, float]
    end: Dict[str, float]
    ship: Dict[str, float]
    date: str
    wind: Optional[Dict[str, float]] = None

@app.post("/calculate-routes")
async def calculate_routes(request: RouteRequestBody):
    """Calculate safe navigation routes"""
    
    start_pos = (request.start['lat'], request.start['lon'])
    end_pos = (request.end['lat'], request.end['lon'])
    
    ship_config = ShipConfig(
        speed_knots=request.ship.get('speed_knots', 12.0)
    )
    
    try:
        date = datetime.fromisoformat(request.date)
    except:
        date = datetime.now()
    
    wind = None
    if request.wind:
        wind = (request.wind.get('speed', 0), request.wind.get('direction', 0))
    
    # Get current icebergs for routing
    icebergs = load_icebergs()
    iceberg_positions = [
        (ib.get('Lat') or ib.get('lat'), ib.get('Lon') or ib.get('lon'))
        for ib in icebergs
        if (ib.get('Lat') or ib.get('lat')) and (ib.get('Lon') or ib.get('lon'))
    ]
    
    routes = routing_engine.calculate_routes(
        start=start_pos,
        end=end_pos,
        ship=ship_config,
        date=date,
        icebergs=iceberg_positions,
        wind=wind
    )
    
    return {"routes": routes, "count": len(routes)}

@app.get("/risk")
async def assess_risk(
    ship_lat: float = Query(..., description="Ship latitude"),
    ship_lon: float = Query(..., description="Ship longitude"),
    date: Optional[str] = Query(None, description="Date")
):
    """Assess navigation risk at current position"""
    
    icebergs = load_icebergs()
    
    try:
        current_date = datetime.fromisoformat(date) if date else datetime.now()
    except:
        current_date = datetime.now()
    
    # Calculate risk based on proximity to icebergs
    min_distance = float('inf')
    nearest_iceberg = None
    reasons = []
    
    for iceberg in icebergs:
        lat = iceberg.get('Lat') or iceberg.get('lat')
        lon = iceberg.get('Lon') or iceberg.get('lon')
        
        if lat and lon:
            from math import radians, sin, cos, sqrt, atan2
            R = 6371
            lat1, lon1, lat2, lon2 = map(radians, [ship_lat, ship_lon, lat, lon])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            if distance < min_distance:
                min_distance = distance
                nearest_iceberg = iceberg.get('Iceberg', 'Unknown')
    
    # Determine risk level
    if min_distance < 5:
        level = "RED"
        reasons.append(f"Iceberg {nearest_iceberg} within 5 km (distance: {min_distance:.1f} km)")
        reasons.append("IMMEDIATE DANGER - Change course immediately")
    elif min_distance < 10:
        level = "ORANGE"
        reasons.append(f"Iceberg {nearest_iceberg} within 10 km (distance: {min_distance:.1f} km)")
        reasons.append("High risk - Monitor closely and prepare evasive action")
    elif min_distance < 20:
        level = "YELLOW"
        reasons.append(f"Nearest iceberg {nearest_iceberg}: {min_distance:.1f} km away")
        reasons.append("Moderate risk - Maintain awareness")
    else:
        level = "GREEN"
        reasons.append(f"Clear navigation - Nearest iceberg: {min_distance:.1f} km")
        reasons.append("Low risk - Continue with standard monitoring")
    
    return {
        "level": level,
        "distance_km": round(min_distance, 2),
        "nearest_iceberg": nearest_iceberg,
        "reasons": reasons,
        "timestamp": current_date.isoformat()
    }

class AlertRequest(BaseModel):
    level: str
    position: Dict[str, float]
    details: Dict

@app.post("/alert")
async def send_alert(alert: AlertRequest):
    """Send simulated satellite alert"""
    
    # Log to alerts file
    alerts_path = Path(__file__).parent / "alerts.json"
    
    alert_data = {
        "timestamp": datetime.now().isoformat(),
        "level": alert.level,
        "position": alert.position,
        "details": alert.details,
        "recipients": [
            "Mission Control - McMurdo Station",
            "Rescue Coordination Centre - Christchurch",
            "Ship Operator",
            "Family (if authorized)"
        ],
        "status": "SIMULATED",
        "delivery_method": "Satellite (Iridium)",
        "delivery_time_seconds": 2.3
    }
    
    # Append to alerts log
    alerts = []
    if alerts_path.exists():
        with open(alerts_path, 'r') as f:
            try:
                alerts = json.load(f)
            except:
                alerts = []
    
    alerts.append(alert_data)
    
    with open(alerts_path, 'w') as f:
        json.dump(alerts, f, indent=2)
    
    return {
        "success": True,
        "alert_id": len(alerts),
        "recipients": alert_data["recipients"],
        "timestamp": alert_data["timestamp"],
        "note": "SIMULATED ALERT - Not sent to real recipients"
    }

@app.get("/explain")
async def explain_route(route_id: str = Query(..., description="Route ID")):
    """Get plain-language explanation of route recommendation"""
    
    # Parse route type from ID
    route_type = route_id.split('_')[0] if '_' in route_id else route_id
    
    explanations = {
        "safest": {
            "summary": "This route maximizes distance from icebergs and ice fields.",
            "reasons": [
                "Maintains >15 km safety buffer from all predicted iceberg positions",
                "Avoids areas with ice concentration >40%",
                "Routes through well-monitored shipping lanes",
                "Adds 8% distance but reduces collision risk by 85%"
            ],
            "trade_offs": {
                "extra_distance_km": 12.4,
                "extra_time_hours": 1.2,
                "extra_fuel_percent": 8,
                "risk_reduction_percent": 85
            }
        },
        "fastest": {
            "summary": "This route minimizes travel time using direct path where safe.",
            "reasons": [
                "Direct bearing between start and end points",
                "Maintains minimum 10 km iceberg clearance",
                "Optimized for 12-knot cruising speed",
                "Baseline route for time and fuel comparison"
            ],
            "trade_offs": {
                "extra_distance_km": 0,
                "extra_time_hours": 0,
                "extra_fuel_percent": 0,
                "risk_reduction_percent": 60
            }
        },
        "fuel": {
            "summary": "This route balances safety and fuel efficiency using ocean currents.",
            "reasons": [
                "Leverages favorable ocean currents (0.3-0.5 m/s boost)",
                "Maintains 12 km average iceberg clearance",
                "Reduces fuel consumption by optimizing speed zones",
                "Best option when time is flexible but fuel is constrained"
            ],
            "trade_offs": {
                "extra_distance_km": 5.2,
                "extra_time_hours": 0.6,
                "extra_fuel_percent": -12,
                "risk_reduction_percent": 75
            }
        }
    }
    
    explanation = explanations.get(route_type, explanations["safest"])
    
    return {
        "route_id": route_id,
        "route_type": route_type,
        **explanation,
        "confidence": "High",
        "data_sources": [
            "BYU Antarctic Iceberg Tracking Database (real positions)",
            "Copernicus Marine Service ocean currents (monthly, Oct 2025 - Aug 2026)",
            "Physics-based drift model with Monte Carlo uncertainty",
            "SIMULATED ice concentration field (demo data)"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
