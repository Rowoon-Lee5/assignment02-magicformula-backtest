"""README 한계 '3월 결산 재무가 예전 원본과 다른 행'(감독 #51) 원인 분류. 새 = 읽기.연간재무()(H1 확인 뒤), 예전 = data\통합_202611\통합_연간재무.parquet(대조용, 읽기만).
3월 결산 (코드, 회계연도) 행에서 값이 다른 칸을: 새 = 예전 다음 회계연도 값 / 새 = 예전 앞 회계연도 값 / 그 밖 으로 나누고, 연도·종목별로 센다. 공통/에서 PYTHONPATH=."""
import pandas as pd
import 데이터읽기 as 읽기

OLD = 읽기.DATA.parent / "통합_202611" / "통합_연간재무.parquet"
A = pd.read_parquet(OLD).rename(columns=lambda c: c.rsplit("_", 1)[-1]).dropna(subset=["CP10002200"])
N = 읽기.연간재무()
items = ["M000901001", "M000903001", "M000904001", "M000902001", "M000907001", "M000909001"]  # 자산·자본·매출·부채·세전이익·영업CF
키 = ["코드", "회계연도", "CP10002200"]
a = A[A["CP10002200"] == 3].set_index(키)[items]
n = N[N["CP10002200"] == 3].set_index(키)[items]
a = a[~a.index.duplicated()]; n = n[~n.index.duplicated()]
both = a.index.intersection(n.index)
같 = lambda x, y: (x - y).abs() <= 1e-6 * y.abs().clip(lower=1)
rows, ex = {}, []
for it in items:
    x, y = n.loc[both, it], a.loc[both, it]
    ok = x.notna() & y.notna()
    eq = 같(x[ok], y[ok])
    bad = eq[~eq].index
    다음 = a[it].rename(index=lambda v: v - 1, level=1)  # (코드, 회계연도) → 예전 다음 회계연도 값
    앞 = a[it].rename(index=lambda v: v + 1, level=1)
    다음, 앞 = 다음[~다음.index.duplicated()], 앞[~앞.index.duplicated()]
    d1 = 같(x[bad], 다음.reindex(bad)).fillna(False)
    d0 = 같(x[bad], 앞.reindex(bad)).fillna(False)
    rows[it] = {"둘 다 값": int(ok.sum()), "같음": int(eq.sum()), "같음 비율": round(eq.mean(), 4), "다름": len(bad),
                "새 = 예전 다음 해": int(d1.sum()), "새 = 예전 앞 해": int((d0 & ~d1).sum()), "그 밖": int((~d0 & ~d1).sum()),
                "예전 값 있음·새 빈칸": int((y.notna() & x.isna()).sum())}
    ex.append(pd.DataFrame({"항목": it, "새": x[bad], "예전": y[bad], "예전 다음 해": 다음.reindex(bad).to_numpy(), "분류": ["다음 해" if p else ("앞 해" if q else "그 밖") for p, q in zip(d1, d0)]}, index=bad))
print("3월 결산 행 비교(새 연간재무 대 예전 통합_연간재무)")
print(pd.DataFrame(rows).T.to_string())
E = pd.concat(ex)
print("\n다른 칸 회계연도별(모든 항목):\n", E.reset_index().groupby(["회계연도", "분류"]).size().unstack(fill_value=0).to_string())
print("\n다른 칸 종목 수:", E.index.get_level_values(0).nunique(), "/ 다른 칸 많은 종목 10:\n", E.index.get_level_values(0).value_counts().head(10).to_string())
print("\n'그 밖' 예 15:\n", E[E["분류"] == "그 밖"].head(15).to_string())

# 1987 회계연도 3월 결산 행 전체 중 다른 칸 비율(H1이 확인 못 하는 첫 행: 데이터가 1988-01부터라 회계연도 첫 영업일 값이 없음)
r87 = both[both.get_level_values(1) == 1987]
print(f"\nFY1987 3월 결산 행 {len(r87)} 중 다른 칸이 있는 행 {E.index.unique().get_level_values(1).tolist().count(1987)}; FY1987 이 값을 쓰는 날: 결산일 1988-03-31 + 150일 = 1988-08, 2년 넘은 재무 안 씀 → 1990-03까지만(백테스트 첫 리밸런싱 1990-04 전)")
