# Chennai → Maitri voyage-route scenarios

This folder contains four **hackathon visualisation datasets**, not navigational instructions.

| File | Situation | Viable routes |
|---|---|---|
| `routes_scenario_0.json` | Favourable early-summer conditions | Safest, fastest, fuel-efficient |
| `routes_scenario_1.json` | Tabular iceberg alert | All three; fastest deviates |
| `routes_scenario_2.json` | Storm and denser pack ice | All three, with reroutes |
| `routes_scenario_3.json` | Calving-related iceberg field | Modified safest route only |

## Route selection logic

- **Safest:** widest weather and iceberg clearance; longest distance and lowest exposure.
- **Fastest:** direct geometry with reduced margin around iceberg-monitoring areas; highest risk.
- **Fuel-efficient:** seeks favourable current windows, but does not assume a current is available. Current observations override the planning assumption.

Totals are scenario-planning estimates rather than sums of straight-line segments. They include port operations, weather allowance, slower ice operations, manoeuvring, and a 15% fuel reserve. The plot is intentionally geographic rather than a legal route chart.

## Generate files and maps

```bash
python generate_voyage_routes.py
pip install matplotlib cartopy
python plot_voyage_routes.py 0
```

The plot script writes `route_map_scenario_X.png` and includes waypoints, hazard areas, route colours, and route statistics.

## Operational limitation

Only a qualified master and polar ice adviser can approve a passage plan. Before sailing and before every polar-ice entry, use current ENCs/Notices to Mariners, satellite ice products, weather and wave forecasts, vessel-specific Polar Water Operational Manual limits, mandatory reporting requirements, safe-speed limits, icebreaker/escort availability, and a verified SAR/contingency plan. The IMO Polar Code specifically calls for consideration of ice, icebergs, darkness, swell, fog, pressure ice, safe speed and contingency arrangements.

References: [IMO Polar Code](https://www.imo.org/en/ourwork/safety/pages/polar-code.aspx), [NSIDC sea-ice data](https://nsidc.org/data/seaice_index), and [British Antarctic Survey Southern Ocean overview](https://www.bas.ac.uk/about/where-we-work/antarctica/).
