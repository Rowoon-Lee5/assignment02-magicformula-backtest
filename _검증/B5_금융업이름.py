"""README 한계 '금융업 이름 규칙'(감독 #30) 전수 확인: 업종(CP10001090) 빈칸이라 이름 규칙으로 금융업 판정되는 종목-달 전부.
매달 첫 거래일, 시장구분 KS·KQ, 상장 가격 있음. 낱말마다 걸린 종목·달 수, 그날 WICS(CP10000600)와 비교. 공통/에서 PYTHONPATH=. 로 실행."""
import pandas as pd
import 데이터읽기 as 읽기
import 포트폴리오 as 포

import sys
기준 = sys.argv[1] if len(sys.argv) > 1 else "첫거래일"  # 04 Novy-Marx 판은 '마지막거래일'
g = 포.기준일({**포.기본설정, "기간": ("1990-01", "2026-09"), "기준일": 기준})
print("기준일:", 기준)
p = 읽기.상장가격(읽기.수정주가).loc[g]
krx = 읽기.일간(읽기.업종).reindex(index=g, columns=p.columns)
wics = 읽기.일간(읽기.WICS).reindex(index=g, columns=p.columns)
name = 읽기.종목정보()["코드명"].reindex(p.columns).str.replace(r"\(주\)|㈜", "", regex=True).str.strip()
낱말 = ["은행", "보험", "증권", "금융", "금고", "캐피탈", "카드", "저축", "신금", "리츠", "스팩", "지주$"]
빈 = p.notna() & krx.isna()
print(f"상장·가격 있음 종목-달 {int(p.notna().sum().sum())}, 그중 업종 빈칸 {int(빈.sum().sum())} (종목 {int(빈.any().sum())})")
rows = []
for w in 낱말:
    hit = name.str.contains(w, na=False)
    for c in hit[hit].index:
        m = 빈[c]
        if m.any():
            ww = wics[c][m].astype(object).dropna()
            rows.append(dict(낱말=w, 코드=c, 이름=name[c], 달수=int(m.sum()), 첫달=f"{m[m].index[0]:%Y-%m}", 끝달=f"{m[m].index[-1]:%Y-%m}",
                             그때_WICS=", ".join(sorted(set(map(str, ww)))) or "(빈칸)", 다른날_거래소업종=", ".join(sorted(set(map(str, krx[c].astype(object).dropna())))) or "(빈칸)"))
t = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500); pd.set_option("display.max_colwidth", 60)
print(t.groupby("낱말").agg(종목=("코드", "nunique"), 종목달=("달수", "sum")))
print(t.to_string())
t.to_csv(f"../_검증/B5_금융업이름_목록_{기준}.csv", index=False, encoding="utf-8-sig")

# 반대쪽: 업종 빈칸이고 그날 WICS가 '금융'인데 이름 규칙에 안 걸린 종목-달(놓친 금융업 후보)
걸림 = name.str.contains("|".join(낱말), na=False)
놓침 = 빈 & wics.astype(object).eq("금융") & ~걸림.reindex(p.columns).to_numpy()
x = 놓침.sum()[lambda v: v > 0]
print(f"업종 빈칸·WICS 금융·이름 규칙 안 걸림: 종목 {len(x)}, 종목-달 {int(x.sum())}")
print(pd.DataFrame({"이름": name[x.index], "달수": x, "다른날_거래소업종": [", ".join(sorted(set(map(str, krx[c].astype(object).dropna())))) or "(빈칸)" for c in x.index]}).to_string())
