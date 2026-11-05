import json,sys,re
nb=json.load(open(sys.argv[1],encoding="utf-8"))
pat=re.compile(sys.argv[2])
for i,c in enumerate(nb["cells"]):
    s=c["source"]; s="".join(s) if isinstance(s,list) else s
    for j,l in enumerate(s.split("\n")):
        if pat.search(l): print(f"[{i}:{c['cell_type'][0]}:{j}] {l[:400]}")
