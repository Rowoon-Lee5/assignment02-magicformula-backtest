"""_검증/추가로_받을것.md 의 숫자를 원자료에서 직접 센다. 원본은 읽기만 한다(쓰기·옮기기 없음).
실행: C:/Users/benef/AppData/Local/Python/pythoncore-3.11-64/python.exe _검증/추가로_받을것_확인.py > _검증/추가로_받을것_확인_결과.txt"""
import re
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

D = Path(r"D:\26-2_데이터기반투자전략\과제02\data")
NEW, OLD, XL = D / "통합_전체_202611", D / "통합_202611", D / "DataGuide_전체_202611"
F4129 = D / "DataGuide_추가_202610" / "회계기준_결산_발표일_확정치_최초치_4129_1999-2026.xlsx"
R30 = D / "DataGuide_추가_202611" / "R30_이자비용대체항목시험_이자비용_금융비용_순이자비용_비영업비용_이자발생부채_547종목_회계기준결산.xlsx"
HERE = Path(__file__).resolve().parent.parent
pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 400)


def 새파일(item):
    (f,) = [f for f in NEW.glob(f"통합_일간_{item}_*.parquet") if not f.name.endswith(".tmp.parquet")]
    return f


def 열읽기(f, codes):
    have = set(pq.read_schema(f).names)
    cols = [c for c in codes if c in have]
    t = pq.read_table(f, columns=["날짜", *cols] if "날짜" in have else cols).to_pandas()
    return t, cols


# ---------- 1. 1990년대 폐지 종목 가격 ----------
print("=== 1. 1990년대 상장폐지 종목 가격 (F7) ===")
r = lambda f, c: pd.read_excel(next(XL.glob(f)), header=None, skiprows=6, names=["코드", "코드명", c], dtype={c: "Int64"}).set_index("코드")
info = r("X03_*.xlsx", "상장일").join(r("X04_*.xlsx", "상장폐지일")["상장폐지일"])  # 데이터읽기.종목정보()와 같은 읽기
info["폐지"] = pd.to_datetime(info["상장폐지일"].astype("string"), format="%Y%m%d", errors="coerce")
info["상장"] = pd.to_datetime(info["상장일"].astype("string"), format="%Y%m%d", errors="coerce")
print("X03·X04 종목 수", len(info), "| 상장폐지일 있음", int(info["폐지"].notna().sum()))
for lo, hi in [("1988-01-01", "1989-12-31"), ("1990-01-01", "1999-12-31")]:
    print(f"  상장폐지일 {lo[:4]}~{hi[:4]}: {int(info['폐지'].between(lo, hi).sum())}")
q = info[info["폐지"].between("1990-01-01", "1999-12-31")].copy()
codes = list(q.index)

새 = {}
for nm, item in [("수정주가", "S410000700"), ("TR", "S410007700"), ("종가", "S41000060F"), ("시총", "S410001250")]:
    t, cols = 열읽기(새파일(item), codes)
    t = t.set_index(t.columns[0]) if "날짜" not in t.index.names and not isinstance(t.index, pd.DatetimeIndex) else t
    새[nm] = t
    print(f"  새 {nm}({item}) 파일에 열 있음 {len(cols)}/{len(codes)}, 값 1개 이상 {int(t[cols].notna().any().sum())}")
p = 새["수정주가"]
q["열있음"] = [c in p.columns for c in codes]
q["가격첫날"] = [p[c].first_valid_index() if c in p.columns else pd.NaT for c in codes]
q["가격끝날"] = [p[c].last_valid_index() if c in p.columns else pd.NaT for c in codes]
q["가격칸"] = [int(p[c].notna().sum()) if c in p.columns else 0 for c in codes]
for nm in ("TR", "종가", "시총"):
    x = 새[nm]
    q[nm + "칸"] = [int(x[c].notna().sum()) if c in x.columns else 0 for c in codes]
없음 = q[q["가격칸"] == 0]
print(f"  → 1990년대 폐지 {len(q)} 중 새 수정주가 값 있음 {int((q['가격칸'] > 0).sum())}, 없음 {len(없음)}")
print(f"  → 없는 {len(없음)}종목 중 TR·종가·시총 어느 하나라도 값 있음: {int((없음[['TR칸', '종가칸', '시총칸']].sum(1) > 0).sum())}")

# 예전 합친 데이터(통합_202611)로도 셈 → 통합_확인기록 F7 '47' 과 비교
fo = OLD / "통합_일간_S410000700_수정주가.parquet"
to, co = 열읽기(fo, codes)
to = to.set_index(to.columns[0]) if not isinstance(to.index, pd.DatetimeIndex) else to
old_has = {c for c in co if to[c].notna().any()}
print(f"  예전 통합_202611 수정주가: 열 있음 {len(co)}, 값 있음 {len(old_has)}, 없음 {len(codes) - len(old_has)}")
print(f"  새에는 없고 예전에는 있음: {sorted(set(없음.index) & old_has)} | 새에는 있고 예전에는 없음 {len(set(q.index[q['가격칸'] > 0]) - old_has)}")

# 비는 기간 = 상장 구간(상장일과 데이터 첫날 1988-01-04 중 늦은 날 ~ 상장폐지일)
start = p.index.min()
없음 = 없음.assign(빈구간시작=없음["상장"].where(없음["상장"] > start, start).dt.date, 빈구간끝=없음["폐지"].dt.date)
print(f"\n  가격 없는 {len(없음)}종목 표 (데이터 첫날 {start.date()}):")
print(없음[["코드명", "상장일", "상장폐지일", "열있음", "빈구간시작", "빈구간끝", "TR칸", "종가칸", "시총칸"]].to_string())
print("  상장폐지 연도별:", 없음["폐지"].dt.year.value_counts().sort_index().to_dict())
print("  상장일이 1988-01-04 이전:", int((없음["상장"] < start).sum()), "/ 상장일 빈칸:", int(없음["상장"].isna().sum()))
print("  코드 끝자리(0=보통주 아님 확인용):", 없음.index.str[-1].value_counts().to_dict())
print("  한 줄 코드 목록:", ",".join(없음.index))
mk, _ = 열읽기(새파일("CP10000300"), list(없음.index))
mk = mk.set_index(mk.columns[0]) if not isinstance(mk.index, pd.DatetimeIndex) else mk
print("  42종목 새 시장구분(CP10000300) 값 있는 종목:", int(mk.notna().any().sum()), "| 값 종류:", pd.unique(mk.stack().astype(str)).tolist()[:10])
ks = mk.astype(object).eq("KS")
print("  42종목 시장구분 'KS'인 첫날·끝날·일수:")
print(pd.DataFrame({"KS첫날": ks.idxmax().where(ks.any()).dt.date, "KS끝날": ks[::-1].idxmax().where(ks.any()).dt.date,
                    "KS일수": ks.sum()}).to_string())
# 예전에 따로 받은 1990s 수정주가(R24, 3040종목)에 이 종목들이 있는지
r24 = next((D / "DataGuide_추가_202611").glob("R24_1990s수정주가*.xlsx"))
z = pd.read_excel(r24, header=None, nrows=14)
row = next(i for i in range(14) if z.iloc[i].astype(str).str.match(r"A\d{5}").sum() > 100)
zc = z.iloc[row].astype(str).tolist()
inr = [c for c in 없음.index if c in zc]
print(f"  {r24.name}: 코드 줄 {row + 1}행, 42종목 중 열 있음 {len(inr)}")
if inr:
    zz = pd.read_excel(r24, header=None, usecols=[zc.index(c) for c in inr], skiprows=row + 1)
    print("   그 열들 중 값(숫자) 있는 종목:", int(zz.apply(lambda s: pd.to_numeric(s, errors='coerce').notna().any()).sum()))

# 값이 있는 종목 중 상장 구간 안에서 앞·뒤가 30일 넘게 비는 것(부분 결측)
있음 = q[q["가격칸"] > 0]
s0 = 있음["상장"].where(있음["상장"] > start, start)
앞 = (있음["가격첫날"] - s0).dt.days > 30
뒤 = (있음["폐지"] - 있음["가격끝날"]).dt.days > 30
print(f"\n  값 있는 {len(있음)}종목 중 상장 구간 앞쪽이 30일 넘게 빔 {int(앞.sum())}, 폐지 전 30일 넘게 빔 {int(뒤.sum())}")
print(있음[앞 | 뒤][["코드명", "상장일", "상장폐지일", "가격첫날", "가격끝날", "가격칸"]].to_string())
# 상장 구간(상장일·1988-01-04 중 늦은 날 이상, 상장폐지일 미만) 안 거래일 중 수정주가 빈칸 수(중간 빈칸 포함)
빈 = pd.Series({c: int(p.loc[(p.index >= s0[c]) & (p.index < 있음.at[c, "폐지"]), c].isna().sum()) for c in 있음.index})
print(f"  값 있는 {len(있음)}종목의 상장 구간 안 빈 거래일: 0일 {int((빈 == 0).sum())}, 1~19일 {int(빈.between(1, 19).sum())}, 20일 이상 {int((빈 >= 20).sum())}")
print("  20일 이상 비는 종목:", 빈[빈 >= 20].sort_values(ascending=False).to_dict())
for c in 빈[빈 >= 1].index:  # 빈 거래일이 이어진 구간(시작~끝)
    m = p.loc[(p.index >= s0[c]) & (p.index < 있음.at[c, "폐지"]), c].isna()
    g = (m != m.shift()).cumsum()[m]
    print(f"   {c} {있음.at[c, '코드명']}: " + ", ".join(f"{x.index[0].date()}~{x.index[-1].date()}({len(x)}일)" for _, x in m[m].groupby(g)))

# 예전 통합_종목정보.csv 기준으로 다시 셈(통합_확인기록 F7 '47'의 출처 확인용)
oi = pd.read_csv(OLD / "통합_종목정보.csv", dtype=str)
print("\n  예전 통합_종목정보.csv 열:", list(oi.columns))
dcol = [c for c in oi.columns if "폐지일" in c][0]
od = pd.to_datetime(oi[dcol], format="%Y%m%d", errors="coerce")
oc = list(oi.loc[od.between("1990-01-01", "1999-12-31"), oi.columns[0]])
to2, co2 = 열읽기(fo, oc)
print(f"  예전 종목정보로 1990년대 폐지 {len(oc)}, 예전 수정주가 열 있음 {len(co2)}, 값 없음(열 없음 포함) {len(oc) - sum(to2[c].notna().any() for c in co2)}")
print("  예전 목록에만 있는 코드:", sorted(set(oc) - set(codes)), "| 새 목록에만:", sorted(set(codes) - set(oc)))

# ---------- 2. 4129 확정치·최초치 파일 ----------
print("\n=== 2. 회계기준_결산_발표일_확정치_최초치_4129_1999-2026.xlsx ===")
x = pd.read_excel(F4129, header=None)
print("시트 크기(행, 열)", x.shape)
for i in range(11):
    print(f"  {i + 1}행:", [v for v in x.iloc[i].tolist() if pd.notna(v)])
hdr = x.iloc[8, 5:].tolist()
body = x.iloc[11:].reset_index(drop=True)
body.columns = ["코드", "코드명", "결산월", "회계연도", "분기", *hdr]
print("  자료 행", len(body), "| 종목", body["코드"].nunique(), "| 회계연도", body["회계연도"].min(), "~", body["회계연도"].max(),
      "| 분기 값", body["분기"].value_counts().to_dict(), "| 결산월", body["결산월"].value_counts().sort_index().to_dict())
for i, c in enumerate(hdr):
    v = body.iloc[:, 5 + i]
    print(f"  {x.iloc[7, 5 + i]} {c} {x.iloc[9, 5 + i]}: 값 {int(v.notna().sum()):,}, 종목 {body.loc[v.notna(), '코드'].nunique()}, "
          f"회계연도 {body.loc[v.notna(), '회계연도'].min()}~{body.loc[v.notna(), '회계연도'].max()}")
print("  공시구분 FP70000500 값:", body["FP70000500"].value_counts(dropna=False).to_dict() if "FP70000500" in body else "없음")

# 우리가 쓰는 새 자산총계 일간 파일에 값이 있는 종목 중 4129 파일에 없는 종목(2001~2026 = 01~04 원문 기간의 재무 해)
t = pq.read_table(새파일("M000901001")).to_pandas()
t = t.set_index(t.columns[0]) if not isinstance(t.index, pd.DatetimeIndex) else t
for lo in ("1999-01-01", "2002-01-01"):
    have = set(t.columns[t.loc[lo:].notna().any()])
    in4129 = set(body["코드"])
    print(f"  새 자산총계(M000901001) {lo[:4]}년 이후 값 있는 종목 {len(have)}, 그중 4129 파일에 없음 {len(have - in4129)}, 끝자리 0(보통주)만 {sum(c[-1] == '0' for c in have - in4129)}")
print("   4129 파일에 없는 종목(2002년 이후 기준):", ",".join(sorted(have - in4129)))
del t
src = "".join((HERE / "공통" / f).read_text(encoding="utf-8") for f in ("지표.py", "데이터읽기.py", "종목거르기.py", "포트폴리오.py"))
used = sorted(set(re.findall(r"\b(M000\d{6}|FP\d{8})\b", src)))
print("  공통/*.py 에 나오는 재무 코드:", used)
print("  그중 4129 파일에 있음:", [c for c in used if c in hdr])
print("  그중 4129 파일에 없음:", [c for c in used if c not in hdr])
print("  새 통합_전체_202611 parquet 있음:", [c for c in used if list(NEW.glob(f"통합_일간_{c}_*.parquet"))])

# ---------- 3. data 폴더 xlsx 머리줄(1~14행)에서 '중단'·금융비용 등 찾기 ----------
print("\n=== 3. data 폴더 xlsx 머리줄 검색 (60MB 넘는 파일은 건너뜀) ===")
import openpyxl
pat = re.compile("중단|M000907005|금융비용|금융원가|순이자|이자발생부채|M000992009|M000911010|M000906016|M000991040")
skip, n = [], 0
for f in sorted(D.rglob("*.xlsx")):
    if f.name.startswith("~$"):
        continue
    if f.stat().st_size > 60e6:
        skip.append(f.relative_to(D).as_posix())
        continue
    n += 1
    try:
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        hits = set()
        for ws in wb.worksheets:
            for row in ws.iter_rows(min_row=1, max_row=14, values_only=True):
                hits |= {str(v) for v in row if v is not None and pat.search(str(v))}
        wb.close()
        if hits:
            print(f"  {f.relative_to(D).as_posix()}: {sorted(hits)[:12]}")
    except Exception as e:
        print(f"  읽기 실패 {f.relative_to(D).as_posix()}: {type(e).__name__}")
print(f"  본 파일 {n}개, 건너뛴 파일 {len(skip)}개:", skip)

# ---------- 4. R30 이자비용 대체 항목 시험 ----------
print("\n=== 4. R30 이자비용대체항목시험 xlsx ===")
wb = openpyxl.load_workbook(R30, read_only=True)
print("  시트:", {ws.title: (ws.max_row, ws.max_column) for ws in wb.worksheets})
wb.close()
y = pd.read_excel(R30, sheet_name="Sheet1 (2)", header=None)
for i in range(11):
    print(f"  {i + 1}행:", [v for v in y.iloc[i].tolist() if pd.notna(v)])
h = y.iloc[8, 5:10].tolist()
b = y.iloc[11:, :10].reset_index(drop=True)
b.columns = ["코드", "코드명", "결산월", "회계연도", "분기", *h]
print("  자료 행", len(b), "| 종목", b["코드"].nunique(), "| 회계연도", b["회계연도"].min(), "~", b["회계연도"].max(), "| 분기", b["분기"].value_counts().to_dict())
for c, n in zip(h, y.iloc[9, 5:10]):
    v = pd.to_numeric(b[c], errors="coerce")
    print(f"  {c} {n}: 값 {int(v.notna().sum()):,} (0인 칸 {int((v == 0).sum()):,}, 음수 {int((v < 0).sum()):,}), 빈칸 {int(v.isna().sum()):,}")
ie = pd.to_numeric(b["M000906020"], errors="coerce")
print(f"  이자비용 빈칸 {int(ie.isna().sum()):,}행에서 다른 항목 값 있음:",
      {c: int(pd.to_numeric(b.loc[ie.isna(), c], errors="coerce").notna().sum()) for c in h[1:]})
print(f"  이자비용 빈칸 & 금융비용 0: {int((pd.to_numeric(b.loc[ie.isna(), 'M000992009'], errors='coerce') == 0).sum())}, "
      f"이자비용 빈칸 & 이자발생부채 0: {int((pd.to_numeric(b.loc[ie.isna(), 'M000991040'], errors='coerce') == 0).sum())}")
print("  회계연도 구간별 값 있는 행:")
b["구간"] = pd.cut(pd.to_numeric(b["회계연도"]), [1986, 1999, 2010, 2026], labels=["1987-1999", "2000-2010", "2011-2026"])
print(b.groupby("구간", observed=True)[h].count().to_string())

# 예전 합친 연간재무에 이자발생부채 등 있는지
cols = pq.read_schema(OLD / "통합_연간재무.parquet").names
print("\n  예전 통합_202611/통합_연간재무.parquet 열 중 관련:", [c for c in cols if re.search("M000991040|M000992009|M000911010|M000906016|M000907005|중단|금융비용|이자", c)])
for c in [c for c in cols if "M000991040" in c or "M000906020" in c]:
    v = pd.read_parquet(OLD / "통합_연간재무.parquet", columns=[c])[c]
    print(f"   {c}: 값 {int(v.notna().sum()):,}, 0 {int((v == 0).sum()):,}, 빈칸 {int(v.isna().sum()):,}")
print("  새 통합_전체_202611 에 M000907005·M000992009·M000911010·M000991040 parquet:",
      {c: [f.name for f in NEW.glob(f"통합_일간_{c}_*.parquet")] for c in ("M000907005", "M000992009", "M000911010", "M000991040")})
print("  DataGuide_전체_202611 에 R32 이후 xlsx:", sorted(f.name for f in XL.glob("R3[2-9]_*.xlsx")))
