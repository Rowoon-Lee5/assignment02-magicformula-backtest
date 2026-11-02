"""합친 파일 읽기. 경로는 이 파일 맨 위 세 줄에서만 정한다(노트북에서 바꿀 때는 `데이터읽기.DATA = Path(...)`).
값은 원본 그대로 돌려준다. 고치거나 채우지 않는다."""
from functools import cache
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

DATA = Path(r"D:\26-2_데이터기반투자전략\과제02\data\통합_202611")
RF_FILE = Path(r"D:\26-2_데이터기반투자전략\과제02\data\DataGuide_1990s_202610\무위험이자율후보_DataGuide_시장금리전체아이템35종_월간_19880101-20260930.xlsx")
FACTOR_FILE = Path(r"D:\26-2_데이터기반투자전략\과제02\data\DataGuide_추가_202610\요인_팩터모델과시장지수_일간_1990-2026.xlsx")

# 일간 아이템코드
TR, 수정주가, 종가, 거래량, 시총, 주식수, 정지구분 = "S410007700", "S410000700", "S41000060F", "S41000080F", "S410001250", "S41000100F", "S410002600"
시장구분, 업종, WICS, 관리여부, 정지여부 = "CP10000300", "CP10001090", "CP10000600", "CP10001660", "CP10001650"


@cache
def 공통끝():
    """통합_확인기록 F6: 항목마다 값이 끝나는 날이 다르다. 모든 일간 파일에 값이 있는 마지막 날 중 가장 이른 날 하나로 자른다."""
    ends = [(t := pq.read_table(f)).slice(t.num_rows - 260).to_pandas().dropna(how="all").index.max() for f in DATA.glob("통합_일간_*.parquet")]
    assert pd.notna(ends).all(), ends
    return min(ends)


@cache
def 일간(item):
    """통합_일간_{item}_*.parquet. 행=날짜(공통끝까지), 열=종목코드. 글자 값(시장구분·업종 등)은 범주형으로 읽는다(값은 같고 메모리만 줄임)."""
    (f,) = DATA.glob(f"통합_일간_{item}_*.parquet")
    return pq.read_table(f).to_pandas(strings_to_categorical=True).loc[:공통끝()]


@cache
def 상장가격(item):
    """F2·F3: 시장구분(CP10000300)이 코스피·코스닥('KS'·'KQ')인 날의 가격만 계산에 쓴다.
    상장 전(이전상장 전 가격)·상장폐지 뒤(장외 K-OTC 등) 가격은 계산에서 빈칸으로 본다. 원본 값은 그대로."""
    p = 일간(item)
    return p.where(일간(시장구분).reindex(columns=p.columns).isin(["KS", "KQ"]))


@cache
def 쓰지말것(item):
    """README_데이터.md '쓰지 말 것' 칸 → 표(코드, 시작, 끝). 값은 그대로 두고, 이 구간 가격을 쓰는 편입·수익률 계산만 피한다.
    A008080 2004-01~2013-09(D-05), 수정주가 병합·감자 미반영 7칸의 그 달(D27), 배당 포함 가격(TR)을 쓸 때 TR 이상칸의 앞날~그날(D-06·U3)."""
    d = DATA.parent / "DataGuide_추가_202610"
    m = pd.read_csv(d / "수정주가_병합미반영_7칸.csv", encoding="utf-8-sig", parse_dates=["날짜(월말)"])
    t = [("A008080", "2004-01-01", "2013-09-30", "D-05")] + [(c, x.replace(day=1), x, "D27") for c, x in zip(m["코드"], m["날짜(월말)"])]
    if item == TR:
        a = pd.read_csv(d / "수정주가TR_이상칸.csv", encoding="utf-8-sig")
        t += [(c, x, y, "TR이상칸:" + k) for c, x, y, k in zip(a["코드"], a["앞_날짜"], a["날짜"], a["유형"])]
    return pd.DataFrame(t, columns=["코드", "시작", "끝", "근거"]).astype({"시작": "datetime64[ns]", "끝": "datetime64[ns]"})


@cache
def 연간재무():
    """통합_연간재무.parquet. 값 열 이름 '{항목명}_{아이템코드}' → 아이템코드만 남긴다(단위 천원)."""
    return pd.read_parquet(DATA / "통합_연간재무.parquet").rename(columns=lambda c: c.rsplit("_", 1)[-1])


@cache
def 종목정보():
    return pd.read_csv(DATA / "통합_종목정보.csv", encoding="utf-8-sig").set_index("코드")


@cache
def 무위험(item):
    """DataGuide 금리(연 %, 월말) → 월 수익률(소수). 행=월말 날짜."""
    x = pd.read_excel(RF_FILE, header=None)
    col = x.columns[x.iloc[14].eq(item).to_numpy()][0]  # 15행 = 아이템코드
    s = x.iloc[17:][col].astype(float)
    s.index = pd.to_datetime(x.iloc[17:, 5])
    return s.rename_axis(None) / 1200


@cache
def 지수():
    """요인(SMB·HML·MOM 등)·시장지수(I.001 등)의 종가지수(일간). 열=코드."""
    x = pd.read_excel(FACTOR_FILE, header=None)
    lv = x.columns[1:][x.iloc[11, 1:].eq("I31000040F").to_numpy()]  # 12행 = 아이템코드, 종가지수만
    t = x.iloc[14:][lv].set_axis(x.loc[8, lv], axis=1)  # 9행 = 코드
    t.index = pd.to_datetime(x.iloc[14:, 0])
    return t.astype(float).rename_axis(index=None, columns=None)
