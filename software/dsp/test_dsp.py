# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests on synthetic data. Run: python3 -I software/dsp/test_dsp.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bwr1_dsp as d  # noqa: E402

FS, T, B, LAM = 2e6, 1e-3, 1e6, 0.0517
checks = fails = 0


def check(ok, msg, detail=""):
    global checks, fails
    checks += 1
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + msg + (f" ({detail})" if detail else ""))


def chain(targets, n_chirps=64, noise=-80, prt=None):
    x = d.synth_chirps(targets, n_chirps=n_chirps, fs=FS, chirp_s=T, bandwidth_hz=B, lam=LAM,
                       prt_s=prt, noise_dbfs=noise)
    s, rng = d.range_fft(x, bandwidth_hz=B, chirp_s=T, fs=FS)
    cube, _ = d.doppler_fft(s)
    vel = d.velocity_axis(n_chirps, T, LAM)
    return cube, rng, vel


# Range and velocity of a single target
r0, v0 = 12_000.0, 6.0
cube, rng, vel = chain([(r0, v0, 1e-3)])
pw, vv = d.moments(cube, vel)
k = int(np.argmax(pw))
check(abs(rng[k] - r0) < 150, "range peak within one 150 m gate", f"{rng[k]:.0f} m")
check(abs(vv[k] - v0) < 0.5, "mean velocity within 0.5 m/s", f"{vv[k]:.2f} m/s")

# Negative velocity (toward the radar)
cube, rng, vel = chain([(12_000.0, -4.0, 1e-3)])
pw, vv = d.moments(cube, vel)
check(abs(vv[int(np.argmax(pw))] + 4.0) < 0.5, "negative (approaching) velocity sign")

# Zero-velocity filter: strong static clutter vs weak moving weather at another gate
clut, wx = (3_000.0, 0.0, 0.3), (12_000.0, 5.0, 1e-4)
cube, rng, vel = chain([clut, wx])
gc = int(np.argmin(abs(rng - 3000)))
before = np.abs(cube[:, gc]).max() ** 2
after = np.abs(d.zero_velocity_filter(cube)[:, gc]).max() ** 2
sup = 10 * np.log10(before / max(after, 1e-30))
check(sup > 40, "zero-velocity filter suppresses static clutter by >40 dB", f"{sup:.0f} dB")
pw, vv = d.moments(d.zero_velocity_filter(cube), vel)
gw = int(np.argmin(abs(rng - 12000)))
check(abs(vv[gw] - 5.0) < 0.6, "weather velocity survives the filter", f"{vv[gw]:.2f} m/s")

# Blind-speed cost: velocity bin is lam/(2*M*T) = 0.4 m/s for 64 chirps.
def removed_db(v):
    c0, _, _ = chain([(12_000.0, v, 1e-3)])
    f = d.zero_velocity_filter(c0)
    return 10 * np.log10((np.abs(c0) ** 2).sum() / (np.abs(f) ** 2).sum())


check(removed_db(0.2) > 10, "weather at 0.2 m/s loses >10 dB to the notch (known cost)", f"{removed_db(0.2):.1f} dB")
check(removed_db(2.0) < 0.5, "weather at 2 m/s loses <0.5 dB", f"{removed_db(2.0):.2f} dB")

# Clutter map
cm = d.ClutterMap(4, len(rng), alpha=0.5)
for _ in range(10):
    c, _, _ = chain([clut])
    cm.update(1, d.moments(c, vel)[0])
pw_c, _ = d.moments(chain([clut, wx])[0], vel)
flag = cm.flag(1, pw_c, margin_db=3)
check(flag[gc], "gate with learned clutter is flagged")
check(not flag[gw], "weather gate above the map is not flagged")
check(np.isnan(cm.mean[0]).all(), "unlearned azimuth stays empty")

# Dual-PRF unfolding
T1, T2 = 0.8e-3, 1.2e-3  # 2:3 stagger
n1, n2 = LAM / (4 * T1), LAM / (4 * T2)
vmax = LAM / (4 * abs(T2 - T1))
check(abs(vmax - 2 * n1) < 1e-9 and n2 < n1, "2:3 stagger: extended range is twice the fast-PRT Nyquist", f"+-{vmax:.1f} vs +-{n1:.1f} m/s")
worst = 0.0
for v in np.linspace(-0.97 * vmax, 0.97 * vmax, 81):
    est, err = d.unfold_dual_prf(d.fold(v, n1), d.fold(v, n2), T1, T2, LAM)
    worst = max(worst, abs(est - v))
check(worst < 1e-6, "dual-PRF recovers true velocity across the extended range", f"max err {worst:.2e}")
est, res = d.unfold_dual_prf(d.fold(40.0, n1), d.fold(40.0, n2), T1, T2, LAM)
check(abs(est - 40.0) > 5.0, "velocity beyond the extended range aliases (limit documented)", f"{est:.1f} for 40.0")
rng_ = np.random.default_rng(1)
good = 0
for v in rng_.uniform(-0.9 * vmax, 0.9 * vmax, 400):
    est, _ = d.unfold_dual_prf(d.fold(v, n1) + rng_.normal(0, 0.3), d.fold(v, n2) + rng_.normal(0, 0.3), T1, T2, LAM)
    good += abs(est - v) < 2.0
check(good / 400 > 0.8, "with 0.3 m/s measurement noise most estimates stay within 2 m/s", f"{good / 4:.0f}%")

print(f"\n{checks - fails}/{checks} checks passed")
sys.exit(1 if fails else 0)
