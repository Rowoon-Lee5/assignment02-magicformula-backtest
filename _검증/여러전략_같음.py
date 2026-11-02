"""코드 시험(결과 보고용 아님): 실행()에 '전략들'로 여러 전략을 한 번에 돌린 값이 전략 하나씩 돌린 값과 같은지.
시험 데이터(_시험데이터, 예전 합친 파일에서 뽑은 2003~2006)를 쓴다. 시험 데이터의 연간재무는 예전 모양이라 읽기.연간재무만 그것으로 바꿔 끼운다."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

B = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(B / "공통"))
import 데이터읽기 as 읽기
import 포트폴리오 as 포

T = B / "_시험데이터"
읽기.DATA = T
읽기.공통끝 = lambda: pd.Timestamp("2006-12-28")  # 시험 데이터 한 파일이 끝까지 빈칸이라 끝 날짜를 손으로 줌(시험용)
옛 = pd.read_parquet(T / "통합_연간재무.parquet").rename(columns=lambda c: c.rsplit("_", 1)[-1])
읽기.연간재무 = lambda: 옛
읽기.종목정보 = lambda: pd.read_csv(T / "통합_종목정보.csv", encoding="utf-8-sig").set_index("코드")
cfg = {**포.우동호2023, "기간": ("2004-04", "2006-04"), "비중": ["동일", "시총", "위험균형"]}
전략 = {"MF": dict(지표=[("ROC", "높게"), ("EY", "높게")], 합산="순위합산"), "EY→ROC": dict(지표=[("EY", "높게", 0.5), ("ROC", "높게", 1.0)], 합산="단계별")}
한꺼번 = 포.실행({**cfg, "전략들": 전략})
for 이름, e in 전략.items():
    하나 = 포.실행({**cfg, **e})
    for b in cfg["비중"]:
        a, c = 한꺼번["수익률"][(이름, b, "상위30")], 하나["수익률"][(b, "상위30")]
        assert np.allclose(a, c, equal_nan=True), (이름, b)
        assert (한꺼번["회전율"][(이름, b, "상위30")] == 하나["회전율"][(b, "상위30")]).all()
u = 한꺼번["보유"][("유니버스", "시총", "전체")]
assert all(np.isclose(w.sum(), 1) for w in u.values())
print("ok: 여러 전략 한 번에 = 하나씩,", len(한꺼번["수익률"]), "개월, 유니버스 종목 수", [len(w) for w in u.values()])
