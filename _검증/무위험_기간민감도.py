"""CD1m 감사 MEDIUM(2026-11-03): 교수님 파일 CD1m의 1990-01~1994-12 14% 고정값이 기간별 샤프·알파를 얼마나 바꾸는지.
확장연구 pkl(무위험 CD1m 판)의 수익률 그대로, 무위험만 콜(E11.02.003.001)로 바꾼 것과 기간(평가.구간들)마다 비교한다. 노트북·원본은 바꾸지 않는다.
사용: python _검증/무위험_기간민감도.py > _검증/무위험_기간민감도_결과.txt"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import 평가
import 포트폴리오 as 포

x = pd.read_pickle(Path(__file__).resolve().parent.parent / "연구" / "결과" / "확장연구_20261103.pkl")
설정, 수익, 벤치 = x["설정"], x["수익"], x["벤치"]
assert 설정["무위험"] == "CD1m", "pkl이 아직 CD1m 판이 아님"
grid = 포.기준일(설정)
F = {"CD1m": x["F주"], "콜": 평가.요인(grid, {**설정, "무위험": "E11.02.003.001"}).assign(시장=벤치["유니버스(시총가중)"])}
# 교수님 파일 1990-01~1994-12 값(14%)을 쓴 보유 월. 줄 날짜는 보유 끝 첫 거래일이라 1994-12 값은 1995-02-02 줄까지.
# 1997-09 값도 우연히 14.00이라 날짜로 자른다.
고정 = F["CD1m"]["RF"].eq(14 / 1200) & (F["CD1m"].index < "1995-03-01")
줄들 = {"기준 전략": 수익[("EY+ROC 순위합산", "동일", 12, "비용기본")], "벤치:유니버스(시총가중)": 벤치["유니버스(시총가중)"], "벤치:코스피": 벤치["코스피"]}
칸 = ["개월", "샤프", "CAPM α(월)", "Carhart α(월)", "Carhart t(NW)"]
rows = {}
for n, r in 줄들.items():
    for g, (a, b) in 평가.구간들.items():
        s = 평가.구간(r.dropna(), a, b)
        for 금리, f in F.items():
            rows[(n, g, 금리)] = {k: v for k, v in 평가.성과(s, f).items() if k in 칸} | {"14% 고정 달": int(고정.reindex(s.index).sum())}
pd.set_option("display.width", 200)
print(pd.DataFrame(rows).T.rename_axis(["줄", "기간", "무위험"]).round(4).to_string())
