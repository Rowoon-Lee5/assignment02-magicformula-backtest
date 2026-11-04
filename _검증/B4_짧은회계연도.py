"""README 한계 '짧은 회계연도 283 대 325'(감독 #62): H1 확인(결산일 값 ≠ 회계연도 첫 영업일 값 → 빈칸) 앞·뒤로 자산총계가 있는 짧은 회계연도 행 수를 같은 식으로 센다.
연간재무()는 그대로 부르고, H1으로 빈칸이 된 칸만 따로 다시 뽑아(같은 식) 더한다. 공통/에서 PYTHONPATH=."""
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import 데이터읽기 as 읽기
import 지표

f = 읽기.연간재무()
item = 지표.자산
# 연간재무와 같은 식으로 결산일 값(a)만 다시 뽑음(H1 빈칸 처리 앞 값)
m = 읽기.일간(읽기.결산월)
last = m.index.to_series().groupby(m.index.to_period("M")).max()
e = m.loc[last].apply(lambda x: pd.to_numeric(x.astype(object))).stack().rename("CP10002200").reset_index()
e.columns = ["날짜", "코드", "CP10002200"]
e = e[e["CP10002200"] == e["날짜"].dt.month].sort_values(["코드", "날짜"]).reset_index(drop=True)
t = pq.read_table(읽기.파일(item))
d = t.take(pd.Index(t.column("날짜").to_pandas()).get_indexer(pd.DatetimeIndex(sorted(set(e["날짜"]))))).to_pandas().reindex(columns=m.columns)
a = d.to_numpy(float)[d.index.get_indexer(e["날짜"]), d.columns.get_indexer(e["코드"])]
assert len(e) == len(f) and (e["코드"].to_numpy() == f["코드"].to_numpy()).all()
앞 = pd.Series(a, f.index)
k = (f["회계연도"] + (f["CP10002200"] <= 5)) * 12 + f["CP10002200"]
gap = k - k.groupby(f["코드"]).shift()
기본 = f["CP10002200"].eq(12) & gap.lt(12)
for nm, 값 in {"H1 뒤(연간재무 값, README 283)": f[item], "H1 앞(결산일 원래 값)": 앞}.items():
    s = 기본 & 값.notna()
    print(f"{nm}: {int(s.sum())} / 개월별 {gap[s].astype(int).value_counts().sort_index().to_dict()}")
h1 = 기본 & 앞.notna() & f[item].isna()
print("차이 = 짧은 회계연도 중 H1이 자산총계를 빈칸으로 둔 행:", int(h1.sum()), "/ H1이 빈칸으로 둔 자산총계 전체:", 읽기.검사[item])
print(f.loc[h1, ["코드", "회계연도", "CP10002200"]].assign(개월=gap[h1].astype(int), 원래값=앞[h1]).head(15).to_string())
