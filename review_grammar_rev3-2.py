#!/usr/bin/env python3
"""Independent review of LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3 (pre-freeze).
Run next to the REV3 JSON, prove_grammar_rev3.py, FROZEN_VQ_REFERENCE.json and
the frozen M_0. Uses the proof's own split() and parse() unchanged."""
import io, contextlib, json, re, itertools, os
cwd_files = set(os.listdir("."))
import types
P = types.SimpleNamespace()
_src = open("prove_grammar_rev3.py", encoding="utf-8").read().replace("sys.exit(", "(lambda *_: None)(")
_ns = {"__file__": os.path.abspath("prove_grammar_rev3.py"), "__name__": "proof"}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(_src, "prove_grammar_rev3.py", "exec"), _ns)  # the proof exits at import; run it without the exit
P.__dict__.update(_ns)
G, V = P.G, P.V
key = lambda f: (f["subject"], f["relation"], json.dumps(f["value"]), f["unit"], f["qualifier"])
WANT = {key(v): v for v in V}

def facts(text):
    rs = [P.parse(c) for c in P.split(text)]
    return rs, [key(r["fact"]) for r in rs if r["status"] == "PARSED"]

print("1. SELF-CONSISTENCY OF THE JSON (three copies of the same vocabulary)")
tc, cv, pr = G["token_classes"], G["closed_vocabulary"], G["placeholder_regexes"]
print("   placeholder_regexes == token_classes regex:", all(pr[k] == tc[k]["regex"] for k in pr if k in tc), "| placeholders with no token class:", [k for k in pr if k not in tc])
inv = lambda d: {a: k for k, al in d.items() for a in al}
units = {}
for c in ("DATA_UNIT", "TIME_UNIT", "RATE_UNIT", "TEMP_UNIT", "DAY_UNIT", "ENTRY_UNIT"): units.update(tc[c]["semantic_map"])
states = {}
for c in ("STATE", "DUPLEX_STATE", "POLICY", "MODE"): states.update(tc[c]["semantic_map"])
print("   subjects agree:", inv(cv["subjects"]) == tc["SUBJECT"]["semantic_map"], "| units agree:", inv(cv["units"]) == units, "| states agree:", inv(cv["states"]) == states)

print("\n2. YESTERDAY'S 40 HELD-OUT CORRUPTIONS")
src = open("/home/claude/nova_q_review/v02/heldout_level0_round1.py", encoding="utf-8").read()
m = re.search(r"CASES = \[.*?\n\]", src, re.S); ns = {}; exec(m.group(0), ns)
ids = {v["fact_id"]: key(v) for v in json.load(open("/home/claude/nova_q_review/v02/NOVA_Q_FIXTURE_01_REVIEW_DRAFT.json"))["V"]}
acc = [(g, new) for g, fid, new, must in ns["CASES"] if must == "FAIL" and all(r["status"] == "PARSED" for r in facts(new)[0]) and ids[fid] in facts(new)[1]]
print(f"   accepted as the true fact: {len(acc)} of 40", acc)

print("\n3. SMALL HOLES FROM THE FIRST REVIEW + NEW PROBES  (expect = what a sound grammar should do)")
A = "Node A has exactly 64 Mi of memory"
probes = [
    ("production mode mode", "The system runs in production mode mode", "reject"),
    ("impossible date 99 April", "Sensor X1 was last calibrated on 99 April 2026", "reject"),
    ("impossible date 31 February (ISO)", "sensor_x1 calibration_date=2026-02-31", "reject"),
    ("leading zeros 0064", "Node A has exactly 0064 Mi of memory", "reject"),
    ("~250 ms", "The maximum latency of cluster 1 is ~250 ms", "APPROX"),
    ("approx. 250 ms", "The maximum latency of cluster 1 is approx. 250 ms", "APPROX"),
    ("marker dropped on latency", "The maximum latency of cluster 1 is 250 ms", "EXACT"),
    ("marker added on memory", "Node A has about 64 Mi of memory", "APPROX"),
    ("two sentences, one line", "Node A is currently active. Node D is disabled.", "2 facts"),
    ("';' and newline mixed", "node_a state=active;node_d state=disabled\nsystem mode=production", "3 facts"),
    ("double space", "Node A has exactly  64 Mi of memory", "reject"),
    ("fullwidth digits (non-ASCII)", "Node A has exactly ６４ Mi of memory", "reject"),
    ("Arabic-Indic digits (non-ASCII)", "Node A has exactly ٦٤ Mi of memory", "reject"),
    ("negative number", "Sensor X1 reports a temperature of about -21.5 °C", "reject"),
    ("unknown clause after a valid one", A + ". Node A is offline.", "reject"),
    ("valid clause + trailing comment", A + " (unverified)", "reject"),
    ("subject of another relation", "Node B is disabled", "1 fact (invented)"),
    ("duplicate statement", A + ". " + A + ".", "2 facts (duplicate)"),
    ("tab instead of space", "Node A has exactly 64\tMi of memory", "reject"),
    ("CRLF line ending", A + ".\r\nNode D is disabled.", "2 facts or reject"),
]
for name, text, expect in probes:
    rs, fs = facts(text)
    ok = all(r["status"] == "PARSED" for r in rs)
    shown = [(r["fact"]["subject"], r["fact"]["relation"], r["fact"]["value"], r["fact"]["unit"], r["fact"]["qualifier"]) for r in rs if r["status"] == "PARSED"]
    print(f"   {name:36s} expect {expect:22s} -> {'ACCEPT' if ok else 'reject'} {shown if ok else ''}")

print("\n4. TRUE SHORTEST TEXT (all productions and aliases, not only the compact ones)")
total = 0; mixed = []
for v in V:
    best = None
    for p, rx in P.PRODS:
        if p["relation"] != v["relation"]: continue
        t = re.sub(r"^\^|\$$", "", p["regex_template"])
        slots = re.findall(r"\(\?P<\w+>\{\{(\w+)\}\}\)|\{\{(NUM_MODIFIER)\}\}", t)
        opts = []
        for a, b in slots:
            n = a or b
            if n == "SUBJECT": opts.append(G["closed_vocabulary"]["subjects"][v["subject"]])
            elif n == "NUM_MODIFIER": opts.append(["~", "about "] if v["qualifier"] == "APPROX" else [""])
            elif n == "NUMBER": opts.append([str(v["value"])])
            elif n in ("DATE", "REGION", "VERSION"): opts.append([str(v["value"])])
            else: opts.append([k for k, c in tc[n]["semantic_map"].items() if c == (v["value"] if n in ("STATE", "DUPLEX_STATE", "POLICY", "MODE", "SCHEDULE") else v["unit"])])
        for combo in itertools.product(*opts):
            it = iter(combo); s = re.sub(r"\(\?P<\w+>\{\{\w+\}\}\)|\{\{NUM_MODIFIER\}\}", lambda _: next(it), t)
            r = P.parse(s)
            if r["status"] == "PARSED" and key(r["fact"]) == key(v) and (best is None or len(s) < len(best[0])): best = (s, p["id"])
    total += len(best[0]); mixed.append(best)
total += len(V) - 1
print(f"   true minimum = {total} chars ({total/789:.1%} of M_0); reported minimum = 481; threshold 552")
print("   clauses where the verbose form is shorter than the compact one:", [s for s, pid in mixed if "VERBOSE" in pid])

print("\n5. MIXED ASCII / NON-ASCII DIGITS (accepted in REV2)")
for name, text in [("6 + fullwidth 4", "Node A has exactly 6\uff14 Mi of memory"), ("1 + Arabic-Indic 2", "Cluster 1 contains 1\u0662 nodes"),
                   ("date, fullwidth day digit", "Sensor X1 was last calibrated on 1\uff18 April 2026"), ("3 + fullwidth 0 days", "The backup job retains its backups for 3\uff10 days")]:
    rs, _ = facts(text); print(f"   {name:28s} -> {'ACCEPT' if all(r['status']=='PARSED' for r in rs) else 'reject'}")
print("\n6. SPACING AFTER MODIFIERS")
for name, text in [("exactly + 2 spaces", "Node A has exactly  64 Mi of memory"), ("about + 2 spaces", "Sensor X1 reports a temperature of about  21.5 \u00b0C"),
                   ("~ + space", "The maximum latency of cluster 1 is ~ 250 ms"), ("~ no space", "The maximum latency of cluster 1 is ~250 ms")]:
    rs, _ = facts(text); print(f"   {name:28s} -> {'ACCEPT' if all(r['status']=='PARSED' for r in rs) else 'reject'}")
