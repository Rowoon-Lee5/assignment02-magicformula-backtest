"""2차 진단 4번: NH(2018) '주요 재무제표 수치는 분기/연간 재무제표가 발표되는 월의 월말에 반영'(02 p.14, 03 p.18) 대 본문(분기 발표일 다음 날부터).
두 규칙이 다른 칸 = 발표일이 그 달 마지막 거래일 이상(마지막 거래일 당일 또는 그 뒤 같은 달 휴일)인 분기 행. 원문은 그 달 말 리밸런싱에 쓰고, 본문은 다음 리밸런싱부터 쓴다.
02(매달 리밸런싱, 2002-03~2018-05)·03(3·6·9·12월 말, 2002-03~2018-09) 기간 안에서 센다. 값은 바꾸지 않는다.
실행: 공통 폴더에서 python ../_검증/2차_04_발표월말_칸수.py > ../_검증/2차_04_발표월말_칸수_결과.txt"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import pandas as pd

import 데이터읽기 as 읽기
import 포트폴리오 as 포

f = 포.분기가능일().dropna(subset=["발표일"])
d = 읽기.지수()["I.001"].dropna().index.to_series()
마지막 = d.groupby(d.dt.to_period("M")).max()  # 달마다 마지막 거래일(코스피 지수 있는 날)
m = f["발표일"].dt.to_period("M")
f = f.assign(달=m, 그달마지막거래일=m.map(마지막))
다름 = f[f["발표일"] >= f["그달마지막거래일"]]
print("분기 행(발표일 있음):", len(f), "/ 발표일 ≥ 그 달 마지막 거래일:", len(다름), f"({len(다름) / len(f):.4%})")
print("  그중 마지막 거래일 당일:", int((다름["발표일"] == 다름["그달마지막거래일"]).sum()), "/ 그 뒤 같은 달 휴일:", int((다름["발표일"] > 다름["그달마지막거래일"]).sum()))
for 이름, a, b, 달들 in [("02", "2002-03", "2018-05", range(1, 13)), ("03", "2002-03", "2018-09", (3, 6, 9, 12))]:
    x = 다름[(다름["달"] >= pd.Period(a, "M")) & (다름["달"] <= pd.Period(b, "M")) & 다름["달"].dt.month.isin(list(달들))]
    print(f"\n{이름} 기간·리밸런싱 달 안 (KOSPI·KOSDAQ 구분 없이 분기 파일 전 종목): {len(x)}행, 종목 {x['코드'].nunique()}개")
    print(x.groupby(x["달"].dt.month).size().rename("달별 행 수").to_string())
    print(x.groupby(x["달"].dt.year).size().rename("해별 행 수").to_string())
