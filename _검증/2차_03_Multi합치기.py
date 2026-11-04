"""2차 진단 3번(지시 2026-11-05): 02 NH 밸류(2018) Multi-Metric 합치는 방법.
원문 정의(p.15, OCR): '5가지 지표의 Z-Score를 합산한 순위에 따라 선정한 종목의 1분위 Long Only 동일가중 포트폴리오' = 본문 z합산과 같음 → 본문 그대로.
원문에 없는 세부(빈 지표 처리, 극단값 처리, z 대신 순위)는 아래 판을 돌리기 전에 정해 두고(진행기록 01:45) 전부 결과를 적는다(확인판, 본문 아님).
  A 본문: z합산, 5지표 모두 있는 종목(=02 노트북, pkl과 같아야 함 → 스크립트 확인)
  B 순위합산, 5지표 모두 있는 종목(공통 코드 '순위합산')
  C z 평균, 있는 지표만(1개 이상)
  D 백분위 순위 평균, 있는 지표만(1개 이상)
  E z합산, 지표마다 z를 ±3에서 자름, 5지표 모두 있는 종목
판정 칸: 그림 19 정의(1분위 월평균/월표준편차)로 단일 지표 5개(02 pkl 본문 값)와 비교한 Multi의 순위, 같은 달만 비교한 순위.
공통 코드는 고치지 않는다: 이 스크립트 안에서만 포.점수를 감싸 새 합산 이름을 더함.
실행: 공통 폴더에서 python ../_검증/2차_03_Multi합치기.py [--짧게] > ../_검증/2차_03_Multi합치기_결과.txt"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import numpy as np
import pandas as pd

import 데이터읽기 as 읽기
import 포트폴리오 as 포

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
OUT = Path(__file__).resolve().parent
T0 = time.time()
짧게 = "--짧게" in sys.argv
기간 = ("2002-03", "2018-05")
기본 = {**포.기본설정, "이름": "NH밸류", "시장": ["KS"], "기간": 기간, "기준일": "마지막거래일", "리밸런싱": 1,
        "재무시점": ("발표월말", 150), "재무주기": ("분기", "4분기합"), "제외": [("거래정지", {"아이템": 읽기.정지여부}), "관리종목"],
        "고르기": ("분위", 5), "비중": ["동일"], "거래비용": dict(수수료=0, 거래세=0, 슬리피지=0)}  # 02 노트북 셀 '공통 설정' 그대로
지표명 = {"P/B": "BP", "P/E": "EP", "P/S": "SP", "P/OCF": "CFP", "EV/EBITDA": "EBITDA_EV"}
그림19 = pd.Series({"Multi-Metric": 0.39, "P/B": 0.34, "P/E": 0.32, "EV/EBITDA": 0.34, "P/S": 0.30, "P/OCF": 0.29})  # 원문 p.16 그림 19(0단계 대조와 같음)
원점수 = 포.점수


def 점수(v, 지표들, how):
    if how not in ("z평균_있는것", "백분위평균_있는것", "z합산_3자름"):
        return 원점수(v, 지표들, how)
    x = v * [1 if m[1] == "높게" else -1 for m in 지표들]
    if how == "z합산_3자름":
        x = x.dropna()
        return ((x - x.mean()) / x.std()).clip(-3, 3).sum(axis=1)
    x = x.dropna(how="all")
    if how == "z평균_있는것":
        return ((x - x.mean()) / x.std()).mean(axis=1)
    return x.rank(pct=True).mean(axis=1)


포.점수 = 점수
판 = {"A 본문: z합산(5지표 모두)": "z합산", "B 순위합산(5지표 모두)": "순위합산", "C z 평균(있는 지표만)": "z평균_있는것",
      "D 백분위 순위 평균(있는 지표만)": "백분위평균_있는것", "E z합산, z ±3 자름(5지표 모두)": "z합산_3자름"}
cfg = {**기본, "지표": [(m, "높게") for m in 지표명.values()]}
if 짧게:
    cfg["기간"] = ("2002-03", "2005-03")
    판 = {k: v for k, v in 판.items() if k[0] in "AC"}
Q = {}
for k, how in 판.items():
    o = 포.실행({**cfg, "합산": how})
    Q[k] = o["수익률"][("동일", "Q1")]
    print(f"{k}: {time.time() - T0:.0f}초, 1분위 첫 달 {Q[k].first_valid_index():%Y-%m}, {Q[k].count()}개월, 1분위 종목 수 첫/끝 {o['기록'].filter(like='편입:Q1').iloc[[0, -1], 0].tolist()}", flush=True)
Q = pd.DataFrame(Q)
pkl = pd.read_pickle(OUT.parent / "결과_월수익률" / "02_NH밸류.pkl")["R"]
단일 = pd.DataFrame({n: pkl[(f"NH밸류 {n} Q1", "동일")] for n in 지표명})
pk_multi = pkl[("NH밸류 Multi-Metric Q1", "동일")]
a = Q["A 본문: z합산(5지표 모두)"].reindex(pk_multi.index) if not 짧게 else Q["A 본문: z합산(5지표 모두)"]
차 = (a - pk_multi.reindex(a.index)).abs().max()
print(f"\n스크립트 확인: A판과 02 pkl Multi Q1 차이 최대 {차:.2e} (같아야 함, 같은 달 {int(a.notna().sum())}개)")
if 짧게:
    print(Q.head(15).to_string()); print(f"걸린 시간 {time.time() - T0:.0f}초"); sys.exit()

r = lambda x: x.mean() / x.std()
rows = {}
for k in Q:
    m = Q[k].reindex(단일.index)
    allx = pd.concat([단일, m.rename("Multi")], axis=1)
    전체 = allx.apply(lambda c: r(c.dropna()))
    같은 = allx.dropna()
    같은r = 같은.apply(r)
    rows[k] = {"Multi 비율(그림19 정의)": 전체["Multi"], "Multi 순위(6개 중, 각자 기간)": int(전체.rank(ascending=False)["Multi"]), "1위": 전체.idxmax(),
               "Multi 개월 수": int(m.count()), "첫 달": f"{m.first_valid_index():%Y-%m}",
               "같은 달만 Multi 비율": 같은r["Multi"], "같은 달만 Multi 순위": int(같은r.rank(ascending=False)["Multi"]), "같은 달만 1위": 같은r.idxmax(), "같은 달 수": len(같은),
               "Multi 1분위 누적": float((1 + m.dropna()).prod() - 1)}
T = pd.DataFrame(rows).T
print("\n## Multi 합치는 방법별(확인판, A만 본문) — 원문 그림 19 Multi 0.39 1위\n", T.to_string())
print("\n단일 지표(02 본문 pkl) 1분위 비율:", 단일.apply(lambda c: r(c.dropna())).round(4).to_dict())
print("원문 그림 19:", 그림19.to_dict())
T.to_csv(OUT / "2차_03_Multi합치기.csv", encoding="utf-8-sig")
print(f"\n걸린 시간 {time.time() - T0:.0f}초")
