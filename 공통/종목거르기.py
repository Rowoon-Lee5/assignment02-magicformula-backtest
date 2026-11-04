"""종목 거르기. 필터마다 함수 1개: (s, c, 옵션) → 남는 종목코드(Index).
s = 포트폴리오.재료()가 만든 그날 자료, c = 지금까지 남은 종목. 값이 빈 종목은 그 필터에서 빠진다(빈칸은 빈칸)."""
import numpy as np
import pandas as pd

import 데이터읽기 as 읽기
import 지표


def 그날(item, t, c):
    """그날 값. 월간 자료(관리종목 등)는 그날 이전 가장 최근 기준일 행을 그대로 쓴다."""
    return 읽기.일간(item).reindex([t], method="ffill").iloc[0].reindex(c)


def 시장(s, c, 시장들):
    """시장구분 CP10000300: 'KS' 유가증권, 'KQ' 코스닥."""
    return c[그날(읽기.시장구분, s["t"], c).isin(시장들)]


def 쓰지말것(s, c):
    """README_데이터 '쓰지 말 것' 구간(읽기.쓰지말것, (시작, 끝])에 기준일이 들어가는 종목 제외 = 그날 값이 의심인 종목(회원 결정 2026-11-02). 값은 그대로.
    기준일까지 알 수 있는 것만 본다(2026-11-04 고침: 전에는 [기준일, 다음 리밸런싱일]을 봐서 미래 정보였음, README 한계 '판정 창').
    보유 중에 걸리는 칸은 포트폴리오.쓰지말것칸이 그 칸 수익률만 바꾼다."""
    b = 읽기.쓰지말것(s["가격"])
    return c[~c.isin(b.loc[(b["시작"] < s["t"]) & (b["끝"] >= s["t"]), "코드"])]


def 종목빼기(s, c, 코드들):
    """확인판: 지정 종목을 뺀다(A070480 이상값 확인, 회원 결정 2026-11-02)."""
    return c[~c.isin(코드들)]


def 보통주(s, c):
    """수업 노트북: 코드 끝자리 0 = 보통주."""
    return c[c.str.endswith("0")]


def 스팩(s, c):
    return c[~읽기.종목정보()["코드명"].reindex(c).str.contains("스팩", na=False)]


def 금융업(s, c, 낱말=("은행", "보험", "증권", "금융", "금고")):
    """그날 거래소 업종(CP10001090)에 낱말이 있으면 제외. 업종은 1988~2026 기간에 있지만 빈칸인 종목이 있다(수는 기록의 확인:업종빈칸).
    업종이 빈 종목은 이름('(주)'를 뗀 지금 이름)에 은행·보험·증권·금융·금고·캐피탈·카드·저축·신금·리츠·스팩이 있거나 '지주'로 끝나면 제외
    (스팩 = 기업인수목적회사, 거래소 업종이 있는 날은 '금융'으로 들어 있어 업종 빈칸 날만 이름으로 잡음, 감사 2026-11-03 #15)
    (수업 노트북 이름 규칙을 넓힘. 금융지주·카드·캐피탈·저축은행이 빠지던 것 막기, '리스'는 엑큐리스 같은 이름이 걸려 뺌).
    업종이 빈 날 그날 WICS(CP10000600, 2000년부터)가 '금융'이어도 제외(2026-11-04: 이름 규칙이 놓친 경매·해외개발 펀드, 지금 이름이 바뀐 스팩 시절 26종목, `_검증/B5_금융업이름_결과.txt`)."""
    krx = 그날(읽기.업종, s["t"], c)
    name = 읽기.종목정보()["코드명"].reindex(c).str.replace(r"\(주\)|㈜", "", regex=True).str.strip()
    wics = 그날(읽기.WICS, s["t"], c).astype(object).eq("금융") if 읽기.있음(읽기.WICS) else False
    fin = krx.str.contains("|".join(낱말), na=False) | (krx.isna() & (name.str.contains("은행|보험|증권|금융|금고|캐피탈|카드|저축|신금|리츠|스팩|지주$", na=False) | wics))
    return c[~fin]


def 투자기구(s, c):
    """선박투자회사·부동산투자회사(CR리츠 포함)·리츠 제외. 일반기업과 재무제표 형태가 달라 금융업을 빼는 이유와 같음(회원 결정 2026-11-01).
    거래소 업종이 '일반서비스' 등으로 들어 있어 이름(지금 이름)으로 판정: 선박투자회사·부동산투자가 들어감, '리츠'로 끝남, 리츠코크렙."""
    name = 읽기.종목정보()["코드명"].reindex(c).str.replace(r"\(주\)|㈜", "", regex=True).str.strip()
    return c[~name.str.contains("선박투자회사|부동산투자|리츠$|리츠코크렙", na=False)]


def 결산월(s, c, 월=12):
    """그날 쓰는 재무 행의 결산월(회계연도별 이력 CP10002200)."""
    return c[s["fin"]["CP10002200"].reindex(c) == 월]


def 거래정지(s, c, 아이템=읽기.정지구분):
    """일간 S410002600('거래정지') 또는 일간 CP10001650('정지', 10,061일 파일)."""
    return c[~그날(아이템, s["t"], c).isin(["거래정지", "정지"])]


def 관리종목(s, c):
    return c[그날(읽기.관리여부, s["t"], c).ne("관리")]


def 동전주(s, c, 하한=1000):
    """종가가 하한 미만인 종목 제외(수업: 1,000원 미만)."""
    return c[그날(읽기.종가, s["t"], c) >= 하한]


def 자본잠식(s, c):
    return c[s["fin"]["M000903001"].reindex(c) > 0]


def 최근20일(item, t, c):
    return 읽기.일간(item).loc[:t, c].iloc[-20:]


def 회전율(s, c, 하위=0.1):
    """최근 20거래일 평균 거래량 / 그날 상장주식수, 하위 비율 제외(수업: 10%)."""
    turn = 최근20일(읽기.거래량, s["t"], c).mean() / 그날(읽기.주식수, s["t"], c)
    return c[turn > turn.quantile(하위)]


def 거래대금(s, c, 하한=1e9, 창="20일"):
    """평균 거래대금(S410000900, 원) ≥ 하한(NH: 10억 원). 창='20일': 최근 20거래일, '월': 기준일이 든 달의 거래일(NH p.26 '월평균 거래대금')."""
    x = 최근20일(읽기.거래대금, s["t"], c) if 창 == "20일" else 읽기.일간(읽기.거래대금).loc[f"{s['t']:%Y-%m}":s["t"], c]
    return c[x.mean() >= 하한]


def 지표있음(s, c, 지표들):
    """지표 값이 모두 있는 종목만(±inf는 없는 것으로 봄). Novy-Marx p.21 '500 largest … for which GP/A and B/M are both available'처럼 시총상위 앞에 둔다."""
    v = pd.DataFrame({m: getattr(지표, m)(s).reindex(c) for m in 지표들}).replace([np.inf, -np.inf], np.nan)
    return c[v.notna().all(axis=1).to_numpy()]


def 시총상위(s, c, n=300):
    return s["mcap"].reindex(c).nlargest(n).index


def 시총분위(s, c, 분위, k=5):
    """그날 시가총액 k분위 중 한 분위만(1 = 가장 작은 분위)."""
    m = s["mcap"].reindex(c).dropna()
    q = pd.qcut(m.rank(method="first"), k, labels=range(1, k + 1))
    return m.index[q == 분위]


def 적용(s, 목록):
    """목록 순서대로 거른다. 항목은 '이름' 또는 ('이름', {옵션}). 단계별 남은 종목 수도 돌려준다."""
    c, n = s["codes"], {"가격있음": len(s["codes"])}
    for f in 목록:
        name, kw = (f, {}) if isinstance(f, str) else f
        c = globals()[name](s, c, **kw)
        n[name] = len(c)
    return c, n
