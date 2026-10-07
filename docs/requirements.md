# BWR-1 Requirements — v0.1

## Mission

Provide local, quantitative nowcasting of convective precipitation approaching a rural property, with emphasis on storms arriving from the west/southwest sector.

## Functional requirements

| ID | Requirement | Initial target |
|---|---|---|
| REQ-001 | Nominal meteorological range | >= 30 km |
| REQ-002 | Stretch range | 50 km |
| REQ-003 | Sector coverage | ~90–120 deg |
| REQ-004 | Sensitivity design target | <= 10 dBZ at 30 km |
| REQ-005 | Range resolution | 50–150 m |
| REQ-006 | Initial volume/update time | <= 30 s |
| REQ-007 | Azimuth knowledge | target <= 0.2–0.3 deg error |
| REQ-008 | Acquisition | bidirectional sector sweeps |
| REQ-009 | Measurements | range, received power, Doppler |
| REQ-010 | Primary visualization | PPI |
| REQ-011 | Calibration | repeatable response first; absolute Z calibration later |
| REQ-012 | Data integration | structured output suitable for Beackman |

## Environmental/meteorological scope

The first operational problem is severe-convection nowcasting, not nationwide surveillance. Sectoral scanning is intentional because severe storms of practical interest overwhelmingly approach from W/SW in the target area.

Multi-elevation scanning is desirable after azimuth scanning is proven.

## Candidate bands

Two bands remain under engineering evaluation:

- **C band:** approximately 5–6 GHz.
- **X band:** approximately 9–10 GHz.

The project may ultimately use both. No dual-band architecture is frozen until both meteorological link budgets are calculated.

## Existing antenna assets

- 1 x 1.70 m parabolic reflector
- 2 x 0.60 m parabolic reflectors

Feeds are **not assumed reusable** merely because the reflectors are reusable. Reflector geometry, focal ratio, illumination, surface accuracy and polarization must be characterized.

## Standards/reference philosophy

Use WMO-No. 8 / ISO-WMO weather-radar guidance and WMO-No. 1257 as engineering references for terminology, sensitivity, calibration, scan strategy, quality control and metadata where applicable.

BWR-1 is experimental/open hardware and does not claim certification.

## Change control

Requirements may change when calculations or measurements justify the change. A requirement should not silently drift: document why it changed and preserve the history in Git.
