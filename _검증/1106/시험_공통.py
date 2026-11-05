"""2026-11-06 c 공통 코드 고친 것 작은 시험(짧은 기간). 실행: python 시험_공통.py"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "공통"))
import numpy as np, pandas as pd
import 데이터읽기 as 읽기, 지표, 포트폴리오 as 포, 평가
T = time.time()
t = pd.Timestamp("2005-04-01")
a, b = 포.재무(t, ("결산후개월", 3)), 포.재무(t, ("결산후개월", 3), "직전년도")
print("재무 2년상한 행", len(a), "회계연도", a["회계연도"].value_counts().to_dict(), "/ 직전년도 행", len(b), b["회계연도"].value_counts().to_dict())
assert (b["결산일"].dt.year == 2004).all()
f = 포.발표재무(pd.Timestamp("2010-05-31"))
print("발표재무 2010-05-31", len(f), f["보고서"].value_counts().to_dict(), f["분기말"].dt.strftime("%Y-%m").value_counts().head(4).to_dict())
x = f.loc["A005930"]; print("삼성전자", x["보고서"], x["분기말"].date(), x["가능일"].date(), x["M000908004"])
f2 = 포.발표재무(pd.Timestamp("2010-04-30")); print("2010-04-30 삼성", f2.loc["A005930", ["보고서", "분기말", "가능일", "M000908004"]].to_dict())
cfg = {**포.기본설정, "시장": ["KS"], "가격": 읽기.수정주가, "기준일": "마지막거래일", "기간": ("2010-03", "2010-06"), "리밸런싱": 1}
s = 포.재료(pd.Timestamp("2010-06-30"), cfg)
v1, v2 = 지표.변동성(s), 지표.변동성_창(s, 12, "일")
print("변동성 같음:", np.allclose(v1.dropna(), v2.dropna()), v1.notna().sum(), v2.notna().sum())
print("변동성 24·주·월 값 수", 지표.변동성_창(s, 24).notna().sum(), 지표.변동성_창(s, 12, "주").notna().sum(), 지표.변동성_창(s, 12, "월").notna().sum())
e = 지표.EP_선행(s); print("EP_선행 값 수", e.notna().sum(), e.describe().round(3).to_dict())
m = 지표.모멘텀11(s); print("모멘텀11 값 수", m.notna().sum())
u = {**포.우동호2023, "기간": ("2004-04", "2005-06")}
F = 포.원문요인(u)
print(F.round(4))
print("DataGuide 요인과 상관:", F.corrwith(평가.요인(포.기준일({**u, "리밸런싱": 1}), u)[["SMB", "HML", "MOM"]]).round(3).to_dict())
print("고르기 상하비율", {k: len(v) for k, v in 포.고르기(pd.Series(range(10), list("abcdefghij")), ("상하비율", 0.3)).items()})
print("회귀", 평가.회귀(pd.Series([0.01, 0.02, 0.0, 0.03]), pd.DataFrame(index=range(4)))[:2])
print(f"끝 {time.time() - T:.0f}초")
