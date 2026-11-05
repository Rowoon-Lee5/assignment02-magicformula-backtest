# 06:12 지시 (1): ECOS 원자료 2개를 제출_원문대로\data\ECOS_202611\ 에 복사(있으면 안 덮음)하고 SHA-256 대조, data_파일목록.csv에 줄 추가
import csv, hashlib, shutil
from pathlib import Path
R = Path(r"D:\26-2_데이터기반투자전략\과제02")
src, dst = R / "data" / "ECOS_202611", R / "제출_원문대로" / "data" / "ECOS_202611"
dst.mkdir(exist_ok=True)
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
목록 = R / "제출_원문대로" / "data_파일목록.csv"
있음 = {r[0] for r in csv.reader(목록.open(encoding="utf-8-sig"))}
rows = []
for f in sorted(src.glob("*.csv")):
    g = dst / f.name
    if not g.exists():
        shutil.copy2(f, g)
    a, b = h(f), h(g)
    assert a == b, f.name
    k = f"data/ECOS_202611/{f.name}"
    if k not in 있음:
        rows.append([k, g.stat().st_size, b, True, str(f), "읽지 않음(무위험 CD1m 출처 대조용 원자료, 노트북은 강의 엑셀 CD1m을 씀; _검증/1106/무위험_CD1m_출처.md)"])
    print(f.name, a == b)
with 목록.open("a", encoding="utf-8", newline="") as o:
    csv.writer(o).writerows(rows)
print("추가", len(rows))
