#!/usr/bin/env python3
"""
NOVA Q / EIT — LEVEL 1 DETERMINISTIC COMPRESSOR V0.1

Protocol:
    LEVEL1_PROTOCOL_V0.4
    commit 6ce264c71c3e8facf6b77de277fb520497f06d7c
    SHA-256 627388d26e451dc8d0410ca16b6d2c3fcd5389813c75f86cdeef28685b58bce1

Frozen grammar:
    LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3
    SHA-256 d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852

Parser strategy:
    SHARED_PARSER_LIMITATION = False

This program DOES NOT import level0_extract_v0_4.py.
It implements an independent deterministic parser/renderer from the frozen
grammar JSON.

Allowed reads:
    --grammar
    --input

Forbidden:
    V
    Q
    comparator
    network
    subprocess
    fixture-specific constants
    known 481-character solution
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import hashlib
import itertools
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

COMPRESSOR_VERSION = "LEVEL1_COMPRESSOR_V0.1"
SHARED_PARSER_LIMITATION = False

FROZEN_GRAMMAR_SHA256 = (
    "d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852"
)

REGEX_FLAGS = re.ASCII


class CompressorError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(message: str, out_path: Path | None, code: int = 2) -> int:
    if out_path is not None and out_path.exists():
        try:
            out_path.unlink()
        except OSError:
            pass
    sys.stderr.write(message.rstrip("\n") + "\n")
    return code


def load_frozen_grammar(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    got = sha256_bytes(raw)
    if got != FROZEN_GRAMMAR_SHA256:
        raise CompressorError(
            "GRAMMAR_HASH_MISMATCH:"
            f"expected={FROZEN_GRAMMAR_SHA256}:got={got}"
        )

    g = json.loads(raw.decode("utf-8"))

    if g.get("artifact") != "LEVEL0_CONSTRAINED_LANGUAGE_V0.1":
        raise CompressorError("UNEXPECTED_GRAMMAR_ARTIFACT")
    if g.get("revision") != "REV3":
        raise CompressorError("UNEXPECTED_GRAMMAR_REVISION")

    dialect = g.get("regex_dialect", {})
    if dialect.get("engine") != "Python re":
        raise CompressorError("UNSUPPORTED_REGEX_ENGINE")
    if dialect.get("flags") != ["re.ASCII"]:
        raise CompressorError("UNSUPPORTED_REGEX_FLAGS")

    return g


def expand_template(template: str, g: dict[str, Any]) -> str:
    placeholders = g["placeholder_regexes"]

    def repl(m: re.Match[str]) -> str:
        name = m.group(1)
        if name not in placeholders:
            raise CompressorError(f"UNKNOWN_PLACEHOLDER:{name}")
        return "(?:" + placeholders[name] + ")"

    return re.sub(
        r"\{\{([A-Z_]+)\}\}",
        repl,
        template,
        flags=REGEX_FLAGS,
    )


def compile_productions(g: dict[str, Any]):
    out = []
    for p in g["productions"]:
        out.append(
            (
                p,
                re.compile(
                    expand_template(p["regex_template"], g),
                    REGEX_FLAGS,
                ),
            )
        )
    return out


def dot_protected_spans(text: str, g: dict[str, Any]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for name in g["clause_boundary_spec"]["dot_protecting_token_classes"]:
        tc = g["token_classes"][name]
        if not tc.get("dot_protecting"):
            raise CompressorError(f"DOT_PROTECTOR_NOT_DECLARED:{name}")
        rx = re.compile(tc["regex"], REGEX_FLAGS)
        spans.extend((m.start(), m.end()) for m in rx.finditer(text))
    return spans


def split_clauses(text: str, g: dict[str, Any]) -> list[str]:
    text = unicodedata.normalize("NFC", text)
    spec = g["clause_boundary_spec"]
    boundaries = set(spec["boundary_chars"])
    spans = dot_protected_spans(text, g)

    def protected(i: int) -> bool:
        return any(a <= i < b for a, b in spans)

    clauses: list[str] = []
    start = 0

    for i, ch in enumerate(text):
        is_boundary = False

        if ch in boundaries:
            if ch == ".":
                is_boundary = not protected(i)
            else:
                is_boundary = True

        if is_boundary:
            clause = text[start:i].strip(" ")
            if clause:
                clauses.append(clause)
            start = i + 1

    tail = text[start:].strip(" ")
    if tail:
        clauses.append(tail)

    return clauses


def semantic_map(g: dict[str, Any], token_class: str, raw: str) -> Any:
    tc = g["token_classes"][token_class]
    mapping = tc.get("semantic_map")
    if mapping is None:
        return raw
    if raw not in mapping:
        raise CompressorError(f"SEMANTIC_MAP_MISS:{token_class}:{raw}")
    return mapping[raw]


def canonicalize_number_lexeme(raw: str, g: dict[str, Any]) -> str:
    if raw in g["number_words"]:
        return str(int(g["number_words"][raw]))

    number_regex = g["token_classes"]["NUMBER"]["regex"]
    if re.fullmatch(number_regex, raw, REGEX_FLAGS) is None:
        raise CompressorError("NUMBER_VALIDATION_FAIL")

    s = raw.replace(",", "")

    if "." not in s:
        return s

    whole, frac = s.split(".", 1)
    frac = frac.rstrip("0")

    if frac == "":
        return whole

    return whole + "." + frac


def canonicalize_date(raw: str, g: dict[str, Any]) -> str:
    date_regex = g["token_classes"]["DATE"]["regex"]
    if re.fullmatch(date_regex, raw, REGEX_FLAGS) is None:
        raise CompressorError("DATE_VALIDATION_FAIL")

    try:
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", raw, REGEX_FLAGS):
            d = _datetime.date.fromisoformat(raw)
        else:
            d = _datetime.datetime.strptime(raw, "%d %B %Y").date()
    except ValueError as exc:
        raise CompressorError("DATE_VALIDATION_FAIL") from exc

    return d.isoformat()


def unit_token_class_for_production(
    p: dict[str, Any],
    g: dict[str, Any],
) -> str | None:
    """
    Derive the captured unit token class from the frozen production template.

    No per-fixture or per-production value table is used.
    """
    template = p["regex_template"]
    candidates = []

    for token_name, token_spec in g["token_classes"].items():
        if "{{" + token_name + "}}" not in template:
            continue

        semantic_map_obj = token_spec.get("semantic_map")
        if not isinstance(semantic_map_obj, dict):
            continue

        # A captured unit is specifically named 'unit' in the production.
        needle = "(?P<unit>{{" + token_name + "}})"
        if needle in template:
            candidates.append(token_name)

    if len(candidates) > 1:
        raise CompressorError(
            "AMBIGUOUS_UNIT_TOKEN_CLASS:"
            + p["id"]
            + ":"
            + ",".join(sorted(candidates))
        )

    return candidates[0] if candidates else None


def qualifier_from_groups(g: dict[str, Any], groups: dict[str, str | None]) -> str:
    qspec = g["slot_to_fact_field_mapping"]["qualifier"]
    sources = set(qspec["source_groups"])
    expected = {"qualifier_word", "qualifier_tilde", "exact_word"}

    if sources != expected:
        raise CompressorError("QUALIFIER_MAPPING_CONTRACT_MISMATCH")

    if groups.get("qualifier_word") or groups.get("qualifier_tilde"):
        return "APPROX"

    return "EXACT"


def parse_clause(
    clause: str,
    g: dict[str, Any],
    productions,
) -> dict[str, Any]:
    matches = []

    for p, rx in productions:
        m = rx.fullmatch(clause)
        if m is not None:
            matches.append((p, m))

    if len(matches) != 1:
        raise CompressorError(
            "CLAUSE_NOT_UNIQUELY_PARSEABLE:"
            f"count={len(matches)}:"
            f"clause={clause!r}"
        )

    p, m = matches[0]
    groups = m.groupdict()

    subject = semantic_map(g, "SUBJECT", groups["subject"])
    value_class = p.get("value_class")
    raw_value = groups["value"]

    if value_class == "NUMBER":
        value = canonicalize_number_lexeme(raw_value, g)
    elif value_class == "DATE":
        value = canonicalize_date(raw_value, g)
    elif value_class in {
        "STATE",
        "DUPLEX_STATE",
        "POLICY",
        "MODE",
        "SCHEDULE",
    }:
        value = semantic_map(g, value_class, raw_value)
    elif value_class in {"REGION", "VERSION"}:
        value = raw_value
    else:
        raise CompressorError(
            f"UNSUPPORTED_VALUE_CLASS:{p['id']}:{value_class}"
        )

    unit_class = unit_token_class_for_production(p, g)

    if unit_class is None:
        unit = p["unit_default"]
    else:
        raw_unit = groups.get("unit")
        if raw_unit is None:
            raise CompressorError(f"MISSING_UNIT_CAPTURE:{p['id']}")
        unit = semantic_map(g, unit_class, raw_unit)

    return {
        "subject": subject,
        "relation": p["relation"],
        "operator": p["operator"],
        "value": value,
        "unit": unit,
        "qualifier": qualifier_from_groups(g, groups),
    }


def fact_key(fact: dict[str, Any]) -> str:
    return json.dumps(
        fact,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


PLACEHOLDER_SCAN = re.compile(
    r"\(\?P<(?P<group>[A-Za-z_][A-Za-z0-9_]*)>"
    r"\{\{(?P<named>[A-Z_]+)\}\}\)"
    r"|\{\{(?P<plain>[A-Z_]+)\}\}",
    REGEX_FLAGS,
)


def aliases_for_slot(
    slot: str,
    fact: dict[str, Any],
    g: dict[str, Any],
) -> list[str]:
    cv = g["closed_vocabulary"]

    if slot == "SUBJECT":
        return list(cv["subjects"][fact["subject"]])

    if slot == "NUMBER":
        # The canonical digit form is always a valid rendering for a numeric fact.
        return [fact["value"]]

    if slot == "DATE":
        return [fact["value"]]

    if slot in {"REGION", "VERSION"}:
        return [fact["value"]]

    if slot in {"STATE", "DUPLEX_STATE", "POLICY", "MODE", "SCHEDULE"}:
        mapping = g["token_classes"][slot].get("semantic_map", {})
        return sorted(
            [alias for alias, canonical in mapping.items() if canonical == fact["value"]],
            key=lambda s: (len(s), s),
        )

    if slot == "NUM_MODIFIER":
        if fact["qualifier"] == "APPROX":
            # Every value comes from the frozen grammar vocabulary.
            return sorted(
                [
                    "~",
                    "about ",
                    "around ",
                    "roughly ",
                    "approximately ",
                    "approx. ",
                    "approximately equal to ",
                ],
                key=lambda s: (len(s), s),
            )
        return ["", "exactly "]

    tc = g["token_classes"].get(slot)
    if isinstance(tc, dict) and isinstance(tc.get("semantic_map"), dict):
        return sorted(
            [
                alias
                for alias, canonical in tc["semantic_map"].items()
                if canonical == fact["unit"]
            ],
            key=lambda s: (len(s), s),
        )

    raise CompressorError(f"NO_RENDER_RULE_FOR_SLOT:{slot}")


def instantiate_template(template: str, values: tuple[str, ...]) -> str:
    values_iter = iter(values)

    body = template
    if body.startswith("^"):
        body = body[1:]
    if body.endswith("$"):
        body = body[:-1]

    return PLACEHOLDER_SCAN.sub(lambda _: next(values_iter), body)


def render_shortest_fact(
    fact: dict[str, Any],
    g: dict[str, Any],
    productions,
) -> str:
    candidates: list[str] = []

    for p in g["productions"]:
        if p["relation"] != fact["relation"]:
            continue

        slots = []
        for m in PLACEHOLDER_SCAN.finditer(p["regex_template"]):
            slots.append(m.group("named") or m.group("plain"))

        option_lists = [aliases_for_slot(slot, fact, g) for slot in slots]

        for combo in itertools.product(*option_lists):
            candidate = instantiate_template(p["regex_template"], combo)

            try:
                parsed = parse_clause(candidate, g, productions)
            except CompressorError:
                continue

            if fact_key(parsed) == fact_key(fact):
                candidates.append(candidate)

    if not candidates:
        raise CompressorError(
            "NO_VALID_RENDERING_FOR_FACT:"
            + fact_key(fact)
        )

    return min(candidates, key=lambda s: (len(s), s))


def compress(input_text: str, g: dict[str, Any]) -> str:
    productions = compile_productions(g)
    clauses = split_clauses(input_text, g)

    if not clauses:
        raise CompressorError("NO_NONEMPTY_CLAUSES")

    facts = [parse_clause(c, g, productions) for c in clauses]

    keys = [fact_key(f) for f in facts]
    if len(keys) != len(set(keys)):
        raise CompressorError("DUPLICATE_FACT_ASSERTION")

    rendered = [
        render_shortest_fact(fact, g, productions)
        for fact in facts
    ]

    # Preserve input fact order. This is deterministic and avoids introducing
    # semantic ordering assumptions not stated by the grammar.
    separator = g["minimum_rendering"]["separator"]
    terminator = g["minimum_rendering"]["final_terminator"]

    candidate = separator.join(rendered) + terminator

    # Independent self-check: reparse our own output and require exact fact set
    # and exact clause count before writing any file.
    out_clauses = split_clauses(candidate, g)
    out_facts = [parse_clause(c, g, productions) for c in out_clauses]

    if len(out_facts) != len(facts):
        raise CompressorError("SELF_CHECK_FACT_COUNT_MISMATCH")

    if [fact_key(f) for f in out_facts] != [fact_key(f) for f in facts]:
        raise CompressorError("SELF_CHECK_FACT_SEQUENCE_MISMATCH")

    return candidate


def read_utf8_no_bom(path: Path) -> str:
    raw = path.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        raise CompressorError("UTF8_BOM_PROHIBITED")

    if b"\x00" in raw:
        raise CompressorError("ZERO_BYTE_PROHIBITED")

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CompressorError("INPUT_NOT_UTF8") from exc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", required=True, type=Path)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    # Required valid-run success behavior: stdout remains empty.
    # All diagnostics go to stderr only.

    try:
        # Do not leave a stale output file that could be mistaken for this run.
        if args.out.exists():
            args.out.unlink()

        g = load_frozen_grammar(args.grammar)
        input_text = read_utf8_no_bom(args.input)
        candidate = compress(input_text, g)

        # UTF-8, LF, no BOM. Candidate itself has no forced final LF.
        data = candidate.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")

        # Atomic enough for this protocol: write only after full parse/render/self-check.
        args.out.write_bytes(data)
        return 0

    except Exception as exc:
        return fail(
            f"{type(exc).__name__}:{exc}",
            args.out,
            code=2,
        )


if __name__ == "__main__":
    raise SystemExit(main())
