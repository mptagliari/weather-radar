# Regulatory notes — working notes v0.1 (issue #4, REQ-014)

**Not legal advice, and not a decision.** This records what a desk search did and did not establish, so the question to put to Anatel is precise. Nothing here authorizes any transmission. REQ-014 stays open: no outdoor high-gain transmission before the legal basis is closed.

## What was established

- **ITU Radio Regulations, as quoted in the sources found.** Ground-based meteorological radars are recognised in 5600–5650 MHz (footnotes 5.450B and 5.452 describe their status relative to maritime radionavigation). This is the reason the candidate band **avoids 5600–5650 MHz**: operational weather radars use it (an Australian regulator notes most national weather radars licensed there operate near 5625 MHz).
- **5 GHz RLAN coexistence.** The 5470–5725 MHz band was allocated to RLANs with Dynamic Frequency Selection to protect radars, including weather radars in 5600–5650 MHz. This shows the band is shared and sensitive, not that 5.8 GHz is free of constraints.
- **Brazilian restricted-radiation equipment rules exist for 5725–5850 MHz.** Anatel Resolution No. 680/2017 (*Resolução nº 680*, restricted-radiation radiocommunication equipment) and the technical-requirements Act No. 14448/2017 (*Ato nº 14448*) cover spread-spectrum and other digital-modulation devices in that range.
- In the part of Act 14448 that was read, the 5.725–5.875 GHz item (4.1.4) gives **field-strength limits** (50 mV/m at 3 m fundamental, 500 µV/m harmonics) and a 50 dB out-of-band attenuation requirement, not an EIRP figure. Other parts, including amendments, were not read (the text is ~250 000 characters and only the first part was retrieved).

## What was NOT established

- Whether a **weather radar** (an FMCW radiodetermination transmitter, outdoors, with a 1.70 m dish) falls under the restricted-radiation regime at all, or needs a licence/authorization as a different kind of station. Restricted-radiation rules are written for low-power unlicensed devices; the baseline here is a 1 W (30 dBm) transmitter into a 1.70 m dish with about 37.7 dBi of gain (η = 0.55), an EIRP of about 67.7 dBm, roughly 5.9 kW; a 0.60 m TX dish gives about 58.6 dBm (≈ 0.7 kW). These come from the `eirp` output of the link-budget model. This is the central open question.
- The current EIRP, peak-power and antenna-gain limits for 5725–5850 MHz, and any point-to-point exceptions, in the consolidated text.
- How Brazil's national frequency table treats weather radar near 5.8 GHz and whether the 5600–5650 MHz exclusion applies the same way.
- Any limit on continuous (FMCW) emission and the required emission mask.

Search snippets also disagreed on which band limits apply (a 4 W / 36 dBm figure belongs to 5150–5250 MHz, not 5725–5850 MHz). No EIRP number in this repository should be taken from them.

## Questions to put to Anatel

1. Which regime applies to a ground-based, non-commercial experimental weather radar near 5.8 GHz: restricted radiation, an experimental/scientific licence, or a radiodetermination station authorization?
2. What are the allowed centre frequency, bandwidth (1 MHz FMCW), peak power and EIRP, and what emission mask applies?
3. Is a low-power, low-gain configuration for bench and anechoic/short-range tests allowed without authorization, and under which limits?
4. Does the 5600–5650 MHz weather-radar sub-band impose protection distances or coordination for a secondary user?

## Implications for the project while this is open

- Bench work (integration step 2) should use conducted connections, attenuators or dummy loads and low-gain antennas at powers that stay within the unlicensed limits that are confirmed for the band; confirm those limits first.
- The link budget treats 1–2 W CW with two 1.70 m dishes as the paper baseline. That combination is the one most likely to need an authorization, so it should not be built until the answer is in.
- A lower-power, lower-gain compromise would trade away the 10 dBZ / 30 km target; the link-budget models quantify the cost.
