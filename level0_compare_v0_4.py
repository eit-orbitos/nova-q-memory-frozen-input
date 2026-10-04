#!/usr/bin/env python3
"""
NOVA Q / EIT — LEVEL 0 COMPARATOR V0.4

V0.3 status:
    FAILED_HELD_OUT

V0.4 change scope:
    Numeric canonicalization only, plus fail-closed top-level exception handling.

Only this comparator reads V.
Q is never read.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

COMPARATOR_VERSION = "LEVEL0_COMPARATOR_V0.4"
REQUIRED_EXTRACTOR = "LEVEL0_EXTRACTOR_V0.4"
FROZEN_GRAMMAR_SHA256 = (
    "d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852"
)


def canonicalize_number_text(value: Any) -> str:
    """
    Context-free canonicalization for numeric V values.

    No Decimal, no float arithmetic, no normalize(), no quantize().

    V's JSON parser gives ordinary int/float values for the frozen fixture.
    str(value) is used only as the lexical source; the canonicalization itself
    is exact string processing.
    """
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric value")

    s = str(value)

    # Frozen grammar does not admit exponent notation. If V contains it,
    # refuse rather than silently reinterpret.
    if "e" in s.lower():
        raise ValueError(f"exponent notation unsupported in V numeric value: {s}")

    if s.startswith("+") or s.startswith("-"):
        raise ValueError(f"signed numeric value unsupported by frozen grammar: {s}")

    s = s.replace(",", "")

    if not s:
        raise ValueError("empty numeric text")

    if "." not in s:
        if not s.isascii() or not s.isdigit():
            raise ValueError(f"invalid numeric V text: {s}")
        return str(int(s))

    whole, frac = s.split(".", 1)

    if (
        not whole
        or not whole.isascii()
        or not whole.isdigit()
        or not frac
        or not frac.isascii()
        or not frac.isdigit()
    ):
        raise ValueError(f"invalid decimal V text: {s}")

    frac = frac.rstrip("0")
    if frac == "":
        return str(int(whole))

    return str(int(whole)) + "." + frac


def load_v(path: Path) -> list[dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(obj, dict) and isinstance(obj.get("V"), list):
        return obj["V"]

    if isinstance(obj, list):
        return obj

    raise ValueError("V input must be a list or object containing list field 'V'")


def expected_fact(v: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject": v["subject"],
        "relation": v["relation"],
        "operator": v.get("operator", "EQUAL"),
        "value": v["value"],
        "unit": v["unit"],
        "qualifier": v["qualifier"],
    }


def semantic_key(fact: dict[str, Any]) -> str:
    base = {
        "subject": fact["subject"],
        "relation": fact["relation"],
        "operator": fact.get("operator", "EQUAL"),
        "unit": fact["unit"],
        "qualifier": fact["qualifier"],
    }

    if "number_canonical" in fact:
        value_key = "N:" + str(fact["number_canonical"])
    elif isinstance(fact["value"], (int, float)) and not isinstance(
        fact["value"], bool
    ):
        value_key = "N:" + canonicalize_number_text(fact["value"])
    else:
        value_key = "S:" + str(fact["value"])

    base["value_key"] = value_key

    return json.dumps(
        base,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def stripped_fact(fact: dict[str, Any]) -> dict[str, Any]:
    return {
        k: fact[k]
        for k in ("subject", "relation", "operator", "value", "unit", "qualifier")
    }


def compare(
    extraction: dict[str, Any],
    v_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        if extraction.get("evaluator") != REQUIRED_EXTRACTOR:
            return {
                "comparator": COMPARATOR_VERSION,
                "status": "BLOCKER",
                "reason": "WRONG_EXTRACTOR_VERSION",
            }

        if extraction.get("grammar_sha256") != FROZEN_GRAMMAR_SHA256:
            return {
                "comparator": COMPARATOR_VERSION,
                "status": "BLOCKER",
                "reason": "WRONG_GRAMMAR_HASH",
            }

        extract_status = extraction.get("status")

        if extract_status == "UNRESOLVED":
            return {
                "comparator": COMPARATOR_VERSION,
                "grammar_sha256": FROZEN_GRAMMAR_SHA256,
                "status": "UNRESOLVED",
                "trial_verdict": "UNRESOLVED",
                "extractor_reason": extraction.get("reason"),
            }

        if extract_status != "PARSED":
            return {
                "comparator": COMPARATOR_VERSION,
                "status": "BLOCKER",
                "reason": f"UNSUPPORTED_EXTRACTOR_STATUS:{extract_status}",
            }

        parsed_facts = extraction.get("facts")
        if not isinstance(parsed_facts, list):
            return {
                "comparator": COMPARATOR_VERSION,
                "status": "BLOCKER",
                "reason": "EXTRACTOR_FACTS_NOT_LIST",
            }

        expected = [expected_fact(v) for v in v_rows]

        expected_map: dict[str, dict[str, Any]] = {}
        for fact in expected:
            k = semantic_key(fact)
            if k in expected_map:
                return {
                    "comparator": COMPARATOR_VERSION,
                    "status": "BLOCKER",
                    "reason": "DUPLICATE_FACT_IN_V",
                }
            expected_map[k] = fact

        parsed_map: dict[str, dict[str, Any]] = {}
        for fact in parsed_facts:
            k = semantic_key(fact)
            if k in parsed_map:
                return {
                    "comparator": COMPARATOR_VERSION,
                    "status": "BLOCKER",
                    "reason": "DUPLICATE_FACT_ESCAPED_EXTRACTOR",
                }
            parsed_map[k] = fact

        expected_keys = set(expected_map)
        parsed_keys = set(parsed_map)

        invented_keys = sorted(parsed_keys - expected_keys)
        missing_keys = sorted(expected_keys - parsed_keys)

        invented = [stripped_fact(parsed_map[k]) for k in invented_keys]
        missing = [expected_map[k] for k in missing_keys]

        if invented:
            return {
                "comparator": COMPARATOR_VERSION,
                "grammar_sha256": FROZEN_GRAMMAR_SHA256,
                "status": "COMPARED",
                "fact_level_verdict": "FACT_INVENTED",
                "trial_verdict": "INVALID_TRANSFORMATION",
                "parsed_fact_count": len(parsed_facts),
                "expected_fact_count": len(expected),
                "invented_facts": invented,
                "missing_facts": missing,
            }

        if missing:
            return {
                "comparator": COMPARATOR_VERSION,
                "grammar_sha256": FROZEN_GRAMMAR_SHA256,
                "status": "COMPARED",
                "fact_level_verdict": "INVARIANT_LOST",
                "trial_verdict": "INVARIANT_LOST",
                "parsed_fact_count": len(parsed_facts),
                "expected_fact_count": len(expected),
                "invented_facts": [],
                "missing_facts": missing,
            }

        return {
            "comparator": COMPARATOR_VERSION,
            "grammar_sha256": FROZEN_GRAMMAR_SHA256,
            "status": "COMPARED",
            "fact_level_verdict": "ALL_REQUIRED_FACTS_PRESERVED",
            "trial_verdict": "TWIN_VALID",
            "parsed_fact_count": len(parsed_facts),
            "expected_fact_count": len(expected),
            "invented_facts": [],
            "missing_facts": [],
        }

    except Exception as exc:
        return {
            "comparator": COMPARATOR_VERSION,
            "status": "BLOCKER",
            "reason": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extraction", required=True, type=Path)
    ap.add_argument("--v", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    try:
        extraction = json.loads(args.extraction.read_text(encoding="utf-8"))
        v_rows = load_v(args.v)
        result = compare(extraction, v_rows)
    except Exception as exc:
        result = {
            "comparator": COMPARATOR_VERSION,
            "status": "BLOCKER",
            "reason": f"{type(exc).__name__}: {exc}",
        }

    try:
        payload = json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        ) + "\n"
    except Exception as exc:
        payload = json.dumps(
            {
                "comparator": COMPARATOR_VERSION,
                "status": "BLOCKER",
                "reason": f"JSON_SERIALIZATION_FAILURE:{type(exc).__name__}:{exc}",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
        result = {"status": "BLOCKER"}

    if args.out:
        try:
            args.out.write_text(payload, encoding="utf-8", newline="\n")
        except Exception as exc:
            sys.stdout.write(
                json.dumps(
                    {
                        "comparator": COMPARATOR_VERSION,
                        "status": "BLOCKER",
                        "reason": f"OUTPUT_WRITE_FAILURE:{type(exc).__name__}:{exc}",
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            return 2
    else:
        sys.stdout.write(payload)

    if result["status"] == "BLOCKER":
        return 2
    if result.get("trial_verdict") == "TWIN_VALID":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
