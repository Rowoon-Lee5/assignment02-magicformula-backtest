r"""B2 뒤 한 번(지시 04:58·05:26): 저장소 결과 폴더 3개를 _보관_20261106\ 에 통째로 복사(이미 있으면 멈춤)한 뒤,
제출_원문대로\결과 의 파일을 저장소 같은 이름 자리로 복사(합치기의 경로 규칙 거꾸로: 결과/결과_월수익률 → 결과_월수익률, 결과/결과_전략수익률 → 결과_전략수익률, 결과/ 바로 아래 → 연구/결과).
새 결과에 없는 옛 파일은 지우지 않고 그대로 둔다. 복사한 파일 목록과 SHA-256 = _검증/1106/결과_저장소로_목록.csv."""
import csv, hashlib, shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
S = REPO.parent / "제출_원문대로" / "결과"
보관 = REPO / "_보관_20261106"
짝 = [(S / "결과_월수익률", REPO / "결과_월수익률"), (S / "결과_전략수익률", REPO / "결과_전략수익률")]
assert S.is_dir() and not 보관.exists(), "제출 결과가 없거나 _보관_20261106 이 이미 있음(덮어쓰지 않음)"
for d in ["결과_월수익률", "결과_전략수익률", "연구/결과"]:
    shutil.copytree(REPO / d, 보관 / d)
목록 = REPO / "_검증" / "1106" / "결과_저장소로_목록.csv"
assert not 목록.exists()
rows = []
for f in sorted(p for p in S.rglob("*") if p.is_file()):
    r = f.relative_to(S)
    if r.parts[0] == "시험결과":
        continue
    a, b = next(((a, b) for a, b in 짝 if r.parts[0] == a.name), (S, REPO / "연구" / "결과"))
    q = b / f.relative_to(a)
    q.parent.mkdir(parents=True, exist_ok=True)
    있었음 = q.exists()
    shutil.copy2(f, q)
    rows.append([str(r), str(q.relative_to(REPO)), 있었음, hashlib.sha256(q.read_bytes()).hexdigest()])
with 목록.open("w", encoding="utf-8-sig", newline="") as o:
    csv.writer(o).writerows([["제출 결과", "저장소 자리", "옛 파일 있었음", "SHA-256"]] + rows)
print(len(rows), "개 복사, 옛 파일 바꿈", sum(r[2] for r in rows), "→", 목록)
