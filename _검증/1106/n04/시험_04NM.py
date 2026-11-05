"""N04 작은 시험: 04 노트북의 불러오기·기간·7절(Novy-Marx)·대조 칸만 FOLLOW_TEST=1로 실행(노트북 전체 실행 아님). 결과는 _검증/1106/시험결과/."""
import json, os, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
os.environ["FOLLOW_TEST"] = "1"
root = Path(__file__).resolve().parents[3]
os.chdir(root / "따라하기")
nb = json.loads((root / "따라하기" / "04_신마법공식.ipynb").read_text(encoding="utf-8"))
칸 = {c["id"]: "".join(c["source"]) for c in nb["cells"]}
g = {"display": print}
T = time.time()
for i in sys.argv[1:] or ["ef7481c1", "72e15d0a", "1162853b", "4b7c0e21", "4b7c0e22", "4b7c0e23", "4b7c0e24"]:
    print(f"===== {i}  {time.time() - T:.0f}초")
    exec(칸[i], g)
    if i in ("4b7c0e21", "4b7c0e22", "4b7c0e23"):
        print(g[{"4b7c0e21": "NM대조", "4b7c0e22": "NM문장", "4b7c0e23": "판정"}[i]].to_string())
print(f"끝 {time.time() - T:.0f}초")
