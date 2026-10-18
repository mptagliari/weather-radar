# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Beam height and horizon blockage with the effective-Earth-radius model
(issue #14). Standard 4/3 Earth radius; real refraction varies with weather.

    python3 software/tools/beam.py [elevation_deg ...]
"""
from __future__ import annotations

import math
import sys

EARTH_RADIUS_M = 6_371_000.0
K_EFF = 4.0 / 3.0


def beam_height_m(range_m: float, elev_deg: float, antenna_height_m: float = 0.0) -> float:
    """Height above the antenna's local horizontal plane reference (ground at the
    antenna + antenna height) of the beam centre at slant range range_m."""
    ae = K_EFF * EARTH_RADIUS_M
    e = math.radians(elev_deg)
    return math.sqrt(range_m ** 2 + ae ** 2 + 2 * range_m * ae * math.sin(e)) - ae + antenna_height_m


def beamwidth_deg(diameter_m: float, freq_ghz: float, k: float = 70.0) -> float:
    """Approximate half-power beamwidth, 70*lambda/D degrees (a rule of thumb)."""
    lam = 299_792_458.0 / (freq_ghz * 1e9)
    return k * lam / diameter_m


def clearance_elevation_deg(horizon_deg: float, beamwidth: float, margin_deg: float = 0.0) -> float:
    """Lowest elevation whose beam centre keeps the beam's lower half-power edge
    above a terrain horizon at `horizon_deg` elevation angle."""
    return horizon_deg + beamwidth / 2.0 + margin_deg


def table(elevs, ranges_km=(5, 10, 20, 30, 40, 50), bw=2.1, ant_h=0.0):
    rows = []
    for e in elevs:
        rows.append((e, [(r, beam_height_m(r * 1e3, e, ant_h), beam_height_m(r * 1e3, e - bw / 2, ant_h),
                          beam_height_m(r * 1e3, e + bw / 2, ant_h)) for r in ranges_km]))
    return rows


if __name__ == "__main__":
    elevs = [float(x) for x in sys.argv[1:]] or [0.5, 1.0, 2.0]
    bw = beamwidth_deg(1.7, 5.8)
    print(f"1.70 m @ 5.8 GHz half-power beamwidth ~ {bw:.2f} deg; 4/3 Earth; antenna height 0")
    for e, rows in table(elevs, bw=bw):
        print(f"\nelevation {e} deg: range km -> beam centre (lower edge .. upper edge) m")
        for r, c, lo, hi in rows:
            print(f"  {r:3d} km: {c:6.0f}  ({lo:6.0f} .. {hi:6.0f})")
