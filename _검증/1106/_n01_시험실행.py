"""N01 짧은 시험: 노트북 코드 칸을 차례로 exec(FOLLOW_TEST=1, 작업 폴더 = 노트북 폴더). nbconvert 안 씀.
python _n01_시험실행.py [노트북 경로(기본 = 시안 _n01_시안.ipynb)] [작업 폴더(기본 = 따라하기)]"""
import json
import os
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

os.environ["FOLLOW_TEST"] = "1"
here = Path(__file__).resolve().parent
nbp = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "_n01_시안.ipynb"
wd = Path(sys.argv[2]) if len(sys.argv) > 2 else here.parents[1] / "따라하기"
os.chdir(wd)
cells = [c for c in json.loads(nbp.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code"]
g = {"display": lambda *a: [print(x) for x in a], "__name__": "__main__"}
T = time.time()
for i, c in enumerate(cells):
    src = "".join(c["source"])
    t = time.time()
    lines = src.rstrip().split("\n")
    last = lines[-1].rstrip(";")
    body, tail = ("\n".join(lines[:-1]), last) if not lines[-1].startswith((" ", "\t", "#")) and not lines[-1].endswith(";") else (src, None)
    exec(compile(body, f"<칸{i}>", "exec"), g)
    if tail:
        try:
            v = eval(compile(tail, f"<칸{i} 끝>", "eval"), g)
            if v is not None:
                print(v if not hasattr(v, "to_string") else v.to_string()[:4000])
        except SyntaxError:
            exec(compile(tail, f"<칸{i} 끝>", "exec"), g)
    print(f"--- 코드 칸 {i} 끝 {time.time() - t:.0f}초", flush=True)
print(f"전체 끝 {time.time() - T:.0f}초")
