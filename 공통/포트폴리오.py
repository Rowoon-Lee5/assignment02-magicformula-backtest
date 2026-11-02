"""포트폴리오 만들기와 보유. 노트북은 설정(dict)만 바꿔 `실행(설정)`을 부른다.
흐름(수업 노트북과 같음): 날짜×종목 표 → 월 기준일 → 기준일마다 거르기·지표·고르기·비중 → 다음 리밸런싱까지 매수보유 → 월수익률."""
from collections import defaultdict
from functools import cache

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

import 데이터읽기 as 읽기
import 종목거르기
import 지표

기본설정 = dict(
    시장=["KS", "KQ"],                 # 시장구분 CP10000300
    가격=읽기.TR,                       # 수익률 계산 가격: 읽기.TR(배당 포함) | 읽기.수정주가
    기간=("2004-04", "2006-12"),        # (첫 리밸런싱 월, 마지막 기준일 월)
    기준일="첫거래일",                  # 월 기준일: '첫거래일' | '마지막거래일'
    리밸런싱=12,                        # 몇 달마다 다시 고르나: 1 | 3 | 12 (사이에는 매수보유)
    재무시점=("결산후개월", 3),          # ('결산후개월', k): 결산일+k개월부터(발표일 안 봄) | ('발표일', k): 실적보고서발표일 다음 거래일부터(없으면 결산일+k일)
    제외=["보통주", "금융업", "투자기구", "거래정지"],  # 종목거르기 함수 이름, 또는 ('이름', {옵션})
    지표=[("ROC", "높게"), ("EY", "높게")],  # (지표 함수, 방향[, 단계별일 때 남길 비율])
    합산="순위합산",                    # '순위합산' | 'z합산' | '단계별'
    고르기=("상위N", 30),               # ('상위N', n) | ('분위', k): Q1이 가장 좋은 쪽
    비중=["동일"],                      # '동일' | '시총' | '시총상한' | '위험균형' | '최소분산'
    비중상한=0.1,                       # 시총상한에서만 씀
    거래비용=dict(수수료=0.00015, 거래세=0.0025, 슬리피지=0.005),  # 매수·매도마다 수수료+슬리피지, 매도에 거래세. 월비용=x를 넣으면 매달 x를 뺌(NH 현실판)
    전량교체=False,                     # True: 리밸런싱 때 전부 팔고 새로 삼(겹치는 종목도 비용) | False: 비중 바뀐 만큼만
    무위험="E11.02.003.001",            # 콜금리(1일물 중개거래). 1988년부터 빈 달 없는 것은 이것과 무담보콜(E11.02.003.002) 둘
    시장지수="I.001",                   # 코스피
)

# 우동호 외(2023) 재현 설정. 연구_틀의 비교 기준으로도 쓴다.
우동호2023 = {**기본설정, "이름": "우동호2023_MF", "기간": ("2004-04", "2022-04"),
              "제외": ["보통주", "금융업", "투자기구", ("결산월", {"월": 12}), "거래정지"], "무위험": "E11.02.003.008", "가격": 읽기.수정주가, "전량교체": True}


def 기준일(cfg):
    d = 읽기.일간(cfg["가격"]).index.to_series()
    g = d.groupby(d.dt.to_period("M"))
    g = g.min() if cfg["기준일"] == "첫거래일" else g.max()
    return pd.DatetimeIndex(g.loc[cfg["기간"][0]:cfg["기간"][1]].to_numpy())


@cache
def 재무가능일(how):
    """연간재무 행마다 결산일·발표일과 '쓸 수 있는 날'. 결산월은 회계연도별 이력(CP10002200).
    결산월 1~5월은 회계연도 다음 해에 끝난다(DataGuide 표기). 발표일이 결산일보다 이르면 믿지 않는다."""
    f = 읽기.연간재무().dropna(subset=["CP10002200"])
    m = f["CP10002200"].astype(int)
    end = pd.to_datetime((f["회계연도"] + (m <= 5)).astype(int).astype(str) + m.astype(str).str.zfill(2), format="%Y%m") + pd.offsets.MonthEnd(0)
    pub = pd.to_datetime(f["FP56000900"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce")
    pub = pub.where(pub > end)
    kind, k = how
    ok = end + pd.DateOffset(months=k) if kind == "결산후개월" else (pub + pd.Timedelta(days=1)).fillna(end + pd.Timedelta(days=k))
    return f.assign(결산일=end, 발표일=pub, 가능일=ok)


def 발표지연(키="CP10002200"):
    """12월 결산 연간 보고서의 결산일→실적보고서발표일 일수(발표일 > 결산일만)와 발표일 있는 비율. '발표일' 규칙의 k를 고른 근거.
    키="CP10002200": 결산월 이력이 12인 회계연도. 키="결산월": 정적 결산월 12(결산월을 바꾼 회사도 12월 31일로 계산 → 꼬리가 길어짐)."""
    f = 읽기.연간재무()
    f = f[(f[키] == 12) & f["M000901001"].notna()]  # 자산총계가 있는 행 = 보고서가 있는 회사-연도
    end = pd.to_datetime(f["회계연도"].astype(int).astype(str) + "1231")
    pub = pd.to_datetime(f["FP56000900"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce")
    d = (pub - end).dt.days.where(pub > end)
    구간 = pd.cut(f["회계연도"], [1986, 1994, 1999, 2004, 2010, 2026], labels=["1987~94", "1995~99", "2000~04", "2005~10", "2011~26"])
    표 = lambda x: pd.Series({"행": len(x), "발표일 있음": x.notna().mean(), "건수": x.count()} | ({} if x.count() == 0 else {
        "중앙값(일)": x.median(), "95%(일)": x.quantile(0.95), "99%(일)": x.quantile(0.99),
        **{f"{k}일 초과": (x > k).sum() / x.count() for k in (90, 150, 180)}}))
    return pd.concat({**{g: 표(x) for g, x in d.groupby(구간, observed=False)}, "전체": 표(d)}, axis=1).T


def 재무(t, how):
    """그날 쓸 수 있는 가장 최근 회계연도 행(종목마다 한 행). ponytail: 결산일이 2년보다 오래된 행은 안 씀(묵은 값 막기)."""
    f = 재무가능일(how)
    f = f[(f["가능일"] <= t) & (f["결산일"] >= t - pd.DateOffset(years=2))]
    return f.sort_values(["회계연도", "결산일"]).drop_duplicates("코드", keep="last").set_index("코드")  # F9: 같은 회계연도 두 결산월이면 늦은 결산일


def 다음리밸런싱(t, cfg):
    g = 기준일(cfg)
    return g[min(g.get_loc(t) + cfg["리밸런싱"], len(g) - 1)] if t in g else t


def 재료(t, cfg):
    """기준일 t의 자료: 그날 상장 가격(읽기.상장가격) 있는 종목, 재무, 시가총액, 직전 12개월 일간수익률(빈칸은 빈칸, '쓰지 말 것' 칸은 빈칸으로 봄).
    다음 = 다음 리밸런싱일(종목거르기.쓰지말것이 보유 구간을 봄), 일년상장 = 직전 12개월 내내 시장구분 KS·KQ."""
    p = 읽기.상장가격(cfg["가격"]).loc[:t]
    codes = p.columns[p.iloc[-1].notna()]
    a = t - pd.DateOffset(years=1)
    p = p.loc[a:, codes].copy()
    for c, x, y in 읽기.쓰지말것(cfg["가격"])[["코드", "시작", "끝"]].itertuples(index=False):
        if c in p:
            p.loc[x:y, c] = np.nan
    return dict(t=t, 다음=다음리밸런싱(t, cfg), 가격=cfg["가격"], codes=codes, fin=재무(t, cfg["재무시점"]).reindex(codes),
                mcap=읽기.일간(읽기.시총).loc[t, codes], ret=p.pct_change(fill_method=None).iloc[1:],
                일년상장=읽기.일간(읽기.시장구분).loc[a:t].reindex(columns=codes).isin(["KS", "KQ"]).all())


def 거르기(t, cfg):
    """재료 → 시장 → '쓰지 말 것' → 설정의 제외 순서로 거른다. (재료, 남은 종목, 단계별 수)."""
    s = 재료(t, cfg)
    return (s, *종목거르기.적용(s, [("시장", {"시장들": cfg["시장"]}), "쓰지말것"] + cfg["제외"]))


def 점수(v, 지표들, how):
    """v: 종목×지표 값. 높을수록 좋은 점수를 돌려준다. 지표 하나라도 빈 종목은 빠진다."""
    x = v.dropna() * [1 if m[1] == "높게" else -1 for m in 지표들]
    if how == "순위합산":
        return -x.rank(ascending=False).sum(axis=1)
    if how == "z합산":
        return ((x - x.mean()) / x.std()).sum(axis=1)
    for m, _, keep in 지표들:  # 단계별: 앞 지표부터 상위 keep만 남기고, 마지막 지표로 줄 세움
        x = x[x[m] >= x[m].quantile(1 - keep)]
    return x[m]


def 고르기(sc, how):
    kind, n = how
    if kind == "상위N":
        return {f"상위{n}": sc.nlargest(n).index}
    q = pd.qcut(sc.rank(method="first", ascending=False), n, labels=[f"Q{i}" for i in range(1, n + 1)])
    return {g: sc.index[q == g] for g in q.cat.categories}


# 비중: (종목, 재료, 설정) → 합 1인 Series
def 동일(c, s, cfg):
    return pd.Series(1 / len(c), c)


def 시총(c, s, cfg):
    m = s["mcap"][c]
    return m / m.sum()


def 시총상한(c, s, cfg):
    cap = cfg["비중상한"]
    assert cap * len(c) >= 1, "종목 수 × 상한 < 1"
    w = 시총(c, s, cfg)
    while w.max() > cap + 1e-12:
        over = w >= cap
        w[over] = cap
        w[~over] *= (1 - cap * over.sum()) / w[~over].sum()
    return w


def 이력(c, s):
    """위험 비중용 직전 12개월 수익률. 12개월 내내 상장된 종목만(지표.변동성과 같은 기준)."""
    r = s["ret"][c]
    return r.loc[:, 지표.일년상장(s)[c].to_numpy()]


def 위험균형(c, s, cfg):
    iv = 1 / 이력(c, s).std()
    return iv / iv.sum()


def 시총상한10(c, s, cfg):
    return 시총상한(c, s, {**cfg, "비중상한": 0.1})


def 시총상한30(c, s, cfg):
    return 시총상한(c, s, {**cfg, "비중상한": 0.3})


def 최소분산(c, s, cfg, 개월=36):
    """공매도 없는 최소분산. 직전 36개월 월수익률(설정의 기준일 간격) 공분산을 Ledoit-Wolf로 수축.
    36개월 수익률이 다 있는 종목만 쓴다(나머지는 빠짐 — 편입 수는 보유 비중 > 0 종목 수로 확인)."""
    g = 기준일({**cfg, "기간": (None, None)})
    g = g[g <= s["t"]][-(개월 + 1):]
    r = 읽기.상장가격(cfg["가격"]).loc[g, c].pct_change(fill_method=None).iloc[1:].dropna(axis=1)
    if len(g) <= 개월 or r.shape[1] < 2:
        return pd.Series(dtype=float)
    S, n = LedoitWolf().fit(r.to_numpy()).covariance_, r.shape[1]
    w = minimize(lambda w: w @ S @ w, np.full(n, 1 / n), jac=lambda w: 2 * S @ w, bounds=[(0, 1)] * n,
                 constraints={"type": "eq", "fun": lambda w: w.sum() - 1}, method="SLSQP").x.clip(0)
    return pd.Series(w / w.sum(), r.columns)


def 거래비용(old, new, c):
    """비중 변화로 매수·매도 금액(포트폴리오 대비 비율)을 구해 비용률을 돌려준다."""
    d = new.sub(old, fill_value=0)
    buy, sell = d.clip(lower=0).sum(), -d.clip(upper=0).sum()
    return buy * (c["수수료"] + c["슬리피지"]) + sell * (c["수수료"] + c["거래세"] + c["슬리피지"])


def 기간수익률(p, grid):
    """기준일 간 수익률. 구간 안에서 상장폐지되면 마지막 가격으로 판 것으로 본다(가격 값은 바꾸지 않고 마지막 값을 찾기만 함)."""
    return p.ffill().loc[grid] / p.loc[grid].shift(1) - 1


def 보유(R, W, 비용, 전량=False, 회전=None):
    """R: 기준일 간 수익률(행=구간 끝 기준일). W: {리밸런싱일: 비중}. 리밸런싱 사이엔 매수보유(비중이 값 따라 변함).
    수익률이 빈 종목(폐지 다음 구간부터)은 그달 계산에서 빠진다 = 남은 종목에 값 비례로 다시 넣은 것과 같다. 비용은 리밸런싱 뒤 첫 달에 뺀다."""
    out, old, dates = [], pd.Series(dtype=float), sorted(W)
    for t0, t1 in zip(dates, dates[1:] + [R.index[-1]]):
        w = W[t0]
        r = R.loc[(R.index > t0) & (R.index <= t1), w.index]
        g = (1 + r.fillna(0)).cumprod()
        v = g.shift(1, fill_value=1) * w
        pr = (1 + (v * r).sum(axis=1) / v.where(r.notna()).sum(axis=1)) * (1 - 비용.get("월비용", 0)) - 1
        c = 거래비용(old, w[:0], 비용) + 거래비용(w[:0], w, 비용) if 전량 else 거래비용(old, w, 비용)
        if 회전 is not None:
            회전[t0] = w.sub(old, fill_value=0).clip(lower=0).sum()  # 한쪽 회전율 = 산 비중 합(처음 매수 = 1). 전량교체 비용과 별개
        pr.iloc[0] = (1 - c) * (1 + pr.iloc[0]) - 1
        old = g.iloc[-1] * w / (g.iloc[-1] * w).sum()
        out.append(pr)
    return pd.concat(out)


def 실행(cfg):
    """설정대로 돌려 dict(수익률=월수익률 표(열=(비중, 그룹)), 기록=리밸런싱일별 종목 수, 보유=비중, 설정)."""
    cfg = {**기본설정, **cfg}
    grid = 기준일(cfg)
    R = 기간수익률(읽기.상장가격(cfg["가격"]), grid)
    W, 기록 = defaultdict(dict), []
    for t in grid[:-1][::cfg["리밸런싱"]]:
        s, c, n = 거르기(t, cfg)
        v = pd.DataFrame({m[0]: getattr(지표, m[0])(s).reindex(c) for m in cfg["지표"]})
        sc = 점수(v, cfg["지표"], cfg["합산"])
        groups = 고르기(sc, cfg["고르기"])
        for b in cfg["비중"]:
            for g, cc in groups.items():
                W[(b, g)][t] = globals()[b](cc, s, cfg) if len(cc) else pd.Series(dtype=float)  # 0종목이면 그 구간 수익률 빈칸
        기록.append({"기준일": t, **n, **{f"빈칸:{k}": x for k, x in v.isna().sum().items()},
                   "빈칸으로 빠짐": len(c) - len(sc), **{f"편입:{g}": len(cc) for g, cc in groups.items()},
                   "확인:업종빈칸": 종목거르기.그날(읽기.업종, t, c).isna().sum(),
                   "확인:WICS금융": 종목거르기.그날(읽기.WICS, t, c).eq("금융").sum()})  # 금융업 판정은 거래소 업종, WICS는 확인용(2000년 이후만 있음)
    회전 = defaultdict(dict)
    수익률 = pd.DataFrame({k: 보유(R, w, cfg["거래비용"], cfg["전량교체"], 회전[k]) for k, w in W.items()})
    return dict(수익률=수익률, 기록=pd.DataFrame(기록).set_index("기준일"), 보유=W, 설정=cfg, 종목수익률=R, 회전율=pd.DataFrame(회전))


def 큰수익률(R, 하한=3):
    """기준일 간 종목 수익률이 하한 초과(기본 3 = +300%, 이전 보고의 '한 달 3배 초과')인 종목-월. 원본 그대로 공개용(고치지 않음)."""
    x = R.stack()
    return x[x > 하한].rename("수익률")


def 이상값보유(결과, 하한=3):
    """열(비중, 그룹)마다 큰수익률 종목-월을 보유한 건수. 0보다 크면 그 열은 '이상값 영향'."""
    big, out = 큰수익률(결과["종목수익률"], 하한), {}
    for k, W in 결과["보유"].items():
        d = pd.DatetimeIndex(sorted(W))
        out[k] = sum(c in W[d[d < m][-1]].index for m, c in big.index if (d < m).any() and m <= 결과["수익률"].index[-1])
    return pd.Series(out, name="이상값 보유 건수")
