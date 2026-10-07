// SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Regression test: runs the link-budget model from index.html with its default
// parameters and checks it against the baseline table in docs/link-budget.md.
// If either the model or the documented numbers change, this test fails until
// both agree again.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "index.html"), "utf8");
const doc = readFileSync(join(here, "..", "..", "docs", "link-budget.md"), "utf8");

const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
if (!script) throw new Error("no inline <script> found in index.html");

const el = () => ({ innerHTML: "", textContent: "", append() {}, addEventListener() {}, setAttribute() {} });
const els = {};
const sandbox = {
  window: {},
  document: { getElementById: (id) => (els[id] ??= el()), createElement: el },
  localStorage: { getItem: () => null, setItem() {} },
};
sandbox.window.window = sandbox.window;
vm.runInNewContext(script, sandbox);
const { compute, DEF } = sandbox.window.BWR1 ?? {};
if (typeof compute !== "function") throw new Error("window.BWR1.compute not exported by index.html");

// Documented table rows -> default scenario index in index.html
const ROWS = [
  ["C 5.8 GHz, 1.70 m TX + 1.70 m RX", 0],
  ["C 5.8 GHz, 0.60 m TX + 1.70 m RX", 1],
  ["X 9.5 GHz, 1.70 m TX + 1.70 m RX", 2],
  ["X 9.5 GHz, 0.60 m TX + 1.70 m RX", 3],
];
const TOL = 0.051; // documented values are rounded to 0.1 dB
let failures = 0, checks = 0;

for (const [label, idx] of ROWS) {
  const line = doc.split("\n").find((l) => l.startsWith(`| ${label} |`));
  if (!line) { console.error(`missing documented row: ${label}`); failures++; continue; }
  const want = line.split("|").slice(2, 6).map((s) => parseFloat(s));
  const r = compute(DEF.common, DEF.sc[idx], DEF.common.R);
  const got = [r.ZA, r.ZB, r.ZC, r.Zeng];
  ["(a) looks", "(b) radiometer", "(c) Doppler band", "engineering"].forEach((name, k) => {
    checks++;
    const ok = Math.abs(got[k] - want[k]) <= TOL;
    if (!ok) failures++;
    console.log(`${ok ? "ok  " : "FAIL"} ${label} ${name}: model ${got[k].toFixed(2)} dBZ, docs ${want[k]} dBZ`);
  });
}

// Physical sanity checks independent of the docs
const base = compute(DEF.common, DEF.sc[0], 30);
const far = compute(DEF.common, DEF.sc[0], 60);
checks++; if (Math.abs(far.Zeng - base.Zeng - 20 * Math.log10(2)) > 0.01) { failures++; console.error("FAIL Zmin should grow 20log10(R) without rain"); }
const rainy = compute({ ...DEF.common, rainKm: 10 }, DEF.sc[0], 30);
checks++; if (!(rainy.Arain > 5 && rainy.Arain < 7.5)) { failures++; console.error(`FAIL C-band 10 km @50 mm/h two-way attenuation out of range: ${rainy.Arain}`); }

console.log(`\n${checks - failures}/${checks} checks passed`);
process.exit(failures ? 1 : 0);
