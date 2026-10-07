# Meteorological Link Budget — working notes v0.2

This document records assumptions before selecting expensive RF components.

## Important distinction

A point-target radar equation commonly produces an R^-4 dependence. Distributed precipitation filling a radar resolution volume is not modeled as a single point target; meteorological sensitivity is normally expressed as minimum detectable reflectivity **Zmin(R)**.

The engineering question is therefore:

> What minimum reflectivity (dBZ) produces a detectable signal at each range?

The initial requirement is:

**Zmin(30 km) <= 10 dBZ** (design target, not demonstrated).

## Band decision

Band A baseline is now **C band near 5.8 GHz**. X band remains a future complementary Band B.

The choice is driven primarily by precipitation attenuation/penetration for severe-convection nowcasting. X may offer sensitivity/resolution advantages for fixed physical apertures, but intense precipitation can strongly attenuate X-band echoes and obscure weather behind an intervening cell.

Exact center frequency is TBD pending regulatory and RF-component decisions.

## Preliminary antenna estimates

For a parabolic reflector:

```text
G = eta * (pi D / lambda)^2
```

Previous estimates used eta=0.60. Revised calculations should use measured geometry and a documented efficiency assumption.

At the same frequency and efficiency:

```text
Gain ratio, 1.70 m vs 0.60 m
= 20 log10(1.70 / 0.60)
= ~9.05 dB
```

This TX gain penalty is significant: a smaller TX antenna must be compensated by transmitter power, processing gain, sensitivity relaxation, or another system change.

A stationary TX illuminating the entire ~90–120 degree sector is not the baseline because the antenna-gain penalty is expected to be severe.

## Fixed-aperture wavelength scaling

Claims such as an overall lambda^-4 sensitivity advantage for X over C depend on the specific assumptions: fixed physical TX/RX apertures, illumination geometry, precipitation scattering model and which terms cancel in the weather-radar equation.

Do **not** treat lambda^-4 as a universal band-comparison law. The full derivation will be kept with the reproducible link-budget calculation.

## FMCW baseline

Initial engineering point:

- B = 1 MHz
- ideal delta_R = c/(2B) ~= 150 m
- T ~= 1 ms starting point
- nominal range = 30 km
- stretch range = 50 km

Round-trip delay at 30 km:

```text
tau = 2R/c ~= 200 us
```

The ~1 ms chirp is an engineering baseline with margin, not a fundamental requirement that T must equal a fixed multiple of tau.

For a linear chirp:

```text
slope S = B/T
beat frequency f_b ~= S * 2R/c
```

At B=1 MHz and T=1 ms:

- 30 km -> ~200 kHz beat frequency before Doppler contribution
- 50 km -> ~333 kHz

A ~2 MSPS-class acquisition rate therefore leaves substantially more practical margin than designing directly at Nyquist.

## Doppler ambiguity

For uniform slow-time sampling, a useful baseline relation is:

```text
|v_Nyquist| ~= lambda / (4 T_r)
```

At ~5.8 GHz (lambda ~= 51.7 mm) and T_r ~= 1 ms:

```text
|v_Nyquist| ~= 12.9 m/s
```

Convective radial velocities may exceed this, so velocity ambiguity is a design issue.

Candidates:

- staggered chirp/repetition intervals analogous to dual-PRF processing;
- up/down (triangular) sweeps to help separate range and Doppler contributions.

Exact waveform and ambiguity-resolution algorithm remain TBD.

## Receiver noise and phase noise

Thermal noise remains relevant:

```text
N[dBm] = -174 + 10 log10(B_noise[Hz]) + NF[dB]
```

But terrain clutter can be much stronger than weak meteorological returns. Synthesizer/LO phase noise around strong coherent clutter may therefore set a practical detection floor even when the receiver thermal NF appears adequate.

The quantitative budget must include:

- LNA NF/gain;
- pre-LNA loss;
- mixer/receiver noise;
- phase-noise assumptions;
- TX leakage/isolation;
- ADC dynamic range;
- processing/integration gain.

## IF range compensation / STC

For distributed weather echoes, received power has an approximate R^-2 dependence under common beam-filling assumptions. FMCW maps range to beat frequency.

A frequency-dependent analog gain approaching +20 dB/decade in amplitude over an appropriate region can therefore act as a form of range compensation/STC and reduce near-range dynamic-range pressure.

This is a **candidate**, not a frozen requirement. Any analog STC should be bypassable or accompanied by a raw/linear path because it affects noise, clutter and calibration.

## Attenuation

Specific rain attenuation must be calculated from an accepted model using the actual frequency, polarization and rainfall assumptions. Fixed statements such as "X loses N dB/km" must not be treated as universal constants.

The C-vs-X comparison must include at least:

- clear-air path;
- moderate-rain path;
- intense convective rain path;
- one-way and two-way attenuation explicitly distinguished;
- sensitivity to intervening path length through precipitation.

## Preliminary sensitivity claims

Conversation-level estimates suggesting that 1 W with high-gain apertures could reach the 10 dBZ / 30 km target are **not verified design results**.

Do not freeze TX power from those numbers.

Required output is a reproducible curve/table of **Zmin(dBZ) versus range** for C and X, including assumptions and uncertainty.

## Link-budget variables still required

For each evaluated configuration calculate at minimum:

- TX power
- TX antenna gain and beamwidth
- RX antenna gain and beamwidth
- TX/RX feed and cable losses
- atmospheric attenuation
- precipitation attenuation
- LNA noise figure/gain
- mixer/receiver loss/noise
- phase noise / clutter interaction assumption
- effective IF/noise bandwidth
- chirp bandwidth and duration
- chirp repetition/staggering
- dwell time per angular cell
- coherent/non-coherent integration gain
- receiver leakage/dynamic-range constraints
- ADC dynamic range
- required detection SNR
- Zmin versus range

Compare at minimum:

1. C band, high-gain TX + 1.70 m RX.
2. C band, 0.60 m TX + 1.70 m RX.
3. Future X-band equivalent configurations.

No PA should be frozen before this calculation is credible.
