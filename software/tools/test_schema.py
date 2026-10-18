# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validates docs/schemas/ray.schema.json and the example in docs/data-format.md.
Needs: pip install jsonschema.  Run: python3 -I software/tools/test_schema.py"""
import copy
import json
import os
import re
import sys

from jsonschema import Draft202012Validator

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
schema = json.load(open(os.path.join(ROOT, "docs", "schemas", "ray.schema.json")))
doc = open(os.path.join(ROOT, "docs", "data-format.md")).read()
example = next(json.loads(b) for b in re.findall(r"```json\n(.*?)```", doc, re.S) if '"bwr1.ray/' in b)

checks = fails = 0


def check(ok, msg):
    global checks, fails
    checks += 1
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + msg)


def check_lengths(ray):
    keys = [k for k in ("power_dbm", "reflectivity_dbz", "velocity_ms", "quality_flags") if k in ray]
    return len({len(ray[k]) for k in keys}) == 1


Draft202012Validator.check_schema(schema)
v = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
valid = lambda r: not list(v.iter_errors(r))  # noqa: E731

check(valid(example) and check_lengths(example), "example in docs/data-format.md is valid")


def mut(f):
    r = copy.deepcopy(example)
    f(r)
    return r


check(not valid(mut(lambda r: r.pop("quality_flags"))), "missing quality_flags is rejected")
check(not valid(mut(lambda r: r.update(azimuth_deg=360.0))), "azimuth 360 is rejected")
check(not valid(mut(lambda r: r.update(time="2026-10-18T15:00:07+00:00"))), "non-Z timestamp is rejected")
check(not valid(mut(lambda r: r.update(scan_mode="spin"))), "unknown scan_mode is rejected")
check(not valid(mut(lambda r: r.update(extra=1))), "unknown field is rejected")
check(not valid(mut(lambda r: r.update(reflectivity_dbz=[None, 1.0, 2.0, 3.0]))),
      "reflectivity with uncalibrated state is rejected")
check(valid(mut(lambda r: (r.update(reflectivity_dbz=[None, 1.0, 2.0, 3.0]),
                           r["calibration"].update(applied=True, state="relative")))),
      "reflectivity with applied calibration is accepted")
check(not valid(mut(lambda r: r["calibration"].update(applied=True))),
      "state uncalibrated with applied=true is rejected")
check(valid(mut(lambda r: r.update(power_dbm=[None, None, None, None]))), "null gates are accepted")
check(not check_lengths(mut(lambda r: r.update(velocity_ms=[0.0]))), "length mismatch is caught by check_lengths")
check(not valid(mut(lambda r: r.update(quality_flags=[256, 0, 0, 0]))), "flag beyond 8 bits is rejected")

print(f"\n{checks - fails}/{checks} checks passed")
sys.exit(1 if fails else 0)
