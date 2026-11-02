"""계산 점검(손으로 답을 아는 작은 예). 실행: python 점검.py → 'ok'."""
import numpy as np
import pandas as pd

import 포트폴리오 as 포

d = pd.to_datetime(["2020-01-31", "2020-02-28", "2020-03-31", "2020-04-30"])
R = pd.DataFrame({"A": [np.nan, 0.10, 0.10, np.nan], "B": [np.nan, -0.10, np.nan, 0.20]}, index=d)
c0 = dict(수수료=0, 거래세=0, 슬리피지=0)

# 매수보유: 2월 (0.1−0.1)/2 = 0. 3월 B 빈칸 → A만: 0.1. 4월 A 빈칸 → B만(값 0.45 그대로 유지): 0.2.
r = 포.보유(R, {d[0]: pd.Series(0.5, ["A", "B"])}, c0)
assert np.allclose(r, [0.0, 0.1, 0.2]), r

# 비용: 처음 매수 100% × (수수료+슬리피지). 매도 땐 거래세까지.
assert np.isclose(포.거래비용(pd.Series(dtype=float), pd.Series(1.0, ["A"]), dict(수수료=0.001, 거래세=0.01, 슬리피지=0.002)), 0.003)
assert np.isclose(포.거래비용(pd.Series(1.0, ["A"]), pd.Series(1.0, ["B"]), dict(수수료=0.001, 거래세=0.01, 슬리피지=0.002)), 0.003 + 0.013)

# 전량교체: 같은 종목이어도 전부 팔고 다시 삼 → 매도(수수료+거래세+슬리피지) + 매수(수수료+슬리피지)
R1 = pd.DataFrame({"A": [np.nan, 0.0, 0.0]}, index=d[:3])
W1 = {d[0]: pd.Series(1.0, ["A"]), d[1]: pd.Series(1.0, ["A"])}
c1 = dict(수수료=0.001, 거래세=0.01, 슬리피지=0.002)
assert np.isclose(포.보유(R1, W1, c1, 전량=True).iloc[1], -(0.013 + 0.003))

# 월비용: 수익 0인 달마다 −0.2%
assert np.allclose(포.보유(R1, {d[0]: pd.Series(1.0, ["A"])}, dict(수수료=0, 거래세=0, 슬리피지=0, 월비용=0.002)), -0.002)

# 상장폐지 구간: 마지막 가격(11)으로 정산 → 0.1, 그다음 구간은 빈칸
p = pd.DataFrame({"A": [10, 11, np.nan, np.nan]}, index=pd.to_datetime(["2020-01-31", "2020-02-10", "2020-02-28", "2020-03-31"]))
r = 포.기간수익률(p, p.index[[0, 2, 3]])["A"]
assert np.isclose(r.iloc[1], 0.1) and np.isnan(r.iloc[2]), r

# 시총상한: 합 1, 최대 = 상한
w = 포.시총상한(pd.Index(list("abcdefghij") + ["k"]), {"mcap": pd.Series([100] + [1] * 10, list("abcdefghij") + ["k"])}, {"비중상한": 0.2})
assert np.isclose(w.sum(), 1) and np.isclose(w.max(), 0.2), w

# 고르기: 분위 Q1 = 점수 가장 높은 쪽
g = 포.고르기(pd.Series(range(10), list("abcdefghij")), ("분위", 5))
assert list(g["Q1"]) == ["i", "j"] and list(g["Q5"]) == ["a", "b"], g

# 순위합산: 둘 다 1등인 종목이 최고
v = pd.DataFrame({"x": [3, 2, 1], "y": [1, 2, 3]}, index=["p", "q", "r"])
assert 포.점수(v, [("x", "높게"), ("y", "낮게")], "순위합산").idxmax() == "p"

# '쓰지 말 것' 구간: A008080 2004-01~2013-09가 [기준일, 다음 리밸런싱]에 걸리면 뺀다
import 종목거르기, 지표
c = pd.Index(["A008080", "A005930"])
ts = lambda a, b: dict(가격="수정주가", t=pd.Timestamp(a), 다음=pd.Timestamp(b))
assert list(종목거르기.쓰지말것(ts("2013-04-01", "2014-04-01"), c)) == ["A005930"]
assert list(종목거르기.쓰지말것(ts("2013-10-01", "2014-10-01"), c)) == ["A008080", "A005930"]

# 빈칸으로 볼 칸: 호텔신라 FY2023 매출원가만 빈칸, FY2024와 다른 항목은 그대로
f = pd.DataFrame({"회계연도": [2023, 2023], "M000905001": [0.0, 5.0], "M000904001": [9.0, 9.0]}, index=["A008770", "A000001"])
assert 지표.값({"fin": f}, "M000905001").isna().tolist() == [True, False] and 지표.값({"fin": f}, "M000904001").notna().all()
assert 지표.값({"fin": f.assign(회계연도=2024)}, "M000905001").notna().all()

# 큰수익률: 기본 하한 3(+300%) 초과만
assert 포.큰수익률(pd.DataFrame({"A": [3.0, 3.5]}, index=d[:2])).index.tolist() == [(d[1], "A")]

# 회전율: A 100% → B 100%면 한쪽 회전율 1, 처음 매수도 1
h = {}
포.보유(R1.assign(B=0.0), {d[0]: pd.Series(1.0, ["A"]), d[1]: pd.Series(1.0, ["B"])}, c0, 회전=h)
assert np.allclose(list(h.values()), [1, 1]), h

# 보유 월로 자르기: 첫거래일 기준 (2017-03-02, 2017-04-03] = 3월 보유, 월말 기준 (2017-03-31, 2017-04-28] = 4월 보유
import 평가
r = pd.Series(1.0, pd.to_datetime(["2004-05-03", "2017-04-03", "2017-05-02"]))
assert list(평가.구간(r, "2004-04", "2017-03").index.strftime("%Y-%m-%d")) == ["2004-05-03", "2017-04-03"]
assert list(평가.구간(pd.Series(1.0, pd.to_datetime(["2017-03-31", "2017-04-28"])), "2017-04", None).index.month) == [4]

# 빈 비중(0종목) 구간은 수익률 빈칸
assert 포.보유(R1, {d[0]: pd.Series(dtype=float)}, c0).isna().all()
assert len(평가.구간(r, None, None)) == 3
# 일간(달력기준) 재무 → 회계연도 값(읽기.연간재무): 작은 가짜 파일로. A = 12월 결산, B = 3월 결산, C = 3월 결산인데 값이 1월에 바뀜(믿을 수 없어 빈칸)
import tempfile
from pathlib import Path
import 데이터읽기 as 읽기
dd = pd.bdate_range("2009-01-01", "2011-12-31")
y = lambda a, b, c: pd.Series(np.select([dd <= a, dd <= b], [1.0, 2.0], 3.0), dd)
fin = pd.DataFrame({"A": y("2009-12-31", "2010-12-31", None), "B": y("2010-03-31", "2011-03-31", None), "C": y("2009-12-31", "2010-12-31", None)})
ym = pd.DataFrame({"A": 12.0, "B": 3.0, "C": 3.0}, index=dd)
옛 = 읽기.DATA, 읽기.공통끝
with tempfile.TemporaryDirectory() as tmp:
    읽기.DATA, 읽기.공통끝 = Path(tmp), lambda: dd[-1]
    ym.rename_axis("날짜").to_parquet(Path(tmp) / "통합_일간_CP10002200_결산월.parquet")
    fin.rename_axis("날짜").to_parquet(Path(tmp) / "통합_일간_M000901001_자산.parquet")
    a = 읽기.연간재무().set_index(["코드", "회계연도"])["M000901001"]
    읽기.DATA, 읽기.공통끝 = 옛
    읽기.일간.cache_clear(); 읽기.연간재무.cache_clear()
assert a[("A", 2009)] == 1 and a[("A", 2010)] == 2 and a[("A", 2011)] == 3, a
assert a[("B", 2008)] == 1 and a[("B", 2009)] == 1 and a[("B", 2010)] == 2, a  # 3월 결산: 2009-03 결산 = FY2008(첫 행은 데이터 전이라 확인 못 하고 그대로), 2011-03 결산 = FY2010
assert np.isnan(a[("C", 2009)]) and np.isnan(a[("C", 2010)]) and 읽기.검사["M000901001"] == 2, (a, 읽기.검사)
print("ok")
