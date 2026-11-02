"""성과 평가: 누적·연환산 수익률, 표준편차, 샤프, MDD(최대낙폭), 정보비율, CAPM·FF3·Carhart 알파(t는 OLS와 Newey-West).
'초과평균'은 설명변수 없는 회귀 = 월평균 초과수익률과 그 t."""
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
    """알파(월)와 t(OLS), t(Newey-West, 시차 = floor(4(T/100)^(2/9)))."""
    d = X.assign(_y=y).dropna()
    Xc = sm.add_constant(d.drop(columns="_y"), has_constant="add")
    m = sm.OLS(d["_y"], Xc)
    ols, nw = m.fit(), m.fit(cov_type="HAC", cov_kwds={"maxlags": int(4 * (len(d) / 100) ** (2 / 9))})
    return ols.params["const"], ols.tvalues["const"], nw.tvalues["const"]


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
        out[f"{name} α(월)"], out[f"{name} t(OLS)"], out[f"{name} t(NW)"] = 회귀(ex, F[cols])
    return out


def 성과표(R, F, 롱숏열=()):
    """R: 열마다 월수익률. 표 한 장(행=전략)."""
    return pd.DataFrame({k: 성과(R[k], F, k in 롱숏열) for k in R}).T


def 누적그림(R, 제목):
    """누적수익률. 흑백으로도 구분되게 선 모양·표식을 다르게."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    styles = [("-", None), ("--", None), (":", None), ("-.", None), ("-", "o"), ("--", "s"), (":", "^"), ("-.", "x")]
    for (ls, mk), k in zip(styles * 4, R):
        ax.plot((1 + R[k].dropna()).cumprod(), color="black" if ls == "-" else "dimgray", ls=ls, marker=mk, markevery=6, ms=4, lw=1.2, label=str(k))
    ax.set(title=제목, ylabel="누적 가치(시작=1)")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    return fig


결과폴더 = Path(__file__).resolve().parent.parent / "결과_월수익률"
구간들 = {"전체": (None, None), "1990-04~2004-03": ("1990-04", "2004-03"), "2004-04~2017-03": ("2004-04", "2017-03"), "2017-04~": ("2017-04", None)}


def 구간(r, a, b):
    """보유 월로 자른다. 기준일 간 수익률의 보유 월 = (구간 끝 − 15일)의 달(첫거래일·마지막거래일 기준일 모두 맞음)."""
    m = (r.index - pd.Timedelta(days=15)).to_period("M")
    return r[(m >= pd.Period(a or "1900-01", "M")) & (m <= pd.Period(b or "2999-12", "M"))]


def 저장(R, F, 이름, 롱숏=()):
    """요약표용: 월수익률(열 = (전략, 가중))과 요인을 결과_월수익률/이름.pkl로 남긴다."""
    결과폴더.mkdir(exist_ok=True)
    pd.to_pickle(dict(R=R, F=F, 롱숏=list(롱숏)), 결과폴더 / f"{이름}.pkl")


def 요약(최소개월=24):
    """결과_월수익률의 모든 전략 × 가중 × 기간: 평균(월 초과수익)과 t(NW), 샤프, MDD, Carhart 알파와 t(NW). 최소개월 미만 구간은 뺀다."""
    rows = {}
    for f in sorted(결과폴더.glob("*.pkl")):
        d = pd.read_pickle(f)
        for k, r in d["R"].items():
            for g, (a, b) in 구간들.items():
                x = 구간(r.dropna(), a, b)
                if len(x) >= 최소개월:
                    o = 성과(x, d["F"], k in d["롱숏"])
                    rows[(f.stem, *k, g)] = {"보유 첫 달": f"{x.index[0] - pd.Timedelta(days=15):%Y-%m}", "보유 끝 달": f"{x.index[-1] - pd.Timedelta(days=15):%Y-%m}",
                                             "개월": o["개월"], "평균(월 초과)": o["초과평균 α(월)"], "평균 t(NW)": o["초과평균 t(NW)"], "샤프": o["샤프"],
                                             "MDD": o["MDD"], "Carhart α(월)": o["Carhart α(월)"], "α t(NW)": o["Carhart t(NW)"]}
    return pd.DataFrame(rows).T.rename_axis(["파일", "전략", "가중", "기간"])
