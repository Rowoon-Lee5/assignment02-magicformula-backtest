"""F01(2026-11-06 c): 우동호 외(2023) p.513 요인을 포.원문요인으로 전 기간 만들고 DataGuide 2×3 요인지수와 비교.
실행: python F01_원문요인.py [--시험]  (시험 = 2004-04~2005-06, 저장 경로 _검증/1106/시험결과)
저장: _캐시/원문요인_우동호2023.pkl (DataFrame, 열 SMB·HML·MOM, 행 = 기준일 간 구간 끝), 결과 글 _검증/1106/F01_원문요인_결과.txt"""
import sys, time
from pathlib import Path

루트 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(루트 / "공통"))
import numpy as np, pandas as pd
import 데이터읽기 as 읽기, 지표, 포트폴리오 as 포, 평가

시험 = "--시험" in sys.argv
T0 = time.time()
print("시작", time.strftime("%Y-%m-%d %H:%M:%S"), "시험" if 시험 else "전 기간")
cfg = {**포.우동호2023, **({"기간": ("2004-04", "2005-06")} if 시험 else {})}
print("설정 기간", cfg["기간"], "제외", cfg["제외"], "가격", cfg["가격"], "재무시점", cfg["재무시점"])

# 원문요인 안에서 부르는 실행 결과(기록·보유)도 받아 두려고 감쌈(원문요인 코드는 그대로)
잡음 = {}
원래실행 = 포.실행
포.실행 = lambda c: 잡음.setdefault("r", 원래실행(c))
F = 포.원문요인(cfg)
포.실행 = 원래실행
print(f"원문요인 끝 {time.time() - T0:.0f}초, 행 {len(F)}")

out = (루트 / "_검증/1106/시험결과") if 시험 else (루트 / "_캐시")
out.mkdir(parents=True, exist_ok=True)
F.to_pickle(out / ("원문요인_우동호2023_시험.pkl" if 시험 else "원문요인_우동호2023.pkl"))
기록 = 잡음["r"]["기록"]
기록.to_csv(out / ("원문요인_기록_시험.csv" if 시험 else "원문요인_기록.csv"), encoding="utf-8-sig")

# DataGuide 2×3 요인지수(평가.요인)와 같은 구간
grid = 포.기준일({**cfg, "리밸런싱": 1})
D = 평가.요인(grid, cfg)
rows = {}
for k in ("SMB", "HML", "MOM"):
    a, b = F[k], D[k]
    m, t, _ = 평가.회귀(a.dropna(), pd.DataFrame(index=a.dropna().index))
    mb, tb, _ = 평가.회귀(b.dropna(), pd.DataFrame(index=b.dropna().index))
    d = 평가.평균차이(a, b)
    rows[k] = {"월수": a.notna().sum(), "원문요인 평균(월)": m, "원문요인 t(OLS)": t, "원문요인 SD(월)": a.std(),
               "DataGuide 평균(월)": mb, "DataGuide t(OLS)": tb, "DataGuide SD(월)": b.std(),
               "상관": a.corr(b), "평균 차이(월)": d["평균 차이(월)"], "차이 t(OLS)": d["t(OLS)"]}
표 = pd.DataFrame(rows).T
pd.set_option("display.width", 250)
print("\n[원문요인 vs DataGuide 2×3 요인지수, 월(기준일 간) 수익률]")
print(표.round(4).to_string())
print("\n[원문요인끼리 상관]"); print(F.corr().round(3).to_string())
print("\n[DataGuide끼리 상관]"); print(D[["SMB", "HML", "MOM"]].corr().round(3).to_string())
print("\n[MKT(KOSPI − RF)와 상관] 원문요인:", F.corrwith(D["MKT"]).round(3).to_dict(), " DataGuide:", D[["SMB", "HML", "MOM"]].corrwith(D["MKT"]).round(3).to_dict())

# 묶음 크기(30% 반올림)·빈칸으로 빠진 종목 수
열 = [c for c in 기록.columns if c.startswith(("편입:", "빈칸으로 빠짐:"))] + [c for c in 기록.columns if not c.startswith(("편입:", "빈칸", "보유수", "확인"))]
print("\n[기준일마다 종목 수: 최소·중앙값·최대]")
print(기록[열].astype(float).agg(["min", "median", "max"]).T.round(0).to_string())

# 확인: 음(−)의 장부가(BP < 0) 종목 수(HML 하위 30%에 들어감), 모멘텀11 창
t0 = grid[0]
s, c, _ = 포.거르기(t0, {**cfg, "재무연도": "최근"})
bp = 지표.BP(s).reindex(c)
print(f"\n[확인 {t0.date()}] 거른 종목 {len(c)}, BP 있음 {bp.notna().sum()}, BP<0 {(bp < 0).sum()}, 모멘텀11 있음 {지표.모멘텀11(s).reindex(c).notna().sum()}, 시총 있음 {s['mcap'].reindex(c).notna().sum()}")
fy = s["fin"].reindex(c)["회계연도"].value_counts().sort_index()
print("  쓴 재무 회계연도:", fy.to_dict())
if not 시험:
    t1 = grid[grid.month == 1][-1]  # 1월: '최근'이면 t−2 회계연도를 씀
    s1, c1, _ = 포.거르기(t1, {**cfg, "재무연도": "최근"})
    print(f"[확인 {t1.date()}] 쓴 재무 회계연도:", s1["fin"].reindex(c1)["회계연도"].value_counts().sort_index().tail(4).to_dict())
    print("[해마다 평균(월)] 원문요인"); print(F.groupby(F.index.year).mean().round(4).T.to_string())
print(f"\n끝 {time.strftime('%Y-%m-%d %H:%M:%S')} ({time.time() - T0:.0f}초)")
