"""새로 통째로 받은 파일 읽기(추가 지시 1: 예전에 나눠 받아 합친 data\\통합_202611은 쓰지 않음, 값 대조용으로만).
경로는 이 파일 맨 위에서만 정한다. 읽은 표는 @cache로 아이템코드만 키로 들고 있으므로, 노트북에서 `데이터읽기.DATA`를 바꾸면 커널을 다시 시작해야 한다(감사 #17).
값은 원본 그대로 돌려준다. 고치거나 채우지 않는다."""
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

DATA = Path(r"D:\26-2_데이터기반투자전략\과제02\data\통합_전체_202611")  # DataGuide 달력기준 일간, I.00P, 1988-01-04~2026-09-30
XLSX = Path(r"D:\26-2_데이터기반투자전략\과제02\data\DataGuide_전체_202611")  # X01 지수, X03 상장일, X04 상장폐지일(원본 xlsx)
# 한 번에 받은 원본이라 그대로 씀(추가 지시 1 예외)
RF_FILE = Path(r"D:\26-2_데이터기반투자전략\과제02\data\DataGuide_1990s_202610\무위험이자율후보_DataGuide_시장금리전체아이템35종_월간_19880101-20260930.xlsx")
FACTOR_FILE = Path(r"D:\26-2_데이터기반투자전략\과제02\data\DataGuide_추가_202610\요인_팩터모델과시장지수_일간_1990-2026.xlsx")
새목록 = Path(__file__).resolve().parent.parent / "_검증" / "새목록"  # B2(2026-11-04): 예전 데이터로 만든 목록을 새 데이터에서 같은 규칙으로 다시 만든 것(저장소 안)
ADD10 = FACTOR_FILE.parent  # DataGuide_추가_202610: '쓰지 말 것' 목록 csv(README_데이터), 코드 재사용 16종목 csv
CD_FILE = Path(r"D:\26-2_데이터기반투자전략\과제02\data\교수제공\08.[액셀실습]TSMom(K200).xlsx")  # 교수님 수업 자료, CD1m(추가 지시 10)
KRX_FILE = Path(r"D:\26-2_데이터기반투자전략\과제02\data\DataGuide_추가_202611\R12_통합지수_KRXTMI_KRX300_KRX300TR_KRX100_코스닥TR_I31000040F_일별_19991228-20260930.xlsx")

# 일간 아이템코드
TR, 수정주가, 종가, 거래대금, 거래량, 시총, 주식수, 정지구분 = "S410007700", "S410000700", "S41000060F", "S410000900", "S41000080F", "S410001250", "S41000100F", "S410002600"
시장구분, 업종, WICS, 관리여부, 정지여부, 결산월, 발표일 = "CP10000300", "CP10001090", "CP10000600", "CP10001660", "CP10001650", "CP10002200", "FP56000900"


def 목록(pat):
    return [f for f in DATA.glob(f"통합_일간_{pat}.parquet") if not f.name.endswith(".tmp.parquet")]  # 변환 중인 .tmp 파일은 안 봄


def 있음(item):
    return bool(목록(f"{item}_*"))


def 파일(item):
    f = 목록(f"{item}_*")
    if not f:
        raise FileNotFoundError(f"{item} 파일이 {DATA}에 아직 없음 → 파일 오면 다시 실행")
    (f,) = f
    return f


@cache
def 공통끝():
    """통합_확인기록 F6: 항목마다 값이 끝나는 날이 다를 수 있다. 가격·시가총액·시장구분 일간 파일에 값이 있는 마지막 날 중 가장 이른 날 하나로 자른다.
    재무(M·FP)·결산월 일간은 아직 끝나지 않은 회계연도가 빈칸이라(예: 2026년 회계연도) 끝 날짜 판정에서 뺀다."""
    ends = [(t := pq.read_table(파일(i))).slice(max(t.num_rows - 260, 0)).to_pandas().dropna(how="all").index.max()
            for i in (TR, 수정주가, 종가, 시총, 시장구분) if 있음(i)]  # 결산월 등 회계연도 항목·드문드문한 항목은 안 봄(감사 M2)
    assert pd.notna(ends).all(), ends
    return min(ends)


@cache
def 일간(item):
    """통합_일간_{item}_*.parquet. 행=날짜(공통끝까지), 열=종목코드. 글자 값(시장구분·업종 등)은 범주형으로 읽는다(값은 같고 메모리만 줄임).
    6,293종목 파일(A0147B0 없음)도 그대로 읽는다. 다른 파일과 맞출 때 그 칸은 빈칸(reindex)."""
    return pq.read_table(파일(item)).to_pandas(strings_to_categorical=True).loc[:공통끝()]


@cache
def 상장가격(item):
    """F2·F3: 시장구분(CP10000300)이 코스피·코스닥('KS'·'KQ')인 날의 가격만 계산에 쓴다.
    상장 전(이전상장 전 가격)·상장폐지 뒤(장외 K-OTC 등) 가격은 계산에서 빈칸으로 본다. 원본 값은 그대로.
    가격 0도 빈칸으로 본다: 0원은 거래 가격일 수 없고 수익률이 −100%·무한대가 된다(상장 구간 0원 칸 TR 4,748·수정주가 2,253, 대부분 1998~2001년 우선주 '우B',
    TR은 한국ANKOR유전 A152550 2012~2022년 2,652칸. `_검증/전처리_영향_결과.txt`, 진행기록 2026-11-03 08:15)."""
    p = 일간(item)
    return p.where(일간(시장구분).reindex(index=p.index, columns=p.columns).isin(["KS", "KQ"]) & (p > 0))


@cache
def 쓰지말것(item):
    """README_데이터.md '쓰지 말 것' 칸 → 표(코드, 시작, 끝). 값은 그대로 두고, 이 구간 가격을 쓰는 편입·수익률 계산만 피한다.
    A008080 2004-01~2013-09(D-05), 수정주가 병합·감자 미반영 7칸의 그 달(D27), 배당 포함 가격(TR)을 쓸 때 TR 이상칸의 앞날~그날(D-06·U3, 새 데이터로 다시 만든 목록).
    병합미반영은 예전 7칸 그대로: 새 데이터에 판정 조건 ③(DataGuide 1개월대비수익률)이 없어 새 목록(3,582줄)은 조건이 빠진 후보일 뿐."""
    d = ADD10
    m = pd.read_csv(d / "수정주가_병합미반영_7칸.csv", encoding="utf-8-sig", parse_dates=["날짜(월말)"])
    t = [("A008080", "2004-01-01", "2013-09-30", "D-05")] + [(c, x.replace(day=1), x, "D27") for c, x in zip(m["코드"], m["날짜(월말)"])]
    if item == TR:
        a = pd.read_csv(새목록 / "수정주가TR_이상칸.csv", encoding="utf-8-sig")  # 같은 규칙으로 새 데이터에서 다시 만든 232칸(예전 107칸 모두 포함, `_검증/B2_목록다시.py`·`새목록/차이표.md`)
        t += [(c, x, y, "TR이상칸:" + k) for c, x, y, k in zip(a["코드"], a["앞_날짜"], a["날짜"], a["유형"])]
    return pd.DataFrame(t, columns=["코드", "시작", "끝", "근거"]).astype({"시작": "datetime64[ns]", "끝": "datetime64[ns]"})


def 재무항목():
    """새 폴더의 재무(주재무 결산) 일간 파일 아이템코드: M(재무)·FP(발표일 등). FM(컨센서스)은 회계연도 값이 아니라 뺀다."""
    return sorted(f.name.split("_")[2] for p in ("M", "FP") for f in 목록(f"{p}*"))


검사 = {}  # 연간재무(): 항목마다 '결산일 값 ≠ 그 회계연도 첫 영업일 값'이라 빈칸으로 둔 행 수


@cache
def 연간재무():
    """달력기준 일간 재무 → (코드, 회계연도) 행(예전 통합_연간재무와 같은 모양: 코드·회계연도·CP10002200·아이템코드 열, 천원).
    달력기준 일간 값은 그 회계연도 기간 내내 그 회계연도 값이다(발표 전부터 들어감 → 그대로 쓰면 미래 정보).
    그래서 결산일 = 결산월 이력(CP10002200)이 그 달인 달의 마지막 영업일, 그날 값을 그 회계연도 값으로 뽑는다. 쓸 수 있는 날은 포트폴리오.재무가능일이 정한다.
    회계연도 = 결산일 연도 − (결산월 ≤ 5)(예전 연간재무 표기와 같음: 1~5월 결산은 회계연도 다음 해에 끝남).
    확인: 결산일 값이 그 회계연도 첫 영업일(직전 결산일 다음 달 첫 영업일, 첫 행은 11개월 전 달 첫 영업일) 값과 다르면
    그 칸은 그 회계연도 값이라고 믿을 수 없어 빈칸으로 둔다(값이 결산월과 다른 날 바뀌는 종목 = 다음 회계연도 값이 들어갈 수 있음, 감사 H1).
    둘 중 하나가 빈칸이면 확인 못 해 값 그대로 둔다. 빈칸으로 둔 수는 읽기.검사[아이템코드]."""
    m = 일간(결산월)
    g = m.index.to_series().groupby(m.index.to_period("M"))
    last, first = g.max(), g.min()  # 달마다 마지막·첫 영업일
    e = m.loc[last].apply(lambda x: pd.to_numeric(x.astype(object))).stack().rename("CP10002200").reset_index()
    e.columns = ["날짜", "코드", "CP10002200"]
    e = e[e["CP10002200"] == e["날짜"].dt.month].sort_values(["코드", "날짜"]).reset_index(drop=True)  # 그날 결산월 = 그 달 → 결산일
    e["회계연도"] = e["날짜"].dt.year - (e["CP10002200"] <= 5)
    pm = e["날짜"].dt.to_period("M")
    시작 = (pm.groupby(e["코드"]).shift(1).fillna(pm - 12) + 1).map(first)  # 그 회계연도 첫 영업일(데이터 전이면 빈칸)
    need = pd.DatetimeIndex(sorted(set(last) | set(first)))
    for item in 재무항목():  # 일간 전체(항목당 약 500MB)를 들고 있지 않도록 달 첫·마지막 영업일 줄만 읽는다
        t = pq.read_table(파일(item))
        d = t.take(pd.Index(t.column("날짜").to_pandas()).get_indexer(need)).to_pandas().reindex(columns=m.columns)  # 6,293종목 파일의 없는 종목은 빈칸
        assert d.index.equals(need), f"{item}: 결산월 파일과 날짜가 다름"
        c, x = d.columns.get_indexer(e["코드"]), d.to_numpy(float)
        a = x[d.index.get_indexer(e["날짜"]), c]
        ok = 시작.notna().to_numpy()
        b = np.full(len(e), np.nan)
        b[ok] = x[d.index.get_indexer(시작[ok]), c[ok]]
        bad = ~np.isnan(a) & ~np.isnan(b) & (a != b)
        e[item], 검사[item] = np.where(bad, np.nan, a), int(bad.sum())
    return e.drop(columns="날짜")


@cache
def 종목정보():
    """X03 상장일·X04 상장폐지일(특정시점 최근, 원본 xlsx). 코드명은 지금 이름."""
    r = lambda f, c: pd.read_excel(next(XLSX.glob(f)), header=None, skiprows=6, names=["코드", "코드명", c], dtype={c: "Int64"}).set_index("코드")
    a, b = r("X03_*.xlsx", "상장일"), r("X04_*.xlsx", "상장폐지일")
    assert a["코드명"].equals(b["코드명"]), "X03·X04 종목 목록이 다름"
    return a.join(b["상장폐지일"])


@cache
def CD1m():
    """교수님 제공 엑셀(시트 TS모멘텀_m) B열 날짜(월말)·D열 CD1m(연 %) → 월 수익률(소수) = 연 % / 1200.
    엑셀 수식 =D6*(1/12)과 같은 월 단리. 값은 파일 그대로(1990-01~1994-12는 파일에 14로 들어 있음)."""
    x = pd.read_excel(CD_FILE, sheet_name="TS모멘텀_m", header=None)
    assert str(x.iloc[4, 3]).startswith("CD1m"), "D열 머리글이 CD1m이 아님"
    s = x.iloc[5:, 3].astype(float)
    s.index = pd.to_datetime(x.iloc[5:, 1])
    return s[s.index.notna()].rename_axis(None) / 1200


def 무위험(item):
    """DataGuide 금리(연 %, 월말) → 월 수익률(소수). 행=월말 날짜. item="CD1m"이면 교수님 제공 CD1m 한 계열(추가 지시 10)."""
    if item == "CD1m":
        return CD1m()
    x = pd.read_excel(RF_FILE, header=None)
    col = x.columns[x.iloc[14].eq(item).to_numpy()][0]  # 15행 = 아이템코드
    s = x.iloc[17:][col].astype(float)
    s.index = pd.to_datetime(x.iloc[17:, 5])
    return s.rename_axis(None) / 1200


def 지수표(f, 코드행, 시작행):
    x = pd.read_excel(f, header=None)
    lv = x.columns[1:][x.iloc[코드행 + 3, 1:].eq("I31000040F").to_numpy()]  # 아이템코드 = 코드 3행 아래, 종가지수만
    t = x.iloc[시작행:][lv].set_axis(x.loc[코드행, lv], axis=1)
    t.index = pd.to_datetime(x.iloc[시작행:, 0])
    return t.astype(float).rename_axis(index=None, columns=None)


@cache
def 지수():
    """시장지수(X01: 코스피 I.001·코스피TR I.030·코스피200 동일가중 I.401·코스닥 I.201·코스닥TR I.273)와
    요인(FACTOR_FILE: 3FM.2B3.SMB·HML, 3FM.2M3.MOM)의 종가지수(일간). 열=코드. 같은 코드가 두 파일에 있으면 X01을 쓴다."""
    a = 지수표(next(XLSX.glob("X01_*.xlsx")), 8, 14)
    b = 지수표(FACTOR_FILE, 8, 14)
    return a.join(b.drop(columns=a.columns, errors="ignore"), how="outer")


@cache
def KRX지수():
    """R12 KRX 통합지수(KRX TMI 등, 1999-12-28~). 확장 연구의 참고 벤치마크."""
    return 지수표(KRX_FILE, 8, 14)
