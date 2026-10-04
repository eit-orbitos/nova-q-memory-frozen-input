#!/usr/bin/env python3
"""
NOVA Q / EIT — LEVEL 0 EXTRACTOR V0.3

Purpose:
    Deterministically parse candidate text under the frozen
    LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3 grammar.

Critical separation:
    This extractor reads:
      1. the frozen grammar JSON
      2. candidate text

    It does NOT read V.
    It does NOT read Q.
    It does NOT decide whether parsed facts are correct.

Frozen grammar:
    SHA-256 d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import hashlib
import json
import re
import sys
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

EVALUATOR_VERSION = "LEVEL0_EXTRACTOR_V0.3"
FROZEN_GRAMMAR_SHA256 = (
    "d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852"
)

# Explicit unit-token class for every production in frozen REV3.
# None means the production has no captured physical/count unit token and uses
# production.unit_default (for example "state") or the empty string.
PRODUCTION_UNIT_CLASS = {
    "P_MEMORY_VERBOSE": "DATA_UNIT",
    "P_MEMORY_COMPACT": "DATA_UNIT",
    "P_STATE_VERBOSE": None,
    "P_STATE_COMPACT": None,
    "P_NODE_COUNT_VERBOSE": None,
    "P_NODE_COUNT_COMPACT": None,
    "P_LATENCY_VERBOSE": "TIME_UNIT",
    "P_LATENCY_COMPACT": "TIME_UNIT",
    "P_REGION_VERBOSE": None,
    "P_REGION_COMPACT": None,
    "P_BANDWIDTH_VERBOSE": "RATE_UNIT",
    "P_BANDWIDTH_COMPACT": "RATE_UNIT",
    "P_DUPLEX_VERBOSE": None,
    "P_DUPLEX_COMPACT": None,
    "P_TEMP_VERBOSE": "TEMP_UNIT",
    "P_TEMP_COMPACT": "TEMP_UNIT",
    "P_CAL_VERBOSE": None,
    "P_CAL_COMPACT": None,
    "P_DEPTH_VERBOSE": "ENTRY_UNIT",
    "P_DEPTH_COMPACT": "ENTRY_UNIT",
    "P_POLICY_VERBOSE": None,
    "P_POLICY_COMPACT": None,
    "P_CAP_VERBOSE": "DATA_UNIT",
    "P_CAP_COMPACT": "DATA_UNIT",
    "P_SCHED_VERBOSE": None,
    "P_SCHED_COMPACT": None,
    "P_RET_VERBOSE": "DAY_UNIT",
    "P_RET_COMPACT": "DAY_UNIT",
    "P_MODE_VERBOSE": None,
    "P_MODE_COMPACT": None,
    "P_FW_VERBOSE": None,
    "P_FW_COMPACT": None,
}

KNOWN_UNIT_TOKEN_CLASSES = {
    "DATA_UNIT",
    "TIME_UNIT",
    "RATE_UNIT",
    "TEMP_UNIT",
    "DAY_UNIT",
    "ENTRY_UNIT",
}


class GrammarError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_decimal_string(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("non-finite number")
    if value == value.to_integral():
        return str(value.quantize(Decimal(1)))
    s = format(value.normalize(), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def parse_number(
    raw: str,
    grammar: dict[str, Any],
    flags: int,
) -> tuple[int | float, str]:
    """
    Explicit NUMBER validator/canonicalizer.

    Validation source:
      grammar.token_classes.NUMBER.regex
      grammar.number_words
      grammar.semantic_validators.NUMBER_CANONICALIZER

    The returned canonical string is retained so comparison is not dependent
    on binary floating-point formatting.
    """
    words = grammar["number_words"]
    if raw in words:
        n = int(words[raw])
        return n, str(n)

    number_regex = grammar["token_classes"]["NUMBER"]["regex"]
    if re.fullmatch(number_regex, raw, flags) is None:
        raise ValueError("NUMBER lexical validation failed")

    cleaned = raw.replace(",", "")
    try:
        d = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError("NUMBER decimal conversion failed") from exc

    canonical = canonical_decimal_string(d)

    if d == d.to_integral():
        return int(d), canonical

    return float(d), canonical


def parse_date(
    raw: str,
    grammar: dict[str, Any],
    flags: int,
) -> str:
    """
    Explicit DATE semantic validator.

    A lexical DATE match is insufficient: the date must exist in the
    proleptic Gregorian calendar. Output is canonical ISO YYYY-MM-DD.
    """
    date_regex = grammar["token_classes"]["DATE"]["regex"]

    if re.fullmatch(date_regex, raw, flags) is None:
        raise ValueError("DATE lexical validation failed")

    try:
        if re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
            raw,
            flags,
        ):
            d = _datetime.date.fromisoformat(raw)
        else:
            d = _datetime.datetime.strptime(
                raw,
                "%d %B %Y",
            ).date()
    except ValueError as exc:
        raise ValueError("DATE semantic validation failed") from exc

    return d.isoformat()


class FrozenGrammar:
    def __init__(self, path: Path):
        raw = path.read_bytes()
        got = sha256_bytes(raw)

        if got != FROZEN_GRAMMAR_SHA256:
            raise GrammarError(
                "Frozen grammar hash mismatch: "
                f"expected {FROZEN_GRAMMAR_SHA256}, got {got}"
            )

        self.path = path
        self.sha256 = got
        self.g = json.loads(raw.decode("utf-8"))

        self._validate_meta()

        self.flags = re.ASCII

        self._validate_unit_contract()
        self.productions = self._compile_productions()

    def _validate_meta(self) -> None:
        g = self.g

        if g.get("artifact") != "LEVEL0_CONSTRAINED_LANGUAGE_V0.1":
            raise GrammarError(
                "unexpected grammar artifact"
            )

        if g.get("revision") != "REV3":
            raise GrammarError(
                "evaluator V0.3 requires grammar REV3"
            )

        dialect = g.get("regex_dialect", {})

        if dialect.get("engine") != "Python re":
            raise GrammarError(
                "unsupported regex engine"
            )

        if dialect.get("flags") != ["re.ASCII"]:
            raise GrammarError(
                "frozen grammar must declare exactly re.ASCII"
            )

        if (
            g.get("full_consumption_rule")
            != "Productions are matched by fullmatch only."
        ):
            raise GrammarError(
                "unexpected full-consumption rule"
            )

        mapping = g.get("slot_to_fact_field_mapping")

        if not isinstance(mapping, dict):
            raise GrammarError(
                "slot_to_fact_field_mapping missing"
            )

        for field in (
            "subject",
            "relation",
            "operator",
            "value",
            "unit",
            "qualifier",
        ):
            if field not in mapping:
                raise GrammarError(
                    f"slot mapping missing: {field}"
                )

        if g.get("duplicate_policy") != "UNRESOLVED":
            raise GrammarError(
                "V0.3 implements frozen "
                "duplicate_policy=UNRESOLVED only"
            )

    def _validate_unit_contract(self) -> None:
        productions = self.g["productions"]

        actual_ids = {
            p["id"]
            for p in productions
        }

        expected_ids = set(
            PRODUCTION_UNIT_CLASS
        )

        if actual_ids != expected_ids:
            missing = sorted(
                expected_ids - actual_ids
            )
            extra = sorted(
                actual_ids - expected_ids
            )

            raise GrammarError(
                "production/unit map mismatch; "
                f"missing={missing}, extra={extra}"
            )

        for p in productions:
            pid = p["id"]
            expected = PRODUCTION_UNIT_CLASS[pid]
            template = p["regex_template"]

            present = [
                token
                for token in KNOWN_UNIT_TOKEN_CLASSES
                if "{{" + token + "}}" in template
            ]

            if expected is None:
                if present:
                    raise GrammarError(
                        f"{pid}: unexpected captured "
                        f"unit token(s): {present}"
                    )
            else:
                if present != [expected]:
                    raise GrammarError(
                        f"{pid}: expected unit class "
                        f"{expected}, found {present}"
                    )

    def _expand_template(
        self,
        template: str,
    ) -> str:
        placeholders = self.g[
            "placeholder_regexes"
        ]

        def repl(
            match: re.Match[str],
        ) -> str:
            name = match.group(1)

            if name not in placeholders:
                raise GrammarError(
                    f"unknown placeholder {name}"
                )

            return (
                "(?:"
                + placeholders[name]
                + ")"
            )

        return re.sub(
            r"\{\{([A-Z_]+)\}\}",
            repl,
            template,
            flags=self.flags,
        )

    def _compile_productions(
        self,
    ) -> list[
        tuple[
            dict[str, Any],
            re.Pattern[str],
        ]
    ]:
        compiled = []

        for p in self.g["productions"]:
            expanded = self._expand_template(
                p["regex_template"]
            )

            compiled.append(
                (
                    p,
                    re.compile(
                        expanded,
                        self.flags,
                    ),
                )
            )

        return compiled

    def _protected_dot_spans(
        self,
        text: str,
    ) -> list[tuple[int, int]]:
        spec = self.g[
            "clause_boundary_spec"
        ]

        spans: list[
            tuple[int, int]
        ] = []

        for token_name in spec[
            "dot_protecting_token_classes"
        ]:
            tc = self.g[
                "token_classes"
            ][token_name]

            if not tc.get(
                "dot_protecting"
            ):
                raise GrammarError(
                    f"{token_name} listed "
                    "as dot-protecting but "
                    "not declared so"
                )

            rx = re.compile(
                tc["regex"],
                self.flags,
            )

            spans.extend(
                (
                    m.start(),
                    m.end(),
                )
                for m in rx.finditer(text)
            )

        return spans

    def split_clauses(
        self,
        text: str,
    ) -> list[str]:
        """
        Apply frozen REV3 clause-boundary rules.

        Every non-empty clause is preserved for full parsing.
        The splitter never deletes unknown text inside a clause.
        """
        text = unicodedata.normalize(
            "NFC",
            text,
        )

        spec = self.g[
            "clause_boundary_spec"
        ]

        boundaries = set(
            spec["boundary_chars"]
        )

        spans = self._protected_dot_spans(
            text
        )

        def protected_dot(
            i: int,
        ) -> bool:
            return any(
                a <= i < b
                for a, b in spans
            )

        result: list[str] = []
        start = 0

        for i, ch in enumerate(text):
            boundary = False

            if ch in boundaries:
                if ch == ".":
                    boundary = (
                        not protected_dot(i)
                    )
                else:
                    boundary = True

            if boundary:
                clause = (
                    text[start:i]
                    .strip(" ")
                )

                if clause:
                    result.append(
                        clause
                    )

                start = i + 1

        tail = (
            text[start:]
            .strip(" ")
        )

        if tail:
            result.append(
                tail
            )

        return result

    def semantic_map(
        self,
        token_class: str,
        raw: str,
    ) -> Any:
        tc = self.g[
            "token_classes"
        ][token_class]

        mapping = tc.get(
            "semantic_map"
        )

        if mapping is None:
            return raw

        if raw not in mapping:
            raise ValueError(
                f"{token_class} "
                f"semantic-map miss: "
                f"{raw!r}"
            )

        return mapping[raw]

    @staticmethod
    def _value_token_class(
        production: dict[str, Any],
    ) -> str:
        value_class = production.get(
            "value_class"
        )

        if not value_class:
            raise GrammarError(
                f"{production['id']}: "
                "missing value_class"
            )

        return value_class

    def _qualifier(
        self,
        groups: dict[
            str,
            str | None,
        ],
    ) -> str:
        qspec = self.g[
            "slot_to_fact_field_mapping"
        ]["qualifier"]

        declared = set(
            qspec["source_groups"]
        )

        required = {
            "qualifier_word",
            "qualifier_tilde",
            "exact_word",
        }

        if declared != required:
            raise GrammarError(
                "frozen qualifier source groups "
                "differ from V0.3 implementation"
            )

        if (
            groups.get(
                "qualifier_word"
            )
            or groups.get(
                "qualifier_tilde"
            )
        ):
            return "APPROX"

        return "EXACT"

    def parse_clause(
        self,
        clause: str,
    ) -> dict[str, Any]:
        matches: list[
            tuple[
                dict[str, Any],
                re.Match[str],
            ]
        ] = []

        for production, rx in self.productions:
            m = rx.fullmatch(
                clause
            )

            if m is not None:
                matches.append(
                    (
                        production,
                        m,
                    )
                )

        if len(matches) != 1:
            return {
                "status": "UNRESOLVED",
                "clause": clause,
                "production_matches": [
                    p["id"]
                    for p, _ in matches
                ],
                "reason": (
                    "NO_FULL_MATCH"
                    if len(matches) == 0
                    else
                    "AMBIGUOUS_FULL_MATCH"
                ),
            }

        production, match = matches[0]
        groups = match.groupdict()

        try:
            subject = self.semantic_map(
                "SUBJECT",
                groups["subject"],
            )

            value_class = (
                self._value_token_class(
                    production
                )
            )

            raw_value = groups[
                "value"
            ]

            number_canonical: (
                str | None
            ) = None

            if value_class == "NUMBER":
                (
                    value,
                    number_canonical,
                ) = parse_number(
                    raw_value,
                    self.g,
                    self.flags,
                )

            elif value_class == "DATE":
                value = parse_date(
                    raw_value,
                    self.g,
                    self.flags,
                )

            elif value_class in {
                "STATE",
                "DUPLEX_STATE",
                "POLICY",
                "MODE",
                "SCHEDULE",
            }:
                value = self.semantic_map(
                    value_class,
                    raw_value,
                )

            elif value_class in {
                "REGION",
                "VERSION",
            }:
                value = raw_value

            else:
                raise GrammarError(
                    f"{production['id']}: "
                    "unsupported value_class "
                    f"{value_class}"
                )

            unit_class = (
                PRODUCTION_UNIT_CLASS[
                    production["id"]
                ]
            )

            if unit_class is None:
                unit = production[
                    "unit_default"
                ]

            else:
                raw_unit = groups.get(
                    "unit"
                )

                if raw_unit is None:
                    raise GrammarError(
                        f"{production['id']}: "
                        "unit group absent for "
                        f"{unit_class}"
                    )

                unit = self.semantic_map(
                    unit_class,
                    raw_unit,
                )

            fact = {
                "subject": subject,
                "relation": production[
                    "relation"
                ],
                "operator": production[
                    "operator"
                ],
                "value": value,
                "unit": unit,
                "qualifier": (
                    self._qualifier(
                        groups
                    )
                ),
            }

            if number_canonical is not None:
                fact[
                    "number_canonical"
                ] = number_canonical

            return {
                "status": "PARSED",
                "clause": clause,
                "production": production[
                    "id"
                ],
                "unit_class": unit_class,
                "fact": fact,
            }

        except (
            ValueError,
            KeyError,
        ) as exc:
            return {
                "status": "UNRESOLVED",
                "clause": clause,
                "production": production[
                    "id"
                ],
                "reason": (
                    "SEMANTIC_VALIDATOR_FAIL"
                ),
                "detail": str(exc),
            }

    @staticmethod
    def fact_identity_key(
        fact: dict[str, Any],
    ) -> str:
        semantic = {
            k: fact[k]
            for k in (
                "subject",
                "relation",
                "operator",
                "value",
                "unit",
                "qualifier",
            )
        }

        if (
            "number_canonical"
            in fact
        ):
            semantic[
                "_number_canonical"
            ] = fact[
                "number_canonical"
            ]

        return json.dumps(
            semantic,
            ensure_ascii=False,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        )

    def extract(
        self,
        text: str,
    ) -> dict[str, Any]:
        clauses = self.split_clauses(
            text
        )

        if not clauses:
            return {
                "evaluator": EVALUATOR_VERSION,
                "grammar_sha256": self.sha256,
                "status": "UNRESOLVED",
                "reason": (
                    "NO_NONEMPTY_CLAUSES"
                ),
                "clauses": [],
                "facts": [],
            }

        results = [
            self.parse_clause(c)
            for c in clauses
        ]

        unresolved = [
            r
            for r in results
            if r["status"]
            != "PARSED"
        ]

        if unresolved:
            return {
                "evaluator": EVALUATOR_VERSION,
                "grammar_sha256": self.sha256,
                "status": "UNRESOLVED",
                "reason": (
                    "FULL_TEXT_CONSUMPTION_FAILED"
                ),
                "clause_count": len(
                    clauses
                ),
                "clauses": results,
                "facts": [],
            }

        facts = [
            r["fact"]
            for r in results
        ]

        keys = [
            self.fact_identity_key(f)
            for f in facts
        ]

        if len(keys) != len(set(keys)):
            return {
                "evaluator": EVALUATOR_VERSION,
                "grammar_sha256": self.sha256,
                "status": "UNRESOLVED",
                "reason": (
                    "DUPLICATE_FACT_ASSERTION"
                ),
                "clause_count": len(
                    clauses
                ),
                "clauses": results,
                "facts": [],
            }

        return {
            "evaluator": EVALUATOR_VERSION,
            "grammar_sha256": self.sha256,
            "status": "PARSED",
            "clause_count": len(
                clauses
            ),
            "clauses": results,
            "facts": facts,
        }


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--grammar",
        required=True,
        type=Path,
    )

    src = (
        ap.add_mutually_exclusive_group(
            required=True
        )
    )

    src.add_argument(
        "--text-file",
        type=Path,
    )

    src.add_argument(
        "--text"
    )

    ap.add_argument(
        "--out",
        type=Path,
    )

    args = ap.parse_args()

    try:
        grammar = FrozenGrammar(
            args.grammar
        )

        text = (
            args.text_file.read_text(
                encoding="utf-8"
            )
            if args.text_file
            is not None
            else args.text
        )

        result = grammar.extract(
            text
        )

    except (
        OSError,
        json.JSONDecodeError,
        GrammarError,
    ) as exc:
        result = {
            "evaluator": EVALUATOR_VERSION,
            "status": "BLOCKER",
            "reason": str(exc),
        }

    payload = (
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )

    if args.out:
        args.out.write_text(
            payload,
            encoding="utf-8",
            newline="\n",
        )
    else:
        sys.stdout.write(
            payload
        )

    if result["status"] == "BLOCKER":
        return 2

    if result["status"] == "UNRESOLVED":
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
