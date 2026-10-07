# Architecture — v0.1

## System concept

BWR-1 is a sector-scanning FMCW meteorological radar. TX and RX are treated as independent design problems.

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

## Receive antenna

The 1.70 m reflector is currently the preferred high-gain RX candidate. It must scan the useful W/SW sector rather than 360 degrees.

A large reflector is directional; high receive gain therefore requires accurate pointing.

## Azimuth mechanism

Candidate low-cost mechanism:

- independent structural bearings support the reflector;
- automotive windshield-wiper motor/reduction mechanism supplies oscillatory motion;
- adjustable crank/linkage sets sector width;
- motor does **not** carry the reflector structural load;
- an angle sensor measures actual reflector azimuth;
- acquisition occurs in both sweep directions.

The wiper linkage's non-uniform angular velocity is acceptable because samples are tagged with measured azimuth rather than inferred from time.

An absolute angular encoder is preferred.

## Elevation

Initial operation may use a fixed elevation. Mechanical design should avoid preventing later stepped elevation scans.

## TX/RX separation

Separate TX and RX antennas are attractive for FMCW because transmitter leakage into the receiver is a major dynamic-range problem.

TX beamwidth may be wider than RX beamwidth, provided the TX adequately illuminates every volume observed by RX.

## Signal chain

### TX

```text
stable reference -> chirp synthesizer -> driver -> PA -> BPF -> TX antenna
```

### RX

```text
RX feed -> BPF -> low-noise amplifier -> optional gain -> I/Q mixer -> IF filtering/gain -> ADC
```

Place the first LNA as close as practical to the receive feed. Loss before the first LNA directly degrades system noise figure.

## Processing

FMCW range is obtained from beat frequency. Repeated chirps allow Doppler processing.

The base observation tuple should eventually contain at least:

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

Dry-weather scans will be used to characterize stationary clutter. Calibration will later use local precipitation observations plus external radar/meteorological references.

## Open decisions

1. C versus X as the first implemented RF chain.
2. Chirp bandwidth and duration.
3. Required TX power after link-budget calculation.
4. TX antenna gain/beamwidth.
5. RX LNA noise figure and gain.
6. ADC sample rate/effective number of bits.
7. FPGA/SBC division of DSP work.
8. Feed geometry for each band.
9. Exact sector limits and elevation strategy.
