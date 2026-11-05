"""N03 짧은 시험: 따라하기 03 노트북 코드 칸을 FOLLOW_TEST=1로 차례로 실행(nbconvert 아님, 한 프로세스). 사용: python n03_test.py [--compile]"""
import json, os, sys, time, traceback
from pathlib import Path

NB = Path(r"D:\26-2_데이터기반투자전략\과제02\과제02_백테스트\따라하기\03_NH_퀄리티로우볼.ipynb")
cells = [c for c in json.loads(NB.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code"]
if "--compile" in sys.argv:
    for i, c in enumerate(cells):
        compile("".join(c["source"]), f"cell{i}", "exec")
    print("compile ok", len(cells)); sys.exit()
os.environ["FOLLOW_TEST"] = "1"
os.chdir(NB.parent)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
g = {"display": lambda *a, **k: [print(x) for x in a]}
T0 = time.time()
for i, c in enumerate(cells):
    t = time.time()
    src = "".join(c["source"])
    lines = src.rstrip().splitlines()
    try:
        exec(compile("\n".join(lines[:-1]), f"cell{i}", "exec"), g)
        last = lines[-1]
        try:
            v = eval(compile(last, f"cell{i}", "eval"), g)
            if v is not None: print(v)
        except SyntaxError:
            exec(compile(last, f"cell{i}", "exec"), g)
    except Exception:
        print(f"!!! 칸 {i} ({c['id']}) 오류"); traceback.print_exc(); sys.exit(1)
    n = len(plt.get_fignums()); plt.close("all")
    print(f"--- 칸 {i} ({c['id']}) 끝 {time.time() - t:.0f}초, 그림 {n}", flush=True)
print(f"전체 {time.time() - T0:.0f}초")
