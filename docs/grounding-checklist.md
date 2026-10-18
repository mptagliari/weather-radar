# Grounding and surge protection — design checklist v0.1 (issue #13, REQ-015)

A checklist of questions the design must answer before permanent outdoor installation. It was written from general engineering practice and has **not** been checked against the applicable standard text or a site survey. Lightning protection is a safety issue: have a qualified professional design and sign off the installation. In Brazil the lightning-protection standard is ABNT NBR 5419 (based on the IEC 62305 series); the exact requirements need to be read from the current edition.

## Decisions that must be made

1. **Strike risk and zone.** Estimate site lightning density and the consequence of loss. Convective storms are the purpose of this radar, so the antenna will operate in the worst weather by design; severe-weather parking (see [site geometry](site-geometry.md)) and lightning exposure interact.
2. **Air terminal.** Decide whether a separate air terminal and down conductor protect the rotating assembly, or the structure is treated as the strike target and bonded accordingly. A tall mast with a large metal dish is an attractive strike point.
3. **Single-point earth.** One low-impedance ground electrode system for mast, enclosure, power and signal grounds, with all electrodes bonded together. Separate unbonded grounds create dangerous potential differences during a strike.
4. **Rotating joint.** The azimuth bearing is a poor conductor. Provide an explicit bonding path across it (flexible strap or slip ring) for lightning current, not relying on the bearings.
5. **Every conductor that enters the enclosure gets protection at the entry point:** RF coax (coaxial surge protectors at both the antenna side and the shelter side), encoder wiring, motor and control lines, mains and any data link. Protectors are rated for the signal and the frequency (5.8 GHz is above the range of some gas-tube coax protectors; the protector's insertion loss and return loss at the operating band must be checked).
6. **Cable routing.** Keep RF and signal cables away from the down conductor, cross conductors at right angles, and avoid loops.
7. **Isolation of the sensitive end.** Consider fibre or opto-isolation for the encoder and control link to the shelter, removing a conductive path.
8. **Mechanical drive.** The wiper motor and H-bridge sit on the rotating, exposed side. Decide how the bridge supply is protected and whether the motor can be disconnected during storms.
9. **Verification.** Earth-resistance measurement at commissioning and periodically; visual inspection after each severe storm; a log of protector replacement.

## Open facts to establish

- Site lightning density and soil resistivity.
- Whether the existing dish and feed structure is conductive and bonded.
- Insertion/return loss of candidate coax protectors at the chosen frequency.
