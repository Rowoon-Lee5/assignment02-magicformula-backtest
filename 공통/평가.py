"""성과 평가: 누적·연환산 수익률, 표준편차, 샤프, MDD(최대낙폭), 정보비율, CAPM·FF3·Carhart 알파(t는 OLS. 2026-11-06 회원 결정으로 Newey-West t를 뺌, 원문에 없었음).
'초과평균'은 설명변수 없는 회귀 = 월평균 초과수익률과 그 t.
타겟 페이퍼 성과표 지표(서브에이전트가 원문 PDF로 확인, 진행기록 2026-11-03 04:50): 우동호 외(2023) 표 2~7(p.514–516) = 누적·MDD·표준편차·샤프·정보비율·젠센·3요인·4요인 α(t)
→ 위 칸들. Novy-Marx(NBER w15940, 2010년 4월판) 표 = 월평균 초과수익률·α·요인 적재값(β)·adj.-R² → '초과평균 α(월)'·'Carhart β:요인'·'Carhart adj R²' 칸."""
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

import 데이터읽기 as 읽기

plt.rcParams.update({"font.family": "Malgun Gothic", "axes.unicode_minus": False})

모형 = {"초과평균": [], "CAPM": ["MKT"], "FF3": ["MKT", "SMB", "HML"], "Carhart": ["MKT", "SMB", "HML", "MOM"]}


def 요인(grid, cfg):
    """기준일 간 요인 수익률(DataGuide 종가지수 비율). RF = 구간 시작 시점 금리/12. MKT = 시장지수 − RF."""
    r = 읽기.지수().reindex(grid).pct_change(fill_method=None)
    rf = 읽기.무위험(cfg["무위험"]).reindex(grid, method="ffill").shift(1)
    시장 = r[cfg["시장지수"]]
    return pd.DataFrame({"시장": 시장, "RF": rf, "MKT": 시장 - rf, "SMB": r["3FM.2B3.SMB"],
                         "HML": r["3FM.2B3.HML"], "MOM": r["3FM.2M3.MOM"]})


def 회귀(y, X):
    """알파(월)와 t(OLS), OLS 결과(β·adj R²용)."""
    d = X.assign(_y=y).dropna()
    Xc = sm.add_constant(d.drop(columns="_y"), has_constant="add")
    ols = sm.OLS(d["_y"], Xc).fit()
    if ols.rsquared > 1 - 1e-10:  # 시장 자기 자신 회귀(잔차 ≈ 0): t는 계산 오차라 빈칸(결과 감사 LOW 2026-11-03)
        return ols.params["const"], np.nan, ols
    return ols.params["const"], ols.tvalues["const"], ols


def 성과(r, F, 롱숏=False):
    """r: 월수익률. 롱숏이면 초과수익 = r 그대로(무비용 포트폴리오), 아니면 r − RF."""
    r = r.dropna()
    F = F.loc[r.index]
    ex = r if 롱숏 else r - F["RF"]
    w = (1 + r).cumprod()
    a = r - F["시장"]
    out = {"개월": len(r), "누적": w.iloc[-1] - 1, "연환산": w.iloc[-1] ** (12 / len(r)) - 1,
           "표준편차(연)": r.std() * np.sqrt(12), "샤프": ex.mean() / ex.std() * np.sqrt(12),
           "MDD": (w / w.cummax().clip(lower=1) - 1).min(), "정보비율": a.mean() / a.std() * np.sqrt(12) if a.std() else np.nan}  # 시장 자신은 a = 0
    for name, cols in 모형.items():
        out[f"{name} α(월)"], out[f"{name} t(OLS)"], ols = 회귀(ex, F[cols])
    out |= {f"Carhart β:{c}": ols.params[c] for c in cols} | {"Carhart adj R²": ols.rsquared_adj}  # 마지막 모형(Carhart)의 적재값
    return out


def 샤프차이(a, b):
    """두 월수익률의 (평균/표준편차) 차이 검정. Jobson·Korkie(1981) 식을 Memmel(2003)이 고친 식(두 원문 확인 안 함):
    z = (SR_a − SR_b) / √{[2(1−ρ) + ½(SR_a² + SR_b² − 2·SR_a·SR_b·ρ²)] / T}. 같은 달만 쓴다. p = 양측 정규."""
    from scipy.stats import norm
    d = pd.concat([a, b], axis=1).dropna()
    x, y = d.iloc[:, 0], d.iloc[:, 1]
    sa, sb, r, T = x.mean() / x.std(), y.mean() / y.std(), x.corr(y), len(d)
    z = (sa - sb) / np.sqrt((2 * (1 - r) + 0.5 * (sa ** 2 + sb ** 2 - 2 * sa * sb * r ** 2)) / T)
    return pd.Series({"월수": T, "a": sa, "b": sb, "차이": sa - sb, "z": z, "p": 2 * norm.sf(abs(z))})


def 평균차이(a, b):
    """두 월수익률 차이(a − b)의 평균과 t(OLS: 상수항만 있는 회귀의 보통 t), p(양측 정규)."""
    from scipy.stats import norm
    d = (a - b).dropna()
    m, t, _ = 회귀(d, pd.DataFrame(index=d.index))
    return pd.Series({"월수": len(d), "평균 차이(월)": m, "t(OLS)": t, "p": 2 * norm.sf(abs(t))})


def 성과표(R, F, 롱숏열=()):
    """R: 열마다 월수익률. 표 한 장(행=전략)."""
    return pd.DataFrame({k: 성과(R[k], F, k in 롱숏열) for k in R}).T


def 누적그림(R, 제목, 로그=True, 퍼센트=False, 오른쪽=None):
    """누적수익률. 흑백으로도 구분되게 선 모양·표식을 다르게. 세로축은 로그(README 한계 '선형 축', 2026-11-04).
    퍼센트=True: 원문 그림처럼 (누적 가치 − 1) × 100 %, 보통 축. 오른쪽 = {이름: 지수 값 Series}를 주면 오른쪽 축에 그 값을 그대로 그림(NH 그림 26·32 'KOSPI(우)')."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    styles = [(ls, mk) for mk in (None, "o", "s", "^", "x") for ls in ("-", "--", ":", "-.")]  # 20가지(선 9개 그림에서 둘이 겹치던 것, 결과 감사 LOW)
    for (ls, mk), k in zip(styles * (len(R.columns) // len(styles) + 1), R):  # 20개 넘으면 모양 반복(열은 빠지지 않음)
        w = (1 + R[k].dropna()).cumprod()
        ax.plot((w - 1) * 100 if 퍼센트 else w, color="black" if ls == "-" else "dimgray", ls=ls, marker=mk, markevery=6, ms=4, lw=1.2, label=str(k))
    if 퍼센트:
        ax.set(title=제목, ylabel="누적 수익률(%)")
    else:
        ax.set(title=제목, ylabel="누적 가치(시작=1, 로그 축)" if 로그 else "누적 가치(시작=1)", yscale="log" if 로그 else "linear")
    h, l = ax.get_legend_handles_labels()
    if 오른쪽:
        ax2 = ax.twinx()
        for k, v in 오른쪽.items():
            ax2.plot(v, color="gray", lw=0.8, alpha=0.7, label=f"{k}(우)")
        ax2.set_ylabel("지수(우)")
        h2, l2 = ax2.get_legend_handles_labels()
        h, l = h + h2, l + l2
    ax.legend(h, l, fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    return fig


def 일간정의(r, 시장, 무위험일):
    """우동호 외(2023) 표 2~7의 SD·Sharpe·IR·MDD를 원문 숫자가 나오는 정의로(원문에 정의 없음, KOSPI 원문 숫자로 역산 `_검증/01_정의역산.py`):
    일간 수익률 r, SD = 일 표준편차 × √N(N = 전 기간 일 수), Sharpe = 일 초과수익 평균/표준편차 × √N, IR = (r − 시장) 평균/표준편차 × √N, MDD = 일간 가치의 최대 낙폭.
    무위험일 = 그날 쓸 일 무위험수익률(직전 날 값을 씀)."""
    r = r.dropna()
    N, w = len(r), (1 + r).cumprod()
    e = r - 무위험일.reindex(r.index)
    a = r - 시장.reindex(r.index)
    return {"일 수": N, "누적": w.iloc[-1] - 1, "MDD": (w / w.cummax().clip(lower=1) - 1).min(), "SD": r.std() * np.sqrt(N),
            "Sharpe": e.mean() / e.std() * np.sqrt(N), "IR": a.mean() / a.std() * np.sqrt(N) if a.std() else 0.0}


결과폴더 = Path(__file__).resolve().parent.parent / "결과_월수익률"
구간들 = {"전체": (None, None), "1990-04~2004-03": ("1990-04", "2004-03"), "2004-04~2017-03": ("2004-04", "2017-03"), "2017-04~": ("2017-04", None)}


def 구간(r, a, b):
    """보유 월로 자른다. 기준일 간 수익률의 보유 월 = (구간 끝 − 15일)의 달(첫거래일·마지막거래일 기준일 모두 맞음)."""
    m = (r.index - pd.Timedelta(days=15)).to_period("M")
    return r[(m >= pd.Period(a or "1900-01", "M")) & (m <= pd.Period(b or "2999-12", "M"))]


def 저장(R, F, 이름, 롱숏=(), 이상값=None):
    """요약표용: 월수익률(열 = (전략, 가중))과 요인, 이상값 = {열: 포.이상값보유 건수}, 만든 코드의 git 커밋(커밋 안 된 변경 파일 목록 포함)을 결과_월수익률/이름.pkl로 남긴다."""
    결과폴더.mkdir(exist_ok=True)
    git = lambda *a: subprocess.run(["git", *a], cwd=결과폴더.parent, capture_output=True, text=True, encoding="utf-8").stdout.strip()  # 한글 파일 이름(utf-8)을 cp949로 읽다 깨지지 않게
    pd.to_pickle(dict(R=R, F=F, 롱숏=list(롱숏), 이상값=dict(이상값 or {}), 커밋=git("rev-parse", "HEAD"), 변경=git("status", "--porcelain", "--", "공통", "따라하기", "연구")), 결과폴더 / f"{이름}.pkl")


def 요약(최소개월=24):
    """결과_월수익률의 모든 전략 × 가중 × 기간: 평균(월 초과수익)과 t(OLS), 샤프, MDD, Carhart 알파와 t(OLS), 이상값 보유(전 기간 건수, 저장 때 안 준 파일은 빈칸). 최소개월 미만 구간은 뺀다."""
    rows = {}
    for f in sorted(결과폴더.glob("*.pkl")):
        d = pd.read_pickle(f)
        for k, r in d["R"].items():
            for g, (a, b) in 구간들.items():
                x = 구간(r.dropna(), a, b)
                if len(x) >= 최소개월:
                    o = 성과(x, d["F"], k in d["롱숏"])
                    rows[(f.stem, *k, g)] = {"보유 첫 달": f"{x.index[0] - pd.Timedelta(days=15):%Y-%m}", "보유 끝 달": f"{x.index[-1] - pd.Timedelta(days=15):%Y-%m}",
                                             "개월": o["개월"], "평균(월 초과)": o["초과평균 α(월)"], "평균 t(OLS)": o["초과평균 t(OLS)"], "샤프": o["샤프"],
                                             "MDD": o["MDD"], "Carhart α(월)": o["Carhart α(월)"], "α t(OLS)": o["Carhart t(OLS)"],
                                             "이상값 보유": d.get("이상값", {}).get(k, np.nan)}
    return pd.DataFrame(rows).T.rename_axis(["파일", "전략", "가중", "기간"])
