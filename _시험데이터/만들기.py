# 원본에서 '합친 파일' 모양 그대로의 작은 시험 파일을 만든다(2003~2006 일간·그 기간 가격 있는 종목, 연간재무는 전 종목·전 회계연도).
# 원본은 읽기만 한다. 값은 원본 그대로(빈칸은 빈칸).
from pathlib import Path
import pandas as pd

D = Path(r"D:\26-2_데이터기반투자전략\과제02\data")
PQ, A11, G = D / r"DataGuide_갱신_202609\parquet", D / "DataGuide_추가_202611", D / "DataGuide_1990s_202610"
OUT = Path(__file__).parent
DAYS = slice("2003-01-01", "2006-12-31")
DAILY = {  # 아이템코드: (항목명, 원본)
    "S410007700": ("수정주가(현금배당포함)", PQ / "수정주가(현금배당포함).parquet"),
    "S410000700": ("수정주가", PQ / "수정주가.parquet"),
    "S41000060F": ("종가", PQ / "종가.parquet"),
    "S41000080F": ("거래량", PQ / "거래량.parquet"),
    "S410001250": ("시가총액", PQ / "시가총액.parquet"),
    "S41000100F": ("상장주식수", PQ / "상장주식수.parquet"),
    "S410002600": ("거래정지구분", PQ / "거래정지구분.parquet"),
    "CP10000300": ("시장구분", A11 / r"_parquet_from_xlsx\R3_시장구분_CP10000300_4129_일별.parquet"),
    "CP10001090": ("거래소업종(세부)", PQ / "거래소 업종(세부분류).parquet"),
    "CP10001080": ("거래소업종코드(세부)", PQ / "거래소 업종코드 (세부분류).parquet"),
}
R18 = A11 / "R18_관리종목여부CP10001660_지정사유CP10001640_거래정지여부CP10001650_4129_월간_19991201-20260930.xlsx"
R18_NAME = {"CP10001660": "관리종목여부", "CP10001640": "관리종목지정사유", "CP10001650": "거래정지여부"}
WICS = A11 / "R4_WICS_FnGuideSector_CP10000600_4129_일별_19991228-20260930.xlsx"  # 합치기 대상에 들어가기 전까지 xlsx를 직접 읽음
GROUPS = ["코스피닥상장", "코스닥피상폐", "보충_목록누락78"]
FIN_FILES = ["회계기준결산_주재무M_7항목_FY1987-2026", "회계기준결산_추가재무14항목_FY1987-2026", "회계기준결산_단기차입금_유동성장기부채_FY1987-2026",
             "회계기준결산_우동호3항목_무형자산_세전계속사업이익_이자비용_FY1987-2026", "회계기준결산_발표일FP50000900_결산월이력_FY1987-2026"]
FIN_KEEP = ("M", "CP10002200")  # 붙일 열: 재무(M…)와 결산월이력. FP50000900은 세 묶음 모두 값이 없어 뺀다.
KEY = ["코드", "코드명", "결산월", "회계연도"]

price = pd.read_parquet(DAILY["S410007700"][1]).loc[DAYS]
codes = price.columns[price.notna().any()]
for code, (name, f) in DAILY.items():
    pd.read_parquet(f).loc[DAYS].reindex(columns=codes).to_parquet(OUT / f"통합_일간_{code}_{name}.parquet")

# 관리종목·거래정지여부(월간, 월간 날짜 그대로)와 WICS 대분류(일간). 같은 엑셀 모양: 9행 코드, 12행 아이템코드, 15행부터 값.
for f, names in [(R18, R18_NAME), (WICS, {"CP10000600": "WICS대분류"})]:
    x = pd.read_excel(f, sheet_name=0, header=None)
    body = x.iloc[14:]
    body.index = pd.to_datetime(x.iloc[14:, 0])
    for item, name in names.items():
        cols = x.columns[1:][x.iloc[11, 1:].eq(item).to_numpy()]
        t = body[cols].set_axis(x.loc[8, cols], axis=1).rename_axis(index=None, columns=None).loc[DAYS]
        t.reindex(columns=codes).to_parquet(OUT / f"통합_일간_{item}_{name}.parquet")


def read_fin(f):
    x = pd.read_excel(f, sheet_name=0, header=None)
    names = [f"{str(n).replace('(천원)', '')}_{c}" for c, n in zip(x.iloc[8, 5:], x.iloc[9, 5:])]
    t = x.iloc[11:, :5].set_axis(KEY + ["분기"], axis=1).join(x.iloc[11:, 5:].set_axis(names, axis=1))
    return t.drop(columns="분기")


fin = []
for g in GROUPS:
    parts = [read_fin(G / f"{g}_{n}.xlsx") for n in FIN_FILES]
    t = parts[0]
    for p in parts[1:]:
        t = t.merge(p[KEY + [c for c in p.columns if c.split("_")[-1].startswith(FIN_KEEP)]], on=KEY, how="outer")
    fin.append(t)
fin = pd.concat(fin).drop_duplicates(KEY)
assert not fin.duplicated(["코드", "회계연도"]).any()
fin.to_parquet(OUT / "통합_연간재무.parquet", index=False)

reuse = set(pd.read_csv(D / r"DataGuide_추가_202610\코드재사용_16종목.csv")["코드"])
info = []
for g, state in [("코스피닥상장", "상장"), ("코스닥피상폐", "상장폐지"), ("보충_목록누락78", None)]:
    t = pd.read_excel(G / f"{g}_상장일_상장폐지일_특정시점.xlsx", sheet_name=0, header=None, skiprows=6, usecols=range(4))
    t.columns = ["코드", "코드명", "상장일", "상장폐지일"]
    t["상태"] = state or t["상장폐지일"].notna().map({True: "상장폐지", False: "상장"})
    t["출처묶음"] = g
    info.append(t)
info = pd.concat(info).drop_duplicates("코드")
info["코드재사용"] = info["코드"].isin(reuse)
info[info["코드"].isin(codes)].to_csv(OUT / "통합_종목정보.csv", index=False, encoding="utf-8-sig")
print(f"종목 {len(codes)}, 일간 {price.shape[0]}일, 재무 {len(fin)}행, 종목정보 {info['코드'].isin(codes).sum()}행")
