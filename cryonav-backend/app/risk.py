"""
Risk Assessment Rules for CryoNav AI
Real risk calculation logic based on distance and collision probability.
"""
from typing import Tuple, List, Optional
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    RED = "RED"
    ORANGE = "ORANGE"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


def calculate_risk_level(
    distance_km: float,
    collision_probability: float,
    ice_concentration: Optional[float] = None
) -> Tuple[RiskLevel, List[str]]:
    """
    Calculate risk level based on distance and collision probability.
    
    Real risk assessment rules:
    - RED: Immediate danger (>80% collision probability OR <5 km distance)
    - ORANGE: High risk (<10 km distance OR >50% collision probability)
    - YELLOW: Moderate risk (<20 km distance OR ice concentration >60%)
    - GREEN: Low risk (all other cases)
    
    Args:
        distance_km (float): Distance to nearest iceberg in kilometers
        collision_probability (float): Collision probability as a decimal (0.0 to 1.0)
        ice_concentration (Optional[float]): Ice concentration percentage (0-100)
        
    Returns:
        Tuple[RiskLevel, List[str]]: Risk level and list of reasons
        
    Examples:
        >>> calculate_risk_level(3.5, 0.85)
        (RiskLevel.RED, ['Immediate danger: Distance <5 km (3.5 km)', ...])
        
        >>> calculate_risk_level(8.2, 0.45)
        (RiskLevel.ORANGE, ['High risk: Distance <10 km (8.2 km)', ...])
        
        >>> calculate_risk_level(15.0, 0.30, ice_concentration=65)
        (RiskLevel.YELLOW, ['Moderate risk: Distance <20 km (15.0 km)', ...])
        
        >>> calculate_risk_level(35.0, 0.10)
        (RiskLevel.GREEN, ['Low risk: Distance >20 km (35.0 km)', ...])
    """
    reasons = []
    
    # Convert probability to percentage for comparison
    collision_percent = collision_probability * 100
    
    # RED: Immediate danger
    if collision_probability > 0.80 or distance_km < 5.0:
        if collision_probability > 0.80:
            reasons.append(
                f"Immediate danger: Collision probability >{collision_percent:.0f}% ({collision_percent:.1f}%)"
            )
        if distance_km < 5.0:
            reasons.append(f"Immediate danger: Distance <5 km ({distance_km:.1f} km)")
        reasons.append("CRITICAL: Take evasive action immediately")
        reasons.append("Recommend full stop or emergency course change")
        return RiskLevel.RED, reasons
    
    # ORANGE: High risk
    if distance_km < 10.0 or collision_probability > 0.50:
        if distance_km < 10.0:
            reasons.append(f"High risk: Distance <10 km ({distance_km:.1f} km)")
        if collision_probability > 0.50:
            reasons.append(
                f"High risk: Collision probability >{collision_percent:.0f}% ({collision_percent:.1f}%)"
            )
        reasons.append("WARNING: Prepare evasive maneuvers")
        reasons.append("Increase monitoring frequency")
        reasons.append("Brief crew on emergency procedures")
        return RiskLevel.ORANGE, reasons
    
    # YELLOW: Moderate risk
    if distance_km < 20.0 or (ice_concentration is not None and ice_concentration > 60.0):
        if distance_km < 20.0:
            reasons.append(f"Moderate risk: Distance <20 km ({distance_km:.1f} km)")
        if ice_concentration is not None and ice_concentration > 60.0:
            reasons.append(f"Moderate risk: Ice concentration >{ice_concentration:.0f}%")
        reasons.append("CAUTION: Maintain heightened awareness")
        reasons.append("Monitor iceberg drift trajectory")
        reasons.append("Review alternative routes")
        return RiskLevel.YELLOW, reasons
    
    # GREEN: Low risk
    reasons.append(f"Low risk: Distance >{distance_km:.1f} km from nearest hazard")
    reasons.append(f"Collision probability: {collision_percent:.1f}%")
    reasons.append("Continue with standard monitoring procedures")
    reasons.append("Weather and ice conditions permitting")
    return RiskLevel.GREEN, reasons


def calculate_collision_probability(
    distance_km: float,
    iceberg_speed_ms: float = 0.3,
    time_horizon_hours: float = 24.0,
    uncertainty_radius_km: float = 5.0
) -> float:
    """
    Estimate collision probability based on distance and drift characteristics.
    
    Simplified collision probability model:
    - Closer distances -> higher probability
    - Faster iceberg drift -> higher probability
    - Greater uncertainty -> higher probability
    
    Args:
        distance_km (float): Current distance to iceberg
        iceberg_speed_ms (float): Iceberg drift speed in m/s (default: 0.3)
        time_horizon_hours (float): Time horizon for prediction (default: 24h)
        uncertainty_radius_km (float): Prediction uncertainty radius
        
    Returns:
        float: Collision probability (0.0 to 1.0)
        
    Note:
        This is a simplified model. Production would use Monte Carlo simulation
        with full physics-based drift prediction.
    """
    # Convert speed to km/h
    iceberg_speed_kmh = iceberg_speed_ms * 3.6
    
    # Maximum distance iceberg could travel
    max_travel_km = iceberg_speed_kmh * time_horizon_hours
    
    # Effective danger zone (distance - travel + uncertainty)
    danger_zone_km = distance_km - max_travel_km + uncertainty_radius_km
    
    # If danger zone is negative, high collision risk
    if danger_zone_km <= 0:
        return min(0.95, 1.0 + (danger_zone_km / 10.0))
    
    # Exponential decay with distance
    # At 5km: ~75%, at 10km: ~50%, at 20km: ~25%, at 40km: ~10%
    probability = 0.95 * (2.71828 ** (-danger_zone_km / 15.0))
    
    return max(0.0, min(1.0, probability))


def calculate_safe_distance(
    iceberg_size_meters: float,
    ship_speed_knots: float = 12.0,
    reaction_time_minutes: float = 30.0
) -> float:
    """
    Calculate minimum safe distance based on iceberg size and ship characteristics.
    
    Args:
        iceberg_size_meters (float): Iceberg length/width (use larger dimension)
        ship_speed_knots (float): Ship speed in knots
        reaction_time_minutes (float): Time needed to react and maneuver
        
    Returns:
        float: Minimum safe distance in kilometers
        
    Formula:
        safe_distance = 3 * iceberg_size + (ship_speed * reaction_time)
    """
    # Convert ship speed to km/h
    ship_speed_kmh = ship_speed_knots * 1.852
    
    # Distance traveled during reaction time
    reaction_distance_km = (ship_speed_kmh / 60.0) * reaction_time_minutes
    
    # Safety buffer (3x iceberg size)
    iceberg_buffer_km = (3 * iceberg_size_meters) / 1000.0
    
    # Total safe distance
    safe_distance_km = iceberg_buffer_km + reaction_distance_km
    
    return safe_distance_km


def get_risk_color(level: RiskLevel) -> str:
    """
    Get color code for risk level (for UI rendering).
    
    Args:
        level (RiskLevel): Risk level
        
    Returns:
        str: Hex color code
    """
    colors = {
        RiskLevel.RED: "#DC2626",      # Red-600
        RiskLevel.ORANGE: "#F97316",   # Orange-500
        RiskLevel.YELLOW: "#EAB308",   # Yellow-500
        RiskLevel.GREEN: "#16A34A"     # Green-600
    }
    return colors.get(level, "#6B7280")  # Gray-500 fallback


def format_risk_message(level: RiskLevel, distance_km: float, probability: float) -> str:
    """
    Generate a human-readable risk message.
    
    Args:
        level (RiskLevel): Risk level
        distance_km (float): Distance to nearest hazard
        probability (float): Collision probability (0.0-1.0)
        
    Returns:
        str: Formatted risk message
    """
    messages = {
        RiskLevel.RED: f"EMERGENCY - Immediate danger at {distance_km:.1f} km ({probability*100:.0f}% collision risk)",
        RiskLevel.ORANGE: f"WARNING - Hazard approaching at {distance_km:.1f} km ({probability*100:.0f}% collision risk)",
        RiskLevel.YELLOW: f"CAUTION - Monitoring situation at {distance_km:.1f} km ({probability*100:.0f}% collision risk)",
        RiskLevel.GREEN: f"All clear - Nearest hazard at {distance_km:.1f} km ({probability*100:.0f}% collision risk)"
    }
    return messages.get(level, "Status UNKNOWN")


# Example usage and testing
if __name__ == "__main__":
    print("=== CryoNav Risk Assessment Rules ===\n")
    
    # Test cases
    test_cases = [
        (3.2, 0.87, 75, "Scenario 3: Imminent collision"),
        (8.5, 0.55, 68, "Scenario 2: Approaching hazard"),
        (15.0, 0.30, 65, "Scenario 1: Moderate ice concentration"),
        (45.0, 0.12, 35, "Scenario 0: Safe conditions"),
    ]
    
    for distance, prob, ice_conc, description in test_cases:
        level, reasons = calculate_risk_level(distance, prob, ice_conc)
        print(f"{description}")
        print(f"  Distance: {distance} km")
        print(f"  Probability: {prob*100:.0f}%")
        print(f"  Ice Conc: {ice_conc}%")
        print(f"  → Risk Level: {level.value}")
        print(f"  → Reasons:")
        for reason in reasons:
            print(f"      - {reason}")
        print()
