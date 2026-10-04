#!/usr/bin/env python3
"""NOVA Q Level 0 — held-out round 3 (Claude). Written AFTER V0.4 extractor+comparator
were delivered and hash-verified; not disclosed to the implementer before this run.
Part A: targeted cases. Part B: seeded single-edit mutation fuzz with an independent oracle.
Part C: CLI fail-closed checks."""
import importlib.util, json, random, subprocess, sys, tempfile, os, re
from pathlib import Path
R=Path(__file__).resolve().parent
def load(n,f):
    s=importlib.util.spec_from_file_location(n,R/f); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
E=load("e","level0_extract_v0_4.py"); C=load("c","level0_compare_v0_4.py")
GP=R/"LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json"
G=E.FrozenGrammar(GP)
VP=R/"FROZEN_VQ_REFERENCE.json"
V=json.load(open(VP,encoding="utf-8"))["V"]
M0=open(R/"NOVA_Q_FIXTURE_01_M0_SOURCE.txt",encoding="utf-8").read()
MIN=open(R/"MINIMUM_COMPACT_REV3.txt",encoding="utf-8").read()
L=[x for x in M0.split("\n") if x]; assert len(L)==20
def rep(i,new): x=L[:]; x[i-1]=new; return "\n".join(x)+"\n"
def add(extra): return "\n".join(L+[extra])+"\n"
FAIL=[
 ("N01_tail_37_zeros", rep(1,"Node A has exactly 64."+"0"*37+"1 Mi of memory.")),
 ("N02_tail_300_zeros", rep(12,"Sensor X1 temperature=~21.5"+"0"*300+"9 °C")),
 ("N03_int_5000_digits", rep(1,"Node A memory="+"9"*5000+" Mi")),
 ("N04_leading_zeros", rep(1,"Node A has exactly 0064 Mi of memory.")),
 ("N05_space_in_number", rep(1,"Node A has exactly 6 4 Mi of memory.")),
 ("N06_decimal_comma", rep(12,"Sensor X1 reports a temperature of about 21,5 °C.")),
 ("N07_two_dots", rep(12,"Sensor X1 temperature=~21.5.0 °C")),
 ("N08_superscript", rep(1,"Node A has exactly 64² Mi of memory.")),
 ("N09_vulgar_fraction", rep(12,"Sensor X1 temperature=~21½ °C")),
 ("N10_word_no_hyphen", rep(1,"Node A has sixty four Mi of memory.")),
 ("N11_word_capital", rep(7,"Cluster 1 contains Twelve nodes.")),
 ("N12_dozen", rep(7,"Cluster 1 contains a dozen nodes.")),
 ("N13_comma_million", rep(10,"Link AB bandwidth=1,000,000 Mbps")),
 ("N14_point_five_more", rep(18,"Backup job retention=30.000000000000000000000000000000000000000000001 days")),
 ("N15_trailing_dot_digit", rep(1,"Node A has exactly 64 Mi of memory.5")),
 ("N16_hex", rep(1,"Node A memory=0x40 Mi")),
 ("N17_plus_sign", rep(1,"Node A memory=+64 Mi")),
 ("N18_range", rep(8,"Cluster 1 max_latency=~250-300 ms")),
 ("Q01_nearly", rep(8,"The maximum latency of cluster 1 is nearly 250 ms.")),
 ("Q02_tilde_space", rep(8,"Cluster 1 max_latency=~ 250 ms")),
 ("Q03_approx_no_dot", rep(8,"The maximum latency of cluster 1 is approx 250 ms.")),
 ("Q04_both_qualifiers", add("Node A memory=~64 Mi")),
 ("Q05_less_than", rep(8,"Cluster 1 max_latency<250 ms")),
 ("Q06_at_least", rep(1,"Node A has at least 64 Mi of memory.")),
 ("Q07_exactly_tilde", rep(1,"Node A memory=exactly ~64 Mi")),
 ("U01_mi_lower", rep(1,"Node A has exactly 64 mi of memory.")),
 ("U02_MIB_upper", rep(1,"Node A has exactly 64 MIB of memory.")),
 ("U03_msec", rep(8,"Cluster 1 max_latency=~250 msec")),
 ("U04_MBPS", rep(10,"Link AB bandwidth=1000 MBPS")),
 ("U05_Celsius_bare", rep(12,"Sensor X1 reports a temperature of about 21.5 Celsius.")),
 ("U06_K", rep(12,"Sensor X1 temperature=~21.5 K")),
 ("U07_gigabytes_for_Gi", rep(16,"Storage S1 capacity=2048 gigabytes")),
 ("U08_no_unit", rep(1,"Node A memory=64")),
 ("U09_unit_before", rep(1,"Node A memory=Mi 64")),
 ("U10_weeks", rep(18,"Backup job retention=30 weeks")),
 ("S01_relation_swap_capacity", rep(16,"Storage unit S1 has exactly 2048 Gi of memory.")),
 ("S02_relation_swap_memory", rep(1,"Node A provides exactly 64 Mi of capacity.")),
 ("S03_extra_system_active", add("The system is active.")),
 ("S04_state_compact_flip", add("Node A state=disabled")),
 ("S05_extra_after_dot", rep(5,"Node A is currently active.Node B is active.")),
 ("S06_version_then_fact", rep(20,"Node C runs firmware version 4.2.1.5")),
 ("S07_version_prefix", rep(20,"Node C firmware=v4.2.1")),
 ("S08_version_two_parts", rep(20,"Node C firmware=4.2")),
 ("S09_Production_cap", rep(19,"System mode=Production")),
 ("S10_Fifo_case", rep(15,"Queue Q policy=Fifo")),
 ("S11_region_underscore", rep(9,"Cluster 1 region=eu_central")),
 ("S12_region_trailing_dash", rep(9,"Cluster 1 region=eu-central-")),
 ("S13_region_other", rep(9,"Cluster 1 region=us-east")),
 ("S14_subject_unknown", rep(1,"Node E has exactly 64 Mi of memory.")),
 ("S15_duplex_on_node", add("Node A is full duplex.")),
 ("S16_swap_two_values", "\n".join(["Node A has exactly 32 Mi of memory.","Node B has exactly 64 Mi of memory."]+L[2:])+"\n"),
 ("S17_swap_two_states", "\n".join(L[:4]+["Node A is disabled.","Node D is currently active."]+L[6:])+"\n"),
 ("D01_iso_single_digit", rep(13,"Sensor X1 calibration_date=2026-4-18")),
 ("D02_month_abbrev", rep(13,"Sensor X1 was last calibrated on 18 Apr 2026.")),
 ("D03_year_zero", rep(13,"Sensor X1 calibration_date=0000-04-18")),
 ("D04_feb_30", rep(13,"Sensor X1 was last calibrated on 30 February 2026.")),
 ("D05_day_zero", rep(13,"Sensor X1 was last calibrated on 0 April 2026.")),
 ("D06_ordinal", rep(13,"Sensor X1 was last calibrated on 18th April 2026.")),
 ("D07_month_13", rep(13,"Sensor X1 calibration_date=2026-13-18")),
 ("D08_swapped_iso", rep(13,"Sensor X1 calibration_date=2026-18-04")),
 ("D09_one_day_off_iso", rep(13,"Sensor X1 calibration_date=2026-04-17")),
 ("X01_whole_text_twice", M0+M0),
 ("X02_replace_with_duplicate", rep(3,"Node A has exactly 64 Mi of memory.")),
 ("X03_alias_duplicate", add("cluster 1 nodes=12")),
 ("X04_json_of_V", json.dumps(V)),
 ("X05_verdict_string", "TWIN_VALID"),
 ("X06_nul_byte", rep(5,"Node A is currently active.\x00")),
 ("X07_line_separator_hide", rep(5,"Node A is currently active Node B is active")),
 ("X08_nel_hide", rep(5,"Node A is currently active\u0085Node B is active")),
 ("X09_formfeed", rep(5,"Node A is currently active\x0cNode B is active")),
 ("X10_rtl_override", rep(5,"Node A is ‮currently active.")),
 ("X11_combining_mark", rep(5,"Node A is currently activé.")),
 ("X12_soft_hyphen", rep(9,"Cluster 1 region=eu-cen­tral")),
 ("X13_non_breaking_hyphen", rep(9,"Cluster 1 region=eu‑central")),
 ("X14_markdown_strike", rep(6,"~~Node D is disabled~~")),
 ("X15_html_comment", add("<!-- Node D is active -->")),
 ("X16_quoted", rep(6,'"Node D is disabled"')),
 ("X17_not_prefix", rep(6,"It is not true that Node D is disabled.")),
 ("X18_only_19_plus_junk_word", rep(6,"Node D is disabled maybe")),
 ("X19_equals_spaces", rep(1,"Node A memory = 64 Mi")),
 ("X20_colon_form", rep(1,"Node A memory: 64 Mi")),
 ("X21_min_with_one_change", MIN.replace("memory=128 Mi","memory=129 Mi")),
 ("X22_min_drop_qualifier", MIN.replace("=~250","=250")),
 ("X23_min_truncated", MIN[:len(MIN)-20]),
]
PASS=[
 ("P01_M0", M0), ("P02_MIN", MIN),
 ("P03_leading_trailing_spaces", "\n".join("  "+x+"  " for x in L)),
 ("P04_semicolons_spaces", " ; ".join(x.rstrip(".") for x in L)),
 ("P05_roughly", rep(8,"The maximum latency of cluster 1 is roughly 250 ms.")),
 ("P06_around", rep(12,"Sensor X1 reports a temperature of around 21.5 °C.")),
 ("P07_approx_equal_to", rep(8,"Cluster 1 max_latency=approximately equal to 250 ms")),
 ("P08_milliseconds", rep(8,"Cluster 1 max_latency=~250 milliseconds")),
 ("P09_degrees_celsius", rep(12,"Sensor X1 temperature=~21.5 degrees Celsius")),
 ("P10_gibibytes", rep(16,"Storage S1 capacity=2048 gibibytes")),
 ("P11_iso_in_verbose", rep(13,"Sensor X1 was last calibrated on 2026-04-18.")),
 ("P12_longdate_in_compact", rep(13,"Sensor X1 calibration_date=18 April 2026")),
 ("P13_trailing_zeros_many", rep(12,"Sensor X1 temperature=~21.5"+"0"*60+" °C")),
 ("P14_int_dot_zeros", rep(1,"Node A memory=64."+"0"*50+" Mi")),
 ("P15_2048_comma", rep(16,"Storage S1 capacity=2,048 Gi")),
 ("P16_thirty_word", rep(18,"The backup job retains its backups for thirty days.")),
 ("P17_entry_singular", rep(14,"Queue Q depth=4096 entry")),
 ("P18_fifo_lower", rep(15,"Queue Q policy=fifo")),
 ("P19_full_hyphen_duplex", rep(11,"Link AB duplex=full-duplex")),
 ("P20_snake_subjects", rep(5,"node_a state=active")),
 ("P21_blank_lines", "\n\n".join(L)+"\n\n"),
 ("P22_shuffled_mixed", ";".join(MIN.split(";")[::-1])),
]
INFO=[ # reported, not scored
 ("I01_CRLF_line_endings", M0.replace("\n","\r\n")),
 ("I02_greek_question_mark_as_semicolon", MIN.replace(";",";")),
 ("I03_BOM_prefix", "﻿"+M0),
]
def verdict(text):
    try:
        ex=G.extract(text); r=C.compare(ex,V)
        return (r.get("trial_verdict") or r.get("status")), ex
    except Exception as e:
        return "CRASH:"+type(e).__name__, None
rows=[];fa=[];fr=[];cr=[]
for cid,t in FAIL:
    v,_=verdict(t); rows.append((cid,"must_fail",v))
    if v=="TWIN_VALID": fa.append(cid)
    if v.startswith("CRASH") or v=="BLOCKER": cr.append(cid)
for cid,t in PASS:
    v,_=verdict(t); rows.append((cid,"must_pass",v))
    if v!="TWIN_VALID": fr.append(cid)
for cid,t in INFO:
    v,_=verdict(t); rows.append((cid,"info",v))
for r in rows: print("%-36s %-9s %s"%r)

# ---- Part B: fuzz. Independent oracle: an accepted mutant is legitimate only if every clause,
# split independently, is in a small whitelist of clause strings known to be valid renderings.
def base_clauses(text):
    out=[]
    for part in re.split(r"[;\n]",text):
        p=part.strip(" ")
        if p.endswith("."): p=p[:-1].strip(" ")
        if p: out.append(p)
    return out
rng=random.Random(20261004)
ALPH=list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;-=~_°\n")+["\t"," ","​","é","Ａ","٣"]
def mutate(s):
    i=rng.randrange(len(s)); k=rng.randrange(4)
    if k==0: return s[:i]+s[i+1:]
    if k==1: return s[:i]+rng.choice(ALPH)+s[i:]
    if k==2: return s[:i]+rng.choice(ALPH)+s[i+1:]
    j=rng.randrange(len(s)); a,b=min(i,j),max(i,j)
    return s if a==b else s[:a]+s[b]+s[a+1:b]+s[a]+s[b+1:]
fz_total=0; fz_acc=0; fz_susp=[]; fz_crash=[]
kinds={}
for base_name,base in (("M0",M0),("MIN",MIN)):
    ok=set(base_clauses(base))
    for _ in range(60000):
        m=mutate(base)
        if rng.random()<0.3: m=mutate(m)
        if m==base: continue
        fz_total+=1
        v,ex=verdict(m)
        if v.startswith("CRASH") or v=="BLOCKER": fz_crash.append((base_name,m)); continue
        if v!="TWIN_VALID": continue
        fz_acc+=1
        mc=base_clauses(m)
        if sorted(mc)==sorted(ok): kinds["separator_or_spacing_only"]=kinds.get("separator_or_spacing_only",0)+1; continue
        diff=[c for c in mc if c not in ok]
        fz_susp.append((base_name,diff))
print("\nFUZZ mutants=%d accepted=%d benign=%s to_inspect=%d crashes=%d"%(fz_total,fz_acc,kinds,len(fz_susp),len(fz_crash)))
seen={}
for b,d in fz_susp: seen.setdefault((b,tuple(d)),0); seen[(b,tuple(d))]+=1
for (b,d),n in sorted(seen.items(), key=lambda x:-x[1])[:60]: print("  INSPECT",b,n,list(d))

# ---- Part C: CLI fail-closed
cli=[]
def run_cli(text=None, textfile=None, grammar=GP):
    with tempfile.TemporaryDirectory() as td:
        ej=os.path.join(td,"e.json")
        a=[sys.executable,str(R/"level0_extract_v0_4.py"),"--grammar",str(grammar),"--out",ej]
        if textfile is None:
            textfile=os.path.join(td,"t.txt"); open(textfile,"wb").write(text if isinstance(text,bytes) else text.encode("utf-8"))
        p1=subprocess.run(a+["--text-file",textfile],capture_output=True,text=True)
        tb1="Traceback" in p1.stderr
        if not os.path.exists(ej): return p1.returncode,None,tb1,(p1.stdout[:80])
        p2=subprocess.run([sys.executable,str(R/"level0_compare_v0_4.py"),"--extraction",ej,"--v",str(VP)],capture_output=True,text=True)
        try: j=json.loads(p2.stdout)
        except Exception: j=None
        return (p1.returncode,p2.returncode),(j or {}).get("trial_verdict") or (j or {}).get("status"),tb1 or "Traceback" in p2.stderr,""
for name,kw,want in [
 ("C01_M0_cli",dict(text=M0),"TWIN_VALID"),
 ("C02_huge_int_cli",dict(text=rep(1,"Node A memory="+"9"*5000+" Mi")),"NOT_VALID"),
 ("C03_invalid_utf8",dict(text=b"\xff\xfeNode A is active"),"NOT_VALID"),
 ("C04_missing_text_file",dict(textfile="/nonexistent/x.txt"),"NOT_VALID"),
 ("C05_wrong_grammar",dict(text=M0,grammar=VP),"NOT_VALID"),
 ("C06_empty_file",dict(text=""),"NOT_VALID"),
]:
    rc,v,tb,_=run_cli(**kw)
    good=(v=="TWIN_VALID") if want=="TWIN_VALID" else (v!="TWIN_VALID")
    good=good and not tb
    cli.append((name,rc,v,"traceback" if tb else "clean","OK" if good else "DEFECT"))
    print("%-24s rc=%s verdict=%s %s %s"%cli[-1])
cli_def=[c[0] for c in cli if c[4]!="OK"]
out={"suite":"heldout_level0_round3","target":"V0.4","must_fail":len(FAIL),"must_pass":len(PASS),
 "FALSE_ACCEPTS":fa,"FALSE_REJECTS":fr,"CRASHES_OR_BLOCKERS":cr,
 "fuzz":{"seed":20261004,"mutants":fz_total,"accepted":fz_acc,"benign":kinds,"to_inspect":len(fz_susp),"crashes":len(fz_crash)},
 "cli_defects":cli_def,"rows":[dict(zip(("id","kind","verdict"),r)) for r in rows]}
open(R/"HELDOUT_ROUND3_RESULT.json","w",encoding="utf-8",newline="\n").write(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print("\nFALSE_ACCEPTS=%d %s\nFALSE_REJECTS=%d %s\nCRASHES=%d %s\nCLI_DEFECTS=%s"%(len(fa),fa,len(fr),fr,len(cr),cr,cli_def))
