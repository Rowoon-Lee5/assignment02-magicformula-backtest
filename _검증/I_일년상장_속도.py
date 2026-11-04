"""추가 지시 I: 재료()의 일년상장을 시장구분 범주형 표 isin(기준일마다) → 한 번 만든 bool 표(읽기.상장중)로 바꿔도 값이 같은지, 시간.
02 기간(2002-03~2018-05, 월말) 모든 기준일 × 그날 상장 가격 있는 종목(TR·수정주가 둘 다)에서 비교.
공통/에서 PYTHONPATH=. 로 실행 → _검증/I_일년상장_속도_결과.txt"""
import time
import pandas as pd
import 데이터읽기 as 읽기
import 포트폴리오 as 포

g = 포.기준일({**포.기본설정, "기간": ("1990-04", "2026-09"), "기준일": "마지막거래일"})
읽기.상장중()
다름, 칸, ta, tb = 0, 0, 0.0, 0.0
for item in (읽기.TR, 읽기.수정주가):
    P = 읽기.상장가격(item)
    for t in g[:-1]:
        p = P.loc[:t]
        codes = p.columns[p.iloc[-1].notna()]
        a = t - pd.DateOffset(years=1)
        t0 = time.time(); A = 읽기.일간(읽기.시장구분).loc[a:t].reindex(columns=codes).isin(["KS", "KQ"]).all(); ta += time.time() - t0
        t0 = time.time(); B = 읽기.상장중().loc[a:t].reindex(columns=codes, fill_value=False).all(); tb += time.time() - t0
        다름 += int((A != B).sum()) + int(not A.index.equals(B.index)); 칸 += len(A)
print(f"기준일 {len(g) - 1}개 × 가격 2개, 비교 종목-기준일 {칸}, 값이나 순서 다름 {다름}")
print(f"옛 {ta:.1f}초, 새 {tb:.1f}초")
