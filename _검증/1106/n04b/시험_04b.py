"""N04b 짧은 시험: 04 노트북 불러오기·기간·3절 실행·4절 대조(Panel A·B·C)·문장·판정·저장 칸만 FOLLOW_TEST=1로 exec(노트북 전체 실행 아님). 결과는 _검증/1106/시험결과/."""
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
for i in ["ef7481c1", "72e15d0a", "1162853b", "4b7c0e21", "4b7c0e22", "4b7c0e23", "4b7c0e24"]:
    print(f"===== {i}  {time.time() - T:.0f}초", flush=True)
    exec(칸[i], g)
    if i in ("4b7c0e21", "4b7c0e22", "4b7c0e23", "4b7c0e24"):
        import pandas as pd
        with pd.option_context("display.width", 400, "display.max_columns", 40):
            print({"4b7c0e21": lambda: g["NM대조"].round(3).to_string(), "4b7c0e22": lambda: g["NM문장"].to_string(),
                   "4b7c0e23": lambda: g["판정"].to_string(), "4b7c0e24": lambda: str(list(g["R"]))}[i]())
o = g["o"]
print("C 편입 열:", [c for c in o["기록"] if c.startswith("편입:")][:6])
print(o["기록"][["편입:Q1", "편입:Q2", "편입:Q3"]].to_string())
print(f"끝 {time.time() - T:.0f}초")
