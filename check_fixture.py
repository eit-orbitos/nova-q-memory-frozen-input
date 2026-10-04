#!/usr/bin/env python3
"""NOVA Q FIXTURE_01 pre-freeze checker (stdlib only).

Usage: python3 check_fixture.py <folder with the nova_q files>

Reports file-level SHA-256, byte hygiene, schema checks, canonical V/Q bytes
and hashes as CANON_SPEC_V0.1 sections 1-2 and 9 describe them, and the M_0
length figures needed for the 70 % form-change threshold.
It does not freeze anything: it only prints what the bytes are.
"""
import hashlib, json, re, sys, unicodedata
from pathlib import Path

FACT_KEYS = ["fact_id", "subject", "relation", "value", "unit", "qualifier"]
Q_KEYS = ["fact_id", "subject", "relation"]
SEP = "=" * 79


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_bytes(obj) -> bytes:
    """CANON_SPEC_V0.1 s.2: sorted keys, no insignificant whitespace,
    ensure_ascii=False, UTF-8, strings NFC."""
    def nfc(x):
        if isinstance(x, str):
            return unicodedata.normalize("NFC", x)
        if isinstance(x, list):
            return [nfc(i) for i in x]
        if isinstance(x, dict):
            return {nfc(k): nfc(v) for k, v in x.items()}
        return x
    return json.dumps(nfc(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def hygiene(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    return {
        "bytes": len(raw),
        "sha256": sha(raw),
        "bom": raw.startswith(b"\xef\xbb\xbf"),
        "crlf": b"\r\n" in raw,
        "nfc": unicodedata.normalize("NFC", text) == text,
        "ends_with_newline": raw.endswith(b"\n"),
        "non_ascii": sorted({c for c in text if ord(c) > 127}),
    }


def check_fixture(path: Path):
    d = json.loads(path.read_text("utf-8"))
    V, Q = d["V"], d["Q"]
    problems = []
    if len(V) != 20:
        problems.append(f"V has {len(V)} facts, expected 20")
    ids = [f["fact_id"] for f in V]
    if ids != sorted(ids) or len(set(ids)) != len(ids):
        problems.append("fact_id not unique/ascending")
    for f in V:
        if sorted(f) != sorted(FACT_KEYS):
            problems.append(f"{f['fact_id']}: keys {sorted(f)} != spec keys")
        if not re.fullmatch(r"F[0-9]{2}", f["fact_id"]):
            problems.append(f"{f['fact_id']}: bad id pattern")
        for k in ("subject", "relation"):
            if not re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", f[k]):
                problems.append(f"{f['fact_id']}: {k}={f[k]!r} not lowercase snake_case")
    pairs = [(f["subject"], f["relation"]) for f in V]
    if len(set(pairs)) != len(pairs):
        problems.append("duplicate (subject, relation) pair")
    if [{k: f[k] for k in Q_KEYS} for f in V] != Q:
        problems.append("Q is not exactly V without value/unit/qualifier")
    for k in d:
        if "SHA256" in k.upper():
            problems.append(f"hash field {k!r} is written inside the artifact it hashes (CANON_SPEC s.9 forbids)")
    by_unit = {}
    for f in V:
        if isinstance(f["value"], (int, float)):
            by_unit.setdefault(f["unit"], []).append((f["fact_id"], f["value"]))
    return d, problems, by_unit


def m0_figures(path: Path):
    text = path.read_text("utf-8")
    parts = text.split(SEP)
    # body-only file (no separators): the whole text, final newline excluded
    body = (parts[1] if len(parts) == 3 else text).strip("\n")
    lines = [l for l in body.split("\n") if l.strip()]
    return text, body, lines


def main(folder):
    folder = Path(folder)
    print("== FILES ==")
    for p in sorted(folder.iterdir()):
        h = hygiene(p)
        print(f"{p.name}\n  sha256={h['sha256']}\n  bytes={h['bytes']} bom={h['bom']} crlf={h['crlf']} "
              f"nfc={h['nfc']} final_newline={h['ends_with_newline']} non_ascii={''.join(h['non_ascii'])!r}")
    for name in sorted(p.name for p in folder.glob("*.json")):
        probe = json.loads((folder / name).read_text("utf-8"))
        if not (isinstance(probe, dict) and "V" in probe and "Q" in probe):
            continue  # not a fixture (e.g. the freeze record)
        print(f"\n== FIXTURE {name} ==")
        d, problems, by_unit = check_fixture(folder / name)
        print("status:", d.get("status"), "| created:", d.get("created"))
        print("problems:", problems or "none")
        print("same-unit numeric groups:", {u: v for u, v in by_unit.items() if len(v) > 1})
        vb, qb = canonical_bytes(d["V"]), canonical_bytes(d["Q"])
        print(f"canonical V: {len(vb)} bytes sha256={sha(vb)}")
        print(f"canonical Q: {len(qb)} bytes sha256={sha(qb)}")
        for k in ("V_SHA256", "Q_SHA256"):
            if k in d:
                mine = sha(vb if k[0] == "V" else qb)
                print(f"embedded {k}={d[k]} -> {'MATCH' if mine == d[k] else 'DOES NOT MATCH recomputation'}")
    m0 = next(folder.glob("*M0*"), None)
    if m0:
        text, body, lines = m0_figures(m0)
        print(f"\n== M_0 ({m0.name}) ==")
        print("statement lines:", len(lines), "| header/footer present:", len(text.split(SEP)) == 3)
        print(f"whole file: {len(text)} chars / {len(text.encode())} bytes")
        print(f"body only : {len(body)} chars / {len(body.encode())} bytes")
        print(f"body / whole file = {len(body)/len(text):.3f}  (70 % threshold = 0.700)")
        print(f"0.70 x body = {0.70*len(body):.0f} chars")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
