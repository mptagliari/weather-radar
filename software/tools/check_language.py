# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fails if tracked text files contain Portuguese. Project rule: all
documentation, comments, strings and commit-facing text are in English.

Two heuristics, both deliberately simple:
  1. Latin letters with diacritics (accents, cedilla, tilde).
  2. A line with two or more distinct common Portuguese words.
Official foreign names may be kept, in italics next to their English
translation, by adding the exact phrase to ALLOWED_PHRASES below. Bare uses
of the original name are flagged.

    python3 -I software/tools/check_language.py        # scans `git ls-files`
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Exact phrases removed before checking: official names that must stay in the
# original language, written in italics right after their English translation.
ALLOWED_PHRASES = ("*Resolução nº 680*", "*Ato nº 14448*")

SKIP_DIRS = ("LICENSES/",)
# These files must spell Portuguese words out to do their job.
SKIP_FILES = ("software/tools/check_language.py", "software/tools/test_language.py")

DIACRITICS = re.compile("[À-ÖØ-öø-ÿ]")  # Latin-1 letters, excluding x and division sign
STOPWORDS = {
    "não", "uma", "você", "são", "está", "então", "porque", "também", "sobre",
    "entre", "para", "mas", "como", "quando", "isso", "esse", "essa", "pela",
    "pelo", "dos", "das", "nos", "nas", "seu", "sua", "são", "ainda", "onde",
    "medição", "potência", "ruído", "frequência", "antena", "alcance",
}
WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")


def check_text(text: str):
    """Yield (line_number, reason, line) for each suspicious line."""
    for n, line in enumerate(text.splitlines(), 1):
        scrubbed = line
        for phrase in ALLOWED_PHRASES:
            scrubbed = scrubbed.replace(phrase, "")
        if DIACRITICS.search(scrubbed):
            yield n, "accented letter", line
            continue
        hits = {w.lower() for w in WORD.findall(scrubbed)} & STOPWORDS
        if len(hits) >= 2:
            yield n, "Portuguese words: " + ", ".join(sorted(hits)), line


def tracked_files(root: Path):
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True,
                         capture_output=True).stdout.decode()
    return [f for f in out.split("\0") if f]


def main() -> int:
    root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True,
                               capture_output=True, text=True).stdout.strip())
    bad = 0
    for rel in tracked_files(root):
        if rel.startswith(SKIP_DIRS) or rel in SKIP_FILES:
            continue
        try:
            text = (root / rel).read_bytes().decode("utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue  # binary or removed
        for n, why, line in check_text(text):
            bad += 1
            print(f"{rel}:{n}: {why}\n    {line.strip()[:140]}")
    if bad:
        print(f"\n{bad} line(s) look Portuguese. Write them in English "
              "(or add an official name to ALLOWED_PHRASES with a translation).")
        return 1
    print("language check: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
