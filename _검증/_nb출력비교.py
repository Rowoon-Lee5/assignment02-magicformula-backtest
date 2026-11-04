"""노트북 실행 전(git 리비전)·후 칸별 출력 비교: 오류 칸 수, 출력이 바뀐 칸 번호. python _nb출력비교.py 노트북 리비전"""
import json, subprocess, sys
p, rev = sys.argv[1], sys.argv[2]
old = json.loads(subprocess.run(["git", "show", f"{rev}:{p}"], capture_output=True, encoding="utf-8").stdout)
new = json.load(open(p, encoding="utf-8"))
txt = lambda c: "".join("".join(o.get("text", "")) + "".join(o.get("data", {}).get("text/plain", "")) for o in c.get("outputs", []))
err = [i for i, c in enumerate(new["cells"]) if any(o.get("output_type") == "error" for o in c.get("outputs", []))]
print("오류 칸:", err, "/ 칸 수 전·후", len(old["cells"]), len(new["cells"]))
for i, (a, b) in enumerate(zip(old["cells"], new["cells"])):
    if a["cell_type"] == "code" and txt(a) != txt(b):
        print("바뀐 칸", i, "|", "".join(b["source"])[:70].replace("\n", " "))
