"""회원이 따로 받은 자본총계(지배)·당기순이익(지배) xlsx(data\\DataGuide_추가_202611, 대조용으로만 읽음) vs 새로 받은 R30·R31 parquet.
xlsx를 한 줄씩 읽어(360MB라 통째로 안 읽음) 같은 날짜·종목 칸을 비교한다. 어느 쪽도 고치지 않는다.
사용: python _검증/지배_xlsx대조.py M000903003 "자본총계(지배)_9001_2609.xlsx" """
import sys
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

item, xl = sys.argv[1], Path(r"D:\26-2_데이터기반투자전략\과제02\data\DataGuide_추가_202611") / sys.argv[2]
(fn,) = Path(r"D:\26-2_데이터기반투자전략\과제02\data\통합_전체_202611").glob(f"통합_일간_{item}_*.parquet")
p = pd.read_parquet(fn)
rows = openpyxl.load_workbook(xl, read_only=True).worksheets[0].iter_rows(values_only=True)
head = [next(rows) for _ in range(14)]
assert head[11][1] == item, head[11][:3]
codes = pd.Index(head[8][1:])
j = p.columns.get_indexer(codes)  # xlsx 종목 → parquet 열(없으면 -1)
n = dict(날짜=0, 날짜없음=0, 둘다=0, 같음=0, 다름=0, xlsx만=0, parquet만=0)
예 = []
for r in rows:
    if r[0] is None:
        n["날짜없음"] += 1
        continue
    t = pd.Timestamp(r[0])
    if t not in p.index:
        continue
    n["날짜"] += 1
    a = np.array([np.nan if v is None else float(v) for v in r[1:]])
    b = np.full(len(a), np.nan)
    b[j >= 0] = p.loc[t].to_numpy(float)[j[j >= 0]]
    both = ~np.isnan(a) & ~np.isnan(b)
    eq = both & (np.abs(a - b) <= 1e-6 * np.maximum(np.abs(b), 1))
    n["둘다"] += both.sum(); n["같음"] += eq.sum(); n["다름"] += (both & ~eq).sum()
    n["xlsx만"] += (~np.isnan(a) & np.isnan(b)).sum(); n["parquet만"] += (np.isnan(a) & ~np.isnan(b)).sum()
    for k in np.nonzero(both & ~eq)[0][: max(0, 5 - len(예))]:
        예.append((str(t.date()), codes[k], a[k], b[k]))
print(f"{item} {xl.name}: xlsx 종목 {len(codes)}, parquet {p.shape}, parquet에 없는 xlsx 종목 {(j < 0).sum()}, xlsx에 없는 parquet 종목 {len(p.columns.difference(codes))}")
print({k: int(v) for k, v in n.items()}, "다른 칸 예(날짜, 코드, xlsx, parquet):", 예)
