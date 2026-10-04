#!/usr/bin/env python3
"""LEVEL1_PROTOCOL_V0.4 — execution and scoring (operator/scorer: Claude).
Usage: level1_run_and_score.py <repo_clone_dir> <control_package.json> <out_dir> <committed_hash>
Every compressor execution is a fresh process. Scoring uses the frozen V0.4 CLI tools from the clone."""
import json, sys, os, subprocess, hashlib, datetime, platform, unicodedata, shutil
from pathlib import Path
REPO=Path(sys.argv[1]).resolve(); PKG=Path(sys.argv[2]).resolve(); OUT=Path(sys.argv[3]).resolve(); COMMITTED=sys.argv[4]
OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")
EXPECT={"level1_compressor_v0_1.py":"0ed99cb21048e8e1f8c9e526469c23697d5b6b414401e85120f5c26e360dba81",
 "level0_extract_v0_4.py":"17605981e658565fb5bb0d00798dfad1979436e311d3d117a540e223fe397ff0",
 "level0_compare_v0_4.py":"72788e986723fd8ab2f649809eae6c6d256d7da7f52f81c5f6ad6e3c6b157f61",
 "LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json":"d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852",
 "NOVA_Q_FIXTURE_01_M0_SOURCE.txt":"c0f1ffc9bc2679380ee8da77a8e98a0fb2987b606f8b0aaa69a40d4be758d439",
 "LEVEL1_PROTOCOL_V0.4.txt":"627388d26e451dc8d0410ca16b6d2c3fcd5389813c75f86cdeef28685b58bce1"}
for n,h in EXPECT.items():
    assert sha((REPO/n).read_bytes())==h, "FROZEN_FILE_HASH_MISMATCH "+n
pkg_bytes=PKG.read_bytes(); pkg_sha=sha(pkg_bytes)
commit_text=(REPO/"LEVEL1_CONTROL_COMMITMENT_V0_1.txt").read_text(encoding="utf-8")
commitment_ok=(pkg_sha==COMMITTED and COMMITTED in commit_text)
pkg=json.loads(pkg_bytes.decode("utf-8"))
head=subprocess.run(["git","-C",str(REPO),"rev-parse","HEAD"],capture_output=True,text=True).stdout.strip()
G=REPO/"LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json"
V0_rows=json.loads((REPO/"FROZEN_VQ_REFERENCE.json").read_text(encoding="utf-8"))["V"]
netns=subprocess.run(["unshare","-n","true"],capture_output=True).returncode==0
PRE=["unshare","-n"] if netns else []
def sem_len(b):
    if b.startswith(b"\xef\xbb\xbf") or b"\x00" in b: return None
    t=unicodedata.normalize("NFC",b.decode("utf-8"))
    return len(t[:-1] if t.endswith("\n") else t)
def compress(inp:Path, outp:Path):
    if outp.exists(): outp.unlink()
    a=now(); p=subprocess.run(PRE+[sys.executable,str(REPO/"level1_compressor_v0_1.py"),"--grammar",str(G),"--input",str(inp),"--out",str(outp)],capture_output=True); b=now()
    return {"start":a,"end":b,"exit_code":p.returncode,"stdout_bytes":len(p.stdout),"stderr":p.stderr.decode("utf-8","replace").strip(),
            "out":outp.read_bytes() if outp.exists() else None}
def score(cand:Path, vfile:Path, tag:str):
    ej=OUT/f"{tag}.extract.json"; cj=OUT/f"{tag}.compare.json"
    subprocess.run([sys.executable,str(REPO/"level0_extract_v0_4.py"),"--grammar",str(G),"--text-file",str(cand),"--out",str(ej)],capture_output=True)
    subprocess.run([sys.executable,str(REPO/"level0_compare_v0_4.py"),"--extraction",str(ej),"--v",str(vfile),"--out",str(cj)],capture_output=True)
    r=json.loads(cj.read_text(encoding="utf-8")); return r.get("trial_verdict") or r.get("status")
v0f=OUT/"V_L1_R01.json"; v0f.write_text(json.dumps({"V":V0_rows},indent=1,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
inputs=[("L1_R01","ORIGINAL_M0",(REPO/"NOVA_Q_FIXTURE_01_M0_SOURCE.txt").read_bytes(),V0_rows)]
for c in pkg["controls"]: inputs.append((c["run_id"],c["role"],c["input_text"].encode("utf-8"),c["V"]))
assert len({i[2] for i in inputs})==5
records=[]
for rid,role,ib,V in inputs:
    inp=OUT/f"INPUT_{rid}.txt"; inp.write_bytes(ib)
    vf=OUT/f"V_{rid}.json"; vf.write_text(json.dumps({"V":V},indent=1,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    A=compress(inp,OUT/f"OUTPUT_{rid}_A.txt"); B=compress(inp,OUT/f"OUTPUT_{rid}_B.txt")
    rec={"RUN_ID":rid,"INPUT_ROLE":role,"INPUT_SHA256":sha(ib),"INPUT_BYTE_LENGTH":len(ib),"INPUT_SEMANTIC_CHARACTER_LENGTH":sem_len(ib),
         "REFERENCE_V_SHA256":sha(vf.read_bytes()),"COMPRESSOR_SHA256":EXPECT["level1_compressor_v0_1.py"],"COMPRESSOR_VERSION":"LEVEL1_COMPRESSOR_V0.1",
         "GRAMMAR_SHA256":EXPECT["LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json"]}
    for k,X in (("A",A),("B",B)):
        o=X["out"]
        rec.update({f"EXECUTION_{k}_START":X["start"],f"EXECUTION_{k}_END":X["end"],f"EXECUTION_{k}_EXIT_CODE":X["exit_code"],
          f"EXECUTION_{k}_STDOUT_BYTES":X["stdout_bytes"],f"OUTPUT_{k}_SHA256":sha(o) if o is not None else None,
          f"OUTPUT_{k}_BYTE_LENGTH":len(o) if o is not None else None,f"OUTPUT_{k}_SEMANTIC_CHARACTER_LENGTH":sem_len(o) if o is not None else None})
    ok_exec=A["exit_code"]==0 and B["exit_code"]==0 and A["out"] is not None and B["out"] is not None
    det=ok_exec and A["out"]==B["out"]
    rec["DETERMINISM_PASS"]=bool(det)
    err=None
    if ok_exec:
        pos=score(OUT/f"OUTPUT_{rid}_A.txt",vf,f"{rid}.positive")
        anti=score(OUT/f"OUTPUT_{rid}_A.txt",v0f,f"{rid}.anti_constant") if rid!="L1_R01" else "NOT_APPLICABLE"
        ol=rec["OUTPUT_A_SEMANTIC_CHARACTER_LENGTH"]; ratio=(ol/rec["INPUT_SEMANTIC_CHARACTER_LENGTH"]) if ol is not None else None
    else:
        pos=anti=None; ratio=None; err=(A["stderr"] or B["stderr"] or "EXECUTION_FAILURE")
    rec.update({"POSITIVE_COMPARATOR_VERDICT":pos,"ANTI_CONSTANT_COMPARATOR_VERDICT":anti,"LENGTH_RATIO":round(ratio,6) if ratio is not None else None,
        "LENGTH_PASS":bool(ratio is not None and ratio<0.70)})
    passed=bool(ok_exec and det and pos=="TWIN_VALID" and rec["LENGTH_PASS"] and (rid=="L1_R01" or anti!="TWIN_VALID")
                and A["stdout_bytes"]==0 and B["stdout_bytes"]==0)
    rec.update({"RUN_STATUS":"PASS" if passed else "FAIL","ERROR_OR_BLOCKER":err})
    records.append(rec)
# invalid-input control
ib=pkg["invalid_input"]["input_text"].encode("utf-8"); inp=OUT/"INPUT_INVALID.txt"; inp.write_bytes(ib)
X=compress(inp,OUT/"OUTPUT_INVALID.txt")
inv={"INVALID_INPUT_SHA256":sha(ib),"INVALID_INPUT_BYTE_LENGTH":len(ib),"COMPRESSOR_SHA256":EXPECT["level1_compressor_v0_1.py"],
 "GRAMMAR_SHA256":EXPECT["LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json"],"START_TIMESTAMP":X["start"],"END_TIMESTAMP":X["end"],
 "EXIT_CODE":X["exit_code"],"STDOUT_BYTE_LENGTH":X["stdout_bytes"],"STDERR_SHA256":sha(X["stderr"].encode()) if X["stderr"] else None,
 "STDERR_TEXT":X["stderr"],"CANDIDATE_CREATED":X["out"] is not None}
inv["INVALID_INPUT_CONTROL_STATUS"]="PASS" if (X["exit_code"]!=0 and X["stdout_bytes"]==0 and X["out"] is None) else "FAIL"
# witnesses (section 11) and V_i != V (section 12/14)
wit=[]
for c in pkg["controls"]:
    w=OUT/f"WITNESS_{c['run_id']}.txt"; w.write_bytes(c["witness_text"].encode("utf-8"))
    wv=score(w,OUT/f"V_{c['run_id']}.json",f"{c['run_id']}.witness")
    iv=score(OUT/f"INPUT_{c['run_id']}.txt",v0f,f"{c['run_id']}.input_vs_original_V")
    r=sem_len(w.read_bytes())/sem_len(c["input_text"].encode("utf-8"))
    wit.append({"RUN_ID":c["run_id"],"WITNESS_VERDICT":wv,"WITNESS_RATIO":round(r,6),"WITNESS_VALID":wv=="TWIN_VALID" and r<0.70,
                "V_i_DIFFERS_FROM_ORIGINAL_V":iv!="TWIN_VALID"})
protocol_error=not all(w["WITNESS_VALID"] and w["V_i_DIFFERS_FROM_ORIGINAL_V"] for w in wit)
primary=all(r["RUN_STATUS"]=="PASS" for r in records) and inv["INVALID_INPUT_CONTROL_STATUS"]=="PASS" and commitment_ok and not protocol_error
agg={"protocol":"LEVEL1_PROTOCOL_V0.4","repo_head_at_run":head,"control_package_sha256":pkg_sha,"committed_sha256":COMMITTED,
 "CONTROL_COMMITMENT_VALID":commitment_ok,"PROTOCOL_ERROR":protocol_error,
 "environment":{"PYTHON_VERSION":platform.python_version(),"OPERATING_ENVIRONMENT":platform.platform(),
   "NETWORK_ISOLATION":"ENFORCED_AT_OS_LEVEL (unshare -n)" if netns else "NOT_ENFORCED_AT_OS_LEVEL"},
 "roles":{"control_author":"Claude","operator":"Claude","scorer":"Claude","ROLE_CONCENTRATION_LIMITATION":True},
 "SHARED_PARSER_LIMITATION":False,"valid_input_records":records,"invalid_input_record":inv,"witness_checks":wit,
 "passes":sum(r["RUN_STATUS"]=="PASS" for r in records),"LEVEL1_PRIMARY_RESULT":"LEVEL1_PRIMARY_PASS" if primary else "LEVEL1_PRIMARY_FAIL"}
(OUT/"LEVEL1_RESULT_RECORD.json").write_text(json.dumps(agg,indent=1,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
for r in records: print(r["RUN_ID"],r["INPUT_ROLE"],"in",r["INPUT_SEMANTIC_CHARACTER_LENGTH"],"out",r["OUTPUT_A_SEMANTIC_CHARACTER_LENGTH"],"ratio",r["LENGTH_RATIO"],
   "pos",r["POSITIVE_COMPARATOR_VERDICT"],"anti",r["ANTI_CONSTANT_COMPARATOR_VERDICT"],"det",r["DETERMINISM_PASS"],r["RUN_STATUS"],r["ERROR_OR_BLOCKER"] or "")
print("INVALID",inv["EXIT_CODE"],inv["STDOUT_BYTE_LENGTH"],inv["CANDIDATE_CREATED"],inv["INVALID_INPUT_CONTROL_STATUS"],"|",inv["STDERR_TEXT"][:90])
print("WITNESS",[(w["RUN_ID"],w["WITNESS_VALID"],w["V_i_DIFFERS_FROM_ORIGINAL_V"]) for w in wit])
print("COMMITMENT_VALID",commitment_ok,"NETNS",netns,"HEAD",head); print(agg["LEVEL1_PRIMARY_RESULT"])
