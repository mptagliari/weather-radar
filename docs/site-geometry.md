# Site geometry, wind load and solar passes — working notes v0.1

Screening calculations for issues #12 (wind), #14 (sector and elevation) and #21 (solar calibration). Code: [`software/tools/`](../software/tools/) (`beam.py`, `wind.py`, `solar.py`, tested by `test_tools.py`). These are estimates built on stated assumptions; none replaces a site survey, a structural calculation or a proper ephemeris.

## Beam height and elevation (#14)

With the 4/3 effective Earth radius, the 1.70 m reflector at 5.8 GHz has a half-power beamwidth of about 2.1° (rule of thumb 70 λ/D). For a fixed 1° elevation and zero antenna height above the reference ground:

| Range | Beam centre | Lower .. upper half-power edge |
|---|---|---|
| 10 km | 180 m | −5 .. 366 m |
| 20 km | 373 m | 1 .. 744 m |
| 30 km | 577 m | 19 .. 1133 m |
| 50 km | 1020 m | 91 .. 1948 m |

Observations:

- At 1° the lower beam edge grazes the ground out to ~20 km. Terrain at or above the antenna level in the W–SW sector will clip the beam there, so the usable minimum elevation is set by the surveyed horizon: `elevation ≥ horizon angle + beamwidth/2` (+ margin), implemented as `clearance_elevation_deg`.
- A 2.1° beam at 30 km is about 1.1 km tall; precipitation structure below the beam centre is not seen, and low-altitude hail or rain can be missed at long range.
- The survey needed for #14 is simply the horizon elevation angle versus azimuth over the sector (a clinometer or phone app at the antenna position, every few degrees). Feed those numbers to `clearance_elevation_deg`; nothing else is required from the site.

Refraction varies with weather; 4/3 is a convention, not a measurement.

## Wind load and parking (#12)

`wind.py` evaluates `F = ½ ρ V² Cd A` for the 1.70 m reflector (A ≈ 2.27 m²). Assumptions, all open to correction: sea-level air density, Cd between 1.0 and 1.8 for flow normal to the dish, a mesh reflector modeled as 50% effective area, a centre-of-pressure offset of 0.15 m from the azimuth axis, and a 3 m mast.

At 40 m/s (144 km/h), normal to the aperture:

| Case | Force | Azimuth torque | Overturning moment at base |
|---|---|---|---|
| Solid, Cd 1.0 | 2.2 kN | 334 N·m | 6.7 kN·m |
| Solid, Cd 1.8 | 4.0 kN | 601 N·m | 12.0 kN·m |
| Mesh 50%, Cd 1.0 | 1.1 kN | 167 N·m | 3.3 kN·m |

Observations:

- The azimuth torque in a gust, even with a small centre-of-pressure offset, is plausibly **far larger than a wiper motor and gearbox are meant to hold**. The BOM note that the worm gear self-locks only helps against back-driving at modest load; it does not make the gear train safe at these torques. Verify the actual motor's rated and stall torque, which has not been measured or looked up here.
- This argues for a mechanical park lock or brake that carries gust load into the structure, and for a park orientation that minimizes torque (edge-on or aligned with the expected gust direction). The azimuth controller currently has no park lock output.
- The overturning moment sets the mast, foundation and guying requirement and is usually the dominant structural item.
- Design wind speeds are location-specific. For Brazil, ABNT NBR 6123 gives the basic wind speed by region and the gust factors; use it or a structural engineer for design values.

## Solar passes (#21)

`solar.py` computes the apparent solar azimuth and elevation (NOAA formulation, cross-checked in the tests against an independent Almanac formulation: elevations agree within 0.01°, azimuths within 0.02° away from the zenith) and lists the times when the sun crosses a chosen elevation inside the sector:

```sh
python3 software/tools/solar.py LAT LON 2026-12-21 1.0 200 320
```

Site coordinates are inputs; none are stored. Two facts the tests confirm for a southern-hemisphere site: the sunset azimuth swings from about 244° (WSW, December) to about 297° (WNW, June), and in both cases it falls inside the 200–320° sector, so sunset passes are available all year at a fixed low elevation without moving the antenna in elevation.

Practical limits: the sun is 0.53° across versus a ~2.1° beam, so a drift scan across it gives a beam-shaped response useful for pointing (azimuth/elevation offset) and relative gain trending. Absolute gain from the sun needs a solar flux value for the date, which is not included here. At the horizon the sun is also attenuated and refracted, so elevations below a few degrees need the refraction correction already applied and some scatter is expected.
