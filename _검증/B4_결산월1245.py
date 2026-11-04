"""README 한계 '결산월 1·2·4·5월 다음 해 결산 규칙'(감독 #35): 결산월마다 (실적보고서발표일 − 결산일) 일수 분포. 규칙이 맞으면 결산 뒤 0~150일 안에 몰린다(틀리면 약 −1년·+1년 쪽으로 몰림).
결산일 = 포.재무가능일과 같은 계산(회계연도 + (결산월 ≤ 5)). 공통/에서 PYTHONPATH=."""
import pandas as pd
import 포트폴리오 as 포

f = 포.재무가능일(("발표일", 150))
f = f[f["M000901001"].notna()]
pub = pd.to_datetime(f["FP56000900"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce")  # 결산일보다 이른 것도 보려고 원래 값으로
d = (pub - f["결산일"]).dt.days
구간 = pd.cut(d, [-10000, -200, 0, 90, 150, 365, 10000], labels=["≤−200", "−199~0", "1~90", "91~150", "151~365", ">365"])
t = pd.crosstab(f["CP10002200"].astype(int), 구간)
t["발표일 있음"] = d.groupby(f["CP10002200"].astype(int)).count()
t["행"] = f.groupby(f["CP10002200"].astype(int)).size()
t["중앙값(일)"] = d.groupby(f["CP10002200"].astype(int)).median()
print(t.to_string())
x = f[f["CP10002200"].isin([1, 2, 4, 5])].assign(일수=d)
print("\n결산월 1·2·4·5 행 중 발표일이 결산일 앞이거나 365일 넘게 뒤인 행:\n", x[(x["일수"] <= 0) | (x["일수"] > 365)][["코드", "회계연도", "CP10002200", "결산일", "일수"]].to_string())
