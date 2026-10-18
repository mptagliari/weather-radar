# Phase noise and dynamic range — working notes v0.1

Companion to [link-budget notes](link-budget.md). The link-budget model carries TX→RX leakage, phase noise on terrain clutter and ADC limits as a single explicit 6 dB engineering margin. This note replaces that margin with first-order calculations so the open decisions (#8 ADC/SDR, #9 leakage, #10 phase noise) have numbers to argue with.

Code: [`simulations/dynamic-range/`](../simulations/dynamic-range/) (`model.mjs`, `report.mjs`, `test.mjs`). It reuses `compute()` from the link-budget page without modifying it. Run `node simulations/dynamic-range/report.mjs [key=value ...]`.

**Everything below is a design estimate built on assumed inputs.** The clutter cross-section, the synthesizer phase-noise curve, the TX→RX isolation and the ADC figures are placeholders until measured. Treat the *shape* of the results (which term dominates, how requirements scale) as more reliable than the absolute numbers.

## Method

All levels are referred to the receiver input reference plane, the same plane as the received weather power in the link budget.

**Phase noise on clutter.** A strong clutter line at range R_c has a beat frequency `f_c = S·2R_c/c`. The synthesizer phase-noise skirt of that line lands in the weather range bin at offset `f_off = |f_w − f_c|`. Because the same oscillator generates TX and LO, the beat sees the phase noise attenuated by range correlation:

```text
N_pn = P_clutter + L(f_off) + 10 log10( 4 sin²(π f_off τ_c) ) + 10 log10(B_bin)
τ_c  = 2 R_c / c          B_bin = ENBW / T_chirp
```

The Zmin degradation is `10 log10(1 + N_pn / N_thermal)`. The required `L(f_off)` is the value that keeps it within a stated allowance (1 dB by default).

**Dynamic range.** The strongest line at the ADC is the larger of the TX→RX leakage (`P_tx − isolation − rejection`) and the clutter. The weather echo must sit above ADC noise, and the strongest line below full scale with headroom. That gives a window of receiver gain; if its lower bound exceeds its upper bound the architecture cannot work as drawn.

## Results under the default assumptions

Defaults: C 5.8 GHz, 1 W, B = 1 MHz, T = 1 ms, weather at 30 km; clutter 30 dBsm at 3 km; L(100 kHz) = −100 dBc/Hz falling 20 dB/decade; TX→RX isolation 60 dB; ADC 10 effective bits, 2 MSPS, +4 dBm full scale, 6 dB back-off.

| Quantity | 2×1.70 m | TX 0.60 m + RX 1.70 m |
|---|---|---|
| Weather at 10 dBZ / 30 km | −150.2 dBm | −156.7 dBm |
| Thermal noise per range bin | −139.2 dBm | −139.2 dBm |
| Clutter at the receiver | −66.4 dBm | −75.5 dBm |
| Zmin degradation from phase noise | 6.2 dB | 1.4 dB |
| **L(180 kHz) required for ≤ 1 dB** | **−116.0 dBc/Hz** | −106.9 dBc/Hz |

Dynamic range:

| TX→RX isolation | Leakage at RX | Extra leakage reduction needed | ADC window |
|---|---|---|---|
| 40 dB | −10 dBm | 55 dB | infeasible |
| 60 dB | −30 dBm | 35 dB | infeasible |
| 80 dB | −50 dBm | 15 dB | infeasible |
| 100 dB | −70 dBm | 0 dB | feasible, ~1 dB of window |

## What this suggests

1. **Phase noise matters more than the 6 dB margin implies.** With strong clutter at a few kilometres and a moderate synthesizer, the phase-noise floor can exceed thermal noise by several dB at the weather bin. The requirement scales steeply with clutter strength, so it depends on the dry-weather clutter map (issue #20) more than on the synthesizer data sheet. A single "−X dBc/Hz" number cannot be frozen without that measurement.
2. **The equal-aperture configuration is the harder one.** Higher gain also raises clutter, so the same synthesizer degrades the 2×1.70 m case by about 5 dB more than the 0.60 m TX case. The extra TX gain does not translate one-for-one into sensitivity once clutter is considered.
3. **Direct leakage is the dominant dynamic-range problem.** At 60 dB isolation the leakage line sits about 109 dB above the thermal bin, far beyond what a 10-bit ADC provides. Either isolation near 100 dB, an analog high-pass/notch on the near-DC beat before the ADC, or active cancellation is needed. This is consistent with the architecture note that leakage is a dynamic-range requirement, and it argues for measuring isolation early (issue #9) before choosing the ADC (issue #8).
4. **A higher-resolution ADC buys window directly** (a few bits is tens of dB), but only if the analog front end preserves the linearity to use it.

## What the model leaves out

- **Slow-time phase noise.** Phase noise also spreads clutter in the Doppler domain, which limits how deep the zero-velocity filter (issue #20) can reject. Not modeled.
- **Distributed clutter.** One point clutter line stands in for a whole terrain profile; real ground clutter is spread over many ranges and adds up.
- **Spurs and leakage-related noise.** Leakage-line phase noise is largely correlated out (its τ is near zero) and is neglected, but LO/TX spurs and reflections from nearby structures are not.
- **STC / range compensation** (issue #18) changes the gain window versus range. A flat gain is assumed here.
- **Receiver compression** beyond a simple LNA check, mixer limits and ADC aliasing of out-of-band beat frequencies.

## Inputs to measure

| Input | Measure with | Issue |
|---|---|---|
| TX→RX isolation (dB) | two antennas on the mount, CW | #9 |
| Clutter level vs range | dry-weather fixed-azimuth scan | #20 |
| Synthesizer L(f) at 50–500 kHz | spectrum analyser on the candidate source | #10 |
| ADC effective bits at the beat frequencies | ADC test with a tone sweep | #8 |
