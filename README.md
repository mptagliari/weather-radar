# Bobby Weather Radar (BWR-1)

Experimental, low-cost, open weather-radar project for rural nowcasting.

The goal is a **sector-scanning FMCW weather radar** optimized for convective storms approaching from the west/southwest, using COTS parts, reusable electronics and salvaged mechanics where practical.

## Baseline goals

- Sector scan: about 90–120 degrees
- Nominal range: >= 30 km; 50 km stretch goal
- Initial sensitivity target: <= 10 dBZ at 30 km (design target; not yet demonstrated)
- Range resolution target: 50–150 m
- Update interval: <= 30 s initially
- Products: range, received power/reflectivity, Doppler velocity, PPI
- Candidate bands: C (~5–6 GHz) and X (~9–10 GHz)
- Architecture: FMCW with separate TX/RX considered first
- Large receive reflector available: 1.70 m
- Two additional 0.60 m reflectors available
- Initial scan is sectoral rather than 360 degrees
- Future integration: Beackman / Chuvalski

This repository starts with requirements and engineering calculations. RF parts should not be selected merely because they are cheap: every significant RF purchase should map to a link-budget requirement.

## Status

**Concept / requirements definition.** No final RF band or RF BOM has been frozen.

See [requirements](docs/requirements.md), [architecture](docs/architecture.md), [link-budget notes](docs/link-budget.md), and [references](docs/references.md).

## Design philosophy

Build one radar in modules. Bench tests validate modules; they are not separate product generations. Changes are documented as engineering revisions.

The project aims to use WMO/ISO weather-radar practices as engineering references where applicable. It does **not** claim WMO certification or operational equivalence to a professional radar network.
