"""01 우동호(2023) 원문 차이 진단(지시 2026-11-04 01-2·3·4번). 기본 설정 = 노트북 3절(원문 기간, 끝 = 2022-03-31). 설정은 바꾸지 않고 바꿔 본 판을 나란히 놓는다.
A 표본 수: 거르기 단계를 하나씩 끄고 순위 매긴 종목 수와 그 종목들의 1년(4월 첫 거래일 → 다음 3월 마지막 거래일) 수익률 평균·표준편차를 원문 표 1(p.512)과 비교.
B 시총 1분위: 분위 모집단 3가지, 1분위 MF 연도별 수익률·종목 기여.
C 설정: 3월 말~4월 첫 거래일 하루 비보유, 거래세 매수·매도 모두, TR 가격, 발표일 확인판, 비용 0, 세전이익 잠정치(파일 있을 때).
공통/에서 PYTHONPATH=. 로 실행 → _검증/01_진단_결과.txt, 표는 _검증/01_진단_*.csv"""
import numpy as np
import pandas as pd
import 데이터읽기 as 읽기
import 지표
import 포트폴리오 as 포

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
from pathlib import Path
OUT = Path(__file__).resolve().parent
기본 = {**포.우동호2023, "기간": ("2004-04", "2022-03"), "끝": "마지막거래일"}
IMF = {**기본, "이름": "우동호2023_IMF", "지표": [("GPA", "높게"), ("EY", "높게")]}
표1 = pd.read_csv(OUT / "01_원문표1.csv", index_col="연도")
cum = lambda r: float((1 + r.dropna()).prod() - 1)

# ---------- A. 표본 수 ----------
grid = 포.기준일(기본)
reb = grid[:-1][::12]
P = 읽기.상장가격(기본["가격"])
d = P.index.to_series()
마지막 = d.groupby(d.dt.to_period("M")).max()
판들 = {"기본": 기본["제외"], "보통주 안 거름": [f for f in 기본["제외"] if f != "보통주"], "투자기구 안 거름": [f for f in 기본["제외"] if f != "투자기구"],
        "거래정지 안 거름": [f for f in 기본["제외"] if f != "거래정지"], "결산월 안 거름": [f for f in 기본["제외"] if not (isinstance(f, tuple) and f[0] == "결산월")]}
rows, stat = [], []
for t in reb:
    끝 = 마지막[pd.Period(f"{t.year + 1}-03", "M")]
    yr = P.ffill().loc[끝] / P.loc[t] - 1  # 4월 첫 거래일 → 다음 3월 마지막 거래일(중간 폐지는 마지막 가격)
    for 이름, ex in 판들.items():
        for 시장 in (["KS", "KQ"], ["KS"]) if 이름 == "기본" else (["KS", "KQ"],):
            s, c, n = 포.거르기(t, {**기본, "제외": ex, "시장": 시장})
            v = pd.DataFrame({m: getattr(지표, m)(s).reindex(c) for m in ["ROC", "EY"]}).replace([np.inf, -np.inf], np.nan).dropna()
            k = 이름 + ("" if 시장 == ["KS", "KQ"] else " (유가증권만)")
            r = yr.reindex(v.index)
            rows.append({"연도": t.year, "판": k, "순위 매김": len(v), "1년 수익률 있음": int(r.notna().sum())})
            if k == "기본":
                stat.append({"연도": t.year, **{f"단계:{a}": b for a, b in n.items()}, "순위 매김": len(v),
                             "평균(%)": r.mean() * 100, "표준편차(%)": r.std() * 100, "중앙값(%)": r.median() * 100,
                             "평균, +300% 초과 뺌(%)": r[r <= 3].mean() * 100, "다음 3월 말까지 가격 있음": int(P.loc[끝, v.index].notna().sum())})
A = pd.DataFrame(rows).pivot(index="연도", columns="판", values="순위 매김")
A.insert(0, "원문 Number", 표1["Number"])
S = pd.DataFrame(stat).set_index("연도")
S = pd.concat([표1, S], axis=1)
print("## A1. 순위 매긴 종목 수(ROC·EY 둘 다 있음), 판별\n", A.to_string())
print("\n## A2. 기본 판 단계별 남은 수와 1년 수익률 통계 vs 원문 표 1\n", S.round(2).to_string())
print("\n원문 Number − 우리 순위 매김(기본): 평균", round((A["원문 Number"] - A["기본"]).mean(), 1), "/ 해마다", (A["원문 Number"] - A["기본"]).to_dict())
A.to_csv(OUT / "01_진단_표본수.csv", encoding="utf-8-sig"); S.to_csv(OUT / "01_진단_표1비교.csv", encoding="utf-8-sig")

# ---------- B. 시총 1분위 ----------
원문Q1 = {"MF": 44.2427, "IMF": 101.3052}
brow = {}
결과B = {}
for 이름, cfg in {"MF": 기본, "IMF": IMF}.items():
    for 판, ex in {"남은 종목으로 나눔(예전 본문)": [("시총분위", {"분위": 1})],
                  "ROC·EY(또는 GPA·EY) 있는 종목으로 나눔(본문, 2026-11-05)": [("지표있음", {"지표들": [m[0] for m in cfg["지표"]]}), ("시총분위", {"분위": 1})],
                  "상장 전 종목 경계로 나눔": [("시총분위", {"분위": 1, "기준": "상장전체"})]}.items():
        o = 포.실행({**cfg, "제외": cfg["제외"] + ex})
        결과B[(이름, 판)] = o
        r = o["수익률"][("동일", "상위30")]
        brow[(이름, 판)] = {"누적": cum(r), "원문 누적": 원문Q1[이름], "종목 수(첫 해 편입)": int(o["기록"]["편입:상위30"].iloc[0])}
B = pd.DataFrame(brow).T
print("\n## B1. 시총 1분위 MF·IMF 누적(배) — 분위 모집단별\n", B.to_string())
o = 결과B[("MF", "ROC·EY(또는 GPA·EY) 있는 종목으로 나눔(본문, 2026-11-05)")]
W = o["보유"][("동일", "상위30")]; R = o["종목수익률"]
dates = sorted(W)
yr_rows, contrib = [], []
for t0, t1 in zip(dates, dates[1:] + [R.index[-1]]):
    r = R.loc[(R.index > t0) & (R.index <= t1), W[t0].index]
    g = (1 + r.fillna(0)).prod() - 1
    contrib.append((g * W[t0]).rename(t0.year))
    yr_rows.append({"연도": t0.year, "포트 1년(비용 전, 동일가중 매수보유)": float((W[t0] * g).sum()), "+100% 넘은 종목": int((g > 1).sum()), "가장 큰 종목 수익률": float(g.max())})
Y = pd.DataFrame(yr_rows).set_index("연도")
C = pd.concat(contrib, axis=1).stack().rename("기여").reset_index()
C.columns = ["코드", "연도", "기여"]
C["이름"] = 읽기.종목정보()["코드명"].reindex(C["코드"]).to_numpy()
print("\n## B2. 1분위 MF(본문 = 지표 자료 있는 종목으로 나눔) 연도별\n", Y.round(4).to_string())
print("\n## B3. 1분위 MF 기여 큰 종목-연도 15(비중 × 1년 수익률)\n", C.nlargest(15, "기여").round(4).to_string())
Y.to_csv(OUT / "01_진단_1분위연도.csv", encoding="utf-8-sig"); B.to_csv(OUT / "01_진단_1분위모집단.csv", encoding="utf-8-sig")

# ---------- C. 설정 ----------
def 하루비보유(cfg):
    """4월 첫 거래일 앞 마지막 거래일을 기준일에 더하고 그 하루 구간 수익률을 0(현금)으로: 원문 p.512 '4월 첫 거래일부터 다음연도 3월 마지막 거래일까지'."""
    o = 포.실행(cfg)
    g = 포.기준일(cfg)
    rb = pd.DatetimeIndex(sorted(o["보유"][("동일", "상위30")]))
    앞날 = pd.DatetimeIndex([P.index[P.index.get_loc(t) - 1] for t in rb[1:]])
    ga = g.union(앞날)
    Ra = 포.쓰지말것칸(포.기간수익률(읽기.상장가격(cfg["가격"]), ga), cfg["가격"])
    Ra.loc[rb[1:]] = 0.0
    return 포.보유(Ra, o["보유"][("동일", "상위30")], cfg["거래비용"], cfg["전량교체"])
판C = {"기본(노트북 본문)": lambda c: 포.실행(c)["수익률"][("동일", "상위30")],
       "3월 말→4월 첫 거래일 하루 비보유": 하루비보유,
       "거래세 매수에도": lambda c: 포.실행({**c, "거래비용": {**c["거래비용"], "수수료": c["거래비용"]["수수료"] + c["거래비용"]["거래세"], "거래세": 0}})["수익률"][("동일", "상위30")],
       "TR(배당 포함) 가격": lambda c: 포.실행({**c, "가격": 읽기.TR})["수익률"][("동일", "상위30")],
       "재무 = 발표일 다음 날(확인판)": lambda c: 포.실행({**c, "재무시점": ("발표일", 150)})["수익률"][("동일", "상위30")],
       "거래비용 0": lambda c: 포.실행({**c, "거래비용": dict(수수료=0, 거래세=0, 슬리피지=0)})["수익률"][("동일", "상위30")]}
if 읽기.있음("FP56000300"):  # 세전이익 잠정치(R55, 회원 결정 15:13): 01 확인판으로만, 잠정치 있는 종목만
    잠정 = {"EY": "EY_잠정", "ROC": "ROC_잠정"}
    판C["세전이익 = 잠정치(FP56000300, 있는 종목만)"] = lambda c: 포.실행({**c, "지표": [(잠정.get(m, m), *r) for m, *r in c["지표"]]})["수익률"][("동일", "상위30")]
crow = {}
for 이름, cfg in {"MF": 기본, "IMF": IMF}.items():
    for 판, f in 판C.items():
        crow[(이름, 판)] = cum(f(cfg))
Cc = pd.Series(crow).unstack(0)
Cc.loc["원문 누적(표 2)"] = pd.Series({"MF": 9.8035, "IMF": 10.2791})
print("\n## C. 설정별 전체 기간 누적(배)\n", Cc.round(4).to_string())
Cc.to_csv(OUT / "01_진단_설정.csv", encoding="utf-8-sig")
