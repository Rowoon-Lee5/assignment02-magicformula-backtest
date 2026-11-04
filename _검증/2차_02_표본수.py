"""2차 진단 2번(지시 2026-11-05): 01 우동호(2023) 표본 수(Table 1 Number, p.512) 대 우리 순위 매긴 수.
1) 해마다 거르기 단계별 남은 수(본문 설정 그대로)와 원문 Number.
2) 마지막 단계(ROC·EY 둘 다 있음)에서 빠진 종목이 어느 재무 항목이 비어서 빠졌는지(항목별 빈 수, 재무 행 자체가 없는 수).
3) 확인판(원문에 없는 조건 — 본문에 넣지 않음): 관리종목·자본잠식·직전 1년 상장·종가 1,000원 미만을 하나씩 더했을 때 순위 매긴 수. 돌린 것 전부 적음.
설정은 노트북 본문 그대로(포.우동호2023, 기간 2004-04~2022-03). 값은 바꾸지 않는다.
실행: 공통 폴더에서 python ../_검증/2차_02_표본수.py [--짧게] > ../_검증/2차_02_표본수_결과.txt"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import numpy as np
import pandas as pd

import 종목거르기
import 지표
import 포트폴리오 as 포

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
OUT = Path(__file__).resolve().parent
T0 = time.time()
짧게 = "--짧게" in sys.argv
기본 = {**포.우동호2023, "기간": ("2004-04", "2022-03"), "끝": "마지막거래일"}
표1 = pd.read_csv(OUT / "01_원문표1.csv", index_col="연도")
reb = 포.기준일(기본)[:-1][::12]
if 짧게:
    reb = reb[[0, 1, 2, -2, -1]]
항목 = {"세전이익": 지표.세전이익, "이자비용": 지표.이자비용, "유동자산": 지표.유동자산, "유동부채": 지표.유동부채, "자산총계": 지표.자산,
        "무형자산": 지표.무형자산, "부채총계": 지표.부채, "현금": 지표.현금}
확인판 = {"+관리종목 제외": "관리종목", "+자본잠식 제외(자본총계 ≤ 0)": "자본잠식", "+종가 1,000원 미만 제외": "동전주"}


def 순위수(s, c):
    v = pd.DataFrame({m: getattr(지표, m)(s).reindex(c) for m in ["ROC", "EY"]}).replace([np.inf, -np.inf], np.nan).dropna()
    return v.index


단계, 빈, 확 = [], [], []
for t in reb:
    s, c, n = 포.거르기(t, 기본)
    r = 순위수(s, c)
    단계.append({"연도": t.year, **n, "ROC·EY 있음(순위 매김)": len(r)})
    빠짐 = c.difference(r)
    f = s["fin"].reindex(빠짐)
    row = {"연도": t.year, "빠진 수": len(빠짐), "재무 행 없음": int(f["회계연도"].isna().sum())}
    for k, code in 항목.items():
        row[f"{k} 빈칸"] = int(f[code].isna().sum())
    row["시가총액 빈칸"] = int(s["mcap"].reindex(빠짐).isna().sum())
    row["값은 있으나 ±inf(분모 0)"] = int(len(빠짐) - pd.DataFrame({m: getattr(지표, m)(s).reindex(빠짐) for m in ["ROC", "EY"]}).isna().any(axis=1).sum())
    # 이자비용만 비고 나머지는 다 있는 수(이자비용 0 미기록 의심, README 한계 — 값은 만들지 않음)
    다른 = [code for k, code in 항목.items() if k != "이자비용"]
    row["이자비용만 빈칸"] = int((f[지표.이자비용].isna() & f[다른].notna().all(axis=1) & s["mcap"].reindex(빠짐).notna()).sum())
    빈.append(row)
    for 이름, flt in 확인판.items():
        c2 = getattr(종목거르기, flt)(s, c)
        확.append({"연도": t.year, "판": 이름, "순위 매김": len(순위수(s, c2))})
    c3 = c[s["일년상장"].reindex(c).fillna(False).to_numpy()]
    확.append({"연도": t.year, "판": "+직전 1년 내내 상장", "순위 매김": len(순위수(s, c3))})
    print(f"{t.date()} {time.time() - T0:.0f}초", flush=True)

A = pd.DataFrame(단계).set_index("연도")
A.insert(0, "원문 Number(p.512)", 표1["Number"].reindex(A.index))
A["원문 − 우리"] = A["원문 Number(p.512)"] - A["ROC·EY 있음(순위 매김)"]
print("\n## 1) 해마다 거르기 단계별 남은 수(본문) vs 원문 Table 1 Number\n", A.to_string())
B = pd.DataFrame(빈).set_index("연도")
print("\n## 2) 마지막 단계에서 빠진 종목의 빈 항목(한 종목이 여러 칸에 셀 수 있음)\n", B.to_string())
C = pd.DataFrame(확).pivot(index="연도", columns="판", values="순위 매김")
C.insert(0, "본문", A["ROC·EY 있음(순위 매김)"]); C.insert(0, "원문 Number(p.512)", A["원문 Number(p.512)"])
print("\n## 3) 확인판(원문에 없는 조건, 본문 아님) 순위 매긴 수 — 돌린 것 전부\n", C.to_string())
D = C.drop(columns="원문 Number(p.512)").rsub(C["원문 Number(p.512)"], axis=0)
print("\n원문 − 판 (해마다)\n", D.to_string(), "\n\n평균 |원문 − 판|:\n", D.abs().mean().round(1).to_string())
if not 짧게:
    A.to_csv(OUT / "2차_02_단계별.csv", encoding="utf-8-sig"); B.to_csv(OUT / "2차_02_빠진항목.csv", encoding="utf-8-sig"); C.to_csv(OUT / "2차_02_확인판.csv", encoding="utf-8-sig")
print(f"\n걸린 시간 {time.time() - T0:.0f}초")
