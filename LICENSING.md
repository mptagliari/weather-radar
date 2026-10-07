# Licensing

BWR-1 is open hardware and free software. Different parts of the project are different kinds of work, so each part uses the license built for that kind of work. All of them are reciprocal: improvements that are distributed must stay open.

| Part of the project | Paths | License |
|---|---|---|
| Hardware design sources: mechanics, antennas/feeds, RF chains, PCBs, BOM | `hardware/`, `bom/` | [CERN-OHL-S-2.0](LICENSES/CERN-OHL-S-2.0.txt) |
| Firmware, DSP, tools, simulations, CI and repository templates | `firmware/`, `software/`, `simulations/`, `.github/` | [GPL-3.0-or-later](LICENSES/GPL-3.0-or-later.txt) |
| Network-facing services: data server, PPI/web publishing, APIs | `server/` | [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt) |
| Documentation, requirements, references, images | `README.md`, `LICENSING.md`, `docs/` | [CC-BY-SA-4.0](LICENSES/CC-BY-SA-4.0.txt) |

The machine-readable map is [`REUSE.toml`](REUSE.toml), following the [REUSE](https://reuse.software) specification. A file's own `SPDX-License-Identifier` header takes precedence over the map.

## Why these licenses

**Hardware: CERN-OHL-S-2.0 (strongly reciprocal).** If you distribute a modified BWR-1 design, or products made from it, the modified design sources must be published under the same license. Off-the-shelf parts (an SDR, an MMIC, a commercial LNA) are "Available Components" under the licence and do not need to be open.

**Software: GPL-3.0-or-later.** Version 3 is required, not version 2: the ESP32 firmware builds against ESP-IDF, which is Apache-2.0, and Apache-2.0 is compatible with GPLv3 but not with GPLv2.

**Network services: AGPL-3.0-or-later.** If someone runs a modified BWR-1 data or PPI service for other people over a network, they must offer those users the modified source. Plain GPL would not require that. AGPL-3.0 and GPL-3.0 code may be combined (section 13 of both licenses).

**Documentation: CC-BY-SA-4.0.** Reuse and adaptation are welcome with attribution and under the same terms. CC-BY-SA-4.0 is one-way compatible with GPL-3.0.

## What the licenses do not cover

- **The name.** "BWR-1" and "Bobby Weather Radar" identify this project. You may build, modify and share BWR-1 under the licenses above, but please do not present a modified or commercial build as the official BWR-1 without saying it is derived and modified.
- **Radio regulation.** BWR-1 transmits. Every builder is responsible for the frequency, power, EIRP and emission limits and for any authorization required where the radar operates (Anatel in Brazil, or the equivalent authority elsewhere). The licenses grant copyright permissions only; they do not authorize any transmission.
- **Fitness and safety.** All licenses above are provided without warranty. A home-built weather radar is an experimental instrument, not a certified warning system. Do not rely on it alone for safety-of-life decisions.

## Contributing

By submitting a contribution you agree it is licensed under the license that applies to the path where it lands, as listed above. Add an SPDX header to new source files when the format allows it.
