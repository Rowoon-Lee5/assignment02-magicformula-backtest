"""새 일간(달력기준) 재무 파일의 값이 어느 회계연도 값인지 확인한다.
예전 연간재무(통합_연간재무.parquet, 원본)와 같은 종목·항목을 대조한다.
규칙 후보: 행(코드, 회계연도)의 결산일(포트폴리오.재무가능일과 같은 계산) 당일 또는 그 전 마지막 영업일의 일간 값.
사용: python 일간재무_대조.py M000901001 [M000904001 ...]"""
import sys
from pathlib import Path
import pandas as pd

NEW = Path(r"D:\26-2_데이터기반투자전략\과제02\data\통합_전체_202611")
OLD = Path(r"D:\26-2_데이터기반투자전략\과제02\data\통합_202611")
A = pd.read_parquet(OLD / "통합_연간재무.parquet").rename(columns=lambda c: c.rsplit("_", 1)[-1])  # 데이터읽기.연간재무()와 같은 이름
A = A.dropna(subset=["CP10002200"])
m = A["CP10002200"].astype(int)
A["결산일"] = pd.to_datetime((A["회계연도"] + (m <= 5)).astype(int).astype(str) + m.astype(str).str.zfill(2), format="%Y%m") + pd.offsets.MonthEnd(0)

for item in sys.argv[1:]:
    (f,) = NEW.glob(f"통합_일간_{item}_*.parquet")
    d = pd.read_parquet(f)
    a = A[["코드", "회계연도", "CP10002200", "결산일", item]].dropna(subset=[item])
    a = a[a["코드"].isin(d.columns) & (a["결산일"] >= d.index[0]) & (a["결산일"] <= d.index[-1])]
    pos = d.index.searchsorted(a["결산일"], side="right") - 1                       # 결산일 당일 또는 그 전 마지막 영업일
    col = d.columns.get_indexer(a["코드"])
    a = a.assign(일간=d.to_numpy()[pos, col])
    eq = (a["일간"] - a[item]).abs() <= 1e-6 * a[item].abs().clip(lower=1)
    print(f"{f.name}: 비교 {len(a)}, 같음 {eq.sum()} ({eq.mean():.5f}), 일간 빈칸 {a['일간'].isna().sum()}")
    print(a.assign(같음=eq).groupby("CP10002200")["같음"].agg(["size", "mean"]).T.round(3).to_string())
    print(a[~eq & a["일간"].notna()].head(6).to_string())
