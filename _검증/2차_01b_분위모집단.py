"""2차 진단 1(d) 다시(독립 대조 HIGH 반영): 01 시총 분위 모집단 = 원문 '표본'.
원문 근거(쪽 그림으로 확인): p.513 '4.1 전 종목 대상 수익률 분석 결과' 바로 아래 'Fig. 1은 표본 전체를 대상으로'(전 종목 = 표본 전체),
p.510 '전체 표본대상을 시가총액 기준 5분위로 나누어', p.512 '필요한 재무자료 및 개별증권자료를 입수 가능한 기업들을 분석 대상으로 하며,
거래일 기준 시점에 거래중지 중이면 표본에서 제외하였다'. → 분위는 '자료 입수 가능' 기업으로 나눈다. 어느 자료가 '필요한' 것인지는 원문에 없어 세 가지로 읽는다:
  (가) 전략별: MF는 ROC·EY, IMF는 GPA·EY 자료가 있는 종목(p.513 IMF 'GP/A를 적용하고, 기타 사항은 마법공식과 동일하다')
  (나) 공통: ROC·EY·GPA 모두 있는 종목(Table 1이 표본 수 하나 → MF·IMF 같은 표본). 이 읽기면 전 종목 상위 30도 같은 표본에서 골라야 함
  (다) IMF도 MF 표본: ROC·EY 있는 종목으로 나누고 IMF 순위(GPA·EY 없는 종목은 순위에서 빠짐)
비교용: 예전 본문(남은 종목, 자료 유무 안 봄). 분위 1~5와 전 종목 상위 30, MF·IMF 누적(배). 원문 Table 2~7(p.514~516).
실행: 공통 폴더에서 python ../_검증/2차_01b_분위모집단.py [--짧게] > ../_검증/2차_01b_분위모집단_결과.txt"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import pandas as pd

import 포트폴리오 as 포

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
OUT = Path(__file__).resolve().parent
T0 = time.time()
짧게 = "--짧게" in sys.argv
기간 = ("2004-04", "2007-03") if 짧게 else ("2004-04", "2022-03")
MF = {**포.우동호2023, "기간": 기간, "끝": "마지막거래일"}
IMF = {**MF, "이름": "우동호2023_IMF", "지표": [("GPA", "높게"), ("EY", "높게")]}
있음 = lambda ms: [("지표있음", {"지표들": ms})]
읽기 = {"예전 본문(남은 종목)": {"MF": [], "IMF": []},
        "(가) 전략별 자료 있음": {"MF": 있음(["ROC", "EY"]), "IMF": 있음(["GPA", "EY"])},
        "(나) ROC·EY·GPA 모두 있음": {"MF": 있음(["ROC", "EY", "GPA"]), "IMF": 있음(["ROC", "EY", "GPA"])},
        "(다) IMF도 MF 표본(ROC·EY 있음)": {"MF": 있음(["ROC", "EY"]), "IMF": 있음(["ROC", "EY"])}}
원문표 = pd.read_csv(OUT.parent / "결과_월수익률" / "01_원문대조.csv", header=[0, 1], index_col=[0, 1])[("Return", "원문")]  # 0단계에서 PDF와 대조한 원문 칸
원문 = {(n, "전 종목" if g == "전체" else g.replace("시총", "")): v for (g, n), v in 원문표.items()}
rows = {}
for k, d in 읽기.items():
    for n, cfg in {"MF": MF, "IMF": IMF}.items():
        for g in ["전 종목"] + [f"{q}분위" for q in (range(1, 6) if not 짧게 else [1])]:
            ex = cfg["제외"] + d[n] + ([] if g == "전 종목" else [("시총분위", {"분위": int(g[0])})])
            o = 포.실행({**cfg, "제외": ex})
            r = o["수익률"][("동일", "상위30")]
            rows[(k, n, g)] = {"누적(배)": float((1 + r.dropna()).prod() - 1), "첫 해 남은 수(분위 뒤)": int(o["기록"]["시총분위" if g != "전 종목" else ("지표있음" if d[n] else "거래정지")].iloc[0]),
                               "원문": 원문.get((n, g))}
        print(k, n, f"{time.time() - T0:.0f}초", flush=True)
T = pd.DataFrame(rows).T
T.index.names = ["읽기", "전략", "묶음"]
print("\n## 분위 모집단 읽기별 누적(배) — 원문 Table 2~7\n", T.to_string())
print("\n## 누적만(행 = 전략·묶음, 열 = 읽기)\n", T["누적(배)"].unstack(0).round(4).to_string())
if not 짧게:
    T.to_csv(OUT / "2차_01b_분위모집단.csv", encoding="utf-8-sig")
print(f"\n걸린 시간 {time.time() - T0:.0f}초")
