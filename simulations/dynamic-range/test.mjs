// SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Physics checks for the phase-noise / dynamic-range model, plus a link to the
// link-budget model it builds on.
import { budget, beatHz, loadLinkBudget, phaseNoise, DEFAULTS } from "./model.mjs";

const lb = loadLinkBudget();
let fails = 0, checks = 0;
const check = (ok, msg, detail = "") => { checks++; if (!ok) fails++; console.log(`${ok ? "ok  " : "FAIL"} ${msg}${detail ? ` (${detail})` : ""}`); };
const near = (a, b, t) => Math.abs(a - b) <= t;

const base = budget(lb, 0);

// Builds on link-budget: same engineering Zmin as the documented baseline row.
check(near(base.ZengDbz, 12.7, 0.06), "baseline Zeng matches link-budget doc (12.7 dBZ)", base.ZengDbz.toFixed(2));

// Beat frequency: 30 km, B=1 MHz, T=1 ms -> 200 kHz (docs/link-budget.md).
check(near(beatHz(1e6, 1e-3, 30e3), 200e3, 1e3), "beat frequency at 30 km is ~200 kHz");

// Point-target clutter falls as R^-4: doubling its range costs 12.04 dB.
const c3 = budget(lb, 0, { clutterRangeKm: 3 }).clutterDbm;
const c6 = budget(lb, 0, { clutterRangeKm: 6 }).clutterDbm;
check(near(c3 - c6, 40 * Math.log10(2), 0.01), "clutter power follows R^-4");

// Clutter power scales 1:1 with its RCS.
const r40 = budget(lb, 0, { clutterRcsDbsm: 40 }).clutterDbm;
check(near(r40 - base.clutterDbm, 10, 1e-9), "clutter power scales with RCS");

// Range correlation: for small f*tau the factor is (2*pi*f*tau)^2.
const near_c = budget(lb, 0, { clutterRangeKm: 0.01 });
const tau = (2 * 10) / 299792458, x = 2 * Math.PI * near_c.fOffHz * tau;
check(near(near_c.corrDb, 20 * Math.log10(x), 0.05), "range correlation ~ (2*pi*f*tau)^2 at close range", near_c.corrDb.toFixed(2));

// Phase-noise law and requirement consistency.
check(near(phaseNoise(DEFAULTS, 1e6) - phaseNoise(DEFAULTS, 1e5), -20, 1e-9), "-20 dB/decade slope");
const atReq = budget(lb, 0, { pnRefDbcHz: base.LfRequiredDbcHz - (base.LfDbcHz - DEFAULTS.pnRefDbcHz) });
check(near(atReq.degradationDb, 1, 0.01), "required L(f) gives exactly the allowed degradation", atReq.degradationDb.toFixed(3));
check(budget(lb, 0, { pnRefDbcHz: -140 }).degradationDb < 0.1, "very clean synthesizer degrades <0.1 dB");

// A weaker (0.60 m TX) scenario sees less clutter -> relaxes the requirement.
check(budget(lb, 1).LfRequiredDbcHz > base.LfRequiredDbcHz, "smaller TX aperture relaxes the phase-noise requirement");

// Leakage / ADC window.
check(near(base.leakageDbm, 30 - DEFAULTS.isolationDb, 1e-9), "leakage = TX power - isolation");
check(!base.adcOk && base.extraLeakReductionDb > 0, "60 dB isolation alone is infeasible with a 10-bit ADC");
const iso90 = budget(lb, 0, { isolationDb: 100 });
check(iso90.adcOk, "100 dB isolation makes the ADC window feasible");
check(iso90.clutterStrongest, "...and clutter, not leakage, is then the strongest line");
check(budget(lb, 0, { adcEnob: 14 }).gainWindowDb > base.gainWindowDb + 20, "more ENOB widens the window");
check(near(budget(lb, 0, { isolationDb: 70 }).gainWindowDb - base.gainWindowDb, 10, 1e-9), "gain window moves 1:1 with isolation while leakage dominates");
const need = budget(lb, 0, { isolationDb: DEFAULTS.isolationDb + base.extraLeakReductionDb });
check(near(need.gMaxDb, need.gMinDb, 1e-6), "extra reduction lands exactly on the window edge");

console.log(`\n${checks - fails}/${checks} checks passed`);
process.exit(fails ? 1 : 0);
