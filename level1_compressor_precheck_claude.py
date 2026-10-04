#!/usr/bin/env python3
"""Claude pre-freeze check of LEVEL1_COMPRESSOR_V0.1. NOT the held-out controls.
Random valid REV3 inputs are generated from the grammar; the expected V' is built directly
from the generating facts (not by any parser). Checks: evaluator verdict vs V', anti-constant
vs original V, determinism under different hash seeds, fail-closed on invalid inputs."""
import json, random, subprocess, sys, os, tempfile, importlib.util, hashlib, re
from pathlib import Path
R=Path(__file__).resolve().parent
def load(n,f):
    s=importlib.util.spec_from_file_location(n,R/f); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
E=load("e","level0_extract_v0_4.py"); C=load("c","level0_compare_v0_4.py")
GP=R/"LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json"; G=E.FrozenGrammar(GP); g=G.g
V0=json.load(open(R/"FROZEN_VQ_REFERENCE.json",encoding="utf-8"))["V"]
rng=random.Random(4242)
subj=g["closed_vocabulary"]["subjects"]; tc=g["token_classes"]
SLOT=re.compile(r"\(\?P<(\w+)>\{\{([A-Z_]+)\}\}\)|\{\{([A-Z_]+)\}\}")
APPROX=["approximately equal to ","approximately ","approx. ","roughly ","around ","about ","~"]
MONTHS=["January","February","March","April","May","June","July","August","September","October","November","December"]
def rnd_number():
    k=rng.randrange(6)
    if k==0:
        n=rng.randrange(0,101); w=[a for a,b in g["number_words"].items() if b==n]
        return (rng.choice(w) if w and rng.random()<.6 else str(n)), n
    if k==1:
        n=rng.randrange(1000,999999); return f"{n:,}", n
    if k==2:
        a=rng.randrange(0,5000); d=rng.randrange(1,999); s=f"{a}.{d:03d}".rstrip("0")
        return s+("0"*rng.randrange(0,3)), float(s)
    if k==3:
        n=rng.randrange(0,10**6); return f"{n}.{'0'*rng.randrange(1,4)}", n
    n=rng.randrange(0,10**rng.randrange(1,9)); return str(n), n
def gen_fact(p, s_can):
    """returns (clause_text, V_row)"""
    vc=p["value_class"]; row={"subject":s_can,"relation":p["relation"],"qualifier":"EXACT","unit":p.get("unit_default","")}
    parts={}
    def fill(m):
        grp,named,plain=m.group(1),m.group(2),m.group(3); cls=named or plain
        if cls=="SUBJECT": return rng.choice(subj[s_can])
        if cls=="NUM_MODIFIER":
            r=rng.random()
            if r<.35: row["qualifier"]="APPROX"; return rng.choice(APPROX)
            return "exactly " if r<.65 else ""
        if cls=="NUMBER":
            t,v=rnd_number(); row["value"]=v; return t
        if cls=="DATE":
            y=rng.randrange(1990,2100); mo=rng.randrange(1,13); d=rng.randrange(1,29)
            row["value"]=f"{y:04d}-{mo:02d}-{d:02d}"
            return row["value"] if rng.random()<.5 else f"{d} {MONTHS[mo-1]} {y}"
        if cls=="REGION":
            v=rng.choice(["eu","us","ap","sa","af"])+"-"+rng.choice(["central","east","west","north","south1","x9"])+rng.choice(["","-1","-2b"])
            row["value"]=v; return v
        if cls=="VERSION":
            v=".".join(str(rng.randrange(0,40)) for _ in range(rng.choice([3,4]))); row["value"]=v; return v
        sm=tc[cls]["semantic_map"]; a=rng.choice(sorted(sm))
        if grp=="unit": row["unit"]=sm[a]
        else: row["value"]=sm[a]
        return a
    body=p["regex_template"].strip("^$")
    return SLOT.sub(fill,body), row
def gen_input():
    n=rng.randrange(1,31); seen=set(); clauses=[]; V=[]
    tries=0
    while len(clauses)<n and tries<500:
        tries+=1
        p=rng.choice([q for q in g["productions"] if rng.random()<.8 and q["id"].endswith("VERBOSE") or rng.random()<.2] or g["productions"])
        s=rng.choice(sorted(subj))
        c,row=gen_fact(p,s)
        key=(s,p["relation"])          # one value per subject/relation keeps V' unambiguous
        if key in seen: continue
        seen.add(key); clauses.append(c); V.append(row)
    style=rng.randrange(3)
    if style==0: text="\n".join(x+"." for x in clauses)+"\n"
    elif style==1: text="; ".join(clauses)
    else: text="\n".join(x+rng.choice([".",";",""]) for x in clauses)+"\n"
    return text,V
def L(t):
    t=t[:-1] if t.endswith("\n") else t
    return len(t)
def run(text, seed="0"):
    with tempfile.TemporaryDirectory() as td:
        i=os.path.join(td,"in.txt"); o=os.path.join(td,"out.txt"); open(i,"wb").write(text if isinstance(text,bytes) else text.encode("utf-8"))
        env=dict(os.environ,PYTHONHASHSEED=seed)
        p=subprocess.run([sys.executable,str(R/"level1_compressor_v0_1.py"),"--grammar",str(GP),"--input",i,"--out",o],capture_output=True,env=env)
        out=open(o,"rb").read() if os.path.exists(o) else None
        return p.returncode,p.stdout,out
def verdict(cand,V):
    r=C.compare(G.extract(cand),V); return r.get("trial_verdict") or r.get("status")
N=int(sys.argv[1]) if len(sys.argv)>1 else 400
stats=dict(n=0,gen_invalid=0,rc_fail=0,stdout=0,not_twin=0,anti_const_fail=0,nondet=0,ratio_ge_070=0,ratio_lt_070=0)
bad=[]
for k in range(N):
    text,V=gen_input()
    if G.extract(text)["status"]!="PARSED" or verdict(text,V)!="TWIN_VALID":
        stats["gen_invalid"]+=1; continue      # generator bug guard: input itself must match V'
    stats["n"]+=1
    rc,so,out=run(text,"0"); rc2,so2,out2=run(text,str(rng.randrange(1,10**6)))
    if rc!=0 or out is None: stats["rc_fail"]+=1; bad.append(("rc",text)); continue
    if so: stats["stdout"]+=1
    if out!=out2: stats["nondet"]+=1; bad.append(("nondet",text))
    cand=out.decode("utf-8")
    if verdict(cand,V)!="TWIN_VALID": stats["not_twin"]+=1; bad.append(("not_twin",text,cand))
    if verdict(cand,V0)=="TWIN_VALID": stats["anti_const_fail"]+=1
    stats["ratio_lt_070" if L(cand)/L(text)<0.70 else "ratio_ge_070"]+=1
print(stats)
for b in bad[:5]: print("BAD",b)
# fail-closed on invalid inputs
M0=open(R/"NOVA_Q_FIXTURE_01_M0_SOURCE.txt",encoding="utf-8").read()
inv={"comment":M0+"All of the above may be outdated.\n","negation":M0.replace("Node D is disabled","Node D is not disabled"),
 "empty":"", "crlf":M0.replace("\n","\r\n"), "bom":"﻿"+M0, "bad_utf8":b"\xff\xfe"+M0.encode(), "nul":M0+"\x00",
 "duplicate":M0+"Node A has exactly 64 Mi of memory.\n", "bad_date":M0.replace("18 April 2026","31 April 2026"),
 "unknown_unit":M0.replace("64 Mi","64 Ki"), "markdown":"```\n"+M0+"```\n", "huge_number":M0.replace("64 Mi","9"*6000+" Mi")}
for name,t in inv.items():
    rc,so,out=run(t)
    print("%-13s rc=%s stdout=%d out_file=%s"%(name,rc,len(so),"CREATED" if out is not None else "none"))
