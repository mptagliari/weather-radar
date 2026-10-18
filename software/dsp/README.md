<!--
SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->
# DSP building blocks

Reference implementation (NumPy) of the processing steps behind issues #17 and #20: range FFT, Doppler FFT, zero-velocity notch, dry-weather clutter map and dual-PRF velocity unfolding. Verified on **synthetic** FMCW data only; no real radar data exists yet, so nothing here is tuned or validated against hardware.

```sh
pip install numpy
python3 -I software/dsp/test_dsp.py
```

## What the synthetic tests establish

- A 12 km target lands in the correct 150 m gate and its velocity is recovered with the right sign (positive away from the radar, per [data format](../../docs/data-format.md)).
- A 3-bin zero-velocity notch suppresses static clutter by ~45 dB (Hann window, 64 chirps).
- **Cost of the notch.** With 64 chirps at T = 1 ms the Doppler bin is 0.4 m/s. Weather with |v| ≈ 0.2 m/s loses ~16 dB, ≈ 0.4 m/s about 8 dB, and ≥ 0.8 m/s about 1 dB or less. Slow stratiform rain moving across the beam therefore suffers, which is why the clutter map is the complement and not an optional extra.
- **Dual-PRF** with a 2:3 stagger (T = 0.8 / 1.2 ms at 5.8 GHz) recovers velocity up to ±32.3 m/s, twice the ±16.2 m/s of the fast PRT alone. Beyond that it aliases silently, so the residual returned by `unfold_dual_prf` must be used as a quality flag (`VELOCITY_AMBIGUOUS`). The extended limit `λ/(4|T₂−T₁|)` holds for PRTs in a ratio of consecutive integers only.

## Not covered

- Real clutter statistics, phase-noise spreading of clutter in Doppler (see [dynamic range](../../docs/dynamic-range.md)).
- Unfolding in the presence of noise-dominated gates; the noise test only perturbs velocities by 0.3 m/s.
- Staggering in a single sweep (interleaved chirps) versus alternating batches; the test assumes two separate measurements.
- Triangular up/down chirps for range-Doppler decoupling (issue #17).
