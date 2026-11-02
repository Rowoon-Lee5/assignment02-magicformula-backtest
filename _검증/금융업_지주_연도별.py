"""감사 #4: 매년 4월 첫 거래일, 상장(KS·KQ) 보통주 중 금융업 거르기(거래소 업종 + 이름 규칙)와 WICS 대분류 '금융'이 다른 종목 수.
사용: python _검증/금융업_지주_연도별.py > _검증/금융업_지주_연도별_결과.txt"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import 데이터읽기 as 읽기
import 종목거르기 as 거르
import 포트폴리오 as 포

이름 = 읽기.종목정보()["코드명"]
rows, 예 = {}, {}
for t in 포.기준일({**포.기본설정, "기간": ("1991-04", "2026-04")})[::12]:
    c = 읽기.상장가격(읽기.수정주가).columns[읽기.상장가격(읽기.수정주가).loc[t].notna()]
    c = c[c.str.endswith("0")]
    s = {"t": t}
    남음 = 거르.금융업(s, c)
    걸림 = c.difference(남음)
    w = 거르.그날(읽기.WICS, t, c)
    krx = 거르.그날(읽기.업종, t, c)
    a = 걸림[w.reindex(걸림).notna() & w.reindex(걸림).ne("금융")]  # 금융업으로 뺐는데 WICS는 금융 아님
    b = 남음[w.reindex(남음).eq("금융")]  # 안 뺐는데 WICS는 금융
    rows[t.year] = {"보통주": len(c), "금융업으로 뺌": len(걸림), "뺀 것 중 WICS 금융 아님": len(a), "그중 이름에 지주·홀딩스": int(이름.reindex(a).str.contains("지주|홀딩스").sum()),
                    "안 뺀 것 중 WICS 금융": len(b), "WICS 빈칸": int(w.isna().sum()), "업종 빈칸": int(krx.isna().sum())}
    if t.year in (2004, 2010, 2016, 2021, 2026):
        예[t.year] = (list(이름.reindex(a).head(8)), list(이름.reindex(b).head(8)), sorted(krx.reindex(걸림).dropna().unique())[:6])
print(pd.DataFrame(rows).T.to_string())
for y, (a, b, k) in 예.items():
    print(f"{y}: 뺐는데 WICS 금융 아님(앞 8) {a} | 안 뺐는데 WICS 금융(앞 8) {b} | 뺀 종목의 거래소 업종 값(앞 6) {k}")
