# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""First-order wind load on a parabolic reflector (issue #12).

F = 0.5 * rho * V^2 * Cd * A, with Cd and the centre-of-pressure offset as
explicit assumptions. This is a screening estimate to size the order of
magnitude of loads; it is not a structural design. Brazilian practice for
design wind loads is ABNT NBR 6123 (basic wind speed by region, gust factors,
terrain category); use it, or a local structural engineer, for the real values.

    python3 software/tools/wind.py [V_ms ...]
"""
from __future__ import annotations

import math
import sys

RHO_AIR = 1.225  # kg/m^3 at sea level, 15 C


def dish_area_m2(diameter_m: float) -> float:
    return math.pi * diameter_m ** 2 / 4.0


def force_n(v_ms: float, diameter_m: float, cd: float, solidity: float = 1.0) -> float:
    """Drag-type force normal to the aperture. `solidity` scales area for a mesh
    reflector (1.0 = solid)."""
    return 0.5 * RHO_AIR * v_ms ** 2 * cd * dish_area_m2(diameter_m) * solidity


def moments(v_ms, diameter_m, cd, solidity, cp_offset_m, mast_height_m):
    """Returns (force N, torque about the vertical axis N*m, overturning moment at
    the base N*m). The torque arm is the horizontal offset of the centre of
    pressure from the azimuth axis; the overturning arm is the mast height to the
    dish centre."""
    f = force_n(v_ms, diameter_m, cd, solidity)
    return f, f * cp_offset_m, f * mast_height_m


if __name__ == "__main__":
    speeds = [float(x) for x in sys.argv[1:]] or [20.0, 30.0, 40.0, 50.0]
    print("1.70 m reflector, Cd 1.0-1.8 (normal to flow), centre-of-pressure offset 0.15 m, mast 3 m")
    for v in speeds:
        for cd in (1.0, 1.8):
            for sol, name in ((1.0, "solid"), (0.5, "mesh 50%")):
                f, tq, ov = moments(v, 1.7, cd, sol, 0.15, 3.0)
                print(f"V {v:4.0f} m/s ({v * 3.6:4.0f} km/h) Cd {cd}  {name:8s}: F {f:6.0f} N  azimuth torque {tq:5.0f} N*m  overturning {ov:6.0f} N*m")
