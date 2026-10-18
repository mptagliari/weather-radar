# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Self-test for check_language.py. Run: python3 -I software/tools/test_language.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_language as c  # noqa: E402

checks = fails = 0


def check(ok, msg):
    global checks, fails
    checks += 1
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + msg)


def flagged(t):
    return bool(list(c.check_text(t)))


check(flagged("A potência da antena não foi medida."), "Portuguese sentence is flagged")
check(flagged("calibração"), "single accented word is flagged")
check(flagged("Isso não é uma decisão."), "accent-free-ish line with several stopwords is flagged")
check(flagged("O ruído de fase sobre o clutter"), "stopword pair is flagged")
check(not flagged("Phase noise on clutter limits sensitivity."), "plain English passes")
check(not flagged("Beam 2.1° wide, ±16 m/s, 5×10 µV/m, ≤ 10 dBZ, R⁻⁴."), "technical symbols pass")
check(not flagged("See https://github.com/mptagliari/weather-radar and docs/para.md"), "URLs and paths pass")
check(not flagged("Anatel Resolution No. 680/2017 (*Resolução nº 680*) and Act No. 14448/2017 (*Ato nº 14448*)."), "allowed official names pass")
check(flagged("Anatel Resolução nº 680/2017 and the Ato nº 14448/2017 cover it."), "bare official names (no gloss form) are flagged")
check(flagged("Resolução 680 foi aprovada"), "official-name exception is exact, not a free pass")
check(not flagged("The mask ensures the para-metric term stays small."), "one stray word is not enough")
check(not flagged("Dwell, the as-built value, and the antenna are fine."), "English with a lone stopword passes")

print(f"\n{checks - fails}/{checks} checks passed")
sys.exit(1 if fails else 0)
