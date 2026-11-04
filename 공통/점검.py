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

# 폐지 종목 몫엔 매도비용 없음(한계 21·40번): A·B 반반, 2월 B 폐지(빈칸) → 3월 리밸런싱(A 100%)에서 팔 것은 A뿐 → 전량교체 비용 = A 매도 1 × 0.013 + 매수 1 × 0.003
R2 = pd.DataFrame({"A": [np.nan, 0.0, 0.0, 0.0], "B": [np.nan, np.nan, np.nan, np.nan]}, index=d)
assert np.isclose(포.보유(R2, {d[0]: pd.Series(0.5, ["A", "B"]), d[2]: pd.Series(1.0, ["A"])}, c1, 전량=True).loc[d[3]], -(0.013 + 0.003))
# 첫 달 빈칸이면 비용은 값 있는 첫 달에(한계 15번): 2월 A 빈칸, 3월 0 → 3월에 매수비용 0.003
R3 = pd.DataFrame({"A": [np.nan, np.nan, 0.0]}, index=d[:3])
r = 포.보유(R3, {d[0]: pd.Series(1.0, ["A"])}, c1)
assert np.isnan(r.loc[d[1]]) and np.isclose(r.loc[d[2]], -0.003), r

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

# '쓰지 말 것' 구간: A008080 2004-01~2013-09에 기준일이 들면 뺀다(다음 리밸런싱일은 안 봄 = 미래 정보 안 씀)
import 종목거르기, 지표
c = pd.Index(["A008080", "A005930"])
ts = lambda a, b: dict(가격="수정주가", t=pd.Timestamp(a), 다음=pd.Timestamp(b))
assert list(종목거르기.쓰지말것(ts("2013-04-01", "2014-04-01"), c)) == ["A005930"]
assert list(종목거르기.쓰지말것(ts("2013-10-01", "2014-10-01"), c)) == ["A008080", "A005930"]
assert list(종목거르기.쓰지말것(ts("2003-12-01", "2004-12-01"), c)) == ["A008080", "A005930"]  # 구간이 보유 중에 시작 → 거르지 않음
# 보유 중 걸린 칸만 빈칸(D-05): 구간 끝 9-30에 걸리는 9월·10월 구간만
m = pd.to_datetime(["2013-08-01", "2013-09-02", "2013-10-01", "2013-11-01"])
q = 포.쓰지말것칸(pd.DataFrame({"A008080": 0.1, "A005930": 0.1}, index=m), "수정주가")
assert q["A008080"].isna().tolist() == [False, True, True, False] and q["A005930"].notna().all(), q

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
옛 = 읽기.DATA, 읽기.공통끝, 읽기.변환캐시
with tempfile.TemporaryDirectory() as tmp:
    읽기.DATA, 읽기.공통끝, 읽기.변환캐시 = Path(tmp), lambda: dd[-1], Path(tmp)  # 시험 폴더만 보게(저장소 캐시의 실제 파일 빼기)
    ym.rename_axis("날짜").to_parquet(Path(tmp) / "통합_일간_CP10002200_결산월.parquet")
    fin.rename_axis("날짜").to_parquet(Path(tmp) / "통합_일간_M000901001_자산.parquet")
    a = 읽기.연간재무().set_index(["코드", "회계연도"])["M000901001"]
    읽기.DATA, 읽기.공통끝, 읽기.변환캐시 = 옛
    읽기.일간.cache_clear(); 읽기.연간재무.cache_clear()
assert a[("A", 2009)] == 1 and a[("A", 2010)] == 2 and a[("A", 2011)] == 3, a
assert a[("B", 2008)] == 1 and a[("B", 2009)] == 1 and a[("B", 2010)] == 2, a  # 3월 결산: 2009-03 결산 = FY2008(첫 행은 데이터 전이라 확인 못 하고 그대로), 2011-03 결산 = FY2010
assert np.isnan(a[("C", 2009)]) and np.isnan(a[("C", 2010)]) and 읽기.검사["M000901001"] == 2, (a, 읽기.검사)
# 분기재무: 4분기 합은 쓸 수 있는 연속 4분기만, 잔액은 최근 분기말 값, 발표일 다음 날부터
q = pd.DataFrame({"코드": ["A"] * 5 + ["B"] * 3, "분기말": pd.to_datetime(["2019-12-31", "2020-03-31", "2020-06-30", "2020-09-30", "2020-12-31", "2020-03-31", "2020-09-30", "2020-12-31"]),
                  "M000908004": [9, 1, 2, 3, 4, 1, 2, 3], "M000903003": [90, 10, 20, 30, 40, 10, 20, 30]})
q["가능일"] = q["분기말"] + pd.Timedelta(days=40)
원래분기 = 포.분기가능일
포.분기가능일 = lambda: q
z = 포.분기재무(pd.Timestamp("2021-03-01"))
assert z.loc["A", "M000908004"] == 1 + 2 + 3 + 4 and z.loc["A", "M000903003"] == 40 and np.isnan(z.loc["B", "M000908004"]), z  # B는 2020-06 분기가 없어 연속 아님
assert 포.분기재무(pd.Timestamp("2021-01-15")).loc["A", "M000908004"] == 9 + 1 + 2 + 3  # 2020-12 분기는 아직 발표 전
assert 포.분기재무(pd.Timestamp("2021-03-01"), "최근분기x4").loc["A", "M000908004"] == 16
포.분기가능일 = 원래분기
print("ok")
