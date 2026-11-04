"""2차 진단 1번(지시 2026-11-05): 01 우동호(2023) 시총 1분위 MF 213배 대 원문 44.24배(Table 3, p.514).
(a) 해마다(4월 첫 거래일 → 다음 4월 첫 거래일, 마지막 해는 2022-03-31) 1분위 MF·IMF 포트 수익률(비용 뒤, 노트북 월수익률을 묶음).
    원문에는 1분위 해마다 표가 없다(Table 3은 전체 기간 값만, Fig. 1은 전 종목만 — OCR p.513·514). 그래서 원문 숫자 칸은 전체 기간(Table 3)만 놓는다.
    같은 정의(일간 × √N, 15절)로 잰 1분위 SD·샤프·MDD를 Table 3과 나란히.
(b) 해마다 1분위 MF 보유 종목 중 1년 수익률 상위 10(18개 해 전부): 이름·코드·시작/끝 수정주가·종가(원본 값)·주식수·거래정지 날 수·관리종목 날 수·상장폐지일.
설정은 노트북 본문 그대로(포.우동호2023, 기간 2004-04~2022-03, 끝 = 마지막거래일, 제외 + ('시총분위', 1)). 아무 값도 바꾸지 않는다.
실행: 공통 폴더에서 python ../_검증/2차_01_시총1분위.py > ../_검증/2차_01_시총1분위_결과.txt"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import numpy as np
import pandas as pd

import 데이터읽기 as 읽기
import 포트폴리오 as 포

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 400)
OUT = Path(__file__).resolve().parent
T0 = time.time()
짧게 = "--짧게" in sys.argv  # 지시 J 짧은 시험: 앞 3년 + 마지막 2년
기본 = {**포.우동호2023, "기간": ("2004-04", "2022-03"), "끝": "마지막거래일"}
IMF = {**기본, "이름": "우동호2023_IMF", "지표": [("GPA", "높게"), ("EY", "높게")]}
Q1 = [("시총분위", {"분위": 1})]
원문T3 = pd.DataFrame({"MF": [44.2427, -0.5760, 1.1082, 3.52, 2.72], "IMF": [101.3052, -0.6203, 1.1828, 4.06, 3.31]},
                     index=["누적", "MDD", "SD", "샤프", "정보비율"]).T  # Table 3 p.514(OCR '4424.27%' 등, 0단계 대조표와 같음)

기간들 = [("2004-04", "2007-03"), ("2020-04", "2022-03")] if 짧게 else [기본["기간"]]
결과 = {}
for 기간 in 기간들:
    for 이름, cfg in {"MF": 기본, "IMF": IMF}.items():
        c = {**cfg, "기간": 기간}
        결과[(이름, "1분위", 기간)] = 포.실행({**c, "제외": c["제외"] + Q1})
        결과[(이름, "전체", 기간)] = 포.실행(c)
print(f"실행 {len(결과)}개 {time.time() - T0:.0f}초")

# ---------- (a) 해마다 ----------
k = 읽기.지수()["I.001"]
rows = []
for 기간 in 기간들:
    o = 결과[("MF", "1분위", 기간)]
    reb = sorted(o["보유"][("동일", "상위30")])
    idx = o["수익률"].index
    for t0, t1 in zip(reb, reb[1:] + [idx[-1]]):
        m = (idx > t0) & (idx <= t1)
        row = {"연도": t0.year, "시작": t0.date(), "끝": t1.date()}
        for 이름 in ("MF", "IMF"):
            for g in ("1분위", "전체"):
                r = 결과[(이름, g, 기간)]["수익률"][("동일", "상위30")][m]
                row[f"{g} {이름}"] = float((1 + r.dropna()).prod() - 1)
        row["KOSPI"] = float(k.loc[t1] / k.loc[t0] - 1)
        row["1분위 MF 편입 수"] = int(o["기록"].loc[t0, "편입:상위30"])
        row["1분위 모집단 수(시총분위 뒤)"] = int(o["기록"].loc[t0, "시총분위"])
        rows.append(row)
Y = pd.DataFrame(rows).set_index("연도")
Y["원문 해마다 값"] = "원문에 없음"
print("\n## (a) 해마다 포트 수익률(비용 뒤, 동일가중 30종목). 원문 1분위 해마다 표 없음(Table 3 p.514는 전체 기간만)\n", Y.round(4).to_string())
if not 짧게:
    cum = (1 + Y[["1분위 MF", "1분위 IMF", "전체 MF", "전체 IMF", "KOSPI"]]).prod() - 1
    print("\n해마다 값을 곱한 누적:", cum.round(4).to_dict(), " / 원문 Table 3 누적: MF 44.2427, IMF 101.3052, KOSPI 2.1239")
    # 진단용(본문 아님): 한 해를 뺀(그 해 0%) 누적 — 어느 해가 누적을 크게 만드는지
    빼기 = pd.DataFrame({y: (1 + Y[["1분위 MF", "1분위 IMF"]].drop(y)).prod() - 1 for y in Y.index}).T
    빼기.columns = ["그 해 빼면 1분위 MF 누적", "그 해 빼면 1분위 IMF 누적"]
    print("\n## (a-2) 진단용: 그 해를 빼고(0%로 보고) 곱한 누적 — 본문 아님\n", 빼기.round(2).to_string())
    Y.join(빼기).to_csv(OUT / "2차_01_1분위_해마다.csv", encoding="utf-8-sig")

    # 같은 정의(일간 × √N, 01 15절·_검증/01_정의역산.py)로 1분위 SD·샤프·MDD·정보비율
    x = pd.read_excel(next(읽기.XLSX.glob("X02_*.xlsx")), header=None)
    y일 = pd.Series(x.iloc[14:, 1].astype(float).to_numpy(), pd.to_datetime(x.iloc[14:, 0])).dropna()
    p = 읽기.상장가격(읽기.수정주가)
    날 = p.loc["2004-04-01":"2022-04-01"].index
    Rd = 포.기간수익률(p, 날)
    kd = k.loc["2004-04-01":"2022-03-31"].pct_change().dropna()
    st = {}
    for 이름, cfg in {"MF": 기본, "IMF": IMF}.items():
        o = 결과[(이름, "1분위", 기본["기간"])]
        d = 포.보유(Rd, o["보유"][("동일", "상위30")], cfg["거래비용"], cfg["전량교체"]).loc[:"2022-03-31"].dropna()
        N = len(d); w = (1 + d).cumprod()
        e = d - y일.reindex(d.index.union(y일.index)).ffill().reindex(d.index).shift(1) / 100 / 365
        a = d - kd.reindex(d.index)
        st[이름] = {"누적": w.iloc[-1] - 1, "MDD": (w / w.cummax().clip(lower=1) - 1).min(), "SD": d.std() * np.sqrt(N),
                   "샤프": e.mean() / e.std() * np.sqrt(N), "정보비율": a.mean() / a.std() * np.sqrt(N), "일 수": N}
    st = pd.DataFrame(st).T
    print("\n## (a-3) 1분위 일간 정의(SD×√N, 샤프=일 초과 평균/SD×√N, 국고3년/365) vs 원문 Table 3(p.514)\n",
          pd.concat({"우리": st, "원문": 원문T3}, axis=1).round(4).to_string())

# ---------- (b) 해마다 상위 10 ----------
o = 결과[("MF", "1분위", 기간들[-1])] if 짧게 else 결과[("MF", "1분위", 기본["기간"])]
W = o["보유"][("동일", "상위30")]; R = o["종목수익률"]
info = 읽기.종목정보()
수정, 종가, 주식 = 읽기.일간(읽기.수정주가), 읽기.일간(읽기.종가), 읽기.일간(읽기.주식수)
정지1, 정지2, 관리, 시장 = 읽기.일간(읽기.정지구분), 읽기.일간(읽기.정지여부), 읽기.일간(읽기.관리여부), 읽기.일간(읽기.시장구분)
P = 읽기.상장가격(읽기.수정주가)
top = []
dates = sorted(W)
for t0, t1 in zip(dates, dates[1:] + [R.index[-1]]):
    r = R.loc[(R.index > t0) & (R.index <= t1), W[t0].index]
    g = ((1 + r.fillna(0)).prod() - 1).sort_values(ascending=False)
    for 순위, (c, v) in enumerate(g.head(10).items(), 1):
        구간 = slice(t0 + pd.Timedelta(days=1), t1)
        lp = P.loc[구간, c].dropna()
        폐지 = info["상장폐지일"].get(c)
        top.append({"연도": t0.year, "순위": 순위, "코드": c, "이름": info["코드명"].get(c), "시장(시작일)": str(시장.loc[t0, c]),
                    "1년 수익률(R 묶음)": v, "수정주가 시작": 수정.loc[t0, c], "수정주가 끝(마지막 상장 가격)": lp.iloc[-1] if len(lp) else np.nan,
                    "마지막 상장 가격 날": lp.index[-1].date() if len(lp) else None, "종가 시작": 종가.loc[t0, c], "종가 끝": 종가.loc[lp.index[-1], c] if len(lp) else np.nan,
                    "주식수 시작": 주식.loc[t0, c], "주식수 끝": 주식.loc[lp.index[-1], c] if len(lp) else np.nan,
                    "거래정지 날(S410002600)": int(정지1.loc[구간, c].astype(object).eq("거래정지").sum()),
                    "정지 날(CP10001650)": int(정지2.loc[구간, c].astype(object).eq("정지").sum()),
                    "관리종목 칸(CP10001660)": int(관리.loc[t0:t1, c].astype(object).eq("관리").sum()),
                    "상장폐지일(X04)": 폐지 if pd.notna(폐지) else None,
                    "구간 안 폐지": bool(pd.notna(폐지) and t0 <= pd.Timestamp(str(폐지)) <= t1 + pd.Timedelta(days=1)),
                    "쓰지말것 걸림": bool(R.loc[(R.index > t0) & (R.index <= t1), c].isna().any())})
B = pd.DataFrame(top)
print("\n## (b) 해마다 1분위 MF 보유 종목 1년 수익률 상위 10(원본 값 그대로)\n", B.to_string(index=False))
if not 짧게:
    B.to_csv(OUT / "2차_01_1분위_상위10.csv", index=False, encoding="utf-8-sig")
    # 해마다 상위 10 합 기여(비중 1/30 × 수익률 합)와 포트 1년 수익률 대비
    s = B.groupby("연도")["1년 수익률(R 묶음)"].agg(["sum", "max", lambda x: int((x > 1).sum())])
    s.columns = ["상위10 수익률 합", "최대", "+100% 초과 수"]
    s["상위10 기여(합/30)"] = s["상위10 수익률 합"] / 30
    print("\n## (b-2) 해마다 상위 10 요약\n", s.round(4).to_string())
    print("\n상위 10 행 중 거래정지 날 > 0:", int((B["거래정지 날(S410002600)"] > 0).sum()), "/ 정지 날 > 0:", int((B["정지 날(CP10001650)"] > 0).sum()),
          "/ 관리종목 칸 > 0:", int((B["관리종목 칸(CP10001660)"] > 0).sum()), "/ 구간 안 폐지:", int(B["구간 안 폐지"].sum()), "/ 쓰지말것 걸림:", int(B["쓰지말것 걸림"].sum()),
          "/ 주식수 바뀜:", int((B["주식수 시작"] != B["주식수 끝"]).sum()), "/ 전체 행:", len(B))
print(f"\n걸린 시간 {time.time() - T0:.0f}초")
