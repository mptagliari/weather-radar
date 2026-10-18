# Radar data format — draft v0.1

Defines what one BWR-1 acquisition produces and how it is handed to consumers (PPI rendering, archive, Beackman / Chuvalski). Resolves the field list left open in [architecture](architecture.md) and tracked in issue #19.

This is a **draft interface**, not a frozen one. Nothing here has been exercised against real hardware; fields and units may change when the bench radar (issue #7) produces real data. Changes are documented, not silent.

## Design choices

- **Unit of data: the ray.** One ray is one dwell at one azimuth/elevation, with a value per range gate. A PPI is a set of rays; a scan is a set of rays with the same sweep metadata. This matches how a sector scan with a slowly moving antenna naturally produces data, and maps cleanly onto the radial-based structure used by common weather-radar formats.
- **Raw before derived.** `power_dbm` (received power at the receiver reference plane) is always present. `reflectivity_dbz` is derived from it and is only meaningful when a calibration is applied (REQ-011: repeatable response first, absolute Z later).
- **Honest missing data.** Gates without a valid estimate are `null`, never `0`. Reasons live in `quality_flags`.
- **Transport-neutral.** The canonical form is JSON (one ray per line, NDJSON, for streaming and archives). A binary encoding can be added later for the radar-to-server link without changing the field semantics.
- **Export, not lock-in.** A later exporter to a standard weather-radar format (for example OPERA/ODIM_H5) is expected. The field names below are chosen to be convertible; no claim of conformance is made.

The ray record is also available as a JSON Schema, [`schemas/ray.schema.json`](schemas/ray.schema.json), with tests in `software/tools/test_schema.py` (the example below is validated against it in CI). The schema rejects reflectivity without an applied calibration, and an `uncalibrated` state marked as applied; equal per-gate array lengths are checked separately because JSON Schema cannot express them.

## Conventions

| Quantity | Unit | Convention |
|---|---|---|
| time | UTC | RFC 3339, `Z` suffix, millisecond precision. Ray timestamp is the dwell **midpoint**. |
| azimuth | degrees | 0–360, clockwise from **true** north, antenna-axis angle after gearbox (REQ-007). |
| elevation | degrees | above the local horizontal. Fixed value allowed. |
| range | metres | to gate **centre**; `range_start_m` + `gate_index * range_step_m`. |
| power | dBm | at a documented reference plane (see `calibration`). |
| reflectivity | dBZ | only with an applied calibration. |
| velocity | m/s | **positive away from the radar**. |

True north versus magnetic north must be recorded in `site` metadata; solar calibration (issue #21) is the intended way to verify the azimuth offset.

## Ray record

One JSON object per ray.

| Field | Type | Required | Description |
|---|---|---|---|
| `schema` | string | yes | `bwr1.ray/0.1` |
| `time` | string | yes | Dwell midpoint, UTC. |
| `scan_id` | string | yes | Identifier of the sweep this ray belongs to. |
| `ray_index` | integer | yes | Position within the sweep, from 0. |
| `azimuth_deg` | number | yes | Mean azimuth over the dwell. |
| `azimuth_span_deg` | number | no | Azimuth travelled during the dwell (beam smearing). |
| `elevation_deg` | number | yes | |
| `scan_mode` | string | yes | `sector`, `stare`, or `park`. |
| `range_start_m` | number | yes | Centre of gate 0. |
| `range_step_m` | number | yes | Gate spacing. Ideal ~150 m at B = 1 MHz; the gate step may be smaller than the true resolution when zero-padded. |
| `power_dbm` | number[] | yes | Per-gate received power, `null` where invalid. |
| `reflectivity_dbz` | number[] | no | Per-gate Z; present only when `calibration.applied` is true. |
| `velocity_ms` | number[] | no | Per-gate Doppler velocity, `null` where invalid. |
| `velocity_unfolded` | boolean | no | True if an ambiguity-resolution scheme was applied (issue #17). |
| `quality_flags` | integer[] | yes | Per-gate bitmask, same length as `power_dbm`. See below. |
| `calibration` | object | yes | State when the ray was taken. See below. |
| `waveform` | object | yes | `bandwidth_hz`, `chirp_s`, `n_chirps`, `centre_freq_hz`, `window` (`rect` or `hann`). |

All per-gate arrays share the same length.

### `quality_flags` bits

| Bit | Name | Meaning |
|---|---|---|
| 0 | `BELOW_THRESHOLD` | Estimate under the detection threshold; value is noise-limited. |
| 1 | `CLUTTER_MAP` | Gate flagged by the dry-weather clutter map (issue #20). |
| 2 | `ZERO_VELOCITY_FILTERED` | Zero-Doppler rejection altered the estimate. |
| 3 | `LEAKAGE_ZONE` | Gate within the TX→RX leakage / near-range region (issue #9). |
| 4 | `SATURATED` | ADC or front-end saturation in the dwell. |
| 5 | `ATTENUATION_UNCORRECTED` | Path attenuation is **not** corrected; Z is a lower bound behind precipitation. |
| 6 | `VELOCITY_AMBIGUOUS` | Velocity may be folded. |
| 7 | `POINTING_UNVERIFIED` | Azimuth offset not yet validated against a solar pass. |

Bit assignments are append-only after v1.0.

### `calibration`

| Field | Type | Description |
|---|---|---|
| `applied` | boolean | Whether `reflectivity_dbz` was derived. |
| `state` | string | `uncalibrated`, `relative` (repeatable response), or `absolute`. |
| `reference_plane` | string | Where `power_dbm` is referenced, e.g. `adc_input` or `lna_input`. |
| `constant_db` | number | Radar constant offset used for Z, if any. |
| `rf_temperature_c` | number | RF module temperature at the time (stability tracking). |
| `last_solar_check` | string | Time of the last solar pointing/gain check, if any. |

Until REQ-011's absolute calibration exists, consumers must treat `state: "uncalibrated"` data as **relative power only**.

## Sweep and site metadata

Sent once per sweep and stored alongside the rays.

```json
{
  "schema": "bwr1.sweep/0.1",
  "scan_id": "2026-10-18T15:00:00Z-0001",
  "site": { "lat": null, "lon": null, "antenna_height_m_agl": null, "north_reference": "true" },
  "sector_deg": { "start": 200, "end": 320 },
  "direction": "cw",
  "ray_count": 240,
  "software_version": "unreleased"
}
```

Site coordinates are left to the operator; the repository does not publish a location.

## Example ray

```json
{
  "schema": "bwr1.ray/0.1",
  "time": "2026-10-18T15:00:07.250Z",
  "scan_id": "2026-10-18T15:00:00Z-0001",
  "ray_index": 17,
  "azimuth_deg": 238.4,
  "azimuth_span_deg": 0.5,
  "elevation_deg": 1.0,
  "scan_mode": "sector",
  "range_start_m": 75,
  "range_step_m": 150,
  "power_dbm": [null, -97.2, -99.8, -104.1],
  "velocity_ms": [null, 0.1, -3.2, null],
  "quality_flags": [8, 6, 0, 1],
  "calibration": { "applied": false, "state": "uncalibrated", "reference_plane": "adc_input" },
  "waveform": { "bandwidth_hz": 1000000, "chirp_s": 0.001, "n_chirps": 64, "centre_freq_hz": null, "window": "hann" }
}
```

(`centre_freq_hz` is `null` until issue #4 fixes the operating frequency. Values above are illustrative, not measured.)

## Beackman / Chuvalski output

Network-facing output belongs under `server/` (AGPL-3.0-or-later). Proposed first interface, to be confirmed with the Beackman side:

- **Latest sweep** as a gridded or polar PPI image plus its sweep metadata.
- **Ray stream** (NDJSON) for consumers that want the raw rays.
- **Derived nowcast summary** (for example, max reflectivity and storm-cell distance/bearing in the monitored sector), clearly separated from raw data and carrying the calibration state, so downstream alerts do not treat uncalibrated power as rainfall rate.

Endpoint paths, authentication and rate limits are open and intentionally not decided here.

## Open questions

1. Does the radar-to-server link need a compact binary encoding, given ~240 rays × a few hundred gates every 30 s? (Likely not: this is small.)
2. How are multiple elevations represented once stepped elevation scans exist: one `scan_id` per elevation, or a volume identifier above it?
3. Is the Doppler-band estimator (link-budget v0.4 estimator c) the one that feeds `power_dbm`, or are several estimators stored?
4. What Beackman fields does the integration actually need? Needs input from that project.
