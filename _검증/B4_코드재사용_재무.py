"""README 한계 '코드 재사용 종목 재무'(감사 #16): 코드 재사용 16종목에서 새 회사 첫날 뒤 기준일(매달 첫·마지막 거래일, 3년)에 포.재무()가 고르는 행의 결산일이
앞 회사 마지막 날 이전(= 앞 회사 재무)인 경우가 있는지. 재무시점 두 규칙 모두. 공통/에서 PYTHONPATH=."""
import pandas as pd
import 데이터읽기 as 읽기
import 포트폴리오 as 포

u = pd.read_csv(읽기.ADD10 / "코드재사용_16종목.csv", encoding="utf-8-sig", parse_dates=["이전회사_마지막날짜", "새회사_첫날짜"])
g = sorted(set(포.기준일({**포.기본설정, "기간": ("1990-01", "2026-09")})) | set(포.기준일({**포.기본설정, "기간": ("1990-01", "2026-09"), "기준일": "마지막거래일"})))
g = pd.DatetimeIndex(g)
rows = []
for how in [("결산후개월", 3), ("발표일", 150)]:
    f = 포.재무가능일(how)
    for c, a, b in zip(u["코드"], u["이전회사_마지막날짜"], u["새회사_첫날짜"]):
        x = f[f["코드"] == c]
        for t in g[(g >= b) & (g < b + pd.DateOffset(years=3))]:
            y = x[(x["가능일"] <= t) & (x["결산일"] >= t - pd.DateOffset(years=2))].sort_values(["회계연도", "결산일"]).tail(1)
            if len(y):
                rows.append(dict(규칙=how[0], 코드=c, 기준일=t, 회계연도=int(y["회계연도"].iloc[0]), 결산일=y["결산일"].iloc[0], 앞회사마지막=a, 새회사첫날=b,
                                 앞회사재무=bool(y["결산일"].iloc[0] <= a)))
r = pd.DataFrame(rows)
print("새 회사 첫날 뒤 3년 기준일에 고른 행:", len(r), "/ 그중 결산일 ≤ 앞 회사 마지막 날(앞 회사 재무):", int(r["앞회사재무"].sum()))
print(r[r["앞회사재무"]].to_string() if r["앞회사재무"].any() else "없음")
print("\nA198940 처음 기준일 몇 개:\n", r[r["코드"] == "A198940"].head(6).to_string())
print("\n코드별 첫 기준일에 고른 회계연도(규칙 결산후개월):\n", r[r["규칙"] == "결산후개월"].groupby("코드").first()[["기준일", "회계연도", "결산일", "앞회사마지막", "새회사첫날"]].to_string())
