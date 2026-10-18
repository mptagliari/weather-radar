<!--
SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->
# Azimuth controller core

Hardware-independent control logic for the azimuth drive (issue #11): programmable sector scan with reversal at the limits, stare, and safe parking. It takes the antenna-axis angle and returns a signed motor command in [-1, 1] for the H-bridge.

Not yet written: the ESP32-class port (encoder driver for the AS5048A-class sensor, PWM/H-bridge output, current limit, watchdog and wind-driven park). The core is plain C11 so it can be reused there.

```sh
make -C firmware/azimuth      # builds and runs the host tests
```

The tests close the loop around a crude plant (first-order lag plus dead zone). They check control **logic** (limits, reversal, wrap across north, shortest-way parking), not gain tuning: the gains in `test.c` are placeholders until the real wiper motor and gearbox are characterized.

Known limits of this first version:

- Encoder is assumed absolute on the antenna axis, after gearbox backlash (REQ-007); no backlash compensation.
- Reversal at the limit is handled by a 10° overshoot window; real stopping distance depends on the mechanics.
- No fault handling (stall, encoder loss, over-current) yet; this must exist before unattended outdoor operation (REQ-015).
