#!/usr/bin/env python3
"""
CryoNav AI - Antarctic Expedition Route Visualization Script
Plots 3 realistic navigation routes from Chennai Port, India to Maitri Station, Antarctica
Supports Matplotlib + Cartopy, with graceful fallback to pure Matplotlib / Standalone SVG generator.

Usage:
  python3 visualize_routes.py --scenario 0
  python3 visualize_routes.py --all
"""

import sys
import os
import json
import argparse

def load_scenario(scenario_idx):
    filename = f"routes_scenario_{scenario_idx}.json"
    if not os.path.exists(filename):
        # Check parent or current directory
        alt_filename = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(alt_filename):
            filename = alt_filename
        else:
            raise FileNotFoundError(f"Cannot find scenario file: {filename}")
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def plot_with_matplotlib(data, scenario_idx, output_png):
    """Plots using Matplotlib (and Cartopy if available)"""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    has_cartopy = False
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        has_cartopy = True
    except ImportError:
        pass

    fig = plt.figure(figsize=(16, 12), dpi=200, facecolor="#0f172a")
    
    if has_cartopy:
        proj = ccrs.PlateCarree()
        ax = fig.add_subplot(1, 1, 1, projection=proj)
        ax.set_extent([0, 100, -75, 20], crs=proj)
        ax.add_feature(cfeature.LAND, facecolor="#1e293b", edgecolor="#334155", linewidth=0.8)
        ax.add_feature(cfeature.OCEAN, facecolor="#0b1329")
        ax.add_feature(cfeature.COASTLINE, edgecolor="#475569", linewidth=1.0)
        ax.add_feature(cfeature.BORDERS, linestyle=":", edgecolor="#334155", alpha=0.5)
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, color="#334155", alpha=0.7, linestyle="--")
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"color": "#94a3b8", "size": 9}
        gl.ylabel_style = {"color": "#94a3b8", "size": 9}
    else:
        ax = fig.add_subplot(1, 1, 1)
        ax.set_facecolor("#0b1329")
        ax.set_xlim(0, 100)
        ax.set_ylim(-75, 20)
        ax.set_xlabel("Longitude (°E)", color="#94a3b8", fontsize=10)
        ax.set_ylabel("Latitude (°)", color="#94a3b8", fontsize=10)
        ax.tick_params(colors="#94a3b8", labelsize=9)
        ax.grid(True, linestyle="--", linewidth=0.5, color="#1e293b", alpha=0.8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#334155")

    # Draw Antarctic Pack Ice and Convergence latitude reference lines
    ax.axhline(y=-40, color="#38bdf8", linestyle=":", linewidth=0.8, alpha=0.5, label="_nolegend_")
    ax.text(3, -39.2, "Roaring Forties (40°S)", color="#38bdf8", fontsize=8, alpha=0.7)

    ax.axhline(y=-50, color="#38bdf8", linestyle=":", linewidth=0.8, alpha=0.5, label="_nolegend_")
    ax.text(3, -49.2, "Furious Fifties (50°S)", color="#38bdf8", fontsize=8, alpha=0.7)

    ax.axhline(y=-60, color="#06b6d4", linestyle="-.", linewidth=1.0, alpha=0.6, label="_nolegend_")
    ax.text(3, -59.2, "Antarctic Convergence / Polar Front (60°S)", color="#06b6d4", fontsize=8, fontweight="bold", alpha=0.8)

    # Shade Iceberg Alley Corridor (40°E to 60°E, 55°S to 62°S)
    alley_rect = plt.Rectangle((35, -62), 25, 7, facecolor="#38bdf8", alpha=0.12, edgecolor="#0284c7", linestyle="--", linewidth=1.2)
    ax.add_patch(alley_rect)
    ax.text(47.5, -57.5, "ICEBERG ALLEY\n(High Concentration)", color="#7dd3fc", fontsize=8, ha="center", va="center", fontweight="bold")

    # Mark key geographical hazard points
    # Prince Edward Islands
    ax.plot(37.8, -46.7, "o", color="#f59e0b", markersize=6)
    ax.text(39.0, -46.7, "Prince Edward Is.\n(46.7°S, 37.8°E)", color="#fbbf24", fontsize=7, va="center")

    # Bouvet Island
    ax.plot(3.4, -54.4, "o", color="#f59e0b", markersize=5)
    ax.text(4.5, -54.4, "Bouvet Island\n(54.4°S, 3.4°E)", color="#fbbf24", fontsize=7, va="center")

    # Scenario specific hazards
    if scenario_idx == 1:
        # ICE-TAB-2024-01
        ax.plot(42.0, -58.5, "s", color="#ef4444", markersize=10, markeredgecolor="#ffffff")
        ax.text(43.5, -58.5, "ALERT: ICE-TAB-2024-01\n(2.5 x 1.8 km Tabular Berg)\nDrift: NW @ 1.2 km/day", color="#fca5a5", fontsize=8, fontweight="bold")
    elif scenario_idx == 2:
        # Storm zone
        storm_rect = plt.Rectangle((30, -58), 20, 6, facecolor="#ef4444", alpha=0.18, edgecolor="#dc2626", linestyle=":", linewidth=1.5)
        ax.add_patch(storm_rect)
        ax.text(40.0, -55.0, "CYCLONE GALE ZONE\n(50-65 kts, Hs=11.5m)", color="#f87171", fontsize=9, ha="center", va="center", fontweight="bold")
    elif scenario_idx == 3:
        # Emergency ice block
        block_rect = plt.Rectangle((0, -71), 22, 3, facecolor="#ef4444", alpha=0.25, edgecolor="#b91c1c", linestyle="-", linewidth=1.8)
        ax.add_patch(block_rect)
        ax.text(11.0, -69.8, "CATASTROPHIC CALVING MELANGE\nDirect Approach Blocked", color="#fca5a5", fontsize=9, ha="center", va="center", fontweight="bold")
        # Escort rendezvous
        ax.plot(22.0, -68.5, "*", color="#38bdf8", markersize=12, markeredgecolor="#ffffff")
        ax.text(23.5, -68.5, "Icebreaker Escort Rendezvous\n(68.5°S, 22.0°E)", color="#38bdf8", fontsize=8, fontweight="bold")

    # Plot Routes
    legend_handles = []
    routes = data.get("routes", [])

    for r in routes:
        wps = r.get("waypoints", [])
        lats = [wp["lat"] for wp in wps]
        lons = [wp["lon"] for wp in wps]

        r_type = r.get("type", "safest")
        status = r.get("status", "")
        is_blocked = "BLOCKED" in status

        if is_blocked:
            color = "#ef4444"
            linestyle = ":"
            lw = 1.8
        elif r_type == "safest":
            color = "#10b981"
            linestyle = "-"
            lw = 2.8
        elif r_type == "fastest":
            color = "#f59e0b"
            linestyle = "--"
            lw = 2.4
        else: # fuel
            color = "#f97316"
            linestyle = "-."
            lw = 2.2

        line, = ax.plot(lons, lats, color=color, linestyle=linestyle, linewidth=lw, alpha=0.9)

        # Plot waypoints
        for wp in wps:
            seq = wp.get("seq", 0)
            ax.plot(wp["lon"], wp["lat"], "o", color=color, markersize=3.5, markeredgecolor="#0f172a", markeredgewidth=0.5)
            # Label selected anchor waypoints
            if seq in [1, 2, 7, 10, len(wps)]:
                ax.text(wp["lon"] + 1.2, wp["lat"] - 0.5, f"W{seq}", color=color, fontsize=6.5, alpha=0.85)

        # Legend label with stats
        dist = r.get("distance_km", 0)
        days = r.get("duration_days", 0)
        fuel = r.get("fuel_liters", 0)
        risk = r.get("risk_score", 0)

        if is_blocked:
            label = f"{r.get('name')}\n  [BLOCKED] Risk: {risk}% | Passage Terminated"
        else:
            label = f"{r.get('name')}\n  Dist: {dist:,} km | {days}d | Fuel: {fuel:,} L | Risk: {risk}%"

        legend_handles.append(mpatches.Patch(color=color, label=label))

    # Mark Start and End Points
    vinfo = data.get("voyage_info", {})
    start = vinfo.get("start", {})
    end = vinfo.get("end", {})

    # Start: Chennai
    ax.plot(start["lon"], start["lat"], "p", color="#38bdf8", markersize=12, markeredgecolor="#ffffff", markeredgewidth=1.5)
    ax.text(start["lon"] - 2, start["lat"] + 1.5, f"START: {start['name']}\n(13.08°N, 80.27°E)", color="#e0f2fe", fontsize=9, fontweight="bold", ha="right")

    # End: Maitri
    ax.plot(end["lon"], end["lat"], "D", color="#ec4899", markersize=10, markeredgecolor="#ffffff", markeredgewidth=1.5)
    ax.text(end["lon"] + 2, end["lat"] - 1.5, f"DESTINATION: {end['name']}\n(70.76°S, 11.74°E)", color="#fbcfe8", fontsize=9, fontweight="bold")

    # Title & Metadata
    meta = data.get("metadata", {})
    title = f"INDIAN ANTARCTIC EXPEDITION - VOYAGE ROUTING SYSTEM\nScenario {scenario_idx}: {meta.get('scenario_name', '')}"
    fig.suptitle(title, color="#f8fafc", fontsize=14, fontweight="bold", y=0.96)

    # Subtitle
    subtitle = f"Vessel: {meta.get('ship_name', 'R/V Bharati Pioneer')} (1A Ice Class) | Season: {meta.get('season', 'Austral Summer')}"
    ax.set_title(subtitle, color="#94a3b8", fontsize=10, pad=10)

    # Legend
    leg = ax.legend(handles=legend_handles, loc="upper right", facecolor="#1e293b", edgecolor="#334155", fontsize=8.5, labelcolor="#e2e8f0", framealpha=0.95)
    for text in leg.get_texts():
        text.set_color("#f1f5f9")

    plt.tight_layout()
    plt.subplots_adjust(top=0.90)
    plt.savefig(output_png, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"✓ Saved route map image: {output_png}")

def generate_svg_fallback(data, scenario_idx, output_svg):
    """Self-contained SVG generator if matplotlib is not available"""
    width = 1200
    height = 900
    # Map bounds: Lon 0 to 100 -> X 100 to 1100; Lat 20 to -75 -> Y 80 to 820
    def lon_to_x(lon):
        return 100 + (lon / 100.0) * 1000.0

    def lat_to_y(lat):
        # lat 20 -> y=80, lat -75 -> y=820
        return 80 + ((20.0 - lat) / 95.0) * 740.0

    routes = data.get("routes", [])
    meta = data.get("metadata", {})
    vinfo = data.get("voyage_info", {})
    start = vinfo.get("start", {"lat": 13.0827, "lon": 80.2707, "name": "Chennai Port, India"})
    end = vinfo.get("end", {"lat": -70.7644, "lon": 11.7386, "name": "Maitri Station, Antarctica"})

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append('<rect width="100%" height="100%" fill="#0b1329"/>')

    # Grid lines
    for lat in [10, 0, -10, -20, -30, -40, -50, -60, -70]:
        y = lat_to_y(lat)
        svg.append(f'<line x1="100" y1="{y}" x2="1100" y2="{y}" stroke="#1e293b" stroke-dasharray="4,4" stroke-width="1"/>')
        label = f"{abs(lat)}°{'S' if lat < 0 else 'N' if lat > 0 else 'EQ'}"
        if lat == -40: label += " (Roaring Forties)"
        elif lat == -50: label += " (Furious Fifties)"
        elif lat == -60: label += " (Convergence / Polar Front)"
        svg.append(f'<text x="105" y="{y - 4}" fill="#64748b" font-family="monospace" font-size="10">{label}</text>')

    for lon in [20, 40, 60, 80, 100]:
        x = lon_to_x(lon)
        svg.append(f'<line x1="{x}" y1="80" x2="{x}" y2="820" stroke="#1e293b" stroke-dasharray="4,4" stroke-width="1"/>')
        svg.append(f'<text x="{x}" y="835" fill="#64748b" font-family="monospace" font-size="10" text-anchor="middle">{lon}°E</text>')

    # Iceberg Alley highlight
    ax1, ay1 = lon_to_x(35), lat_to_y(-55)
    ax2, ay2 = lon_to_x(60), lat_to_y(-62)
    svg.append(f'<rect x="{ax1}" y="{ay1}" width="{ax2-ax1}" height="{ay2-ay1}" fill="#0284c7" fill-opacity="0.12" stroke="#0284c7" stroke-dasharray="6,4" stroke-width="1.5"/>')
    svg.append(f'<text x="{(ax1+ax2)/2}" y="{(ay1+ay2)/2}" fill="#38bdf8" font-family="sans-serif" font-size="11" font-weight="bold" text-anchor="middle">ICEBERG ALLEY (40-60°E)</text>')

    # Scenario specific highlights
    if scenario_idx == 1:
        ix, iy = lon_to_x(42.0), lat_to_y(-58.5)
        svg.append(f'<circle cx="{ix}" cy="{iy}" r="9" fill="#ef4444" stroke="#ffffff" stroke-width="2"/>')
        svg.append(f'<text x="{ix + 15}" y="{iy + 4}" fill="#fca5a5" font-family="sans-serif" font-size="11" font-weight="bold">ICE-TAB-2024-01 (2.5km x 1.8km)</text>')
    elif scenario_idx == 2:
        sx1, sy1 = lon_to_x(30.0), lat_to_y(-52.0)
        sx2, sy2 = lon_to_x(50.0), lat_to_y(-58.0)
        svg.append(f'<rect x="{sx1}" y="{sy1}" width="{sx2-sx1}" height="{sy2-sy1}" fill="#ef4444" fill-opacity="0.18" stroke="#dc2626" stroke-dasharray="4,4" stroke-width="2"/>')
        svg.append(f'<text x="{(sx1+sx2)/2}" y="{(sy1+sy2)/2}" fill="#f87171" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="middle">CYCLONE GALE (50-65 kts, Hs=11.5m)</text>')
    elif scenario_idx == 3:
        bx1, by1 = lon_to_x(0.0), lat_to_y(-68.0)
        bx2, by2 = lon_to_x(20.0), lat_to_y(-71.0)
        svg.append(f'<rect x="{bx1}" y="{by1}" width="{bx2-bx1}" height="{by2-by1}" fill="#ef4444" fill-opacity="0.25" stroke="#b91c1c" stroke-width="2"/>')
        svg.append(f'<text x="{(bx1+bx2)/2}" y="{(by1+by2)/2}" fill="#fca5a5" font-family="sans-serif" font-size="11" font-weight="bold" text-anchor="middle">CALVING MELANGE BLOCKADE</text>')

    # Plot routes
    for r in routes:
        wps = r.get("waypoints", [])
        if not wps: continue
        r_type = r.get("type", "safest")
        is_blocked = "BLOCKED" in r.get("status", "")

        color = "#ef4444" if is_blocked else ("#10b981" if r_type == "safest" else "#f59e0b" if r_type == "fastest" else "#f97316")
        dash = "none" if (not is_blocked and r_type == "safest") else ("8,4" if r_type == "fastest" else "3,3")
        width_px = 3.5 if r_type == "safest" else 2.5

        pts = " ".join([f"{lon_to_x(wp['lon'])},{lat_to_y(wp['lat'])}" for wp in wps])
        svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width_px}" stroke-dasharray="{dash}" opacity="0.9"/>')

        for wp in wps:
            wx, wy = lon_to_x(wp["lon"]), lat_to_y(wp["lat"])
            svg.append(f'<circle cx="{wx}" cy="{wy}" r="3.5" fill="{color}" stroke="#0b1329" stroke-width="1"/>')

    # Start / End markers
    sx, sy = lon_to_x(start["lon"]), lat_to_y(start["lat"])
    svg.append(f'<circle cx="{sx}" cy="{sy}" r="7" fill="#38bdf8" stroke="#ffffff" stroke-width="2"/>')
    svg.append(f'<text x="{sx - 15}" y="{sy - 8}" fill="#e0f2fe" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="end">CHENNAI PORT (START)</text>')

    ex, ey = lon_to_x(end["lon"]), lat_to_y(end["lat"])
    svg.append(f'<polygon points="{ex},{ey-8} {ex+8},{ey} {ex},{ey+8} {ex-8},{ey}" fill="#ec4899" stroke="#ffffff" stroke-width="2"/>')
    svg.append(f'<text x="{ex + 15}" y="{ey + 4}" fill="#fbcfe8" font-family="sans-serif" font-size="12" font-weight="bold">MAITRI STATION (ANTARCTICA)</text>')

    # Title
    svg.append(f'<text x="600" y="40" fill="#f8fafc" font-family="sans-serif" font-size="18" font-weight="bold" text-anchor="middle">INDIAN ANTARCTIC EXPEDITION - SCENARIO {scenario_idx}: {meta.get("scenario_name", "")}</text>')

    # Legend Box
    svg.append(f'<rect x="750" y="90" width="340" height="150" rx="8" fill="#1e293b" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>')
    ly = 115
    for r in routes:
        r_type = r.get("type", "safest")
        is_blocked = "BLOCKED" in r.get("status", "")
        color = "#ef4444" if is_blocked else ("#10b981" if r_type == "safest" else "#f59e0b" if r_type == "fastest" else "#f97316")
        name = r.get("name")
        dist = r.get("distance_km", 0)
        days = r.get("duration_days", 0)
        risk = r.get("risk_score", 0)
        svg.append(f'<circle cx="765" cy="{ly}" r="5" fill="{color}"/>')
        svg.append(f'<text x="780" y="{ly + 4}" fill="#f1f5f9" font-family="sans-serif" font-size="10" font-weight="bold">{name}</text>')
        if is_blocked:
            svg.append(f'<text x="780" y="{ly + 17}" fill="#ef4444" font-family="monospace" font-size="9">[BLOCKED] Risk: {risk}%</text>')
        else:
            svg.append(f'<text x="780" y="{ly + 17}" fill="#94a3b8" font-family="monospace" font-size="9">{dist:,} km | {days}d | Risk: {risk}%</text>')
        ly += 42

    svg.append('</svg>')

    with open(output_svg, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print(f"✓ Generated SVG route map: {output_svg}")

def main():
    parser = argparse.ArgumentParser(description="Visualize India-Antarctica Expedition Routes")
    parser.add_argument("--scenario", type=int, default=0, choices=[0, 1, 2, 3], help="Scenario index (0 to 3)")
    parser.add_argument("--all", action="store_true", help="Generate maps for all 4 scenarios")
    args = parser.parse_args()

    scenarios = [0, 1, 2, 3] if args.all else [args.scenario]

    # Check if matplotlib is available
    has_matplotlib = False
    try:
        import matplotlib
        has_matplotlib = True
    except ImportError:
        print("[Notice] Matplotlib is not installed in the current environment. Generating SVG maps.")

    for s in scenarios:
        data = load_scenario(s)
        if has_matplotlib:
            output_png = f"route_map_scenario_{s}.png"
            plot_with_matplotlib(data, s, output_png)
        else:
            output_svg = f"route_map_scenario_{s}.svg"
            generate_svg_fallback(data, s, output_svg)

if __name__ == "__main__":
    main()
