"""추가 지시 D-1 회귀 검사: 기간 끝·유니버스 고침이 의도한 칸만 바꾸는지. 공통/에서 3.11로 실행."""
import pandas as pd
import 데이터읽기 as 읽기
import 포트폴리오 as 포
import 종목거르기

# 1) 끝 옵션이 없는 설정의 기준일은 예전 식과 같아야 함(02·03·연구 노트북)
def 예전기준일(cfg):
    d = 읽기.일간(cfg["가격"]).index.to_series(); g = d.groupby(d.dt.to_period("M"))
    g = g.min() if cfg["기준일"] == "첫거래일" else g.max()
    return pd.DatetimeIndex(g.loc[cfg["기간"][0]:cfg["기간"][1]].to_numpy())
for c in [{**포.기본설정, "기간": ("2002-03", "2018-05"), "기준일": "마지막거래일"}, {**포.우동호2023, "기간": ("1990-01", "2026-09")}, {**포.우동호2023}]:
    assert 포.기준일(c).equals(예전기준일(c)), c["기간"]
print("끝 옵션 없는 기준일: 예전과 같음(3개 설정)")

# 2) 01 MF: 예전(2004-04~2022-04 첫 거래일) 대 새(2004-04~2022-03 + 2022-03-31). 마지막 달만 달라야 함
old = 포.실행({**포.우동호2023, "기간": ("2004-04", "2022-04")})
new = 포.실행({**포.우동호2023, "기간": ("2004-04", "2022-03"), "끝": "마지막거래일"})
a, b = old["수익률"], new["수익률"]
print("예전 마지막 3칸:", list(a.index[-3:].date), "/ 새 마지막 3칸:", list(b.index[-3:].date), "/ 개월", len(a), len(b))
같은칸 = a.index[:-1]
d = (a.loc[같은칸] - b.loc[같은칸]).abs().max().max()
print("마지막 달 앞 칸 최대 차이:", d)
print("보유 비중 같음:", all(old["보유"][k][t].equals(new["보유"][k][t]) for k in old["보유"] for t in old["보유"][k]))
print("마지막 달 수익률 예전/새:\n", pd.concat([a.iloc[-1], b.iloc[-1]], axis=1, keys=["예전(→2022-04-01)", "새(→2022-03-31)"]))
cum = lambda r: (1 + r).prod() - 1
print("누적 예전/새:", cum(a).round(4).to_dict(), cum(b).round(4).to_dict())
