#!/usr/bin/env python3
"""NOVA Q Level 0 — held-out round 2 (written by Claude AFTER grammar REV3 freeze,
after V0.3 delivery; not disclosed to the implementer before the run).
Each case = frozen M_0 with one mutation. Runs extractor+comparator V0.3 in-process."""
import importlib.util, json, sys, hashlib, traceback
from pathlib import Path
R=Path(__file__).resolve().parent
def load(n,f):
    s=importlib.util.spec_from_file_location(n,R/f); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
E=load("e","level0_extract_v0_4.py"); C=load("c","level0_compare_v0_4.py")
G=E.FrozenGrammar(R/"LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json")
V=json.load(open(R/"FROZEN_VQ_REFERENCE.json",encoding="utf-8"))["V"]
M0=open(R/"NOVA_Q_FIXTURE_01_M0_SOURCE.txt",encoding="utf-8").read()
L=[x for x in M0.split("\n") if x]
assert len(L)==20
def rep(i,new):  # i = 1-based fact line
    x=L[:]; x[i-1]=new; return "\n".join(x)+"\n"
def add(extra): return "\n".join(L+[extra])+"\n"
def drop(i): x=L[:]; del x[i-1]; return "\n".join(x)+"\n"
Z="0"*28
FAIL=[ # (id, text)  -> anything except TWIN_VALID is correct
 # --- A: numeric precision / canonicalization
 ("A01_precision_tail_decimal", rep(12,"Sensor X1 reports a temperature of about 21.5"+Z+"1 °C.")),
 ("A02_precision_tail_integer", rep(1,"Node A has exactly 64."+Z+"1 Mi of memory.")),
 ("A03_precision_tail_latency", rep(8,"The maximum latency of cluster 1 is approximately 250."+Z+"1 ms.")),
 ("A04_precision_tail_compact", rep(16,"Storage S1 capacity=2048."+"0"*40+"7 Gi")),
 ("A05_precision_29th_digit", rep(12,"Sensor X1 temperature=~21.500000000000000000000000004 °C")),
 ("A06_huge_integer", rep(1,"Node A has exactly 1"+"0"*40+" Mi of memory.")),
 ("A07_off_by_small", rep(12,"Sensor X1 reports a temperature of about 21.51 °C.")),
 ("A08_comma_group_wrong", rep(10,"Link AB provides exactly 1,0000 Mbps of bandwidth.")),
 ("A09_comma_value_change", rep(10,"Link AB provides exactly 10,000 Mbps of bandwidth.")),
 ("A10_leading_zero", rep(1,"Node A has exactly 064 Mi of memory.")),
 ("A11_negative", rep(1,"Node A has exactly -64 Mi of memory.")),
 ("A12_exponent", rep(10,"Link AB provides exactly 1e3 Mbps of bandwidth.")),
 ("A13_number_word_wrong", rep(7,"Cluster 1 contains thirteen nodes.")),
 ("A14_number_word_compound", rep(7,"Cluster 1 contains one hundred twelve nodes.")),
 ("A15_fraction", rep(18,"The backup job retains its backups for 30.5 days.")),
 # --- B: qualifier
 ("B01_exact_to_approx", rep(1,"Node A has about 64 Mi of memory.")),
 ("B02_approx_to_exact", rep(8,"The maximum latency of cluster 1 is exactly 250 ms.")),
 ("B03_approx_dropped", rep(12,"Sensor X1 reports a temperature of 21.5 °C.")),
 ("B04_tilde_on_exact", rep(18,"Backup job retention=~30 days")),
 ("B05_double_modifier", rep(8,"The maximum latency of cluster 1 is exactly approximately 250 ms.")),
 ("B06_at_most", rep(8,"The maximum latency of cluster 1 is at most 250 ms.")),
 # --- C: units
 ("C01_Mi_to_MB", rep(1,"Node A has exactly 64 MB of memory.")),
 ("C02_Mi_to_megabytes", rep(2,"Node B has exactly 32 megabytes of memory.")),
 ("C03_Gi_to_GB", rep(16,"Storage unit S1 provides exactly 2048 GB of capacity.")),
 ("C04_Mi_to_Gi", rep(4,"Node D has exactly 128 Gi of memory.")),
 ("C05_ms_to_s", rep(8,"The maximum latency of cluster 1 is approximately 250 s.")),
 ("C06_degF", rep(12,"Sensor X1 reports a temperature of about 21.5 °F.")),
 ("C07_unit_class_cross", rep(8,"Cluster 1 max_latency=~250 days")),
 ("C08_Gbps", rep(10,"Link AB provides exactly 1 Gbps of bandwidth.")),
 ("C09_unit_glued", rep(1,"Node A has exactly 64Mi of memory.")),
 # --- D: subject / relation swaps
 ("D01_subject_swap", rep(1,"Node B has exactly 64 Mi of memory.")+""),
 ("D02_state_flip", rep(5,"Node A is disabled.")),
 ("D03_negation", rep(5,"Node A is not active.")),
 ("D04_inactive", rep(5,"Node A is inactive.")),
 ("D05_was_active", rep(5,"Node A was active.")),
 ("D06_half_duplex", rep(11,"Link AB is half duplex.")),
 ("D07_region_change", rep(9,"Cluster 1 is located in the eu-central-1 region.")),
 ("D08_region_case", rep(9,"Cluster 1 region=EU-central")),
 ("D09_firmware_extra", rep(20,"Node C runs firmware version 4.2.1.0.")),
 ("D10_firmware_10", rep(20,"Node C firmware=4.2.10")),
 ("D11_policy_lifo", rep(15,"Queue Q operates under a LIFO policy.")),
 ("D12_schedule_weekly", rep(17,"The backup job runs weekly.")),
 ("D13_mode_test", rep(19,"The system runs in test mode.")),
 ("D14_relation_cross", rep(14,"Queue Q contains exactly 4096 nodes.")),
 # --- E: dates
 ("E01_date_shift", rep(13,"Sensor X1 was last calibrated on 19 April 2026.")),
 ("E02_date_invalid", rep(13,"Sensor X1 calibration_date=2026-04-31")),
 ("E03_date_us_order", rep(13,"Sensor X1 was last calibrated on April 18 2026.")),
 ("E04_date_slash", rep(13,"Sensor X1 calibration_date=18/04/2026")),
 ("E05_date_year", rep(13,"Sensor X1 was last calibrated on 18 April 2025.")),
 ("E06_date_time_suffix", rep(13,"Sensor X1 calibration_date=2026-04-18T00:00")),
 # --- F: omission / addition / contradiction
 ("F01_drop_one", drop(6)),
 ("F02_drop_last", drop(20)),
 ("F03_invented_extra", add("Node B is active.")),
 ("F04_contradiction_added", add("Node D is active.")),
 ("F05_contradiction_value", add("Node A memory=65 Mi")),
 ("F06_duplicate_same", add("Node A has exactly 64 Mi of memory.")),
 ("F07_duplicate_alias", add("node_a memory=sixty-four MiB")),
 ("F08_empty", ""),
 ("F09_only_separators", ";;\n..\n"),
 # --- G: hidden / unparsed content
 ("G01_trailing_comment", rep(5,"Node A is currently active (as of yesterday).")),
 ("G02_hedge_prefix", rep(5,"Possibly Node A is currently active.")),
 ("G03_conditional", rep(19,"The system runs in production mode unless paused.")),
 ("G04_free_sentence", add("All of the above may be outdated.")),
 ("G05_hash_comment", add("# Node D is active")),
 ("G06_colon_note", rep(6,"Node D is disabled: false")),
 ("G07_question", rep(6,"Node D is disabled?")),
 ("G08_zero_width", rep(5,"Node A is currently​ active.")),
 ("G09_homoglyph_cyrillic_A", rep(5,"Node А is currently active.")),
 ("G10_fullwidth_digits", rep(1,"Node A has exactly ６４ Mi of memory.")),
 ("G11_arabic_digits", rep(18,"The backup job retains its backups for ٣٠ days.")),
 ("G12_double_space", rep(5,"Node A is  currently active.")),
 ("G13_tab", rep(5,"Node A is\tcurrently active.")),
 ("G14_nbsp", rep(5,"Node A is currently active.")),
 ("G15_and_joined", rep(5,"Node A is currently active and Node D is active.")),
 ("G16_comma_joined", rep(5,"Node A is currently active, Node B is active.")),
 ("G17_lowercase_subject", rep(5,"node a is currently active.")),
 ("G18_ring_above_C", rep(12,"Sensor X1 reports a temperature of about 21.5 ˚C.")),
 ("G19_bom_then_wrong", "﻿"+rep(2,"Node B has exactly 33 Mi of memory.")),
 ("G20_fact_id_leak", rep(1,"F01 Node A has exactly 64 Mi of memory.")),
]
PASS=[ # must be TWIN_VALID
 ("P01_M0_frozen", M0),
 ("P02_minimum_compact", open(R/"MINIMUM_COMPACT_REV3.txt",encoding="utf-8").read()),
 ("P03_reordered", "\n".join(reversed(L))+"\n"),
 ("P04_one_line_periods", " ".join(L)),
 ("P05_alias_units", rep(1,"Node A has exactly 64 MiB of memory.")),
 ("P06_mebibytes_word", rep(2,"Node B has exactly 32 mebibytes of memory.")),
 ("P07_number_word_64", rep(1,"Node A has sixty-four Mi of memory.")),
 ("P08_iso_date", rep(13,"Sensor X1 calibration_date=2026-04-18")),
 ("P09_approx_abbrev", rep(8,"The maximum latency of cluster 1 is approx. 250 ms.")),
 ("P10_tilde_degC", rep(12,"sensor_x1 temperature=~21.5 degC")),
 ("P11_trailing_zero", rep(12,"Sensor X1 reports a temperature of about 21.50 °C.")),
 ("P12_comma_1000", rep(10,"Link AB provides exactly 1,000 Mbps of bandwidth.")),
 ("P13_mixed_separators", ";".join(L[:10]).replace(".","")+"\n"+"\n".join(L[10:])),
 ("P14_fifo_long", rep(15,"Queue Q operates under a first-in, first-out policy.")),
 ("P15_every_day", rep(17,"Backup job runs every day")),
 ("P16_no_exactly", rep(4,"Node D has 128 Mi of memory.")),
]
def run(text):
    try:
        ex=G.extract(text); r=C.compare(ex,V)
        return r.get("trial_verdict") or r.get("status"), (ex.get("reason") or "")
    except Exception as e:
        return "CRASH", type(e).__name__
fa=[];fr=[];cr=[];rows=[]
for cid,t in FAIL:
    v,why=run(t); rows.append((cid,"must_fail",v,why))
    if v=="TWIN_VALID": fa.append(cid)
    if v=="CRASH": cr.append(cid)
for cid,t in PASS:
    v,why=run(t); rows.append((cid,"must_pass",v,why))
    if v!="TWIN_VALID": fr.append(cid)
    if v=="CRASH": cr.append(cid)
for r in rows: print("%-30s %-9s %-24s %s"%r)
out={"suite":"heldout_level0_round2","must_fail":len(FAIL),"must_pass":len(PASS),"FALSE_ACCEPTS":fa,"FALSE_REJECTS":fr,"CRASHES":cr,
 "rows":[dict(zip(("id","kind","verdict","detail"),r)) for r in rows]}
open(R/"REGRESSION_ROUND2_ON_V0_4.json","w",encoding="utf-8",newline="\n").write(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print("\nFALSE_ACCEPTS=%d %s\nFALSE_REJECTS=%d %s\nCRASHES=%d %s"%(len(fa),fa,len(fr),fr,len(cr),cr))
