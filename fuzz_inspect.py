import re,runpy,sys,io,contextlib
# re-run fuzz part with the same seed, resolving 'to_inspect' by also splitting on sentence dots
src=open("heldout_level0_round3.py",encoding="utf-8").read()
src=src.split("# ---- Part C")[0]
buf=io.StringIO()
with contextlib.redirect_stdout(buf): exec(compile(src,"r3","exec"),globals())
okall=set(base_clauses(M0))|set(base_clauses(MIN))
left={}
for b,d in fz_susp:
    for c in d:
        for piece in re.split(r"\.(?![0-9])",c):
            piece=piece.strip(" ")
            if piece and piece not in okall: left[piece]=left.get(piece,0)+1
for k,v in sorted(left.items(),key=lambda x:-x[1]): print(v,repr(k))
