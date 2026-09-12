"""
FILE 3: src/visualization.py
Trajectory visualisation for the Antarctic Iceberg Prediction System.

Produces three output figures:
  detection_map.png   — geographic positions with confidence heatmap
  trajectories.png    — 72-hour drift paths with uncertainty cones
  integrated.png      — combined dashboard (map + timeline panels)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines    import Line2D
from matplotlib.gridspec import GridSpec
from pathlib import Path


# ---------------------------------------------------------------------------
# Colour palette (8 distinct colours cycling per iceberg)
# ---------------------------------------------------------------------------
PALETTE = [
    "#ef4444", "#f59e0b", "#10b981", "#3b82f6",
    "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16",
]


def _coast(ax):
    """Sketch a simplified Antarctic Peninsula coastline."""
    cx = [-62, -63, -64, -64.5, -64.8, -65, -66, -67, -68, -69, -69.5, -69, -62]
    cy = [-64, -64.5, -65.5, -66, -67, -68, -68.5, -68, -67, -66, -65, -64, -64]
    ax.fill(cx, cy, color="#374151", alpha=0.7, zorder=2, label="Land")
    ax.plot(cx, cy, color="#6b7280", lw=0.8, zorder=3)


def _style(ax, title: str, bounds: dict):
    ax.set_facecolor("#0b1a30")
    ax.set_xlim(bounds["lon_min"], bounds["lon_max"])
    ax.set_ylim(bounds["lat_min"], bounds["lat_max"])
    ax.set_xlabel("Longitude", fontsize=10, color="#94a3b8")
    ax.set_ylabel("Latitude",  fontsize=10, color="#94a3b8")
    ax.set_title(title, fontsize=12, weight="bold", color="#f1f5f9", pad=8)
    ax.tick_params(colors="#64748b")
    ax.spines[:].set_color("#334155")
    ax.grid(True, color="#1e293b", lw=0.6, ls="--", alpha=0.7)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def plot_integrated_results(
    detections: list,
    predictions: list,
    output_path: str = "outputs/visualizations/integrated.png",
    bounds: dict = None,
) -> Path:
    """
    Create comprehensive visualisation: map + per-iceberg uncertainty timelines.

    Args:
        detections:  List of iceberg dicts from IcebergDetector.
        predictions: List of prediction dicts from the pipeline
                     (each has keys 'iceberg' and 'trajectory').
        output_path: Destination PNG path.
        bounds:      Geographic extent override.

    Returns:
        Path to the saved PNG.
    """
    if bounds is None:
        bounds = {"lat_min": -72, "lat_max": -58,
                  "lon_min": -72, "lon_max": -52}

    n   = max(len(predictions), 1)
    fig = plt.figure(figsize=(18, max(9, 4 * min(n, 6))),
                     facecolor="#080e20")
    gs  = GridSpec(min(n, 6), 3, figure=fig, wspace=0.06, hspace=0.55)

    # ── Main map (left 2/3) ────────────────────────────────────────
    ax_map = fig.add_subplot(gs[:, :2])
    _style(ax_map,
           "Antarctic Iceberg Detection & 72-Hour Drift Prediction",
           bounds)
    _coast(ax_map)

    for i, pred in enumerate(predictions[:len(PALETTE) * 8]):
        color  = PALETTE[i % len(PALETTE)]
        traj   = pred["trajectory"]
        berg   = pred["iceberg"]

        lats = [p["latitude"]            for p in traj]
        lons = [p["longitude"]           for p in traj]
        uncs = [p.get("uncertainty_km", 0) for p in traj]

        # Uncertainty cones
        for lat, lon, unc in zip(lats, lons, uncs):
            if unc > 0:
                ax_map.add_patch(mpatches.Circle(
                    (lon, lat), unc / 111.0,
                    color=color, alpha=0.08, zorder=3,
                ))

        # Drift path
        ax_map.plot(lons, lats, color=color, lw=1.8,
                    ls="--", alpha=0.85, zorder=4)

        # Start (star)
        ax_map.plot(lons[0], lats[0], "*",
                    ms=16, color=color, zorder=6,
                    mec="#ffffff", mew=0.5,
                    label=berg["id"])

        # End (open circle)
        ax_map.plot(lons[-1], lats[-1], "o",
                    ms=9, color=color, zorder=6,
                    mfc="none", mew=1.8)

        # Time labels at 24h / 48h / 72h
        for pt in traj:
            if pt["time_hours"] in (24, 48, 72):
                ax_map.text(
                    pt["longitude"], pt["latitude"],
                    f"{pt['time_hours']}h",
                    color=color, fontsize=7, fontweight="bold", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.12", fc="#0b1a30",
                              ec=color, alpha=0.9),
                )

    ax_map.legend(loc="lower left", ncol=2,
                  facecolor="#1e293b", edgecolor="#334155",
                  labelcolor="#f1f5f9", fontsize=8)

    # ── Uncertainty timeline panels (right 1/3) ────────────────────
    for i, pred in enumerate(predictions[:6]):
        color = PALETTE[i % len(PALETTE)]
        traj  = pred["trajectory"]
        berg  = pred["iceberg"]

        times = [p["time_hours"]            for p in traj]
        uncs  = [p.get("uncertainty_km", 0) for p in traj]

        ax_u = fig.add_subplot(gs[i, 2])
        ax_u.set_facecolor("#0b1a30")
        ax_u.plot(times, uncs, color=color, lw=2.0)
        ax_u.fill_between(times, 0, uncs, alpha=0.18, color=color)
        ax_u.set_xlabel("Hours", fontsize=7, color="#94a3b8")
        ax_u.set_ylabel("±km",   fontsize=7, color="#94a3b8")
        ax_u.set_title(f"{berg['id']} uncertainty",
                       fontsize=8, color="#f1f5f9")
        ax_u.tick_params(colors="#64748b", labelsize=6)
        ax_u.spines[:].set_color("#334155")
        ax_u.grid(True, color="#1e293b", lw=0.4, ls="--")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=300, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"📊 Saved integrated map  → {out}")
    return out


def plot_detections(
    icebergs: list,
    output_path: str = "outputs/visualizations/detection_map.png",
    bounds: dict = None,
) -> Path:
    """Plot detected positions as a confidence-coded scatter map."""
    if bounds is None:
        bounds = {"lat_min": -72, "lat_max": -58,
                  "lon_min": -72, "lon_max": -52}

    fig, ax = plt.subplots(figsize=(12, 9))
    fig.patch.set_facecolor("#080e20")
    _style(ax, f"Iceberg Detections  ({len(icebergs)} found)", bounds)
    _coast(ax)

    for berg in icebergs:
        lon  = berg["position"]["lon"]
        lat  = berg["position"]["lat"]
        conf = berg["confidence"]
        sz   = max(80, min(400,
               max(berg["size_meters"]["width"],
                   berg["size_meters"]["height"]) / 5))
        ax.scatter(lon, lat, s=sz, c=[[conf]], cmap="YlOrRd",
                   vmin=0.2, vmax=1.0, zorder=5,
                   edgecolors="#ffffff", linewidths=0.7, marker="^")
        ax.annotate(
            f"{berg['id']}\n{conf:.0%}",
            (lon, lat), xytext=(6, 5), textcoords="offset points",
            color="#fbbf24", fontsize=6, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="#1e293b",
                      ec="#f59e0b", alpha=0.85),
        )

    sm = plt.cm.ScalarMappable(cmap="YlOrRd",
                                norm=plt.Normalize(0.2, 1.0))
    sm.set_array([])
    cb = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("Confidence", color="#94a3b8", fontsize=9)
    cb.ax.yaxis.set_tick_params(color="#64748b")
    plt.setp(cb.ax.yaxis.get_ticklabels(), color="#94a3b8")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=200, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"📊 Saved detection map   → {out}")
    return out


def plot_trajectories(
    predictions: list,
    output_path: str = "outputs/visualizations/trajectories.png",
    bounds: dict = None,
) -> Path:
    """Plot predicted drift paths with uncertainty cones."""
    if bounds is None:
        bounds = {"lat_min": -72, "lat_max": -58,
                  "lon_min": -72, "lon_max": -52}

    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#080e20")
    _style(ax, "72-Hour Iceberg Drift Trajectories (Physics + Monte Carlo)",
           bounds)
    _coast(ax)

    for i, pred in enumerate(predictions):
        color = PALETTE[i % len(PALETTE)]
        traj  = pred["trajectory"]
        berg  = pred["iceberg"]

        lats = [p["latitude"]            for p in traj]
        lons = [p["longitude"]           for p in traj]
        uncs = [p.get("uncertainty_km", 0) for p in traj]

        for lat, lon, unc in zip(lats, lons, uncs):
            if unc > 0:
                ax.add_patch(mpatches.Circle(
                    (lon, lat), unc / 111.0,
                    color=color, alpha=0.10, zorder=3,
                ))
        ax.plot(lons, lats, color=color, lw=2.0, ls="--",
                alpha=0.85, zorder=4)
        ax.plot(lons[0], lats[0], "*", ms=14, color=color, zorder=6,
                mec="#ffffff", mew=0.5, label=berg["id"])
        ax.plot(lons[-1], lats[-1], "o", ms=9, color=color, zorder=6,
                mfc="none", mew=1.8)

        for pt in traj:
            if pt["time_hours"] in (24, 48, 72):
                ax.text(pt["longitude"], pt["latitude"],
                        f"{pt['time_hours']}h",
                        color=color, fontsize=7, fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.12", fc="#0b1a30",
                                  ec=color, alpha=0.9))

    legend_elems = [
        Line2D([0], [0], marker="*", color="w",
               markerfacecolor="#94a3b8", ms=12, label="Detection (now)"),
        Line2D([0], [0], marker="o", color="w",
               markerfacecolor="none", markeredgecolor="#94a3b8",
               ms=9, label="72h forecast"),
        mpatches.Patch(color="#94a3b8", alpha=0.3, label="Uncertainty cone"),
    ]
    ax.legend(handles=legend_elems, loc="lower left",
              facecolor="#1e293b", edgecolor="#334155",
              labelcolor="#f1f5f9", fontsize=9)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=250, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"📊 Saved trajectory map  → {out}")
    return out
