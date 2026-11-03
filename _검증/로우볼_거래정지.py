"""최종 감사 MEDIUM: 거래정지 날 TR 일간수익률이 대부분 0이라 직전 12개월 변동성이 낮게 잡히는지, 03 로우볼 판정이 바뀌는지.
03 본문 설정 그대로, 변동성만 '거래정지(S410002600) 날 수익률을 빈칸으로 본' 확인판과 비교한다. 원본·공통 코드는 바꾸지 않는다.
사용: python _검증/로우볼_거래정지.py > _검증/로우볼_거래정지_결과.txt"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import 데이터읽기 as 읽기
import 지표
import 포트폴리오 as 포

정지 = 읽기.일간(읽기.정지구분).eq("거래정지")


def 변동성_정지빼기(s):
    r = s["ret"]
    return r.mask(정지.reindex(index=r.index, columns=r.columns, fill_value=False)).std().where(지표.일년상장(s))


지표.변동성_정지빼기 = 변동성_정지빼기
기본 = {**포.기본설정, "이름": "NH퀄리티로우볼", "시장": ["KS"], "기간": ("2002-03", "2018-09"), "기준일": "마지막거래일", "리밸런싱": 3,
        "재무시점": ("발표일", 150), "제외": [("거래정지", {"아이템": 읽기.정지여부}), "관리종목"],
        "고르기": ("분위", 5), "비중": ["동일"], "거래비용": dict(수수료=0, 거래세=0, 슬리피지=0)}  # 03 노트북 6번 칸과 같음
결과 = {n: 포.실행({**기본, "지표": [(m, "낮게")]}) for n, m in {"본문": "변동성", "정지 날 빼기": "변동성_정지빼기"}.items()}
LS = pd.DataFrame({n: o["수익률"]["동일"]["Q1"] - o["수익률"]["동일"]["Q5"] for n, o in 결과.items()})
print("로우볼 LS(Q1 − Q5) 누적:", ((1 + LS).prod() - 1).round(4).to_dict())
print("판정 '로우볼 LS 누적이 양(+)':", ((1 + LS).prod() - 1 > 0).to_dict())

rows = {}
for t, w in 결과["본문"]["보유"][("동일", "Q1")].items():
    창 = 정지.loc[t - pd.DateOffset(years=1):t].reindex(columns=w.index, fill_value=False).iloc[1:]
    n = 창.sum()
    w2 = 결과["정지 날 빼기"]["보유"][("동일", "Q1")][t]
    rows[t] = {"Q1 종목": len(w), "직전 1년 거래정지 1일 이상": int((n > 0).sum()), "20일 이상": int((n >= 20).sum()),
               "두 판 Q1이 다른 종목": len(w.index.symmetric_difference(w2.index))}
r = pd.DataFrame(rows).T
print(r.describe().loc[["mean", "max"]].round(2).to_string())
print("리밸런싱", len(r), "회 중 Q1에 직전 1년 20일 이상 거래정지 종목이 있던 회:", int((r["20일 이상"] > 0).sum()))
