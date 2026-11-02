"""읽기.연간재무()(새 일간 재무 → 회계연도 값, 감사 H1 확인 포함)의 출력을 예전 연간 원본(통합_연간재무.parquet)과 대조한다.
항목마다: 둘 다 있는 (코드, 회계연도) 행 수, 같은 값 비율, 예전에는 값이 있는데 새로 빈칸인 행 수, 확인(H1) 때문에 빈칸으로 둔 수(읽기.검사).
결과 보고용 아님(검증용). 사용: python _검증/연간재무_함수대조.py"""
import sys
from pathlib import Path

import pandas as pd

B = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(B / "공통"))
import 데이터읽기 as 읽기

OLD = Path(r"D:\26-2_데이터기반투자전략\과제02\data\통합_202611")
A = pd.read_parquet(OLD / "통합_연간재무.parquet").rename(columns=lambda c: c.rsplit("_", 1)[-1])
N = 읽기.연간재무()
키 = ["코드", "회계연도", "CP10002200"]  # 같은 회계연도에 결산월이 둘인 행(결산월 바꾼 해, F9)이 있어 결산월까지 맞춘다
print("새 행", len(N), "(코드, 회계연도) 중복", int(N.duplicated(키[:2]).sum()), "| 예전 행", len(A), "중복", int(A.duplicated(키[:2]).sum()))
print("결산월까지 맞춘 키 중복: 새", int(N.duplicated(키).sum()), "예전", int(A.dropna(subset=["CP10002200"]).duplicated(키).sum()))
A = A.dropna(subset=["CP10002200"]).set_index(키)
N = N.set_index(키)
print("예전 (코드, 회계연도, 결산월) 행 중 새에 없는 수", len(A.index.difference(N.index)))
rows = {}
for item in 읽기.재무항목():
    if item not in A:
        rows[item] = {"예전에 없음": True}
        continue
    a, n = A[item].dropna(), N[item].reindex(A.index)
    both = n.reindex(a.index).dropna()
    eq = ((both - a.reindex(both.index)).abs() <= 1e-6 * a.reindex(both.index).abs().clip(lower=1))
    rows[item] = {"예전 값 있음": len(a), "둘 다 있음": len(both), "같음 비율": round(eq.mean(), 5),
                  "예전 있음·새 빈칸": int(n.reindex(a.index).isna().sum()), "확인으로 빈칸(검사)": 읽기.검사.get(item)}
print(pd.DataFrame(rows).T.to_string())
