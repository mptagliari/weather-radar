# Architecture — v0.2

## System concept

BWR-1 is a sector-scanning FMCW meteorological radar. TX and RX are treated as independent RF chains but scan the same atmospheric volume.

```text
              precipitation / hydrometeors
                       ^     |
                       |     | echo
                  illumination
                       |     v
                    TX ANT  RX reflector
                       |       |
                      PA      feed
                       |       |
chirp/reference -------+      BPF
        |                      |
        +--------------------> LNA
        |                      |
        +---- LO ----------> I/Q mixer
                              |
                           IF / LPF
                              |
                             ADC
                              |
                             DSP
                              |
                 range + Doppler + power
                              |
azimuth encoder --------------+
                              |
                             PPI
                              |
                         Beackman output
```

## RF baseline

Band A is C band near 5.8 GHz. Exact center frequency remains TBD pending regulatory closure and component/filter selection.

Band B may later add X band as a complementary channel after Band A is operational and calibrated.

Initial waveform baseline for engineering calculations:

- FMCW
- bandwidth: ~1 MHz
- ideal range bin: ~150 m
- chirp duration: ~1 ms starting point, not a fundamental requirement
- staggered chirp timing is a candidate for Doppler ambiguity resolution
- triangular/up-down chirps are a candidate for range-Doppler decoupling

## Antennas

The 1.70 m reflector is currently the preferred high-gain RX candidate.

TX gain matters directly to meteorological sensitivity. A 0.60 m TX reflector loses roughly 9 dB versus 1.70 m at equal frequency and efficiency. Therefore the baseline is **not** a stationary wide-sector transmitter. Preferred options are comparable-gain TX/RX apertures scanning together, or a smaller TX only if the PA/link budget explicitly pays the gain penalty.

TX beam should illuminate the complete RX-observed volume with modest margin rather than unnecessarily illuminating the full sector.

## Azimuth mechanism

Revised low-cost mechanism:

- independent structural bearings support the reflector;
- automotive wiper motor is used as a geared reversible drive rather than through a crank/biela oscillator;
- H-bridge provides bidirectional motor control;
- absolute angle sensor is mounted on the **antenna axis**, downstream of gearbox backlash;
- closed-loop control provides programmable sector limits and approximately constant scan rate;
- acquisition may occur in both directions;
- controller supports stare mode and safe parking.

The earlier crank/linkage concept is superseded.

## Elevation

Initial operation may use a fixed elevation. Mechanical design should avoid preventing later stepped elevation scans.

Final elevation must consider terrain/horizon and effective-Earth-radius beam geometry rather than using a generic angle blindly.

## TX/RX separation

Separate TX and RX antennas are attractive for FMCW because transmitter leakage into the receiver is a major dynamic-range problem.

Isolation, direct leakage and close-range clutter must be treated as receiver dynamic-range requirements, not merely as sensitivity losses.

## Signal chain

### TX

```text
stable reference -> chirp synthesizer/SDR -> driver -> PA -> BPF -> TX antenna
```

### RX

```text
RX feed -> BPF -> low-noise amplifier -> optional gain -> coherent I/Q receiver -> IF/baseband filtering -> ADC
```

Place the first LNA as close as practical to the receive feed. Loss before the first LNA directly degrades system noise figure.

A full-duplex coherent SDR is a candidate for early integration testing. A dedicated FMCW PLL/RF chain remains a later optimization option.

## IF / dynamic range

Because FMCW beat frequency maps to range, an analog frequency-dependent gain/STC network may compensate part of the approximately R^-2 weather-echo power dependence and suppress leakage/near clutter before the ADC.

This is **not frozen**. The receiver should preserve a linear/raw path or bypass so STC effects can be measured and calibrated rather than hidden.

Synthesizer phase noise in the presence of strong terrain clutter is expected to be a major design variable and must be characterized alongside receiver NF.

## Processing

Repeated FMCW chirps provide range and Doppler information. The baseline data path should eventually contain at least:

```text
timestamp
azimuth
elevation
range
received_power
doppler_velocity
quality_flags
calibration_state
```

Staggered chirp intervals and/or up/down sweeps should be evaluated for velocity ambiguity and range-Doppler coupling.

Dry-weather scans characterize stationary clutter. Doppler filtering around 0 m/s complements, rather than replaces, the static clutter map.

## Calibration

Solar observations should be supported as a repeatable external reference for:

- azimuth/elevation pointing error;
- encoder alignment;
- receive-chain stability;
- relative gain monitoring.

Local precipitation measurements and external meteorological radars may later support reflectivity/rainfall validation.

## Electrical/environmental protection

The outdoor antenna platform requires deliberate grounding and surge protection on RF/coax and encoder/control wiring. Severe-weather operation is a primary use case, so wind loading and a safe parking orientation are first-order mechanical requirements.

## Integration sequence

1. Characterize reflector geometry/surface and close regulatory constraints.
2. Bench radar with coherent SDR + two fixed 5 GHz antennas against a known static target; validate chirp, leakage, IF and range FFT.
3. Develop mechanics/encoder in parallel; validate pointing independently, including solar observations when practical.
4. Install high-gain apertures, feed/LNA and PA; obtain first precipitation echoes in fixed stare mode.
5. Enable sector scan, PPI and clutter processing.
6. Perform solar, rain-gauge and external-radar calibration/validation.
7. Consider X-band Band B only after C-band Band A is understood.

These are integration/verification steps for one BWR-1, not separate prototype generations.

## Open decisions

1. Exact C-band operating frequency and regulatory/EIRP constraints.
2. Quantitative meteorological link budget and required TX power.
3. TX aperture/gain and mechanical arrangement.
4. Exact chirp timing/stagger scheme.
5. Phase-noise requirement.
6. RX LNA noise figure/gain.
7. ADC/SDR architecture and effective dynamic range.
8. Feed geometry.
9. Exact sector limits and elevation strategy.
