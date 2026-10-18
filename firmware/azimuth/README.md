<!--
SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->
# Azimuth controller core

Hardware-independent control logic for the azimuth drive (issue #11): programmable sector scan with reversal at the limits, stare, and safe parking. It takes the antenna-axis angle and returns a signed motor command in [-1, 1] for the H-bridge.

## Layout

| File | Role | Tested |
|---|---|---|
| `azctl.[ch]` | control core: sector scan, stare, park, PI rate loop | host tests |
| `azsup.[ch]` | supervisor: HAL boundary, command ramp, latched faults (encoder loss, stall, over-current, late tick) | host tests, fake HAL |
| `as5048a.[ch]` | AS5048A SPI frame parity/decoding | host tests |
| `esp32/` | PlatformIO project wiring the above to SPI, PWM and an ADC | **not built, not run** |

```sh
make -C firmware/azimuth      # builds and runs the host tests
```

The `esp32/` port was written without a toolchain or hardware. Pins, the current-sense scale and all gains are placeholders. Treat it as a starting point to be built and checked on the bench, not as working firmware.

Still open: wind-driven park, gain tuning on the real motor, backlash and stopping-distance characterization.

The tests close the loop around a crude plant (first-order lag plus dead zone). They check control **logic** (limits, reversal, wrap across north, shortest-way parking), not gain tuning: the gains in `test.c` are placeholders until the real wiper motor and gearbox are characterized.

Known limits of this first version:

- Encoder is assumed absolute on the antenna axis, after gearbox backlash (REQ-007); no backlash compensation.
- Reversal at the limit is handled by a 10° overshoot window; real stopping distance depends on the mechanics.
- Fault limits (stall time, current) are placeholders. A latched fault cuts motor power and relies on the worm gear to hold the antenna; verify that holds in wind before unattended outdoor operation (REQ-015).
