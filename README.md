# Bobby Weather Radar (BWR-1)

Experimental, low-cost weather-radar project for rural nowcasting.

The goal is a **sector-scanning FMCW weather radar** optimized for convective storms approaching from the west/southwest, using COTS parts, reusable electronics and salvaged mechanics where practical.

## Baseline goals

- Sector scan: about 90–120 degrees
- Nominal range: >= 30 km; 50 km stretch goal
- Initial sensitivity target: <= 10 dBZ at 30 km (design target; not yet demonstrated)
- Initial range resolution: ~150 m
- Update interval: <= 30 s initially
- Products: range, received power/reflectivity, Doppler velocity, PPI
- **Band A baseline: C band near 5.8 GHz**, subject to regulatory and link-budget closure
- Future Band B candidate: X band (~9–10 GHz)
- Architecture: FMCW with separate TX/RX
- Preferred RX reflector: 1.70 m
- TX should have comparable gain to RX; a 0.60 m TX reflector has ~9 dB less antenna gain than 1.70 m at the same frequency, which costs ~6.6 dB of meteorological sensitivity (the wider TX beam slightly enlarges the illuminated volume)
- Initial scan is sectoral rather than 360 degrees
- Future integration: Beackman / Chuvalski

This repository starts with requirements and engineering calculations. RF parts should not be selected merely because they are cheap: every significant RF purchase should map to a link-budget requirement.

## Status

**Architecture / requirements definition.** C band near 5.8 GHz is now the preferred first implementation, but RF power, exact frequency, waveform timing and final RF BOM remain unfrozen until the quantitative link budget and regulatory constraints are closed.

See [requirements](docs/requirements.md), [architecture](docs/architecture.md), [link-budget notes](docs/link-budget.md), and [references](docs/references.md).

The interactive link-budget model lives in [`simulations/link-budget/index.html`](simulations/link-budget/index.html). It is a single self-contained page: open it in any browser, no build or server needed. CI runs it against the baseline table in the link-budget notes, so the documented numbers and the model cannot drift apart.

Work is tracked in [issues](https://github.com/mptagliari/weather-radar/issues) grouped by [milestones](https://github.com/mptagliari/weather-radar/milestones) that follow the integration sequence. Measurements and engineering decisions have their own issue templates.

## Design philosophy

Build one radar in modules. Bench tests validate modules; they are not separate product generations. Changes are documented as engineering revisions.

The project aims to use WMO/ISO weather-radar practices as engineering references where applicable. It does **not** claim WMO certification or operational equivalence to a professional radar network.

## License

BWR-1 is open hardware and free software, and every part of it stays open when shared:

- **Hardware design** (mechanics, antennas, RF, PCBs, BOM): [CERN-OHL-S-2.0](LICENSES/CERN-OHL-S-2.0.txt)
- **Firmware, DSP, tools, simulations**: [GPL-3.0-or-later](LICENSES/GPL-3.0-or-later.txt)
- **Network services** (data server, PPI/web publishing, APIs): [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt)
- **Documentation**: [CC-BY-SA-4.0](LICENSES/CC-BY-SA-4.0.txt)

See [LICENSING.md](LICENSING.md) for the path-by-path map, the reasons behind each choice, use of the project name, and the builder's responsibility for radio regulation in their own country.
