// SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Prints the phase-noise / dynamic-range budget for the baseline scenarios.
//   node simulations/dynamic-range/report.mjs [key=value ...]   (e.g. isolationDb=80)
import { budget, loadLinkBudget } from "./model.mjs";

const over = Object.fromEntries(process.argv.slice(2).map((a) => {
  const [k, v] = a.split("="); return [k, parseFloat(v)];
}));
const lb = loadLinkBudget();
const f = (x, d = 1) => (Number.isFinite(x) ? x.toFixed(d) : "—");

for (const idx of [0, 1]) {
  const b = budget(lb, idx, over);
  console.log(`\n== ${b.inputs.scenario}, weather at ${b.inputs.rangeKm} km ==`);
  console.log(`weather @ target Z: ${f(b.PrDbm)} dBm   thermal/bin: ${f(b.NthDbm)} dBm   clutter: ${f(b.clutterDbm)} dBm   leakage: ${f(b.leakageDbm)} dBm`);
  console.log(`phase noise: offset ${f(b.fOffHz / 1e3, 0)} kHz, L(f) assumed ${f(b.LfDbcHz)} dBc/Hz, range-correlation ${f(b.corrDb)} dB`);
  console.log(`  -> floor ${f(b.phaseNoiseFloorDbm)} dBm, Zmin degradation ${f(b.degradationDb)} dB; need L(f) <= ${f(b.LfRequiredDbcHz)} dBc/Hz for <= ${b.inputs.maxDegradationDb} dB`);
  console.log(`dynamic range: need ${f(b.dynRangeNeededDb, 0)} dB; ADC gain window ${f(b.gMinDb)}..${f(b.gMaxDb)} dB (${b.adcOk ? "feasible" : "INFEASIBLE"}, ${f(b.gainWindowDb)} dB)`);
  console.log(`  strongest tolerated ${f(b.strongestMaxDbm)} dBm; extra leakage reduction needed ${f(b.extraLeakReductionDb)} dB; LNA ${b.lnaOk ? "ok" : "COMPRESSES"}`);
}

console.log("\nRequired L(f_off) [dBc/Hz] vs clutter range (scenario 1, 1 dB budget):");
for (const rc of [1, 2, 3, 5, 10, 20]) {
  const b = budget(lb, 0, { ...over, clutterRangeKm: rc });
  console.log(`  clutter @ ${String(rc).padStart(2)} km: clutter ${f(b.clutterDbm)} dBm, offset ${f(b.fOffHz / 1e3, 0)} kHz, need ${f(b.LfRequiredDbcHz)}`);
}
console.log("\nLeakage reduction needed [dB] vs TX->RX isolation (scenario 1):");
for (const iso of [40, 60, 80, 100]) {
  const b = budget(lb, 0, { ...over, isolationDb: iso });
  console.log(`  isolation ${String(iso).padStart(3)} dB: leakage ${f(b.leakageDbm)} dBm, extra ${f(b.extraLeakReductionDb)} dB, ${b.adcOk ? "feasible" : "infeasible"}`);
}
