// SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Phase-noise and dynamic-range budget for the BWR-1 FMCW receiver.
// Complements simulations/link-budget (thermal/statistical Zmin) with the two
// terms that model only covers through a fixed engineering margin:
//   1. synthesizer phase noise on strong terrain clutter (issue #10),
//   2. TX->RX leakage and clutter against the ADC window (issues #8, #9).
//
// Everything is referred to the receiver input reference plane, the same plane
// as `Pr` in link-budget. Results are design estimates; every default marked
// ASSUMPTION is something a measurement is expected to replace.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const C0 = 299792458;
const dB = (x) => 10 * Math.log10(x);

/** Load compute()/DEF from the link-budget page without modifying it. */
export function loadLinkBudget() {
  const here = dirname(fileURLToPath(import.meta.url));
  const html = readFileSync(join(here, "..", "link-budget", "index.html"), "utf8");
  const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
  if (!script) throw new Error("no inline <script> in link-budget/index.html");
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
  if (typeof compute !== "function") throw new Error("window.BWR1.compute missing");
  return { compute, DEF };
}

export const DEFAULTS = {
  // Geometry
  clutterRangeKm: 3, // ASSUMPTION: dominant terrain/structure return
  clutterRcsDbsm: 30, // ASSUMPTION: large hill/building; measure with a dry-weather scan
  // Phase noise L(f) = L_ref + slope * log10(f / f_ref)   [SSB, dBc/Hz]
  pnRefDbcHz: -100, // ASSUMPTION at f_ref
  pnRefHz: 100e3,
  pnSlopeDbPerDec: -20, // ASSUMPTION
  maxDegradationDb: 1, // allowed Zmin loss from phase noise
  // Leakage
  isolationDb: 60, // ASSUMPTION: TX->RX isolation incl. antenna spacing; issue #9 measures it
  leakRejectDb: 0, // rejection of the near-DC leakage line before the ADC (IF high-pass)
  // Receiver / ADC
  adcFullScaleDbm: 4, // ASSUMPTION: full scale at the ADC input
  adcEnob: 10, // ASSUMPTION: effective bits at the beat frequency
  adcRateHz: 2e6, // ~2 MSPS-class per link-budget notes
  adcBackoffDb: 6, // headroom for the strongest line plus noise/crest
  adcNoiseMarginDb: 10, // thermal noise must exceed ADC noise by this much
  lnaIp1dBDbm: -10, // ASSUMPTION: LNA input-referred 1 dB compression
  lnaBackoffDb: 10,
};

/** SSB phase noise at offset f (Hz), dBc/Hz. */
export function phaseNoise(p, f) {
  return p.pnRefDbcHz + p.pnSlopeDbPerDec * Math.log10(f / p.pnRefHz);
}

/** Beat frequency for a range (m): f = S * 2R/c with S = B/T. */
export function beatHz(B, T, R) {
  return ((B / T) * 2 * R) / C0;
}

/**
 * @param lb  {compute, DEF} from loadLinkBudget()
 * @param idx scenario index in DEF.sc
 * @param over overrides for DEFAULTS and DEF.common
 */
export function budget(lb, idx = 0, over = {}) {
  const p = { ...DEFAULTS, ...over };
  const common = { ...lb.DEF.common, ...(over.common ?? {}) };
  const sc = { ...lb.DEF.sc[idx], ...(over.sc ?? {}) };
  const r = lb.compute(common, sc, common.R);

  const B = common.B * 1e6, T = common.T * 1e-3;
  const Rc = p.clutterRangeKm * 1e3, Rw = common.R * 1e3;
  const lam = r.lam;

  // Clutter at the receiver (point-target equation), same reference plane as r.Pr.
  const PtDbm = dB(sc.Pt) + 30;
  const Pc = PtDbm + dB(r.Gt) + dB(r.Gr) + dB(lam * lam) + p.clutterRcsDbsm
    - dB((4 * Math.PI) ** 3) - 40 * Math.log10(Rc) - common.L;

  // Phase-noise skirt of the clutter line landing in the weather range bin.
  const tauC = (2 * Rc) / C0;
  const fOff = Math.abs(beatHz(B, T, Rw) - beatHz(B, T, Rc));
  const corr = dB(4 * Math.sin(Math.PI * fOff * tauC) ** 2); // range correlation
  const Bbin = common.enbw / T;
  const Lf = phaseNoise(p, fOff);
  const Npn = Pc + Lf + corr + dB(Bbin);
  const Nth = r.Nbin;
  const degradationDb = dB(1 + 10 ** ((Npn - Nth) / 10));
  // Largest L(f_off) that keeps the degradation within maxDegradationDb.
  const allowed = 10 ** (p.maxDegradationDb / 10) - 1;
  const LfRequired = Nth + dB(allowed) - Pc - corr - dB(Bbin);

  // Strongest signals and the ADC window.
  const Pleak = PtDbm - p.isolationDb;
  const PleakAdc = Pleak - p.leakRejectDb;
  const strongest = Math.max(PleakAdc, Pc);
  const lnaOk = Pleak <= p.lnaIp1dBDbm - p.lnaBackoffDb;
  const adcSnrFs = 6.02 * p.adcEnob + 1.76; // full-scale sine over fs/2
  const adcNoiseBin = p.adcFullScaleDbm - adcSnrFs + dB(Bbin / (p.adcRateHz / 2));
  // Gains (receiver-input to ADC) for which both ends of the window hold:
  const gMax = p.adcFullScaleDbm - p.adcBackoffDb - strongest;
  const gMin = adcNoiseBin + p.adcNoiseMarginDb - Nth;
  const dynRangeNeededDb = strongest - Nth;
  // Largest strongest-signal level the ADC window tolerates, and how much more
  // leakage reduction (isolation, cancellation, IF high-pass) that implies.
  const strongestMax = p.adcFullScaleDbm - p.adcBackoffDb - gMin;
  const extraLeakReductionDb = Math.max(0, PleakAdc - Math.max(strongestMax, -Infinity));
  const clutterStrongest = Pc >= PleakAdc; // leakage no longer the limiting line

  return {
    inputs: { ...p, scenario: sc.name, rangeKm: common.R },
    PrDbm: r.Pr, NthDbm: Nth, ZengDbz: r.Zeng,
    clutterDbm: Pc, leakageDbm: Pleak,
    fOffHz: fOff, corrDb: corr, LfDbcHz: Lf, phaseNoiseFloorDbm: Npn,
    degradationDb, LfRequiredDbcHz: LfRequired, pnOk: degradationDb <= p.maxDegradationDb,
    lnaOk, strongestDbm: strongest, dynRangeNeededDb,
    adcNoiseBinDbm: adcNoiseBin, gMinDb: gMin, gMaxDb: gMax,
    gainWindowDb: gMax - gMin, adcOk: gMax >= gMin,
    strongestMaxDbm: strongestMax, extraLeakReductionDb, clutterStrongest,
  };
}
