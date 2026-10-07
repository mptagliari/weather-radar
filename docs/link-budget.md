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


## Receiver / processing model v0.3

The first interactive model used the meteorological Doppler spectral width simultaneously as receiver noise bandwidth and as the source of the independent-sample count. That is useful as a radiometric first-order estimate, but it hides the FMCW processing chain.

The refined model separates three quantities:

1. **Range-bin noise bandwidth (fast time).** After dechirp and range FFT/matched filtering, the equivalent noise bandwidth is approximately

```text
B_range ~= ENBW_window / T_chirp
```

where ENBW_window is 1.0 for a rectangular window and about 1.5 for a Hann window. Zero padding does not add processing gain.

2. **Meteorological Doppler spectral width (slow time).**

```text
sigma_f = 2 sigma_v / lambda
B_weather ~= sqrt(2 pi) sigma_f
```

This describes the weather signal spectrum; it is not automatically the receiver noise bandwidth.

3. **Independent looks / power-estimator statistics.** Weather echo is a stochastic process. Dwell time, chirp repetition and Doppler decorrelation determine how many statistically useful looks are available. A first-order estimate is

```text
N_ind ~= min(N_chirps, dwell * B_weather)
```

but this is now exposed as an assumption rather than silently folded into receiver bandwidth.

For incoherent power averaging, estimator significance improves approximately as sqrt(N_ind), i.e. `5 log10(N_ind)` dB. This term is **not labeled coherent SNR gain**.

The model therefore reports separately:

- received meteorological power;
- thermal noise per post-range-FFT bin;
- single-chirp range-bin SNR;
- number of chirps in dwell;
- estimated independent weather looks;
- statistical averaging/significance gain;
- thermal/statistical Zmin;
- engineering Zmin after an explicit implementation margin.

The implementation margin is reserved for effects not yet predicted from first principles: TX->RX leakage, phase-noise skirts on terrain clutter, ADC/quantization limitations, residual clutter and calibration/model error.

### Baseline processing assumptions

Current calculation baseline:

- C band near 5.8 GHz;
- B = 1 MHz (~150 m ideal radial resolution);
- T_chirp = 1 ms;
- Hann range window (ENBW factor ~1.5);
- coherent I/Q acquisition;
- sector/update geometry determines dwell;
- independent-look model is explicit and editable;
- engineering margin is explicit and must not be hidden inside generic "system loss".

This model is intentionally conservative about claims: a calculated Zmin is a design estimate, not demonstrated radar sensitivity.


## Detection statistics — model v0.4

Model v0.3 used `N_ind = min(N_chirps, dwell * B_weather)` as the averaging count for **detection**. That count is right for the *precision* of a reflectivity estimate once the echo is reasonably above noise, but it is pessimistic for detecting a weak echo.

At low single-chirp SNR the detection limit is set by the fluctuation of the **noise** power estimate. Receiver noise is independent from chirp to chirp, so averaging all chirps in the dwell reduces it as `sqrt(N_chirps)` regardless of how correlated the weather signal is (radiometer equation). Capping the count at the weather decorrelation count discards real averaging gain.

A better practical estimator also uses the slow-time spectrum. After a Doppler FFT, weather occupies roughly `B_weather` of the `PRF = 1/T` slow-time bandwidth. Summing only the bins the echo occupies keeps all of the signal and only a `B_weather / PRF` fraction of the noise. This is standard spectral processing and assumes the spectral position of the echo is estimated from the data.

The simulator now reports three estimators side by side:

| Estimator | Significance | Use |
|---|---|---|
| (a) independent looks (v0.3) | `SNR_chirp + 5 log10(N_ind)` | precision of Z at moderate/high SNR; kept for traceability |
| (b) radiometer, all chirps | `SNR_chirp + 5 log10(N_chirps)` | detection without Doppler filtering |
| (c) Doppler-band filtered (**primary**) | `SNR_band + 5 log10(M)`, with `SNR_band` using noise bandwidth `ENBW * min(B_weather, PRF)` and `M = min(N_chirps, dwell * min(B_weather, PRF))` | detection with slow-time spectral processing |

`Zmin_engineering = Zmin(c) + implementation margin`. The margin stays explicit and is not folded into RF losses.

### Effect on the baseline

Defaults: 1 W CW, eta = 0.55, NF = 3 dB, RF loss 4 dB, B = 1 MHz, T = 1 ms, Hann ENBW 1.5, sigma_v = 2 m/s, 120 deg in 30 s, threshold 3 dB, margin 6 dB, 30 km, no rain on the path.

| Configuration | (a) v0.3 | (b) radiometer | (c) Doppler band | Engineering (c + 6 dB) |
|---|---|---|---|---|
| C 5.8 GHz, 1.70 m TX + 1.70 m RX | 13.9 | 10.3 | 6.7 | 12.7 |
| C 5.8 GHz, 0.60 m TX + 1.70 m RX | 20.4 | 16.9 | 13.3 | 19.3 |
| X 9.5 GHz, 1.70 m TX + 1.70 m RX | 5.3 | 2.8 | 0.3 | 6.3 |
| X 9.5 GHz, 0.60 m TX + 1.70 m RX | 11.8 | 9.4 | 6.9 | 12.9 |

Values in dBZ at 30 km. With the explicit 6 dB margin, C band with two 1.70 m apertures misses the 10 dBZ target by about 2.7 dB at 1 W. Roughly 2 W CW, or a lower NF / RF loss, closes it on paper. The v0.3 estimator would have implied about 10 W for the same result.

These are still design estimates. TX-to-RX leakage and synthesizer phase noise on terrain clutter are not modeled from first principles and may dominate in practice.

### Precipitation attenuation

The simulator now applies two-way specific attenuation from ITU-R P.838-3 coefficients (horizontal polarization, log-frequency interpolation) over a user-defined path length through rain. Example: 10 km of 50 mm/h rain costs about 6 dB two-way at 5.8 GHz and about 29 dB at 9.5 GHz. This is the main reason C band remains Band A despite X band's sensitivity advantage for fixed apertures.
