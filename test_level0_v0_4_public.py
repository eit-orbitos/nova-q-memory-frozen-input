#!/usr/bin/env python3
"""
Public V0.4 regression tests.

Round 2 is disclosed, so only disclosed numeric regressions are included here.
No round-3 held-out cases are present.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


E = load("extractor_v04", "level0_extract_v0_4.py")
C = load("comparator_v04", "level0_compare_v0_4.py")

# Exact lexical canonicalization regressions.
cases = {
    "21.50000000000000000000000000001":
        "21.50000000000000000000000000001",
    "64.00000000000000000000000000001":
        "64.00000000000000000000000000001",
    "250.00000000000000000000000000001":
        "250.00000000000000000000000000001",
    "21.5000": "21.5",
    "64.000": "64",
    "1,000.000": "1000",
}

for raw, want in cases.items():
    got = E.canonicalize_number_lexeme(raw)
    assert got == want, (raw, got, want)

# No precision-context crash on huge integers.
huge = "9" * 200
assert E.canonicalize_number_lexeme(huge) == huge
assert isinstance(int(huge), int)

# Comparator-side string canonicalizer.
assert C.canonicalize_number_text(21.5) == "21.5"
assert C.canonicalize_number_text(64) == "64"
assert C.canonicalize_number_text(250) == "250"

EXPECTED_HASH = (
    "d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852"
)
assert E.FROZEN_GRAMMAR_SHA256 == EXPECTED_HASH
assert C.FROZEN_GRAMMAR_SHA256 == EXPECTED_HASH

V = [
    {
        "subject": "sensor_x1",
        "relation": "temperature",
        "value": 21.5,
        "unit": "degC",
        "qualifier": "APPROX",
    }
]

bad = {
    "evaluator": E.EVALUATOR_VERSION,
    "grammar_sha256": EXPECTED_HASH,
    "status": "PARSED",
    "facts": [
        {
            "subject": "sensor_x1",
            "relation": "temperature",
            "operator": "EQUAL",
            "value": "21.50000000000000000000000000001",
            "number_canonical": "21.50000000000000000000000000001",
            "unit": "degC",
            "qualifier": "APPROX",
        }
    ],
}

r = C.compare(bad, V)
assert r["trial_verdict"] == "INVALID_TRANSFORMATION"
assert r["fact_level_verdict"] == "FACT_INVENTED"

good = json.loads(json.dumps(bad))
good["facts"][0]["value"] = "21.5"
good["facts"][0]["number_canonical"] = "21.5"
r = C.compare(good, V)
assert r["trial_verdict"] == "TWIN_VALID"

print("PUBLIC_V0_4_REGRESSION_TESTS: PASS")
