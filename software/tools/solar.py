# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Solar position and pass planning for pointing/gain checks (issue #21, REQ-013).

Azimuth is degrees clockwise from true north, elevation above the horizon,
matching the radar convention. Accuracy of the low-precision formulas used
here is a few hundredths of a degree, well inside a ~2 deg beam but not a
substitute for an ephemeris when calibrating at 0.1 deg.

    python3 software/tools/solar.py LAT LON YYYY-MM-DD [elev_deg] [az_lo az_hi]
"""
from __future__ import annotations

import math
import sys
from datetime import datetime, timedelta, timezone

SUN_DIAMETER_DEG = 0.533


def julian_day(t: datetime) -> float:
    t = t.astimezone(timezone.utc)
    y, m = t.year, t.month
    d = t.day + (t.hour + (t.minute + (t.second + t.microsecond / 1e6) / 60) / 60) / 24
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def _refraction_deg(el: float) -> float:
    """Bennett refraction (standard atmosphere), applied to apparent elevation."""
    if el < -1.0:
        return 0.0
    return 1.02 / math.tan(math.radians(el + 10.3 / (el + 5.11))) / 60.0


def sun_noaa(lat: float, lon: float, t: datetime):
    """NOAA solar-calculator formulation. Returns (azimuth, geometric_elevation)."""
    jd = julian_day(t)
    jc = (jd - 2451545.0) / 36525.0
    l0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360
    m = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    mr = math.radians(m)
    c = (math.sin(mr) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
         + math.sin(2 * mr) * (0.019993 - 0.000101 * jc) + math.sin(3 * mr) * 0.000289)
    true_long = l0 + c
    om = 125.04 - 1934.136 * jc
    app = true_long - 0.00569 - 0.00478 * math.sin(math.radians(om))
    eps0 = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60
    eps = eps0 + 0.00256 * math.cos(math.radians(om))
    decl = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(app))))
    y = math.tan(math.radians(eps / 2)) ** 2
    l0r = math.radians(l0)
    eqt = 4 * math.degrees(y * math.sin(2 * l0r) - 2 * e * math.sin(mr)
                           + 4 * e * y * math.sin(mr) * math.cos(2 * l0r)
                           - 0.5 * y * y * math.sin(4 * l0r) - 1.25 * e * e * math.sin(2 * mr))
    ut = t.astimezone(timezone.utc)
    minutes = ut.hour * 60 + ut.minute + ut.second / 60 + ut.microsecond / 6e7
    tst = (minutes + eqt + 4 * lon) % 1440
    ha = tst / 4 - 180
    if ha < -180:
        ha += 360
    lr, dr, hr = math.radians(lat), math.radians(decl), math.radians(ha)
    cosz = math.sin(lr) * math.sin(dr) + math.cos(lr) * math.cos(dr) * math.cos(hr)
    z = math.degrees(math.acos(max(-1.0, min(1.0, cosz))))
    el = 90 - z
    az_den = math.cos(lr) * math.sin(math.radians(z))
    if abs(az_den) < 1e-9:
        az = 180.0 if lat > 0 else 0.0
    else:
        cosa = (math.sin(lr) * cosz - math.sin(dr)) / az_den
        a = math.degrees(math.acos(max(-1.0, min(1.0, cosa))))
        az = (a + 180) % 360 if ha > 0 else (540 - a) % 360
    return az, el


def sun_almanac(lat: float, lon: float, t: datetime):
    """Independent low-precision formulation (Astronomical Almanac, ~0.01 deg).
    Used only to cross-check sun_noaa."""
    n = julian_day(t) - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    gmst = (280.46061837 + 360.98564736629 * n) % 360
    ha = math.radians((gmst + lon - math.degrees(ra)) % 360)
    lr = math.radians(lat)
    el = math.asin(math.sin(lr) * math.sin(dec) + math.cos(lr) * math.cos(dec) * math.cos(ha))
    az = math.atan2(-math.cos(dec) * math.sin(ha),
                    math.cos(lr) * math.sin(dec) - math.sin(lr) * math.cos(dec) * math.cos(ha))
    return math.degrees(az) % 360, math.degrees(el)


def apparent(lat, lon, t):
    az, el = sun_noaa(lat, lon, t)
    return az, el + _refraction_deg(el)


def passes(lat, lon, day: datetime, elev_deg, az_lo=200.0, az_hi=320.0, step_s=30):
    """Times on `day` (UTC date) when the apparent sun centre crosses elev_deg
    (rising or setting) at an azimuth inside [az_lo, az_hi]. Returns [(time, az)]."""
    t0 = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    out, prev = [], None
    for k in range(0, 86400 + step_s, step_s):
        t = t0 + timedelta(seconds=k)
        az, el = apparent(lat, lon, t)
        if prev is not None and (prev[1] - elev_deg) * (el - elev_deg) < 0:
            f = (elev_deg - prev[1]) / (el - prev[1])
            ta = prev[0] + timedelta(seconds=step_s * f)
            azi = (prev[2] + ((az - prev[2] + 180) % 360 - 180) * f) % 360
            if (az_lo <= azi <= az_hi) if az_lo <= az_hi else (azi >= az_lo or azi <= az_hi):
                out.append((ta, azi))
        prev = (t, el, az)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    la, lo = float(sys.argv[1]), float(sys.argv[2])
    d = datetime.fromisoformat(sys.argv[3]).replace(tzinfo=timezone.utc)
    el = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    lo_az = float(sys.argv[5]) if len(sys.argv) > 5 else 200.0
    hi_az = float(sys.argv[6]) if len(sys.argv) > 6 else 320.0
    for ta, az in passes(la, lo, d, el, lo_az, hi_az):
        print(f"{ta:%Y-%m-%d %H:%M:%S}Z  az {az:6.2f} deg at apparent el {el} deg")
    print(f"(no pass in sector {lo_az}-{hi_az})" if not passes(la, lo, d, el, lo_az, hi_az) else "")
