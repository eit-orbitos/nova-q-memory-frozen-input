#!/usr/bin/env python3
import json,re,sys,hashlib,unicodedata,datetime,itertools
from pathlib import Path
R=Path(__file__).resolve().parent
G=json.load(open(R/"LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json",encoding="utf-8"))
REF=json.load(open(R/"FROZEN_VQ_REFERENCE.json",encoding="utf-8"))
V=REF["V"]; M0=open(R/"NOVA_Q_FIXTURE_01_M0_SOURCE.txt",encoding="utf-8").read()
FLAGS=re.ASCII

def sha(b):return hashlib.sha256(b).hexdigest()
def spans(text):
 out=[]
 for n in G["clause_boundary_spec"]["dot_protecting_token_classes"]:
  rx=re.compile(G["token_classes"][n]["regex"],FLAGS)
  out += [(m.start(),m.end()) for m in rx.finditer(text)]
 return out
def split(text):
 text=unicodedata.normalize("NFC",text);sp=spans(text);res=[];st=0
 for i,ch in enumerate(text):
  b=ch in ";\n" or (ch=="." and not any(a<=i<b for a,b in sp))
  if b:
   c=text[st:i].strip(" ")
   if c:res.append(c)
   st=i+1
 c=text[st:].strip(" ")
 if c:res.append(c)
 return res
def expand(t):
 return re.sub(r"\{\{([A-Z_]+)\}\}",lambda m:"(?:"+G["placeholder_regexes"][m.group(1)]+")",t,flags=FLAGS)
PRODS=[(p,re.compile(expand(p["regex_template"]),FLAGS)) for p in G["productions"]]
def smap(cls,raw):
 return G["token_classes"][cls].get("semantic_map",{}).get(raw,raw)
def num(raw):
 if raw in G["number_words"]:return G["number_words"][raw]
 if not re.fullmatch(G["token_classes"]["NUMBER"]["regex"],raw,FLAGS):raise ValueError
 c=raw.replace(",","");v=float(c) if "." in c else int(c);return int(v) if isinstance(v,float) and v.is_integer() else v
def date(raw):
 try:
  d=datetime.date.fromisoformat(raw) if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}",raw,FLAGS) else datetime.datetime.strptime(raw,"%d %B %Y").date()
  return d.isoformat()
 except:raise ValueError
def qual(gd):return "APPROX" if gd.get("qualifier_word") or gd.get("qualifier_tilde") else "EXACT"
def vcls(p):return p["value_class"]
def ucls(p):
 t=p["regex_template"]
 for n in ("DATA_UNIT","TIME_UNIT","RATE_UNIT","TEMP_UNIT","DAY_UNIT","ENTRY_UNIT"):
  if "{{"+n+"}}" in t:return n
def parse(c):
 ms=[(p,r.fullmatch(c)) for p,r in PRODS if r.fullmatch(c)]
 if len(ms)!=1:return {"status":"UNRESOLVED","clause":c,"matches":[p["id"] for p,_ in ms]}
 p,m=ms[0];gd=m.groupdict();vc=vcls(p);rv=gd["value"]
 try:
  val=num(rv) if vc=="NUMBER" else date(rv) if vc=="DATE" else smap(vc,rv) if vc in ("STATE","DUPLEX_STATE","POLICY","MODE","SCHEDULE") else rv
 except:return {"status":"UNRESOLVED","clause":c,"reason":"SEMANTIC_VALIDATOR_FAIL"}
 uc=ucls(p);unit=smap(uc,gd["unit"]) if uc else p["unit_default"]
 return {"status":"PARSED","production":p["id"],"fact":{"subject":smap("SUBJECT",gd["subject"]),"relation":p["relation"],"operator":p["operator"],"value":val,"unit":unit,"qualifier":qual(gd)}}
def ef(v):return {"subject":v["subject"],"relation":v["relation"],"operator":"EQUAL","value":v["value"],"unit":v["unit"],"qualifier":v["qualifier"]}
def key(f):return json.dumps(f,sort_keys=True,ensure_ascii=False,separators=(",",":"))
EXP=sorted(key(ef(x)) for x in V)
def prove(text,label):
 cs=split(text);rs=[parse(c) for c in cs];fs=[x["fact"] for x in rs if x["status"]=="PARSED"];A=sorted(key(x) for x in fs)
 return {"label":label,"clause_count":len(cs),"all_parsed":all(x["status"]=="PARSED" for x in rs),"fact_count":len(fs),"exact_fact_set":A==EXP,"missing":sorted(set(EXP)-set(A)),"extra":sorted(set(A)-set(EXP)),"results":rs}

# boundary tests
B=[{"id":t["id"],"expected":t["expected_clause_count"],"got":len(split(t["text"]))} for t in G["clause_boundary_spec"]["tests"]]
for x in B:x["pass"]=x["got"]==x["expected"]

# Generate possible concrete clauses from normative production templates.
cv=G["closed_vocabulary"]
def aliases_for_slot(slot,v):
 if slot=="SUBJECT": return cv["subjects"][v["subject"]]
 if slot=="NUMBER": return [str(v["value"])]
 if slot in ("DATE","REGION","VERSION"): return [str(v["value"])]
 if slot=="STATE": return [a for a,c in G["token_classes"]["STATE"]["semantic_map"].items() if c==v["value"]]
 if slot=="DUPLEX_STATE": return [a for a,c in G["token_classes"]["DUPLEX_STATE"]["semantic_map"].items() if c==v["value"]]
 if slot=="POLICY": return [a for a,c in G["token_classes"]["POLICY"]["semantic_map"].items() if c==v["value"]]
 if slot=="MODE": return [a for a,c in G["token_classes"]["MODE"]["semantic_map"].items() if c==v["value"]]
 if slot=="SCHEDULE": return [a for a,c in G["token_classes"]["SCHEDULE"]["semantic_map"].items() if c==v["value"]]
 if slot in ("DATA_UNIT","TIME_UNIT","RATE_UNIT","TEMP_UNIT","DAY_UNIT","ENTRY_UNIT"):
  return [a for a,c in G["token_classes"][slot]["semantic_map"].items() if c==v["unit"]]
 if slot=="NUM_MODIFIER":
  if v["qualifier"]=="APPROX": return ["~", "about ", "around ", "roughly ", "approximately ", "approx. ", "approximately equal to "]
  return ["", "exactly "]
 raise KeyError(slot)

NAMED_OR_PLACEHOLDER=re.compile(r"\(\?P<(?P<group>[A-Za-z_][A-Za-z0-9_]*)>\{\{(?P<named>[A-Z_]+)\}\}\)|\{\{(?P<plain>[A-Z_]+)\}\}",FLAGS)
def instantiate(template,combo):
 t=template
 vals=iter(combo)
 def repl(m): return next(vals)
 body=re.sub(r"^\^","",t);body=re.sub(r"\$$","",body)
 return NAMED_OR_PLACEHOLDER.sub(repl,body)

def candidate_clauses(v):
 out=[]
 for p in G["productions"]:
  if p["relation"]!=v["relation"]:continue
  slots=[]
  for m in NAMED_OR_PLACEHOLDER.finditer(p["regex_template"]):
   slots.append(m.group("named") or m.group("plain"))
  opts=[aliases_for_slot(s,v) for s in slots]
  for combo in itertools.product(*opts):
   s=instantiate(p["regex_template"],combo)
   r=parse(s)
   if r["status"]=="PARSED" and key(r["fact"])==key(ef(v)):
    out.append((s,p["id"]))
 return sorted(set(out),key=lambda x:(len(x[0]),x[0],x[1]))

mins=[]
for v in V:
 cs=candidate_clauses(v)
 if not cs:raise RuntimeError("No rendering for "+v["fact_id"])
 mins.append(cs[0])
MIN=G["minimum_rendering"]["separator"].join(s for s,_ in mins)+G["minimum_rendering"]["final_terminator"]
open(R/"MINIMUM_COMPACT_REV3.txt","w",encoding="utf-8",newline="\n").write(MIN)
open(R/"COMPACT_VALID_REV3.txt","w",encoding="utf-8",newline="\n").write(MIN)

M=prove(M0,"FROZEN_M0");C=prove(MIN,"COMPACT_VALID_REV3")
C["chars"]=len(MIN);C["under_552"]=len(MIN)<552
minimum_record={"chars":len(MIN),"ratio_to_789":len(MIN)/789,"clauses":[{"fact_id":v["fact_id"],"text":s,"production":pid,"chars":len(s)} for v,(s,pid) in zip(V,mins)]}

# extra probes required by review
probes=[
 ("unicode_fullwidth","Node A has exactly ６４ Mi of memory","UNRESOLVED"),
 ("unicode_arabic_indic","Node A has exactly ٦٤ Mi of memory","UNRESOLVED"),
 ("leading_zero","Node A has exactly 0064 Mi of memory","UNRESOLVED"),
 ("invalid_date","sensor_x1 calibration_date=2026-02-31","UNRESOLVED"),
 ("tilde_approx","The maximum latency of cluster 1 is ~250 ms","PARSED"),
 ("approx_dot","The maximum latency of cluster 1 is approx. 250 ms","PARSED"),
 ("double_space","Node A has exactly  64 Mi of memory","UNRESOLVED")
]
probe_results=[]
for name,text,expected in probes:
 rs=[parse(c) for c in split(text)]
 status=rs[0]["status"] if len(rs)==1 else "MULTI"
 probe_results.append({"id":name,"expected":expected,"got":status,"pass":status==expected})

O={"grammar_sha256":sha((R/"LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3.json").read_bytes()),"m0_sha256":sha((R/"NOVA_Q_FIXTURE_01_M0_SOURCE.txt").read_bytes()),
"boundary_tests":B,"m0":M,"compact":C,"minimum":minimum_record,"review_probes":probe_results}
O["all_required_checks_pass"]=all(x["pass"] for x in B) and all(x["pass"] for x in probe_results) and M["all_parsed"] and M["exact_fact_set"] and C["all_parsed"] and C["exact_fact_set"] and C["under_552"]
print(json.dumps(O,ensure_ascii=False,indent=2,sort_keys=True))
sys.exit(0 if O["all_required_checks_pass"] else 1)
