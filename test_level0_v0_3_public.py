#!/usr/bin/env python3
"""
Public structural/smoke tests for Level 0 evaluator V0.3.

These tests intentionally do NOT contain future held-out cases.
They test:
- source separation
- comparator classifications
- syntax/importability
- exact frozen grammar hash constant agreement

The independent reviewer should run the frozen-grammar parser tests separately
against the public REV3 grammar and then create held-out cases only after freeze.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(
    __file__
).resolve().parent


def load(
    name: str,
    filename: str,
):
    spec = (
        importlib.util
        .spec_from_file_location(
            name,
            ROOT / filename,
        )
    )

    mod = (
        importlib.util
        .module_from_spec(spec)
    )

    assert (
        spec.loader
        is not None
    )

    spec.loader.exec_module(
        mod
    )

    return mod


E = load(
    "extractor_v03",
    "level0_extract_v0_3.py",
)

C = load(
    "comparator_v03",
    "level0_compare_v0_3.py",
)

EXPECTED_HASH = (
    "d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852"
)

assert (
    E.FROZEN_GRAMMAR_SHA256
    == EXPECTED_HASH
)

assert (
    C.FROZEN_GRAMMAR_SHA256
    == EXPECTED_HASH
)

V = [
    {
        "subject": "node_a",
        "relation": "memory_capacity",
        "value": 64,
        "unit": "Mi",
        "qualifier": "EXACT",
    }
]

valid_extraction = {
    "evaluator": (
        E.EVALUATOR_VERSION
    ),
    "grammar_sha256": (
        EXPECTED_HASH
    ),
    "status": "PARSED",
    "facts": [
        {
            "subject": "node_a",
            "relation": (
                "memory_capacity"
            ),
            "operator": "EQUAL",
            "value": 64,
            "number_canonical": "64",
            "unit": "Mi",
            "qualifier": "EXACT",
        }
    ],
}

r = C.compare(
    valid_extraction,
    V,
)

assert (
    r["trial_verdict"]
    == "TWIN_VALID"
)

invented = json.loads(
    json.dumps(
        valid_extraction
    )
)

invented[
    "facts"
][0]["value"] = 65

invented[
    "facts"
][0][
    "number_canonical"
] = "65"

r = C.compare(
    invented,
    V,
)

assert (
    r["fact_level_verdict"]
    == "FACT_INVENTED"
)

assert (
    r["trial_verdict"]
    == "INVALID_TRANSFORMATION"
)

assert (
    len(
        r["missing_facts"]
    )
    == 1
)

missing = json.loads(
    json.dumps(
        valid_extraction
    )
)

missing["facts"] = []

r = C.compare(
    missing,
    V,
)

assert (
    r["trial_verdict"]
    == "INVARIANT_LOST"
)

unresolved = {
    "evaluator": (
        E.EVALUATOR_VERSION
    ),
    "grammar_sha256": (
        EXPECTED_HASH
    ),
    "status": "UNRESOLVED",
    "reason": (
        "FULL_TEXT_CONSUMPTION_FAILED"
    ),
}

r = C.compare(
    unresolved,
    V,
)

assert (
    r["trial_verdict"]
    == "UNRESOLVED"
)

print(
    "PUBLIC_V0_3_SMOKE_TESTS: PASS"
)
