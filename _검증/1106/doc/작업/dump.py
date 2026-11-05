import json,sys
nb=json.load(open(sys.argv[1],encoding="utf-8"))
sel=[int(x) for x in sys.argv[2].split(",")] if len(sys.argv)>2 and sys.argv[2] else None
for i,c in enumerate(nb["cells"]):
    s=c["source"]; s="".join(s) if isinstance(s,list) else s
    if sel is None:
        print(f"--- [{i}] {c['cell_type']} {type(c['source']).__name__} len={len(s)} :: {s[:100]!r}")
    elif i in sel:
        print(f"===== [{i}] {c['cell_type']} {type(c['source']).__name__}\n{s}")
