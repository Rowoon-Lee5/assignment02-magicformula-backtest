"""전처리 규칙마다 영향받는 칸·행·종목 수(추가 지시 8). 원본은 읽기만 하고, 규칙은 공통/ 코드 그대로 부른다. 결과 보고용 숫자의 출처.
사용: python _검증/전처리_영향.py > _검증/전처리_영향_결과.txt"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import 데이터읽기 as 읽기
import 지표
import 포트폴리오 as 포


def 줄(이름, 값):
    print(f"- {이름}: {값}")


print("## 영업일 달력")
p = 읽기.일간(읽기.수정주가)
d = p.index
줄("날짜 수·처음·끝(공통끝)", f"{len(d)}, {d[0]:%Y-%m-%d}, {d[-1]:%Y-%m-%d}")
w = d[d.dayofweek >= 5]
줄("토·일 날짜 수(요일별) / 마지막 토·일 날짜 / 중복 날짜 / 오름차순", f"{w.day_name().value_counts().to_dict()} / {w.max():%Y-%m-%d} / {int(d.duplicated().sum())} / {d.is_monotonic_increasing}")
k = 읽기.지수()["I.001"].dropna()
k = k[(k.index >= d[0]) & (k.index <= d[-1])]
줄("코스피(I.001) 값 있는 날 중 가격 파일에 없는 날 / 가격 파일 날 중 코스피 값 없는 날", f"{len(k.index.difference(d))} / {len(d.difference(k.index))}")
for item in (읽기.TR, 읽기.수정주가, 읽기.시총, 읽기.종가, 읽기.주식수, 읽기.시장구분):
    줄(f"{item} 모양(날짜×종목)", 읽기.일간(item).shape)

print("\n## 단위")
t = d[-1]
m, c, n = 읽기.일간(읽기.시총).loc[t], 읽기.일간(읽기.종가).loc[t], 읽기.일간(읽기.주식수).loc[t]
r = (m * 1e6 / (c * n)).dropna()
줄(f"{t:%Y-%m-%d} 시가총액(백만원)×1e6 / (종가×상장주식수) 중앙값, 1% 넘게 다른 종목 수 / 비교 종목", f"{r.median():.4f}, {int(((r - 1).abs() > 0.01).sum())} / {len(r)}")
줄("재무 = 천원(아이템명), 시가총액 = 백만원 → 지표에서 ×1000으로 천원에 맞춤(지표.기업가치·BP 등), 거래대금 = 원(S410000900)", "코드 규칙")

print("\n## 상장 구간(시장구분 KS·KQ인 날만)")
mk = 읽기.일간(읽기.시장구분)
print(pd.Series(mk.to_numpy().ravel()).value_counts(dropna=False).to_string())
for item in (읽기.TR, 읽기.수정주가):
    x = 읽기.일간(item)
    ok = mk.reindex(index=x.index, columns=x.columns).isin(["KS", "KQ"]).to_numpy()
    v = x.notna().to_numpy()
    줄(f"{item} 값 있는 칸 / 그중 상장 구간 밖이라 계산에서 빼는 칸 / 그 종목 수", f"{int(v.sum())} / {int((v & ~ok).sum())} / {int((v & ~ok).any(axis=0).sum())}")
    z = (x == 0).to_numpy() & ok
    줄(f"{item} 상장 구간인데 가격 0이라 빈칸으로 보는 칸 / 종목 수", f"{int(z.sum())} / {int(z.any(axis=0).sum())}")

print("\n## 쓰지 말 것")
for item in (읽기.TR, 읽기.수정주가):
    b = 읽기.쓰지말것(item)
    줄(f"{item} 구간 수(근거별)", b["근거"].str.split(":").str[0].value_counts().to_dict())

print("\n## 재무: 결산월·회계연도")
f = 읽기.연간재무()
줄("연간재무 행 / (코드, 회계연도) 중복(결산월 바꾼 해) / 결산월 빈칸 행", f"{len(f)} / {int(f.duplicated(['코드', '회계연도']).sum())} / {int(f['CP10002200'].isna().sum())}")
있는행 = f[f[지표.자산].notna()]
줄("자산총계 있는 행의 결산월 분포", 있는행["CP10002200"].value_counts().sort_index().to_dict())
줄("결산월이 2가지 이상인 종목 수(자산총계 있는 행, 결산월을 바꾼 적 있음)", int((있는행.groupby("코드")["CP10002200"].nunique() > 1).sum()))
k = (f["회계연도"] + (f["CP10002200"] <= 5)) * 12 + f["CP10002200"]  # 결산 달 번호(연간재무는 코드·결산일 순)
gap = k - k.groupby(f["코드"]).shift()
for nm, 행 in (("결산월 12 행 전부", f["CP10002200"].eq(12)), ("결산월 12 + 자산총계 있음(H1 확인 뒤 값)", f["CP10002200"].eq(12) & f[지표.자산].notna())):
    짧음 = 행 & gap.lt(12)
    줄(f"직전 결산과 12개월보다 짧은 회계연도: {nm} / 개월별", f"{int(짧음.sum())} / {gap[짧음].astype(int).value_counts().sort_index().to_dict()}")
줄("회계연도 값 확인(H1)으로 빈칸으로 둔 수(항목별)", 읽기.검사)

print("\n## 재무: 0과 빈칸, 음수·0 분모 (자산총계 있는 행 기준)")
rows = {}
for item in 읽기.재무항목():
    x = 있는행[item] if item in 있는행 else pd.Series(dtype=float)
    rows[item] = {"빈칸": int(x.isna().sum()), "0": int((x == 0).sum()), "음수": int((x < 0).sum())}
print(pd.DataFrame(rows).T.to_string())
s = {"fin": 있는행.set_index(["코드", "회계연도", "CP10002200"]).assign(회계연도=0)}
roc분모 = 지표.값(s, 지표.유동자산) - 지표.값(s, 지표.유동부채) + 지표.값(s, 지표.자산) - 지표.값(s, 지표.무형자산)
줄("ROC 분모(순운전자본 + 순고정자산) ≤ 0 행 / 값 있는 행", f"{int((roc분모 <= 0).sum())} / {int(roc분모.notna().sum())}")
for nm, item in (("자본총계", 지표.자본), ("자본총계(지배)", 지표.지배자본)):
    if item in 있는행:
        줄(f"{nm} ≤ 0 행 / 값 있는 행", f"{int((있는행[item] <= 0).sum())} / {int(있는행[item].notna().sum())}")
if 지표.지배자본 in 있는행 and 지표.자본 in 있는행:
    줄("자본총계(지배) ≠ 자본총계 행(지배/연결 구분이 실제로 다른 행)", int((있는행[지표.지배자본] != 있는행[지표.자본]).sum()))

print("\n## 4월 첫 거래일(2004~2022, 우동호 본문 재무시점)에서 EV ≤ 0, EY·ROC 분모")
cfg = {**포.우동호2023, "기간": ("2004-04", "2022-04")}
ev0 = []
for t in 포.기준일(cfg)[::12]:
    fin = 포.재무(t, cfg["재무시점"])
    mc = 읽기.일간(읽기.시총).loc[t].reindex(fin.index)
    ev = 지표.기업가치({"fin": fin, "mcap": mc})
    ev0.append({"기준일": f"{t:%Y-%m-%d}", "EV 값 있음": int(ev.notna().sum()), "EV ≤ 0": int((ev <= 0).sum())})
print(pd.DataFrame(ev0).set_index("기준일").T.to_string())

print("\n## 종목 구분(종목정보 X03·X04, 지금 이름)")
info = 읽기.종목정보()
name = info["코드명"].str.replace(r"\(주\)|㈜", "", regex=True).str.strip()
줄("전체 종목 / 보통주(코드 끝 0) / 그 밖(우선주 등)", f"{len(info)} / {int(info.index.str.endswith('0').sum())} / {int((~info.index.str.endswith('0')).sum())}")
줄("이름에 '스팩' / '리츠'로 끝남 / 선박투자·부동산투자 / '지주'로 끝남 / '홀딩스' 포함", f"{int(name.str.contains('스팩').sum())} / {int(name.str.contains('리츠$').sum())} / {int(name.str.contains('선박투자회사|부동산투자').sum())} / {int(name.str.contains('지주$').sum())} / {int(name.str.contains('홀딩스').sum())}")
줄("상장폐지일 있는 종목", int(info["상장폐지일"].notna().sum()))

print("\n## 관리종목·거래정지·업종·발표일(파일 있으면)")
for item, 값 in ((읽기.관리여부, "관리"), (읽기.정지여부, "정지"), (읽기.정지구분, "거래정지")):
    if 읽기.있음(item):
        x = 읽기.일간(item)
        줄(f"{item} 값 분포", pd.Series(x.to_numpy().ravel()).value_counts(dropna=False).head(8).to_dict())
    else:
        줄(item, "파일 없음")
if 읽기.있음(읽기.업종):
    x = 읽기.일간(읽기.업종)
    v = pd.Series(x.to_numpy().ravel()).dropna()
    줄("거래소 업종 값 종류 수 / 금융업 낱말(은행·보험·증권·금융·금고) 걸리는 종류", f"{v.nunique()} / {sorted(u for u in v.unique() if any(w in u for w in ('은행', '보험', '증권', '금융', '금고')))}")
if "FP56000900" in f:
    g = 포.재무가능일(("발표일", 150))
    a = g[g[지표.자산].notna()]
    줄("자산총계 있는 행 중 발표일 있음 / 발표일 ≤ 결산일이라 안 믿는 행", f"{int(a['발표일'].notna().sum())} / {len(a)}, {int((pd.to_datetime(a['FP56000900'].astype('Int64').astype(str), format='%Y%m%d', errors='coerce') <= a['결산일']).sum())}")

print("\n## 주식수 변화·수정주가")
n = 읽기.일간(읽기.주식수)
ch = n.ne(n.shift()) & n.notna() & n.shift().notna()
줄("상장주식수가 전날과 다른 종목-날 / 종목 수", f"{int(ch.sum().sum())} / {int(ch.any().sum())}")
adj = (읽기.일간(읽기.수정주가) / 읽기.일간(읽기.종가))
a2 = (adj / adj.shift() - 1).abs() > 0.01  # 수정주가 반올림 때문에 비율이 매일 조금씩 흔들려 1% 넘는 변화만 셈
줄("수정주가/종가 비율이 1% 넘게 바뀐 종목-날(수정 계수 변화 = 분할·증자 등) / 종목 수", f"{int(a2.sum().sum())} / {int(a2.any().sum())}")

print("\n## 극단 수익률(지우지 않고 표시만)")
g = 포.기준일({**포.기본설정, "기간": ("1990-01", "2026-09")})
for item in (읽기.TR, 읽기.수정주가):
    R = 포.기간수익률(읽기.상장가격(item), g)
    줄(f"{item} 상장 구간 월 수익률 > +300% / < −90% 종목-월", f"{int((R > 3).sum().sum())} / {int((R < -0.9).sum().sum())}")
