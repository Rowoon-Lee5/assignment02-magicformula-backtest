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
    기간=("2004-04", "2006-12"),        # (첫 리밸런싱 월, 마지막 기준일 월). 설정에 "끝": "마지막거래일"을 넣으면 끝 달 마지막 거래일을 한 칸 더함
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
# 재무연도 '직전년도': 원문 p.512 '직전년도에 공시된 재무제표', '2003년에서 2020년 결산자료' → 리밸런싱 해 t의 회계연도 t−1 결산만(없으면 그 종목은 그해 빠짐, 2026-11-06 원문대로 고침: 전에는 2년 안 가장 최근 행이라 FY t−2도 씀)
우동호2023 = {**기본설정, "이름": "우동호2023_MF", "기간": ("2004-04", "2022-04"),
              "제외": ["보통주", "금융업", "투자기구", ("결산월", {"월": 12}), "거래정지"], "무위험": "E11.02.003.008", "가격": 읽기.수정주가, "전량교체": True,
              "재무연도": "직전년도"}


def 기준일(cfg):
    d = 읽기.일간(cfg["가격"]).index.to_series()
    g = d.groupby(d.dt.to_period("M"))
    x = (g.min() if cfg["기준일"] == "첫거래일" else g.max()).loc[cfg["기간"][0]:cfg["기간"][1]]
    if cfg.get("끝") == "마지막거래일":  # 마지막 구간을 끝 달 마지막 거래일에서 끊음(우동호 p.512 '다음연도 3월 마지막 거래일까지')
        x = pd.concat([x, g.max().loc[x.index[-1:]]])
    return pd.DatetimeIndex(x.to_numpy())


@cache
def 재무가능일(how):
    """연간재무 행마다 결산일·발표일과 '쓸 수 있는 날'. 결산월은 회계연도별 이력(CP10002200).
    결산월 1~5월은 회계연도 다음 해에 끝난다(DataGuide 표기). 발표일이 결산일보다 이르면 믿지 않는다."""
    f = 읽기.연간재무().dropna(subset=["CP10002200"])
    m = f["CP10002200"].astype(int)
    end = pd.to_datetime((f["회계연도"] + (m <= 5)).astype(int).astype(str) + m.astype(str).str.zfill(2), format="%Y%m") + pd.offsets.MonthEnd(0)
    kind, k = how
    if "FP56000900" not in f:  # 발표일 파일이 아직 없으면 발표일을 안 보는 '결산후개월'만 돈다(빈 발표일로 대신하지 않음)
        assert kind == "결산후개월", "발표일 FP56000900 파일이 아직 없음 → 파일 오면 다시 실행"
        return f.assign(결산일=end, 가능일=end + pd.DateOffset(months=k))
    pub = pd.to_datetime(f["FP56000900"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce")
    pub = pub.where(pub > end)
    하루 = pd.Timedelta(days=0 if kind == "발표당일" else 1)  # '발표당일': 발표한 날부터(03 진단용)
    if kind == "발표월말":  # NH(2018) 02 p.14·03 p.18 '분기/연간 재무제표가 발표되는 월의 월말에 반영': 발표한 날부터 → 월말 리밸런싱이면 그 달 마지막 거래일까지 발표분을 그 달 말에 씀.
        # 마지막 거래일 뒤 같은 달 휴일(예: 토요일 3/31) 발표분은 다음 리밸런싱부터(그날 종가에는 알 수 없는 정보, 2026-11-05 항목 4 대조에서 고침)
        return f.assign(결산일=end, 발표일=pub, 가능일=pub.fillna(end + pd.Timedelta(days=k)))
    ok = end + pd.DateOffset(months=k) if kind == "결산후개월" else (pub + 하루).fillna(end + pd.Timedelta(days=k))
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


def 재무(t, how, 연도=None):
    """그날 쓸 수 있는 가장 최근 회계연도 행(종목마다 한 행). 연도=None: 결산일이 2년보다 오래된 행은 안 씀(묵은 값 막기, ponytail).
    연도='직전년도': 결산일이 t 전 해(t.year − 1)인 행만(우동호 p.512 '직전년도', Novy-Marx 각주 4 '다음 해 6월 말'). 연도='최근': 상한 없이 가장 최근."""
    f = 재무가능일(how)
    f = f[f["가능일"] <= t]
    if 연도 == "직전년도":
        f = f[f["결산일"].dt.year == t.year - 1]
    elif 연도 is None:
        f = f[f["결산일"] >= t - pd.DateOffset(years=2)]
    return f.sort_values(["회계연도", "결산일"]).drop_duplicates("코드", keep="last").set_index("코드")  # F9: 같은 회계연도 두 결산월이면 늦은 결산일


@cache
def 분기가능일(시점="다음날"):
    """분기 행마다 쓸 수 있는 날 = 분기 보고서 발표일(FP56000900 분기) 다음 날. 발표일이 없거나 분기말보다 이르면 쓰지 않는다(분기는 대신할 일수 근거가 없어 빈칸).
    시점="발표월말": 발표한 날부터 = NH(2018) '발표되는 월의 월말에 반영'(월말 리밸런싱이면 그 달 마지막 거래일까지 발표분이 그 달 말에 들어감. 그 뒤 휴일 발표분은 다음 리밸런싱, 2026-11-05)."""
    f = 읽기.분기재무()
    pub = pd.to_datetime(f["FP56000900"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce") if "FP56000900" in f else pd.Series(pd.NaT, f.index)
    pub = pub.where(pub > f["분기말"])
    return f.assign(발표일=pub, 가능일=pub if 시점 == "발표월말" else pub + pd.Timedelta(days=1))


def 분기재무(t, 흐름="4분기합", 시점="다음날"):
    """그날 쓸 수 있는 분기 행으로 종목마다 한 줄(열 = 아이템코드, 천원). NH(2018) p.14·p.18 '분기/연간 재무제표가 발표되는 월의 월말에 반영'.
    흐름 항목(읽기.분기흐름): '4분기합' = 쓸 수 있는 가장 최근 4개 분기(연속: 첫 분기말과 마지막 분기말이 9개월 차이) 합, '최근분기x4' = 최근 분기 × 4.
    두 방식 모두 원문에 없음(민감도). 잔액 항목(읽기.분기잔액) = 최근 분기말 값. 분기말이 2년보다 오래된 행은 안 씀(연간과 같음)."""
    f = 분기가능일(시점)
    f = f[(f["가능일"] <= t) & (f["분기말"] >= t - pd.DateOffset(years=2))].sort_values(["코드", "분기말"])
    끝 = f.groupby("코드").tail(1).set_index("코드")
    흐름열 = [c for c in 읽기.분기흐름 if c in f]
    if 흐름 == "4분기합":
        f4 = f.groupby("코드").tail(4)
        n, 처음 = f4.groupby("코드")["분기말"].count(), f4.groupby("코드")["분기말"].min()
        연속 = (n == 4) & ((끝["분기말"].dt.to_period("M") - 처음.dt.to_period("M")).map(lambda x: x.n) == 9)
        v = f4.groupby("코드")[흐름열].sum(min_count=4).where(연속, np.nan)
    else:
        v = 끝[흐름열] * 4
    out = 끝.drop(columns=흐름열).join(v)
    return out.assign(회계연도=np.nan)  # 지표.값의 '빈칸으로 볼 칸'(회계연도 기준)은 분기에 안 씀


@cache
def 발표행():
    """보고서마다 한 행: 분기 보고서(1·2·3분기, 분기 3개월 값) + 연간 사업보고서(결산 값). 각 행의 가능일 = 그 보고서 발표일(FP56000900).
    결산월 분기는 분기 행 대신 연간 행(사업보고서가 발표하는 값). 발표일이 없거나 기간 끝보다 이른 보고서는 안 씀(대신할 일수 근거 없음)."""
    q = 분기가능일("발표월말")
    q = q[q["분기말"].dt.month != q["CP10002200"]].dropna(subset=["가능일"])
    y = 재무가능일(("발표월말", 0)).dropna(subset=["발표일"]).rename(columns={"결산일": "분기말"})
    cols = [c for c in 읽기.분기흐름 + 읽기.분기잔액 if c in q and c in y]
    return pd.concat([q[["코드", "분기말", "가능일", "CP10002200", *cols]].assign(보고서="분기"),
                      y[["코드", "분기말", "발표일", "CP10002200", "회계연도", *cols]].assign(가능일=lambda d: d["발표일"], 보고서="연간")], ignore_index=True)


def 발표재무(t, 상한=None):
    """NH(2018) 02 p.14·03 p.18 '주요 재무제표 수치는 분기/연간 재무제표가 발표되는 월의 월말에 반영', 02 p.26 '확정 재무데이터':
    t까지 발표된 가장 최근 보고서(분기 또는 연간) 값 그대로(4분기 합·×4 같은 가공 없음, 회원 결정 2026-11-06). 같은 날 발표면 기간 끝이 늦은 보고서.
    단 영업CF·EBITDA 분기 3개월 값은 DataGuide가 누적값에서 환산·계산한 값(V02 MEDIUM-2).
    상한 = 년 수를 주면 기간 끝이 그보다 오래된 보고서는 안 씀(기본 없음).
    '발표되는 월의 월말' = t가 든 달력 달에 발표된 것까지(마지막 거래일 뒤 같은 달 휴일 발표분 포함, 원문 문장대로 V03 HIGH-1 2026-11-06).
    그 휴일 발표분은 t 종가에는 아직 몰랐던 값 = 최대 2일 미래 정보(1990~2026 전체 1,749행, R1 재감사; 한계, _검증/기본값_목록_20261106.md)."""
    월말 = t + pd.offsets.MonthEnd(0)
    assert (월말 - t).days <= 10, f"발표재무는 월말 리밸런싱일에만: {t:%Y-%m-%d}"  # 달 중간 t면 그 달 뒤쪽 발표분이 새어 들어감
    f = 발표행()
    f = f[f["가능일"] <= 월말]
    if 상한:
        f = f[f["분기말"] >= t - pd.DateOffset(years=상한)]
    return f.sort_values(["가능일", "분기말"]).drop_duplicates("코드", keep="last").set_index("코드")


def 재무표(t, cfg):
    """설정의 재무주기대로 그날 쓸 재무(종목마다 한 행). ('발표값',) = 발표재무, ('분기', 흐름) = 분기재무, 그 밖 = 연간 재무()."""
    kind = cfg.get("재무주기", ("연간",))
    if kind[0] == "발표값":
        return 발표재무(t, cfg.get("재무상한"))
    if kind[0] == "분기":
        return 분기재무(t, kind[1], "발표월말" if cfg["재무시점"][0] == "발표월말" else "다음날")
    return 재무(t, cfg["재무시점"], cfg.get("재무연도"))


def 다음리밸런싱(t, cfg):
    g = 기준일(cfg)
    return g[min(g.get_loc(t) + cfg["리밸런싱"], len(g) - 1)] if t in g else t


def 재료(t, cfg):
    """기준일 t의 자료: 그날 상장 가격(읽기.상장가격) 있는 종목, 재무, 시가총액, 직전 12개월 일간수익률(빈칸은 빈칸, '쓰지 말 것' 칸은 빈칸으로 봄).
    다음 = 다음 리밸런싱일, 일년상장 = 직전 12개월 내내 시장구분 KS·KQ이고 그 창 첫날 상장 가격이 있음
    (시장구분이 첫 가격보다 몇 년 먼저 KS로 들어 있는 우선주 등이 짧은 수익률로 통과하던 것 막기, 감사 2026-11-03 #3·#14)."""
    p = 읽기.상장가격(cfg["가격"]).loc[:t]
    codes = p.columns[p.iloc[-1].notna()]
    a = t - pd.DateOffset(years=1)
    p = p.loc[a:, codes].copy()
    for c, x, y in 읽기.쓰지말것(cfg["가격"])[["코드", "시작", "끝"]].itertuples(index=False):
        if c in p:
            p.loc[x:y, c] = np.nan
    return dict(t=t, 다음=다음리밸런싱(t, cfg), 가격=cfg["가격"], codes=codes, fin=재무표(t, cfg).reindex(codes),
                mcap=읽기.일간(읽기.시총).loc[t, codes], ret=p.pct_change(fill_method=None).iloc[1:],
                일년상장=읽기.상장중().loc[a:t].reindex(columns=codes, fill_value=False).all() & p.iloc[0].notna())


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
    if kind == "상하N":  # 위 n(Q1)·가운데(Q2)·아래 n(Q3): Novy-Marx(2010) p.21 '150 stocks with the highest … 150 … lowest'
        a = sc.sort_values(ascending=False).index
        return {"Q1": a[:n], "Q2": a[n:len(a) - n], "Q3": a[len(a) - n:]}
    if kind == "상하비율":  # 위 n 비율(Q1)·가운데(Q2)·아래 n 비율(Q3): 우동호 p.513 요인 '상위 30% … 하위 30%'(종목 수 × n을 반올림)
        a, k = sc.sort_values(ascending=False).index, int(round(len(sc) * n))
        return {"Q1": a[:k], "Q2": a[k:len(a) - k], "Q3": a[len(a) - k:]}
    if len(sc) < n:  # 0종목이거나 분위 수보다 적으면 빈 묶음(구간 수익률 빈칸, 감사 #11; 02 '최근 분기 × 4' 2002-03-29에 1종목뿐 → 5분위 못 나눔, 2026-11-04)
        return {f"Q{i}": sc.index[:0] for i in range(1, n + 1)}
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
    if cap * len(c) < 1:  # 종목 수 × 상한 < 1이면 상한을 지킬 수 없음 → 빈 비중(그 구간 수익률 빈칸)
        return pd.Series(dtype=float)
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
    sd = 이력(c, s).std()
    iv = 1 / sd.where(sd > 0)  # 변동성 0(가격이 1년 내내 같음)은 역수가 없어 빈칸 → 비중에서 빠짐(감사 #10)
    return iv / iv.sum()


def 시총상한10(c, s, cfg):
    return 시총상한(c, s, {**cfg, "비중상한": 0.1})


def 시총상한30(c, s, cfg):
    return 시총상한(c, s, {**cfg, "비중상한": 0.3})


최소분산기록 = []  # 최소분산을 풀 때마다 (기준일, 종목 수, SLSQP 수렴 여부, 메시지). README 한계 '최소분산 수렴 미확인'(2026-11-04)


def 최소분산(c, s, cfg, 개월=36):
    """공매도 없는 최소분산. 직전 36개월 월수익률(설정의 기준일 간격) 공분산을 Ledoit-Wolf로 수축.
    36개월 수익률이 다 있는 종목만 쓴다(나머지는 빠짐 — 편입 수는 보유 비중 > 0 종목 수로 확인)."""
    g = 기준일({**cfg, "기간": (None, None)})
    g = g[g <= s["t"]][-(개월 + 1):]
    r = 쓰지말것칸(읽기.상장가격(cfg["가격"]).loc[g, c].pct_change(fill_method=None), cfg["가격"]).iloc[1:].dropna(axis=1)  # '쓰지 말 것' 칸은 R과 같게(README 한계 '최소분산 공분산')
    if len(g) <= 개월 or r.shape[1] < 2:
        return pd.Series(dtype=float)
    S, n = LedoitWolf().fit(r.to_numpy()).covariance_, r.shape[1]
    o = minimize(lambda w: w @ S @ w, np.full(n, 1 / n), jac=lambda w: 2 * S @ w, bounds=[(0, 1)] * n,
                 constraints={"type": "eq", "fun": lambda w: w.sum() - 1}, method="SLSQP")
    최소분산기록.append(dict(기준일=s["t"], 종목=n, 수렴=bool(o.success), 메시지=o.message))
    w = o.x.clip(0)
    return pd.Series(w / w.sum(), r.columns)


def 거래비용(old, new, c):
    """비중 변화로 매수·매도 금액(포트폴리오 대비 비율)을 구해 비용률을 돌려준다."""
    d = new.sub(old, fill_value=0)
    buy, sell = d.clip(lower=0).sum(), -d.clip(upper=0).sum()
    return buy * (c["수수료"] + c["슬리피지"]) + sell * (c["수수료"] + c["거래세"] + c["슬리피지"])


def 기간수익률(p, grid):
    """기준일 간 수익률. 구간 안에서 상장폐지되면 마지막 가격으로 판 것으로 본다(가격 값은 바꾸지 않고 마지막 값을 찾기만 함)."""
    return p.ffill().loc[grid] / p.loc[grid].shift(1) - 1


def 쓰지말것칸(R, item):
    """기준일 간 수익률 R(행 = 구간 끝)에서 '쓰지 말 것' 구간(시작, 끝]에 걸린 칸만 바꾼다(README_데이터 권고 D-06·U3·D27):
    TR 이상칸은 그 구간 가격수익률(수정주가)로, 병합·감자 미반영(D27)·A008080(D-05)은 빈칸(그 종목·달을 뺌). 다른 칸은 그대로."""
    R, g = R.copy(), R.index
    prev = pd.DatetimeIndex([pd.NaT, *g[:-1]])
    b = 읽기.쓰지말것(item)
    for c, x, y, k in b[b["코드"].isin(R.columns)][["코드", "시작", "끝", "근거"]].itertuples(index=False):
        hit = (g > x) & (prev < y)
        if k.startswith("TR이상칸"):  # 걸린 종목 한 열만 계산(전 종목 ffill을 최소분산마다 다시 해 느렸음, 지시 H 2026-11-04). 열마다 계산이라 값은 같음
            R.loc[hit, c] = 기간수익률(읽기.상장가격(읽기.수정주가)[c], g).loc[hit]
        else:
            R.loc[hit, c] = np.nan
    return R


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
        i = pr.first_valid_index()  # 첫 달이 빈칸(보유 종목 모두 값 없음)이면 값 있는 첫 달에 뺀다(한계 15번, 2026-11-04). 구간 내내 빈칸이면 비용도 없음
        if i is not None:
            pr.loc[i] = (1 - c) * (1 + pr.loc[i]) - 1
        살아있음 = r.iloc[-1].notna()  # 마지막 달 수익률이 빈 종목(폐지 등)은 pr에서 이미 빠져 남은 종목에 다시 넣은 셈 → 다음 매도비용·회전율에서 뺀다(한계 21·40번, 2026-11-04)
        old = (g.iloc[-1] * w)[살아있음] / (g.iloc[-1] * w)[살아있음].sum()
        out.append(pr)
    return pd.concat(out)


def 실행(cfg):
    """설정대로 돌려 dict(수익률=월수익률 표(열=(비중, 그룹)), 기록=리밸런싱일별 종목 수, 보유=비중, 설정).
    cfg["전략들"] = {이름: dict(지표=..., 합산=...)}을 주면 같은 거르기 결과로 여러 전략을 한 번에 고른다(열 = (이름, 비중, 그룹),
    ('유니버스', '시총', '전체') = 거른 종목 전부 시가총액 가중 = 확장 연구 자체 벤치마크)."""
    cfg = {**기본설정, **cfg}
    전략들 = cfg.get("전략들") or {None: dict(지표=cfg["지표"], 합산=cfg["합산"])}
    grid = 기준일(cfg)
    R = 쓰지말것칸(기간수익률(읽기.상장가격(cfg["가격"]), grid), cfg["가격"])
    W, 기록 = defaultdict(dict), []
    for t in grid[:-1][::cfg["리밸런싱"]]:
        s, c, n = 거르기(t, cfg)
        v = pd.DataFrame({m: getattr(지표, m)(s).reindex(c) for m in dict.fromkeys(m[0] for e in 전략들.values() for m in e["지표"])})
        v = v.mask(np.isinf(v))  # 분모 0 → ±inf는 값이 없는 것과 같아 빈칸으로 본다(inf가 1등으로 줄 서는 것 막기)
        if None not in 전략들:
            m = s["mcap"].reindex(c).dropna()
            W[("유니버스", "시총", "전체")][t] = m / m.sum()
        편입 = {}
        for 이름, e in 전략들.items():
            sc = 점수(v[[m[0] for m in e["지표"]]], e["지표"], e["합산"])
            groups = 고르기(sc, cfg["고르기"])
            for b in cfg["비중"]:
                for g, cc in groups.items():
                    k = (b, g) if 이름 is None else (이름, b, g)
                    W[k][t] = globals()[b](cc, s, cfg) if len(cc) else pd.Series(dtype=float)  # 0종목이면 그 구간 수익률 빈칸
                    편입[":".join(["보유수", *map(str, k)])] = int((W[k][t] > 0).sum())  # 위험균형·최소분산은 과거 수익률이 모자란 종목이 빠져 편입 수보다 적을 수 있음(감사 #2)
            편입 |= {"빈칸으로 빠짐" if 이름 is None else f"빈칸으로 빠짐:{이름}": len(c) - len(v[[m[0] for m in e["지표"]]].dropna())}  # 단계별에서 남길 비율로 잘린 수는 넣지 않음(감사 #12)
            편입 |= {f"편입:{g}" if 이름 is None else f"편입:{이름}:{g}": len(cc) for g, cc in groups.items()}
        기록.append({"기준일": t, **n, **{f"빈칸:{k}": x for k, x in v.isna().sum().items()}, **편입,
                   "확인:업종빈칸": 종목거르기.그날(읽기.업종, t, c).isna().sum() if 읽기.있음(읽기.업종) else pd.NA,  # 업종을 안 쓰는 02·03이 업종 파일 때문에 멈추지 않게(감사 #13)
                   "확인:WICS금융": 종목거르기.그날(읽기.WICS, t, c).eq("금융").sum() if 읽기.있음(읽기.WICS) else pd.NA})  # 금융업 판정은 거래소 업종, WICS는 확인용(2000년 이후만 있음, 파일 없으면 빈칸 = 확인 안 함)
    회전 = defaultdict(dict)
    수익률 = pd.DataFrame({k: 보유(R, w, cfg["거래비용"], cfg["전량교체"], 회전[k]) for k, w in W.items()})
    return dict(수익률=수익률, 기록=pd.DataFrame(기록).set_index("기준일"), 보유=W, 설정=cfg, 종목수익률=R, 회전율=pd.DataFrame(회전))


def 원문요인(cfg, 비율=0.3, 비중="동일", 리밸런싱=1):
    """우동호 외(2023) p.513 요인을 원문 문장대로 직접 만든다: SMB = 시가총액 하위 30% − 상위 30%, HML = 장부가치/시장가치 상위 30% − 하위 30%,
    MOM = 과거 11개월 수익률 상위 30% − 하위 30%(2026-11-06, 전에는 DataGuide 2×3 요인지수).
    원문에 없는 칸(기본값 = 가장 단순, 목록은 `_검증/기본값_목록_20261106.md`, 대안 영향은 회원 결정(03:50)으로 재지 않음): 표본 = 본문 거르기(cfg의 시장·제외), cfg 기준일마다(리밸런싱=1: 매달) 다시 나눔,
    동일가중, 장부가치 = 지배자본(BP), 재무 = 가능일이 지난 가장 최근 회계연도(상한 없음)('직전년도'는 매달 나누면 1~3월에 FY t−1이 아직 없어 결산월 거르기에서 전 종목이 빠짐 → 쓰지 않음, F01 2026-11-06), 비용 0. 각 요인의 지표가 없는 종목은 그 요인에서만 빠짐.
    돌려주는 것: 기준일 간 요인 수익률(열 SMB·HML·MOM)."""
    c = {**cfg, "리밸런싱": 리밸런싱, "고르기": ("상하비율", 비율), "비중": [비중], "거래비용": dict(수수료=0, 거래세=0, 슬리피지=0), "전량교체": False, "재무연도": "최근",
         "전략들": {"SMB": dict(지표=[("시가총액", "낮게")], 합산="순위합산"), "HML": dict(지표=[("BP", "높게")], 합산="순위합산"),
                  "MOM": dict(지표=[("모멘텀11", "높게")], 합산="순위합산")}}
    R = 실행(c)["수익률"]
    return pd.DataFrame({k: R[(k, 비중, "Q1")] - R[(k, 비중, "Q3")] for k in ("SMB", "HML", "MOM")})


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
