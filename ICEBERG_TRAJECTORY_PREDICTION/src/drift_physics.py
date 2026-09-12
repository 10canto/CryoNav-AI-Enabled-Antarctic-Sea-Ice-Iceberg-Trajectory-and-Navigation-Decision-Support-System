"""
FILE 2: src/drift_physics.py
Physics-based Antarctic Iceberg Drift Prediction

Implements:
  DriftPredictor   — deterministic + Monte Carlo ensemble prediction
  EnvironmentalData — realistic Antarctic Peninsula conditions
"""

import numpy as np
from datetime import datetime, timedelta


# Physical constants
EARTH_OMEGA  = 7.2921e-5    # Earth rotation rate (rad/s)
DEG_TO_M     = 111_000.0    # metres per degree latitude
OCEAN_FACTOR = 0.60         # fraction of ocean current applied to drift
WIND_FACTOR  = 0.028        # fraction of wind speed applied to drift
CORIOLIS_W   = 0.10         # weight of Coriolis correction term


class DriftPredictor:
    """
    Physics-based iceberg drift prediction engine.

    Drift equation (per time step):
        u_drift = OCEAN_FACTOR * u_ocean + WIND_FACTOR * u_wind
        v_drift = OCEAN_FACTOR * v_ocean + WIND_FACTOR * v_wind
        + Coriolis deflection (left-hand turn in Southern Hemisphere)
    """

    def predict_trajectory(
        self,
        lat: float,
        lon: float,
        ocean_current: dict,
        wind: dict,
        hours: int = 72,
    ) -> list:
        """
        Deterministic trajectory at 6-hour intervals.

        Args:
            lat, lon:      Start position (degrees).
            ocean_current: {'u': east m/s, 'v': north m/s}.
            wind:          {'u': east m/s, 'v': north m/s}.
            hours:         Forecast horizon.

        Returns:
            List of {time_hours, latitude, longitude, timestamp} dicts
            at t = 0, 6, 12, 24, 48, 72 hours.
        """
        report_at = {0, 6, 12, 24, 48, 72}
        positions = []
        cur_lat, cur_lon = float(lat), float(lon)
        dt = 6 * 3600.0   # 6-hour step in seconds
        t0 = datetime.utcnow()

        for t_hr in range(0, hours + 6, 6):
            if t_hr in report_at:
                positions.append({
                    "time_hours": t_hr,
                    "latitude":   round(cur_lat, 6),
                    "longitude":  round(cur_lon, 6),
                    "timestamp":  (t0 + timedelta(hours=t_hr)).isoformat() + "Z",
                })
            if t_hr >= hours:
                break

            # Base drift
            f = 2.0 * EARTH_OMEGA * np.sin(np.radians(cur_lat))  # neg in SH
            u_base = OCEAN_FACTOR * ocean_current["u"] + WIND_FACTOR * wind["u"]
            v_base = OCEAN_FACTOR * ocean_current["v"] + WIND_FACTOR * wind["v"]

            # Coriolis correction (deflects left in Southern Hemisphere)
            u_total = u_base + (-f * v_base * dt * CORIOLIS_W)
            v_total = v_base + ( f * u_base * dt * CORIOLIS_W)

            # Convert m/s → degrees
            cos_lat = max(np.cos(np.radians(cur_lat)), 1e-6)
            cur_lat += (v_total * dt) / DEG_TO_M
            cur_lon += (u_total * dt) / (DEG_TO_M * cos_lat)

        return positions

    def predict_with_uncertainty(
        self,
        lat: float,
        lon: float,
        ocean_current: dict,
        wind: dict,
        hours: int = 72,
        n_simulations: int = 100,
    ) -> list:
        """
        Monte Carlo ensemble forecast with uncertainty quantification.

        Noise model:
          ocean current sigma = 0.15 m/s (OSCAR product error)
          wind speed sigma    = 0.80 m/s (ECMWF short-range error)

        Args:
            lat, lon:       Start position.
            ocean_current:  Best-estimate conditions.
            wind:           Best-estimate conditions.
            hours:          Forecast horizon.
            n_simulations:  Ensemble size.

        Returns:
            List of {time_hours, latitude, longitude, uncertainty_km, timestamp}.
        """
        rng        = np.random.default_rng(seed=42)
        key_times  = [0, 6, 12, 24, 48, 72]
        # each sim trajectory is a list of positions (index = key_time index)
        all_trajs  = []

        for _ in range(n_simulations):
            oc = {
                "u": ocean_current["u"] + rng.normal(0, 0.15),
                "v": ocean_current["v"] + rng.normal(0, 0.15),
            }
            wi = {
                "u": wind["u"] + rng.normal(0, 0.80),
                "v": wind["v"] + rng.normal(0, 0.80),
            }
            traj = self.predict_trajectory(lat, lon, oc, wi, hours)
            all_trajs.append(traj)

        # Aggregate
        t0 = datetime.utcnow()
        result = []
        for step_idx, t_hr in enumerate(key_times):
            if t_hr > hours:
                break
            lats = np.array([tr[step_idx]["latitude"]  for tr in all_trajs
                             if step_idx < len(tr)])
            lons = np.array([tr[step_idx]["longitude"] for tr in all_trajs
                             if step_idx < len(tr)])

            mean_lat = float(np.mean(lats))
            mean_lon = float(np.mean(lons))

            std_lat_km = float(np.std(lats)) * (DEG_TO_M / 1000.0)
            std_lon_km = (float(np.std(lons))
                          * DEG_TO_M
                          * abs(np.cos(np.radians(mean_lat)))
                          / 1000.0)
            unc_km = float(np.sqrt(std_lat_km**2 + std_lon_km**2))

            result.append({
                "time_hours":     t_hr,
                "latitude":       round(mean_lat, 6),
                "longitude":      round(mean_lon, 6),
                "uncertainty_km": round(unc_km, 2),
                "timestamp":      (t0 + timedelta(hours=t_hr)).isoformat() + "Z",
            })

        return result


class EnvironmentalData:
    """
    Provides realistic Antarctic Peninsula environmental conditions.

    In production this would query OSCAR (ocean) and ECMWF/GFS (wind).
    For the demo we use climatological means with small random perturbations.

    Typical Antarctic Peninsula values:
      Ocean: Antarctic Coastal Current 0.2–0.4 m/s eastward
      Wind:  Prevailing westerlies 8–12 m/s
    """

    def get_conditions_at(self, lat: float, lon: float) -> dict:
        """
        Return environmental conditions at (lat, lon).

        Returns:
            {ocean_current: {u,v}, wind: {u,v}, timestamp, data_source}
        """
        rng = np.random.default_rng(
            seed=int(abs(lat * 1000 + lon)) % (2**31)
        )

        ocean_current = {
            "u": round(float(0.28 + rng.normal(0, 0.06)),  3),  # eastward ACC
            "v": round(float(0.12 + rng.normal(0, 0.04)),  3),  # northward
        }
        wind = {
            "u": round(float(-9.5 + rng.normal(0, 1.5)), 3),    # westerlies
            "v": round(float(      rng.normal(0, 1.0)),  3),    # variable
        }

        return {
            "ocean_current": ocean_current,
            "wind":          wind,
            "data_source":   "Antarctic_Peninsula_climatology",
            "timestamp":     datetime.utcnow().isoformat() + "Z",
            "location":      {"latitude": lat, "longitude": lon},
        }


def drift_distance_km(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Equirectangular distance in km between two geographic points."""
    dlat = (lat2 - lat1) * DEG_TO_M
    dlon = ((lon2 - lon1)
            * DEG_TO_M
            * np.cos(np.radians((lat1 + lat2) / 2.0)))
    return round(float(np.sqrt(dlat**2 + dlon**2)) / 1000.0, 1)
