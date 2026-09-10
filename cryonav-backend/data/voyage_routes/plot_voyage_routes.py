"""Plot a generated demo scenario: python plot_voyage_routes.py 0"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

ROOT = Path(__file__).parent
SCENARIO = int(sys.argv[1]) if len(sys.argv) > 1 else 0
DATA = json.loads((ROOT / f"routes_scenario_{SCENARIO}.json").read_text(encoding="utf-8"))
COLORS = {"safest": "#22a06b", "fastest": "#d9a400", "fuel_efficient": "#e36f1e"}

fig = plt.figure(figsize=(14, 10))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([-10, 100, -78, 18], crs=ccrs.PlateCarree())
ax.add_feature(cfeature.LAND, facecolor="#d9d4c7")
ax.add_feature(cfeature.OCEAN, facecolor="#dceef6")
ax.coastlines(resolution="110m", linewidth=0.6)
ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.6)

for hazard in DATA.get("hazard_zones", []):
    bounds = hazard.get("bounds")
    if bounds:
        lat, lon = bounds["lat"], bounds["lon"]
        ax.fill([lon[0], lon[1], lon[1], lon[0]], [lat[0], lat[0], lat[1], lat[1]], color="#d94b45", alpha=0.18, transform=ccrs.PlateCarree())
        ax.text(sum(lon) / 2, sum(lat) / 2, hazard["name"], fontsize=7, ha="center", transform=ccrs.PlateCarree())

for route in DATA["routes"]:
    points = route["waypoints"]
    lats, lons = [p["lat"] for p in points], [p["lon"] for p in points]
    label = f"{route['name']} — {route['distance_km']:,} km | {route['duration_days']} d | {route['fuel_liters']:,} L"
    ax.plot(lons, lats, color=COLORS[route["type"]], linewidth=2.5, marker="o", markersize=3, label=label, transform=ccrs.PlateCarree())
    for point in points:
        ax.text(point["lon"], point["lat"], str(point["seq"]), fontsize=6, transform=ccrs.PlateCarree())

for key, marker in (("start", "s"), ("end", "*")):
    point = DATA["voyage_info"][key]
    ax.scatter(point["lon"], point["lat"], marker=marker, s=90, color="#173f5f", zorder=5, transform=ccrs.PlateCarree())
    ax.text(point["lon"] + 1, point["lat"] + 1, point["name"], fontsize=8, transform=ccrs.PlateCarree())

ax.set_title(f"Chennai → Maitri Research Expedition — Scenario {SCENARIO}\nDEMO ONLY: not for navigation")
ax.legend(loc="lower left", fontsize=8)
output = ROOT / f"route_map_scenario_{SCENARIO}.png"
plt.savefig(output, dpi=220, bbox_inches="tight")
print(f"Saved {output}")
