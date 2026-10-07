# Meteorological Link Budget — working notes v0.1

This document records assumptions before selecting expensive RF components.

## Important distinction

A point-target radar equation commonly produces an R^-4 dependence. Distributed precipitation filling a radar resolution volume is not modeled as a single point target; meteorological sensitivity is normally expressed as minimum detectable reflectivity **Zmin(R)**.

The engineering question is therefore:

> What minimum reflectivity (dBZ) produces a detectable signal at each range?

The initial requirement is:

**Zmin(30 km) <= 10 dBZ** (design target, not demonstrated).

## Candidate frequencies

Initial calculation points:

- C: 5.6 GHz -> wavelength ~53.5 mm
- X: 9.5 GHz -> wavelength ~31.6 mm

## Available reflectors

For a parabolic reflector, an initial gain estimate is

```text
G = eta * (pi D / lambda)^2
```

Using eta = 0.60 only as a preliminary assumption:

| Configuration | Estimated gain |
|---|---:|
| C, 5.6 GHz, D=1.70 m | ~37.8 dBi |
| X, 9.5 GHz, D=0.60 m | ~33.3 dBi |
| X, 9.5 GHz, D=1.70 m | ~42.4 dBi |

These values are estimates. Real feed illumination, spillover, blockage, surface error and losses must be measured/estimated.

Approximate beamwidth scales with lambda/D. Preliminary values discussed are roughly:

- C / 1.70 m: ~2.2 deg
- X / 0.60 m: ~3.7 deg
- X / 1.70 m: ~1.3 deg

## FMCW range resolution

Ideal range resolution:

```text
delta_R = c / (2 B)
```

Examples:

| Chirp bandwidth | Ideal range resolution |
|---:|---:|
| 1 MHz | ~150 m |
| 2 MHz | ~75 m |
| 3 MHz | ~50 m |
| 30 MHz | ~5 m |

The BWR-1 requirement does not need 5 m meteorological bins. A narrower bandwidth may trade excessive resolution for easier processing/integration.

## Receiver noise

A useful starting relation is:

```text
N[dBm] = -174 + 10 log10(B_noise[Hz]) + NF[dB]
```

Example with NF=2 dB:

- 10 kHz effective noise bandwidth -> ~-132 dBm
- 100 kHz -> ~-122 dBm

These are thermal-noise calculations only, not receiver sensitivity specifications. Required SNR, mixer/ADC noise, phase noise, leakage and processing gain must be included.

## Link-budget variables still required

For each band calculate at minimum:

- TX power
- TX antenna gain and beamwidth
- RX antenna gain
- TX/RX feed and cable losses
- atmospheric attenuation
- precipitation attenuation
- LNA noise figure/gain
- mixer conversion loss/noise
- effective IF/noise bandwidth
- chirp bandwidth and duration
- chirp repetition
- dwell time per angular cell
- coherent/non-coherent integration gain
- receiver leakage/dynamic-range constraints
- required detection SNR
- Zmin versus range

Required output is a curve/table of **Zmin(dBZ) versus range** for both C and X.

No PA should be frozen before this calculation is credible.
