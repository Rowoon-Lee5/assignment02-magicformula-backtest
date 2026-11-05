import json,sys,io
for f in sys.argv[1:]:
    raw=open(f,"rb").read()
    nb=json.loads(raw.decode("utf-8"))
    for nl in ("\r\n","\n"):
        out=(json.dumps(nb,ensure_ascii=False,indent=1)+"\n").replace("\n",nl).encode("utf-8")
        print(f, repr(nl), out==raw, raw.count(b"\r\n"))
