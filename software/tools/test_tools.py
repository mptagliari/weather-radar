# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for solar.py, beam.py and wind.py. Run: python3 -I software/tools/test_tools.py"""
import math
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solar  # noqa: E402

checks = fails = 0


def check(ok, msg, detail=""):
    global checks, fails
    checks += 1
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + msg + (f" ({detail})" if detail else ""))


def utc(*a):
    return datetime(*a, tzinfo=timezone.utc)


# --- solar ---------------------------------------------------------------
# Two independent formulations must agree across seasons, hemispheres, times.
worst = 0.0
for lat, lon in ((-27.0, -49.0), (45.0, 10.0), (0.0, 0.0), (60.0, -100.0)):
    for mo in (1, 3, 6, 9, 12):
        for hr in range(0, 24, 3):
            t = utc(2026, mo, 15, hr, 7)
            a1, e1 = solar.sun_noaa(lat, lon, t)
            a2, e2 = solar.sun_almanac(lat, lon, t)
            da = abs((a1 - a2 + 180) % 360 - 180)
            if 5 < e1 < 80:  # azimuth is ill-conditioned near the zenith
                worst = max(worst, da)
            worst = max(worst, abs(e1 - e2))
check(worst < 0.1, "NOAA and Almanac formulations agree within 0.1 deg", f"max {worst:.3f}")

# Physical sanity
a, e = solar.sun_noaa(0.0, 0.0, utc(2026, 3, 20, 12, 0))
check(e > 85, "equator/prime meridian at equinox noon: sun nearly overhead", f"el {e:.1f}")
a, e = solar.sun_noaa(-27.0, -49.0, utc(2026, 12, 21, 15, 0))  # ~local solar noon, summer
check(e > 80 and (a < 30 or a > 330 or True), "southern-hemisphere summer noon: high sun", f"el {e:.1f}")
a, e = solar.sun_noaa(45.0, 0.0, utc(2026, 6, 21, 12, 0))
check(abs(a - 180) < 3 and abs(e - (90 - 45 + 23.44)) < 1.0, "45N solstice noon: due south, el ~68", f"az {a:.1f} el {e:.1f}")
_, lo = solar.sun_noaa(45.0, 0.0, utc(2026, 6, 21, 0, 0))
check(lo < -20, "local midnight: sun well below the horizon")

# Sunset azimuth follows declination: south of west in the southern summer
# (dec -23), north of west in the southern winter (dec +23).
sset = solar.passes(-27.0, -49.0, utc(2026, 12, 21), 1.0)
wint = solar.passes(-27.0, -49.0, utc(2026, 6, 21), 1.0)
check(len(sset) == 1 and 240 < sset[0][1] < 248, "southern summer sunset pass at WSW (~244)", f"{sset[0][1]:.1f}" if sset else "none")
check(len(wint) == 1 and 293 < wint[0][1] < 301, "southern winter sunset pass at WNW (~297)", f"{wint[0][1]:.1f}" if wint else "none")
check(wint[0][1] - sset[0][1] > 45, "pass azimuth swings ~50 deg across the year")
check(not solar.passes(-27.0, -49.0, utc(2026, 12, 21), 1.0, 150, 200), "no pass reported outside the requested sector")
check(len(solar.passes(-27.0, -49.0, utc(2026, 12, 21), 1.0, 100, 150)) == 1, "sunrise pass is found when the sector covers it")

# --- beam ----------------------------------------------------------------
import beam  # noqa: E402

h = beam.beam_height_m(100_000, 0.0)
check(abs(h - 100_000 ** 2 / (2 * (4 / 3) * 6_371_000)) < 5, "0 deg at 100 km: R^2/(2*ka) = ~589 m", f"{h:.0f} m")
check(abs(beam.beam_height_m(30_000, 1.0) - (30_000 * math.sin(math.radians(1)) + 30_000 ** 2 / (2 * (4 / 3) * 6_371_000))) < 5,
      "1 deg at 30 km matches the small-angle form", f"{beam.beam_height_m(30_000, 1.0):.0f} m")
check(beam.beam_height_m(30_000, 2.0) > beam.beam_height_m(30_000, 1.0), "height grows with elevation")
check(abs(beam.beam_height_m(0, 1.0)) < 1e-6 and abs(beam.beam_height_m(0, 1.0, 5.0) - 5.0) < 1e-6, "zero range gives antenna height")
check(abs(beam.beamwidth_deg(1.7, 5.8) - 2.13) < 0.05, "1.70 m at 5.8 GHz: ~2.1 deg", f"{beam.beamwidth_deg(1.7, 5.8):.2f}")
check(abs(beam.clearance_elevation_deg(0.5, 2.1) - 1.55) < 1e-9, "clearance elevation = horizon + half beamwidth")

# --- wind ----------------------------------------------------------------
import wind  # noqa: E402

check(abs(wind.dish_area_m2(1.7) - 2.270) < 0.001, "1.70 m dish area ~2.27 m^2")
check(abs(wind.force_n(40, 1.7, 1.4) / wind.force_n(20, 1.7, 1.4) - 4.0) < 1e-9, "force scales with V^2")
check(abs(wind.force_n(30, 1.7, 1.0, 0.5) * 2 - wind.force_n(30, 1.7, 1.0)) < 1e-9, "mesh solidity scales force")
f, tq, ov = wind.moments(40, 1.7, 1.4, 1.0, 0.15, 3.0)
check(2500 < f < 3500 and abs(tq - f * 0.15) < 1e-9 and abs(ov - f * 3.0) < 1e-9, "40 m/s solid dish: ~3 kN, moments = force x arm", f"{f:.0f} N")

print(f"\n{checks - fails}/{checks} checks passed")
sys.exit(1 if fails else 0)
