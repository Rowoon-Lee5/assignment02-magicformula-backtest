import json, difflib
from pathlib import Path
R=Path(r"D:\26-2_데이터기반투자전략\과제02\과제02_백테스트"); B=R/"_검증/1106/doc"
nbs={"따라하기/01_우동호2023.ipynb":{20},"따라하기/02_NH_밸류.ipynb":{0,29},"따라하기/03_NH_퀄리티로우볼.ipynb":{0},"따라하기/04_신마법공식.ipynb":{0,7,12,13},
     "연구/따라하기에서_옮김_04.ipynb":{1,17,19},"연구/요약표.ipynb":{0},"연구/확장연구_20261103.ipynb":{0},"연구/결과요약_20261103.ipynb":{14}}
for f,exp in nbs.items():
    a=json.load(open(B/Path(f).name,encoding="utf-8")); b=json.load(open(R/f,encoding="utf-8"))
    assert len(a["cells"])==len(b["cells"]) and a.get("metadata")==b.get("metadata")
    code_same=True; changed=set()
    for i,(x,y) in enumerate(zip(a["cells"],b["cells"])):
        if x["cell_type"]=="code" and x!=y: code_same=False
        if x!=y:
            changed.add(i)
            assert x["cell_type"]=="markdown" and type(x["source"])==type(y["source"]) and {k:v for k,v in x.items() if k!="source"}=={k:v for k,v in y.items() if k!="source"}
    # 고친 칸: 지운 글자 없이 더하거나 바꾼 줄만인지 보이기
    print(f, "코드칸같음", code_same, "바뀐칸", sorted(changed), "예상과같음", changed==exp)
for f in ["_검증/기본값_목록_20261106.md","_검증/1106/문서단계_목록.md"]:
    a=open(B/Path(f).name,encoding="utf-8").read().splitlines(); b=open(R/f,encoding="utf-8").read().splitlines()
    d=[l for l in difflib.unified_diff(a,b,lineterm="",n=0) if l[:1] in "+-" and l[:3] not in("+++","---")]
    print(f, "지운줄", sum(l[0]=="-" for l in d), "더한줄", sum(l[0]=="+" for l in d))
    for l in d: print("   ", l[:110])
