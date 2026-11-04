"""01 우동호(2023) 표준편차·샤프·MDD 정의 역산(지시 2026-11-04 1번).
KOSPI는 누적이 원문과 같으므로 데이터 문제가 아니다 → 원문 KOSPI 숫자(표 2, p.514: 누적 212.39%, MDD −54.54%, 표준편차 83.49%, 샤프 1.34, 정보비율 0.00)가
나오는 정의를 후보마다 계산해 본다. 찾은 정의를 MF·IMF(본문 설정, 일간 포트폴리오 가치)에 그대로 적용해 원문과 비교한다.
일간 포트폴리오 = 노트북과 같은 보유 비중(포.실행 결과)을 일간 수익률 표에 넣은 포.보유(같은 함수). 월로 묶으면 노트북 월수익률과 같은지 확인한다.
실행: 공통 폴더에서 python ../_검증/01_정의역산.py > ../_검증/01_정의역산_결과.txt"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "공통"))
import numpy as np
import pandas as pd

import 데이터읽기 as 읽기
import 포트폴리오 as 포

시작, 끝 = "2004-04-01", "2022-03-31"  # 원문 기간(p.512 '2004년 4월 첫 거래일부터 … 2022년 3월 마지막 거래일')
원문 = pd.DataFrame({"MF": [9.8035, -0.5034, 0.9479, 2.42, 1.48], "IMF": [10.2791, -0.4962, 0.8857, 2.58, 1.57],
                    "KOSPI": [2.1239, -0.5454, 0.8349, 1.34, 0.00]}, index=["누적", "MDD", "표준편차", "샤프", "정보비율"]).T

# 일간 국고 3년(X02 E11.02.011.001, 연 %) — 원문 무위험 '3년 만기 국고채'(p.513). 월말 값은 RF_FILE E11.02.003.008
x = pd.read_excel(next(읽기.XLSX.glob("X02_*.xlsx")), header=None)
y일 = pd.Series(x.iloc[14:, 1].astype(float).to_numpy(), pd.to_datetime(x.iloc[14:, 0])).dropna()
y월 = 읽기.무위험("E11.02.003.008") * 1200


def 후보(r, 일간=True, 벤치=None):
    """r: 기간 수익률(일간 또는 월간). 여러 정의 후보를 dict로."""
    N = len(r)
    w = (1 + r).cumprod()
    out = {"누적": w.iloc[-1] - 1, "MDD": (w / w.cummax().clip(lower=1) - 1).min()}
    sd = r.std()
    out |= {"SD×√N": sd * np.sqrt(N), "SD×√N(ddof0)": r.std(ddof=0) * np.sqrt(N), "SD×√(연간 횟수)": sd * np.sqrt(252 if 일간 else 12)}
    if 일간:
        y = y일.reindex(r.index.union(y일.index)).ffill().reindex(r.index).shift(1)  # 전날 금리(같은 날 값과 거의 같음)
        for 나눔 in (365, 252):
            e = r - y / 100 / 나눔
            out[f"샤프:일 초과(금리/{나눔})×√N"] = e.mean() / e.std() * np.sqrt(N)
            out[f"샤프:일 초과(금리/{나눔})×√252"] = e.mean() / e.std() * np.sqrt(252)
        out["샤프:(누적 − 금리 단순합)/SD×√N"] = (out["누적"] - (y / 100 / 365).sum()) / out["SD×√N"]
    else:
        y = y월.reindex(r.index.union(y월.index)).ffill().reindex(r.index).shift(1)
        e = r - y / 1200
        out["샤프:월 초과×√N"] = e.mean() / e.std() * np.sqrt(N)
        out["샤프:월 초과×√12"] = e.mean() / e.std() * np.sqrt(12)
    if 벤치 is not None:
        a = r - 벤치.reindex(r.index)
        out["정보비율×√N"] = a.mean() / a.std() * np.sqrt(N) if a.std() else 0.0
        out["정보비율×√(연간 횟수)"] = a.mean() / a.std() * np.sqrt(252 if 일간 else 12) if a.std() else 0.0
    return pd.Series(out)


k = 읽기.지수()["I.001"].dropna()
kd = k.loc[시작:끝].pct_change().dropna()
print("== 1. KOSPI(I.001) 일간 종가, 2004-04-01 종가 → 2022-03-31 종가, 일 수 N =", len(kd))
print(후보(kd, True, kd).to_string())
km = k.reindex(포.기준일(포.우동호2023)).pct_change().dropna()
print("\n== 2. KOSPI 월간(노트북 기준일 = 월 첫 거래일, 2004-04-01 → 2022-04-01), N =", len(km))
print(후보(km, False, km).to_string())
print("\n원문 표 2(p.514):\n", 원문.to_string())

# MF·IMF 일간: 노트북 4절 본문 설정과 같은 보유 비중
설정 = {"MF": 포.우동호2023, "IMF": {**포.우동호2023, "이름": "우동호2023_IMF", "지표": [("GPA", "높게"), ("EY", "높게")]}}
p = 읽기.상장가격(읽기.수정주가)
날 = p.loc[시작:"2022-04-01"].index
Rd = 포.기간수익률(p, 날)
일 = {"KOSPI": kd}
for n, cfg in 설정.items():
    o = 포.실행(cfg)
    W = o["보유"][("동일", "상위30")]
    d = 포.보유(Rd, W, cfg["거래비용"], cfg["전량교체"])
    월 = (1 + d).groupby(np.searchsorted(o["수익률"].index, d.index)).prod() - 1  # 기준일 구간마다 묶기(구간 끝 = 기준일 당일 포함)
    m = o["수익률"][("동일", "상위30")].dropna()
    print(f"\n{n}: 일간을 월로 묶은 것과 노트북 월수익률 차이 최대 {np.abs(월.to_numpy() - m.to_numpy()).max():.2e} ({len(m)}달)")
    일[n] = d.loc[:끝]
일 = pd.DataFrame(일)
표 = pd.DataFrame({c: 후보(일[c].dropna(), True, 일["KOSPI"]) for c in 일}).T
print("\n== 3. 일간 정의 후보를 MF·IMF·KOSPI에 적용(2004-04-01 → 2022-03-31)\n", 표.to_string())
일.to_pickle(Path(__file__).with_name("01_일간가치.pkl"))
