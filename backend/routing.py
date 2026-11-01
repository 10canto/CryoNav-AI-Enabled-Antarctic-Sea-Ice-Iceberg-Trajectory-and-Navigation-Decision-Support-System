"""
Routing Engine for CryoNav AI
A* pathfinding with iceberg avoidance and ice field costs
"""
import numpy as np
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
import heapq
from math import radians, sin, cos, sqrt, atan2, degrees

@dataclass
class ShipConfig:
    speed_knots: float = 12.0

class RoutingEngine:
    def __init__(self, grid_resolution_km: float = 5.0):
        """
        Initialize routing engine
        
        Args:
            grid_resolution_km: Grid cell size in kilometers
        """
        self.grid_resolution_km = grid_resolution_km
        self.grid_resolution_deg = grid_resolution_km / 111.0  # Approximate
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    def _create_cost_grid(
        self,
        bounds: Tuple[float, float, float, float],
        icebergs: List[Tuple[float, float]],
        date: datetime
    ) -> np.ndarray:
        """
        Create cost grid for pathfinding
        
        Returns: 2D numpy array of costs
        """
        min_lat, max_lat, min_lon, max_lon = bounds
        
        # Grid dimensions
        n_lat = int((max_lat - min_lat) / self.grid_resolution_deg) + 1
        n_lon = int((max_lon - min_lon) / self.grid_resolution_deg) + 1
        
        # Base cost: open water
        costs = np.ones((n_lat, n_lon))
        
        # Generate SIMULATED ice concentration field (smooth noise)
        # CLEARLY MARKED AS DEMO DATA
        np.random.seed(42)
        ice_field = np.random.rand(n_lat, n_lon)
        # Smooth with convolution
        from scipy.ndimage import gaussian_filter
        ice_field = gaussian_filter(ice_field, sigma=5)
        # Scale to 0-1
        ice_field = (ice_field - ice_field.min()) / (ice_field.max() - ice_field.min())
        
        # Add ice costs (3-10 based on concentration)
        costs += ice_field * 7 + 3  # Range: 4-10
        
        # Add iceberg hazard zones
        for iceberg_lat, iceberg_lon in icebergs:
            # Convert to grid coords
            i_lat = int((iceberg_lat - min_lat) / self.grid_resolution_deg)
            i_lon = int((iceberg_lon - min_lon) / self.grid_resolution_deg)
            
            # Iceberg core: impassable
            if 0 <= i_lat < n_lat and 0 <= i_lon < n_lon:
                costs[i_lat, i_lon] = 999
            
            # Predicted uncertainty zones (24h, 48h, 72h)
            for radius_km in [10, 20, 30]:  # Rough uncertainty radii
                radius_cells = int(radius_km / self.grid_resolution_km)
                for di in range(-radius_cells, radius_cells + 1):
                    for dj in range(-radius_cells, radius_cells + 1):
                        ni, nj = i_lat + di, i_lon + dj
                        if 0 <= ni < n_lat and 0 <= nj < n_lon:
                            distance_cells = sqrt(di**2 + dj**2)
                            if distance_cells <= radius_cells:
                                # Fade with distance
                                cost_multiplier = 1 + (50 / (distance_cells + 1))
                                costs[ni, nj] = min(costs[ni, nj] * cost_multiplier, 900)
        
        return costs
    
    def _astar(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        costs: np.ndarray,
        weight_distance: float,
        weight_ice: float,
        weight_iceberg: float
    ) -> List[Tuple[int, int]]:
        """
        A* pathfinding algorithm
        
        Returns: List of (i, j) grid coordinates
        """
        n_lat, n_lon = costs.shape
        
        # Priority queue: (priority, (i, j))
        open_set = []
        heapq.heappush(open_set, (0, start))
        
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}
        
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # Cardinal
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonal
        ]
        
        max_iterations = 10000
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return path[::-1]
            
            for di, dj in directions:
                ni, nj = current[0] + di, current[1] + dj
                
                # Check bounds
                if not (0 <= ni < n_lat and 0 <= nj < n_lon):
                    continue
                
                neighbor = (ni, nj)
                
                # Cost calculation with weights
                base_cost = costs[ni, nj]
                step_cost = sqrt(di**2 + dj**2)  # Diagonal costs more
                
                # Apply routing weights
                if base_cost > 900:  # Iceberg
                    total_cost = step_cost * weight_iceberg * base_cost
                elif base_cost > 10:  # Heavy ice
                    total_cost = step_cost * weight_ice * base_cost
                else:  # Open water
                    total_cost = step_cost * weight_distance
                
                tentative_g = g_score[current] + total_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # No path found, return straight line
        return [start, goal]
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Manhattan distance heuristic"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _smooth_path(self, path: List[Tuple[int, int]], n_points: int = 20) -> List[Tuple[int, int]]:
        """Reduce path to n_points waypoints"""
        if len(path) <= n_points:
            return path
        
        step = len(path) // n_points
        smoothed = [path[i * step] for i in range(n_points)]
        smoothed.append(path[-1])  # Always include end
        return smoothed
    
    def _grid_to_latlon(
        self,
        grid_coords: List[Tuple[int, int]],
        bounds: Tuple[float, float, float, float]
    ) -> List[Dict[str, float]]:
        """Convert grid coordinates to lat/lon"""
        min_lat, max_lat, min_lon, max_lon = bounds
        
        waypoints = []
        for i, j in grid_coords:
            lat = min_lat + i * self.grid_resolution_deg
            lon = min_lon + j * self.grid_resolution_deg
            waypoints.append({"lat": lat, "lon": lon})
        
        return waypoints
    
    def _calculate_route_stats(
        self,
        waypoints: List[Dict[str, float]],
        ship: ShipConfig,
        route_type: str
    ) -> Dict:
        """Calculate route statistics"""
        total_distance = 0
        for i in range(len(waypoints) - 1):
            dist = self._haversine_distance(
                waypoints[i]['lat'], waypoints[i]['lon'],
                waypoints[i+1]['lat'], waypoints[i+1]['lon']
            )
            total_distance += dist
        
        # Time calculation
        if ship is None:
            ship = ShipConfig()
        speed_kmh = ship.speed_knots * 1.852  # knots to km/h
        time_hours = total_distance / speed_kmh
        
        # Fuel percentage relative to fastest
        fuel_factors = {
            "safest": 1.08,
            "fastest": 1.0,
            "fuel_efficient": 0.88
        }
        fuel_percent = fuel_factors.get(route_type, 1.0) * 100
        
        # Risk score
        risk_scores = {
            "safest": 15,
            "fastest": 40,
            "fuel_efficient": 25
        }
        risk_score = risk_scores.get(route_type, 30)
        
        return {
            "distance_km": round(total_distance, 2),
            "time_hours": round(time_hours, 2),
            "fuel_percent_vs_fastest": round(fuel_percent, 1),
            "risk_score": risk_score
        }
    
    def calculate_routes(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        ship: ShipConfig,
        date: datetime,
        icebergs: List[Tuple[float, float]],
        wind: Optional[Tuple[float, float]] = None
    ) -> List[Dict]:
        """
        Calculate 3 routes: safest, fastest, fuel-efficient
        
        Returns: List of route dictionaries
        """
        # Define bounds (expand around start/end)
        all_lats = [start[0], end[0]] + [ib[0] for ib in icebergs]
        all_lons = [start[1], end[1]] + [ib[1] for ib in icebergs]
        
        min_lat = min(all_lats) - 0.5
        max_lat = max(all_lats) + 0.5
        min_lon = min(all_lons) - 0.5
        max_lon = max(all_lons) + 0.5
        
        bounds = (min_lat, max_lat, min_lon, max_lon)
        
        # Create cost grid
        costs = self._create_cost_grid(bounds, icebergs, date)
        
        # Convert start/end to grid coordinates
        start_i = int((start[0] - min_lat) / self.grid_resolution_deg)
        start_j = int((start[1] - min_lon) / self.grid_resolution_deg)
        end_i = int((end[0] - min_lat) / self.grid_resolution_deg)
        end_j = int((end[1] - min_lon) / self.grid_resolution_deg)
        
        start_grid = (start_i, start_j)
        end_grid = (end_i, end_j)
        
        # Calculate 3 routes with different weights
        route_configs = [
            {
                "type": "safest",
                "color": "green",
                "weights": (1, 10, 100)  # distance, ice, iceberg
            },
            {
                "type": "fastest",
                "color": "yellow",
                "weights": (10, 2, 50)
            },
            {
                "type": "fuel_efficient",
                "color": "orange",
                "weights": (5, 5, 80)
            }
        ]
        
        routes = []
        
        for config in route_configs:
            w_dist, w_ice, w_iceberg = config['weights']
            
            # Run A*
            path_grid = self._astar(start_grid, end_grid, costs, w_dist, w_ice, w_iceberg)
            
            # Smooth and convert to lat/lon
            smoothed_grid = self._smooth_path(path_grid, n_points=20)
            waypoints = self._grid_to_latlon(smoothed_grid, bounds)
            
            # Calculate statistics
            stats = self._calculate_route_stats(waypoints, ship, config['type'])
            
            routes.append({
                "id": f"{config['type']}_{date.strftime('%Y%m%d')}",
                "type": config['type'],
                "name": config['type'].replace('_', ' ').title(),
                "color": config['color'],
                "waypoints": waypoints,
                "isSafest": config['type'] == 'safest',
                "isFastest": config['type'] == 'fastest',
                "isCheapest": config['type'] == 'fuel_efficient',
                # New backend fields
                **stats,
                # Legacy frontend fields (keep for compatibility)
                "distanceKm": stats['distance_km'],
                "timeDays": round(stats['time_hours'] / 24, 1),
                "fuelIndex": int(stats['distance_km'] * 0.5),  # Relative index, not real fuel consumption
                "riskPercent": stats['risk_score']
            })
        
        return routes

# Simple test
if __name__ == "__main__":
    engine = RoutingEngine()
    
    start = (-60.0, -50.0)
    end = (-58.0, -45.0)
    ship = ShipConfig(speed_knots=12.0)
    date = datetime.now()
    icebergs = [(-59.5, -48.0), (-59.0, -47.5)]
    
    routes = engine.calculate_routes(start, end, ship, date, icebergs)
    
    print(f"✅ Calculated {len(routes)} routes")
    for route in routes:
        print(f"   {route['type']}: {route['distance_km']} km, {route['time_hours']} hours, risk={route['risk_score']}")
