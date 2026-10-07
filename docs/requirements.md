# BWR-1 Requirements — v0.2

## Mission

Provide local, quantitative nowcasting of convective precipitation approaching a rural property, with emphasis on storms arriving from the west/southwest sector.

## Functional requirements

| ID | Requirement | Initial target |
|---|---|---|
| REQ-001 | Nominal meteorological range | >= 30 km |
| REQ-002 | Stretch range | 50 km |
| REQ-003 | Sector coverage | ~90–120 deg |
| REQ-004 | Sensitivity design target | <= 10 dBZ at 30 km |
| REQ-005 | Initial range resolution | ~150 m |
| REQ-006 | Initial volume/update time | <= 30 s |
| REQ-007 | Azimuth knowledge | <= 0.2–0.3 deg; pursue ~0.1 deg after calibration |
| REQ-008 | Acquisition | bidirectional programmable sector sweeps plus stare mode |
| REQ-009 | Measurements | range, received power, Doppler |
| REQ-010 | Primary visualization | PPI |
| REQ-011 | Calibration | repeatable response first; absolute Z calibration later |
| REQ-012 | Data integration | structured output suitable for Beackman |
| REQ-013 | Solar calibration | support Sun-based pointing/gain stability checks |
| REQ-014 | RF compliance | exact operating frequency, EIRP and emission constraints must be closed before outdoor high-gain TX |
| REQ-015 | Weather survivability | structure, bearings, parking strategy, grounding and surge protection designed for severe-weather operation |

## Environmental/meteorological scope

The first operational problem is severe-convection nowcasting, not nationwide surveillance. Sectoral scanning is intentional because severe storms of practical interest overwhelmingly approach from W/SW in the target area.

Multi-elevation scanning is desirable after azimuth scanning is proven.

## RF baseline

**Band A:** C band near 5.8 GHz is the preferred first implementation. The exact center frequency is not frozen until regulatory constraints, filters, available components and the link budget are closed.

Reasons for preferring C first include lower precipitation attenuation than X band and a strong ecosystem of 5 GHz RF hardware.

**Band B:** X band (~9–10 GHz) remains a future complementary channel. It is no longer treated as an equal first-build candidate; its higher attenuation in intense precipitation makes C preferable for the primary penetration/nowcasting mission.

## Existing antenna assets

- 1 x 1.70 m parabolic reflector
- 2 x 0.60 m parabolic reflectors

Feeds are **not assumed reusable** merely because the reflectors are reusable. Reflector geometry, focal ratio, illumination, surface accuracy and polarization must be characterized.

A TX antenna with gain comparable to the RX antenna is preferred. At equal frequency/efficiency, reducing diameter from 1.70 m to 0.60 m costs approximately 9 dB of antenna gain, which translates into roughly 6.6 dB of meteorological sensitivity because the wider TX beam slightly enlarges the illuminated volume (see the link-budget model). A very broad fixed-sector TX is therefore not the baseline.

## Mechanics

- Reflector structural load must be carried by dedicated bearings/structure.
- Baseline azimuth drive is a geared automotive wiper motor driven bidirectionally by an H-bridge, **without the original crank/linkage motion law**.
- Closed-loop angle feedback is measured on the antenna axis after gearbox/backlash, preferably with an absolute encoder.
- The controller must support programmable sector limits, approximately constant scan rate, stare mode and a safe parking position.

## Calibration and clutter

Solar observations should be supported for pointing-error and receive-chain stability checks. Dry-weather clutter maps and Doppler-domain rejection near zero radial velocity are complementary tools; neither should be the sole clutter strategy.

## Standards/reference philosophy

Use WMO-No. 8 / ISO-WMO weather-radar guidance and WMO-No. 1257 as engineering references for terminology, sensitivity, calibration, scan strategy, quality control and metadata where applicable.

BWR-1 is experimental/open hardware and does not claim certification.

## Change control

Requirements may change when calculations or measurements justify the change. A requirement should not silently drift: document why it changed and preserve the history in Git.
