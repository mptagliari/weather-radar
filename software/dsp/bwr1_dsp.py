# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Range-Doppler processing, clutter map, zero-velocity filter and dual-PRF
velocity unfolding for BWR-1 (issues #17, #20).

Conventions match docs/data-format.md: velocity is positive away from the
radar. Input is dechirped complex baseband, shape (n_chirps, n_samples).
Everything here is exercised on synthetic data only; no real radar data exists.
"""
from __future__ import annotations

import numpy as np

C0 = 299_792_458.0


def beat_hz(range_m: float, bandwidth_hz: float, chirp_s: float) -> float:
    return bandwidth_hz / chirp_s * 2.0 * range_m / C0


def synth_chirps(targets, *, n_chirps, fs, chirp_s, bandwidth_hz, lam, prt_s=None,
                 noise_dbfs=None, rng=None):
    """Simulate dechirped beats. targets: iterable of (range_m, v_ms, amplitude).
    prt_s: scalar or per-chirp array of start times spacing (staggered PRT)."""
    rng = rng or np.random.default_rng(0)
    n = int(round(fs * chirp_s))
    t = np.arange(n) / fs
    prt = np.full(n_chirps, chirp_s) if prt_s is None else np.broadcast_to(prt_s, (n_chirps,))
    start = np.concatenate([[0.0], np.cumsum(prt[:-1])])
    x = np.zeros((n_chirps, n), complex)
    for r, v, a in targets:
        fb = beat_hz(r, bandwidth_hz, chirp_s)
        # Range migrates with v: phase advances by 4*pi*v*t_start/lam (+v away).
        ph = 2 * np.pi * (2.0 * v / lam) * start
        x += a * np.exp(1j * (2 * np.pi * fb * t[None, :] + ph[:, None]))
    if noise_dbfs is not None:
        s = 10 ** (noise_dbfs / 20) / np.sqrt(2)
        x += s * (rng.standard_normal(x.shape) + 1j * rng.standard_normal(x.shape))
    return x


def range_fft(x, *, bandwidth_hz, chirp_s, fs, window="hann"):
    """Fast-time FFT per chirp. Returns (spectra[n_chirps, n_gates], range_m[n_gates])."""
    n = x.shape[1]
    w = np.hanning(n) if window == "hann" else np.ones(n)
    s = np.fft.fft(x * w, axis=1) / w.sum()
    # Positive beat frequencies only (complex I/Q resolves sign): bins 0..n/2.
    gates = n // 2
    f = np.arange(gates) * fs / n
    rng_m = f * C0 * chirp_s / (2.0 * bandwidth_hz)
    return s[:, :gates], rng_m


def doppler_fft(spectra, *, window="hann"):
    """Slow-time FFT. Returns (cube[n_doppler, n_gates], freq_index) with 0 Hz centred."""
    m = spectra.shape[0]
    w = np.hanning(m) if window == "hann" else np.ones(m)
    d = np.fft.fftshift(np.fft.fft(spectra * w[:, None], axis=0) / w.sum(), axes=0)
    return d, np.fft.fftshift(np.fft.fftfreq(m))


def velocity_axis(n_doppler, prt_s, lam):
    f = np.fft.fftshift(np.fft.fftfreq(n_doppler, d=prt_s))
    return f * lam / 2.0


def zero_velocity_filter(cube, notch_bins=1):
    """Notch the zero-Doppler bin and `notch_bins` each side. Returns (filtered, mask).
    A static clutter line leaks into neighbouring bins through the window, so the
    notch width should match the window mainlobe (Hann: 1 bin each side)."""
    out = cube.copy()
    c = cube.shape[0] // 2
    out[c - notch_bins:c + notch_bins + 1, :] = 0.0
    return out


def moments(cube, vel):
    """Power (linear) and mean velocity per gate from the Doppler spectrum."""
    p = np.abs(cube) ** 2
    ptot = p.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        v = (p * vel[:, None]).sum(axis=0) / ptot
    return ptot, v


class ClutterMap:
    """Per-azimuth-bin, per-gate dry-weather clutter map (running mean of power).

    Learn from dry scans with update(); apply with flag() to mark gates whose
    power is not clearly above the learned clutter. Complements, and does not
    replace, the zero-velocity filter."""

    def __init__(self, n_az, n_gates, alpha=0.1):
        self.mean = np.full((n_az, n_gates), np.nan)
        self.alpha = alpha

    def update(self, az_idx, power_lin):
        m = self.mean[az_idx]
        self.mean[az_idx] = np.where(np.isnan(m), power_lin, (1 - self.alpha) * m + self.alpha * power_lin)

    def flag(self, az_idx, power_lin, margin_db=3.0):
        """True where the gate is NOT clearly above clutter (suspect)."""
        m = self.mean[az_idx]
        thr = np.where(np.isnan(m), 0.0, m * 10 ** (margin_db / 10))
        return power_lin < thr


def unfold_dual_prf(v1, v2, prt1, prt2, lam, max_fold=6):
    """Unfold velocity from two PRTs (staggered dual-PRF).

    v1, v2 are the folded velocities, each within +-lam/(4*prt). Candidates
    v + 2*Nyq*k are searched for the pair that agrees best, restricted to the
    extended range |v| <= lam / (4*|prt2 - prt1|). That limit is the true
    unambiguous velocity for PRTs in a ratio of consecutive integers (2:3,
    3:4, ...); other ratios need their own limit. Without the restriction,
    exact ties between aliases decide the result.

    Returns (velocity, residual). A large residual means the two measurements
    disagree (noise or velocity outside the extended range)."""
    n1 = lam / (4.0 * prt1)
    n2 = lam / (4.0 * prt2)
    vmax = lam / (4.0 * abs(prt2 - prt1))
    ks = np.arange(-max_fold, max_fold + 1)
    c1 = v1 + 2.0 * n1 * ks[:, None]
    c2 = v2 + 2.0 * n2 * ks[None, :]
    err = np.abs(c1 - c2)
    mid = 0.5 * (c1 + c2)
    err = np.where(np.abs(mid) <= vmax, err, np.inf)
    if not np.isfinite(err).any():
        return float("nan"), float("inf")
    i, j = np.unravel_index(np.argmin(err), err.shape)
    return mid[i, j], err[i, j]


def fold(v, nyq):
    """Alias a true velocity into +-nyq."""
    return (v + nyq) % (2 * nyq) - nyq
