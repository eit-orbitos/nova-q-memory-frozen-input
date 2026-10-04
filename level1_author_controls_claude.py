#!/usr/bin/env python3
"""Claude — authoring of the hidden Level 1 control package (LEVEL1_PROTOCOL_V0.4 sections 7, 10, 11, 20).
Written AFTER compressor freeze (commit 2516d18). The frozen compressor is NOT run here.
Facts are hand-specified below; the input text and the feasibility witness are rendered by this
script's own template filler; V_i is built from the specification, not by any parser."""
import json, re, hashlib, importlib.util, secrets, sys
from pathlib import Path
R=Path(__file__).resolve().parent
def load(n,f):
    s=importlib.util.spec_from_file_location(n,R/f); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
E=load("e","level0_extract_v0_4.py"); C=load("c","level0_compare_v0_4.py")
G=E.FrozenGrammar(R/"LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json"); g=G.g
V0=json.load(open(R/"FROZEN_VQ_REFERENCE.json",encoding="utf-8"))["V"]
P={p["id"]:p for p in g["productions"]}; tc=g["token_classes"]; SUBJ=g["closed_vocabulary"]["subjects"]
SLOT=re.compile(r"\(\?P<(\w+)>\{\{([A-Z_]+)\}\}\)|\{\{([A-Z_]+)\}\}")
CANON={a:c for c,al in SUBJ.items() for a in al}
def fill(pid, subj, mod, val, unit):
    def f(m):
        grp,cls=m.group(1),(m.group(2) or m.group(3))
        if cls=="SUBJECT": return subj
        if cls=="NUM_MODIFIER": return mod
        if grp=="unit": return unit
        return val
    return SLOT.sub(f,P[pid]["regex_template"].strip("^$"))
def unit_class(pid):
    m=re.search(r"\(\?P<unit>\{\{([A-Z_]+)\}\}\)",P[pid]["regex_template"]); return m.group(1) if m else None
def vrow(pid, subj, mod, val, unit, vnum):
    p=P[pid]; vc=p["value_class"]; uc=unit_class(pid)
    if vc in("NUMBER","DATE"): value=vnum
    elif vc in("REGION","VERSION"): value=val
    else: value=tc[vc]["semantic_map"][val]
    return {"subject":CANON[subj],"relation":p["relation"],"value":value,
            "unit":tc[uc]["semantic_map"][unit] if uc else p["unit_default"],
            "qualifier":"APPROX" if mod not in("","exactly ") else "EXACT"}
def shortest(xs): return min(xs,key=lambda s:(len(s),s))
def witness_clause(row):
    best=[]
    for pid,p in P.items():
        if p["relation"]!=row["relation"]: continue
        vc=p["value_class"]; uc=unit_class(pid)
        if vc=="NUMBER": val=str(row["value"])
        elif vc in("DATE","REGION","VERSION"): val=row["value"]
        else: val=shortest([a for a,c in tc[vc]["semantic_map"].items() if c==row["value"]])
        unit=shortest([a for a,c in tc[uc]["semantic_map"].items() if c==row["unit"]]) if uc else ""
        best.append(fill(pid,shortest(SUBJ[row["subject"]]),"~" if row["qualifier"]=="APPROX" else "",val,unit))
    return shortest(best)
# spec: (production, subject alias, modifier, value text, unit alias, canonical value for NUMBER/DATE)
C1=[ # same subjects/relations as M_0, every value or qualifier changed
 ("P_MEMORY_VERBOSE","Node A","exactly ","96","Mi",96),
 ("P_MEMORY_VERBOSE","Node B","exactly ","48","Mi",48),
 ("P_MEMORY_VERBOSE","Node C","about ","16","Mi",16),
 ("P_MEMORY_VERBOSE","Node D","exactly ","128","MiB",128),
 ("P_STATE_VERBOSE","Node A","","disabled","",None),
 ("P_STATE_VERBOSE","Node D","","currently active","",None),
 ("P_NODE_COUNT_VERBOSE","Cluster 1","","thirteen","",13),
 ("P_LATENCY_VERBOSE","cluster 1","exactly ","250","ms",250),
 ("P_REGION_VERBOSE","Cluster 1","","eu-west","",None),
 ("P_BANDWIDTH_VERBOSE","Link AB","exactly ","10,000","Mbps",10000),
 ("P_DUPLEX_VERBOSE","Link AB","","full-duplex","",None),
 ("P_TEMP_VERBOSE","Sensor X1","about ","21.6","°C",21.6),
 ("P_CAL_VERBOSE","Sensor X1","","19 April 2026","","2026-04-19"),
 ("P_DEPTH_VERBOSE","Queue Q","exactly ","4097","entries",4097),
 ("P_POLICY_VERBOSE","Queue Q","","FIFO","",None),
 ("P_CAP_VERBOSE","Storage unit S1","exactly ","2048","GB",2048),
 ("P_SCHED_VERBOSE","The backup job","","daily","",None),
 ("P_RET_VERBOSE","The backup job","","31","days",31),
 ("P_MODE_VERBOSE","The system","","production","",None),
 ("P_FW_VERBOSE","Node C","","4.2.2","",None)]
C2=[ # few facts, long aliases, number words, unusual subject/relation pairs
 ("P_TEMP_VERBOSE","Storage unit S1","approximately equal to ","7.250","degrees Celsius",7.25),
 ("P_MEMORY_VERBOSE","The backup job","approximately ","one hundred","mebibytes",100),
 ("P_POLICY_VERBOSE","Sensor X1","","first-in, first-out","",None),
 ("P_CAL_VERBOSE","Queue Q","","1 September 2031","","2031-09-01"),
 ("P_LATENCY_VERBOSE","Link AB","roughly ","1,250,000","milliseconds",1250000),
 ("P_SCHED_VERBOSE","Storage unit S1","","every day","",None),
 ("P_NODE_COUNT_VERBOSE","The system","exactly ","zero","",0)]
C3=[ # many facts, written on one line with periods
 ("P_MEMORY_VERBOSE","Queue Q","exactly ","12","gigabytes",12),
 ("P_MEMORY_VERBOSE","Sensor X1","around ","512.50","megabytes",512.5),
 ("P_MEMORY_VERBOSE","Link AB","","seventy-seven","gibibytes",77),
 ("P_STATE_VERBOSE","Sensor X1","","disabled","",None),
 ("P_STATE_VERBOSE","Cluster 1","","currently active","",None),
 ("P_STATE_VERBOSE","Queue Q","","active","",None),
 ("P_NODE_COUNT_VERBOSE","Node B","approximately ","3","",3),
 ("P_NODE_COUNT_VERBOSE","Storage unit S1","exactly ","1,024","",1024),
 ("P_LATENCY_VERBOSE","Node C","exactly ","0.125","milliseconds",0.125),
 ("P_LATENCY_VERBOSE","The system","approx. ","19","ms",19),
 ("P_REGION_VERBOSE","Node A","","ap-south1-2b","",None),
 ("P_REGION_VERBOSE","Sensor X1","","us-east","",None),
 ("P_BANDWIDTH_VERBOSE","Node D","exactly ","40","mbps",40),
 ("P_BANDWIDTH_VERBOSE","Cluster 1","about ","2.5","Mbps",2.5),
 ("P_DUPLEX_VERBOSE","Node B","","full duplex","",None),
 ("P_TEMP_VERBOSE","Node A","exactly ","0","degC",0),
 ("P_TEMP_VERBOSE","Queue Q","roughly ","88.000","degrees Celsius",88),
 ("P_CAL_VERBOSE","Node D","","29 February 2028","","2028-02-29"),
 ("P_CAL_VERBOSE","Link AB","","2000-01-01","","2000-01-01"),
 ("P_DEPTH_VERBOSE","Storage unit S1","exactly ","1","entry",1),
 ("P_DEPTH_VERBOSE","Node C","approximately equal to ","65,536","entries",65536),
 ("P_POLICY_VERBOSE","Link AB","","first-in first-out","",None),
 ("P_CAP_VERBOSE","Queue Q","exactly ","9","mebibytes",9),
 ("P_CAP_VERBOSE","Node B","around ","300","MiB",300),
 ("P_SCHED_VERBOSE","Node A","","every day","",None),
 ("P_RET_VERBOSE","Sensor X1","exactly ","ninety-nine","days",99),
 ("P_RET_VERBOSE","Cluster 1","","1","day",1),
 ("P_MODE_VERBOSE","Queue Q","","production","",None),
 ("P_FW_VERBOSE","The system","","10.0.3.27","",None),
 ("P_FW_VERBOSE","Link AB","","0.9.12","",None)]
C4=[ # mixed verbose and compact, snake_case aliases, two different values for one subject/relation
 ("P_MEMORY_VERBOSE","Node A","exactly ","64","Mi",64),
 ("P_MEMORY_VERBOSE","Node A","exactly ","64","MB",64),
 ("P_MEMORY_COMPACT","node_b","","32","Mi",32),
 ("P_STATE_COMPACT","node_c","","disabled","",None),
 ("P_LATENCY_VERBOSE","Cluster 1","approximately ","250","ms",250),
 ("P_LATENCY_VERBOSE","Cluster 1","exactly ","250","ms",250),
 ("P_TEMP_VERBOSE","Sensor X1","about ","21.5","degrees Celsius",21.5),
 ("P_TEMP_VERBOSE","Sensor X1","about ","-","",None),   # placeholder removed below
 ("P_REGION_VERBOSE","Storage unit S1","","sa-north-1","",None),
 ("P_BANDWIDTH_VERBOSE","Link AB","approximately equal to ","1,000","Mbps",1000),
 ("P_CAL_COMPACT","sensor_x1","","18 April 2026","","2026-04-18"),
 ("P_CAL_VERBOSE","Sensor X1","","17 April 2026","","2026-04-17"),
 ("P_DEPTH_VERBOSE","Queue Q","exactly ","4096.0","entries",4096),
 ("P_CAP_VERBOSE","Storage unit S1","exactly ","2048","gibibytes",2048),
 ("P_CAP_VERBOSE","Storage unit S1","exactly ","2049","gibibytes",2049),
 ("P_RET_VERBOSE","The backup job","approximately ","thirty","days",30),
 ("P_FW_VERBOSE","Node C","","4.2.1","",None),
 ("P_FW_VERBOSE","Node C","","4.2.1.0","",None),
 ("P_MODE_VERBOSE","The system","","production","",None),
 ("P_SCHED_VERBOSE","The backup job","","every day","",None)]
C4=[s for s in C4 if s[3]!="-"]
def build(spec, style):
    cl=[fill(*s[:5]) for s in spec]; V=[vrow(*s) for s in spec]
    if style=="lines": text="\n".join(c+"." for c in cl)+"\n"
    elif style=="oneline": text=" ".join(c+"." for c in cl)
    elif style=="semi": text="; ".join(cl)+"\n"
    else: text="\n".join(c+("." if i%2 else ";") for i,c in enumerate(cl))+"\n"
    return text,V,";".join(witness_clause(r) for r in V)
def L(t): return len(t[:-1] if t.endswith("\n") else t)
def verdict(t,V):
    r=C.compare(G.extract(t),V); return r.get("trial_verdict") or r.get("status")
M0=open(R/"NOVA_Q_FIXTURE_01_M0_SOURCE.txt",encoding="utf-8").read()
ctl=[]
for i,(spec,style) in enumerate([(C1,"lines"),(C2,"semi"),(C3,"oneline"),(C4,"mixed")],start=2):
    text,V,W=build(spec,style)
    chk={"input_parsed":G.extract(text)["status"],"input_vs_Vi":verdict(text,V),"input_vs_V0":verdict(text,V0),
         "witness_vs_Vi":verdict(W,V),"witness_ratio":round(L(W)/L(text),4),"facts":len(V),"input_len":L(text),"witness_len":L(W)}
    print("L1_R%02d"%i,chk)
    assert chk["input_parsed"]=="PARSED" and chk["input_vs_Vi"]=="TWIN_VALID" and chk["input_vs_V0"]!="TWIN_VALID"
    assert chk["witness_vs_Vi"]=="TWIN_VALID" and L(W)/L(text)<0.70 and text!=M0
    ctl.append({"run_id":"L1_R%02d"%i,"role":"HELD_OUT_CONTROL_%d"%(i-1),"input_text":text,"V":V,"witness_text":W})
assert len({c["input_text"] for c in ctl})==4
lines=[l for l in M0.split("\n") if l]
invalid="\n".join(lines[:9]+["Node B is currently inactive."]+lines[9:14])+"\n"
print("invalid extractor status:",G.extract(invalid)["status"])
assert G.extract(invalid)["status"]=="UNRESOLVED"
nonce=sys.argv[1]
pkg={"artifact":"LEVEL1_CONTROL_PACKAGE_V0.1","protocol":"LEVEL1_PROTOCOL_V0.4",
 "protocol_commit":"6ce264c71c3e8facf6b77de277fb520497f06d7c","compressor_freeze_commit":"2516d18f2213891ac056108f8a65f9dd4566a098",
 "compressor_sha256":"0ed99cb21048e8e1f8c9e526469c23697d5b6b414401e85120f5c26e360dba81",
 "control_author":"Claude","authored_after_compressor_freeze":True,"compressor_run_on_controls_before_commitment":False,
 "commitment_nonce":nonce,"controls":ctl,"invalid_input":{"role":"INVALID_INPUT_CONTROL","input_text":invalid,
 "reason_outside_REV3":"clause 'Node B is currently inactive' matches no production"}}
b=(json.dumps(pkg,indent=1,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8")
open(R/"LEVEL1_CONTROL_PACKAGE_V0_1.json","wb").write(b)
print("PACKAGE_SHA256",hashlib.sha256(b).hexdigest(),len(b))
