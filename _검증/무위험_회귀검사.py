"""추가 지시 11 회귀 검사: 콜금리판 커밋(기본 832888f) 대비 CD1m판 결과 csv에서 바뀐 칸이 무위험과 관계된 칸뿐인지.
무위험과 관계없는 칸(수익률·변동성·MDD·벤치 대비·정보비율·회전율)이 하나라도 바뀌면 '의도하지 않은 변화'로 출력한다.
사용: python _검증/무위험_회귀검사.py [커밋] > _검증/무위험_회귀검사_결과.txt"""
import io
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parent.parent
commit = sys.argv[1] if len(sys.argv) > 1 else "832888f"
무관 = ["개월", "누적", "연환산", "표준편차(연)", "벤치 대비 연환산", "MDD", "정보비율", "회전율(전 기간)"]
files = ["연구/결과/확장연구_20261103.csv"] + [f"결과_전략수익률/{n}.csv" for n in ["1_비중", "2_주기", "3_지표", "4_순서", "5_비용", "6_기간"]]
문제 = 0
for f in files:
    old = pd.read_csv(io.BytesIO(subprocess.run(["git", "show", f"{commit}:{f}"], cwd=root, capture_output=True, check=True).stdout))
    new = pd.read_csv(root / f)
    assert list(old.columns) == list(new.columns) and old.shape == new.shape, f"{f}: 모양·열이 다름 {old.shape} {new.shape}"
    num = old.select_dtypes("number").columns
    txt = old.columns.difference(num)
    assert old[txt].fillna("").equals(new[txt].fillna("")), f"{f}: 글자 칸이 다름"
    a, b = old[num].to_numpy(float), new[num].to_numpy(float)
    diff = ~(np.isclose(a, b, rtol=0, atol=1e-12) | (np.isnan(a) & np.isnan(b)))
    바뀜 = pd.Series(diff.sum(0), index=num)
    bad = 바뀜[바뀜.index.isin(무관) & (바뀜 > 0)]
    문제 += int(bad.sum())
    print(f"{f}: {old.shape[0]}줄, 바뀐 칸 {int(diff.sum())}/{diff.size}")
    print("  열별 바뀐 칸:", 바뀜[바뀜 > 0].to_dict())
    print("  무위험과 관계없는 열에서 바뀐 칸:", bad.to_dict() or "없음")
print("의도하지 않은 변화:", 문제, "칸")
