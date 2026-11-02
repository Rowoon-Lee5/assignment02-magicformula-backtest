"""새 일간 파일(통합_전체_202611) vs 예전 합친 파일(통합_202611) 값 대조(검증용으로만 읽음, 어느 쪽도 안 고침).
겹치는 날짜·종목에서 둘 다 값 있음/같음/한쪽만 값. 사용: python 일간_예전대조.py S410000700 ..."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

NEW = Path(r"D:\26-2_데이터기반투자전략\과제02\data\통합_전체_202611")
OLD = Path(r"D:\26-2_데이터기반투자전략\과제02\data\통합_202611")
for item in sys.argv[1:]:
    (fn,), (fo,) = NEW.glob(f"통합_일간_{item}_*.parquet"), OLD.glob(f"통합_일간_{item}_*.parquet")
    n, o = pd.read_parquet(fn), pd.read_parquet(fo)
    d, c = n.index.intersection(o.index), n.columns.intersection(o.columns)
    a, b = n.loc[d, c].to_numpy(float), o.loc[d, c].to_numpy(float)
    both = ~np.isnan(a) & ~np.isnan(b)
    eq = both & (np.abs(a - b) <= 1e-6 * np.maximum(np.abs(b), 1))
    print(f"{item}: 새 {n.shape} 예전 {o.shape}, 겹침 날짜 {len(d)} 종목 {len(c)} | 둘 다 값 {both.sum()}, 같음 {eq.sum()}, 다름 {(both & ~eq).sum()}, "
          f"새만 값 {(~np.isnan(a) & np.isnan(b)).sum()}, 예전만 값 {(np.isnan(a) & ~np.isnan(b)).sum()} | 새에만 있는 종목 {len(n.columns.difference(o.columns))}, 예전에만 {len(o.columns.difference(n.columns))}")
    i, j = np.nonzero(both & ~eq)
    if len(i):
        k = np.unique(j, return_counts=True)
        top = sorted(zip(k[1], c[k[0]]), reverse=True)[:5]
        print("  다른 칸이 많은 종목:", top, "| 예:", [(str(d[x].date()), c[y], a[x, y], b[x, y]) for x, y in list(zip(i, j))[:3]])
    del n, o, a, b
