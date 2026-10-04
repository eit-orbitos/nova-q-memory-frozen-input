#!/usr/bin/env python3
"""Adversarial calibration cases for the NOVA Q Level 0 extractor + comparator.

Run next to nova_q_level0_extractor.py, nova_q_level0_comparator.py,
NOVA_Q_FIXTURE_01_M0_SOURCE.txt and NOVA_Q_FIXTURE_01_REVIEW_DRAFT.json:

    python3 attack_level0.py

Each case names the fact it targets and the verdict a sound instrument must
give for that fact. FALSE_PASS = a corrupted fact was accepted.
FALSE_FAIL = a correct fact was rejected.
"""
import json, sys
from nova_q_level0_extractor import extract_all
from nova_q_level0_comparator import compare_all

fx = json.load(open("NOVA_Q_FIXTURE_01_REVIEW_DRAFT.json", encoding="utf-8"))
V, Q = fx["V"], fx["Q"]
M0 = open("NOVA_Q_FIXTURE_01_M0_SOURCE.txt", encoding="utf-8").read()


def run(text):
    rep = compare_all(V, extract_all(text, Q))
    return rep, {r["fact_id"]: r for r in rep["results"]}


def show(title, text):
    rep, by = run(text)
    bad = {k: (v["verdict"], v["reason"], v["actual"]["value"]) for k, v in by.items() if v["verdict"] != "TWIN_VALID"}
    print(f"\n== {title}: final={rep['final_verdict']} counts={rep['counts']}")
    for k, v in bad.items():
        print(f"   {k}: {v}")
    return rep, by


# 1. The frozen M_0 itself: every fact must be recovered.
show("FROZEN M_0, unchanged (must recover 20/20)", M0)

# 2. A faithful compact rewrite a real compressor would produce.
COMPACT = ("Node A: 64 Mi, active. Node B: 32 Mi. Node C: 16 Mi, firmware 4.2.1. Node D: 128 Mi, disabled. "
           "Cluster 1: 12 nodes, max latency approximately 250 ms, region eu-central. Link AB: 1000 Mbps, full duplex. "
           "Sensor X1: about 21.5 °C, calibrated 18 April 2026. Queue Q: 4096 entries, FIFO. Storage S1: 2048 Gi. "
           "Backup job: daily, retention 30 days. System: production.")
show("FAITHFUL COMPACT REWRITE (all 20 facts kept, 47 % of M_0)", COMPACT)

# 3. Targeted single-line substitutions on M_0.
CASES = [
    # (name, old line, new line, fact, must)   must: "FAIL" = must not be TWIN_VALID, "PASS" = must be TWIN_VALID
    ("value 64 -> 1064", "Node A has exactly 64 Mi of memory.", "Node A has exactly 1064 Mi of memory.", "F01", "FAIL"),
    ("value 128 -> 2128", "Node D has exactly 128 Mi of memory.", "Node D has exactly 2128 Mi of memory.", "F04", "FAIL"),
    ("value 30 -> 1030 days", "Backups are retained for 30 days.", "The backup job retains backups for 1030 days.", "F18", "FAIL"),
    ("value 21.5 -> 1021.5", "about 21.5 °C", "about 1021.5 °C", "F12", "FAIL"),
    ("sign: 21.5 -> minus 21.5 (U+2212)", "about 21.5 °C", "about −21.5 °C", "F12", "FAIL"),
    ("dual contradiction, same sentence", "Node A has exactly 64 Mi of memory.", "Node A has exactly 64 Mi of memory, or possibly 46 Mi.", "F01", "FAIL"),
    ("dual contradiction, two sentences", "Node A has exactly 64 Mi of memory.", "Node A has exactly 64 Mi of memory. Node A has exactly 46 Mi of memory.", "F01", "FAIL"),
    ("negation: no longer active", "Node A is currently active.", "Node A is no longer active.", "F05", "FAIL"),
    ("negation: isn't active", "Node A is currently active.", "Node A isn't active.", "F05", "FAIL"),
    ("negation: not yet active", "Node A is currently active.", "Node A is not yet active.", "F05", "FAIL"),
    ("negation: inactive", "Node A is currently active.", "Node A is inactive.", "F05", "FAIL"),
    ("negation: no longer full duplex", "Link AB is full duplex.", "Link AB is no longer full duplex.", "F11", "FAIL"),
    ("state of another subject", "Node A is currently active.", "Node A, unlike the currently active node B, is idle.", "F05", "FAIL"),
    ("schedule: weekly, not daily", "The backup job runs daily.", "The backup job runs weekly, not daily.", "F17", "FAIL"),
    ("approx marker dropped, 'around' inside another word", "The maximum latency of cluster 1 is approximately 250 ms.", "The maximum turnaround latency of cluster 1 is 250 ms.", "F08", "FAIL"),
    ("approx marker not in frozen list: nearly", "Node A has exactly 64 Mi of memory.", "Node A has nearly 64 Mi of memory.", "F01", "FAIL"),
    ("unknown unit", "Node A has exactly 64 Mi of memory.", "Node A has exactly 64 Mx of memory.", "F01", "FAIL"),
    ("in-table wrong unit Mi -> Gi", "Node A has exactly 64 Mi of memory.", "Node A has exactly 64 Gi of memory.", "F01", "FAIL"),
    ("subject substring: node C deleted, 'node count' present", "Node C has exactly 16 Mi of memory.", "The node count limit is 16 Mi of memory per pod.", "F03", "FAIL"),
    ("paraphrase: thousands separator", "exactly 4096 entries", "exactly 4,096 entries", "F14", "PASS"),
    ("paraphrase: 64.0", "exactly 64 Mi", "exactly 64.0 Mi", "F01", "PASS"),
    ("paraphrase: word 'about' unrelated to the value", "Node A has exactly 64 Mi of memory.", "About node A: it has 64 Mi of memory.", "F01", "PASS"),
    ("paraphrase: two facts in one sentence", "Node A has exactly 64 Mi of memory.\nNode B has exactly 32 Mi of memory.", "Node A has 64 Mi of memory and node B has 32 Mi.", "F02", "PASS"),
    ("paraphrase: region with another hyphenated word", "Cluster 1 is located in the eu-central region.", "Cluster 1 is located in the low-latency eu-central region.", "F09", "PASS"),
]

print("\n== TARGETED CASES (verdict for the targeted fact only) ==")
tally = {"OK": 0, "FALSE_PASS": 0, "FALSE_FAIL": 0}
for name, old, new, fid, must in CASES:
    assert old in M0, name
    _, by = run(M0.replace(old, new))
    got = by[fid]["verdict"]
    if must == "FAIL":
        res = "FALSE_PASS" if got == "TWIN_VALID" else "OK"
    else:
        res = "OK" if got == "TWIN_VALID" else "FALSE_FAIL"
    tally[res] += 1
    print(f"{res:10s} {fid} {name:55s} -> {got} ({by[fid]['reason']}, value={by[fid]['actual']['value']!r})")
print("\nTALLY", tally, "of", len(CASES))

# 4. Comparator: duplicate fact_id in extractor output.
ext = extract_all(M0, Q)
dup = ext + [dict(ext[0], value=46)]
print("\nduplicate fact_id in extractor output ->", compare_all(V, dup)["final_verdict"], "| F01 actual:",
      [r for r in compare_all(V, dup)["results"] if r["fact_id"] == "F01"][0]["actual"]["value"])
