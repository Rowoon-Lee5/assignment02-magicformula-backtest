"""추가 지시 E·F로 받은 결산 항목(R32~R38, R55)이 무엇을 담는지 세기만 한다(값은 그대로, 백테스트 설정은 안 바꿈).
1 중단사업이익(M000907005): 값 있는·0 아닌 종목-회계연도 수 → README '중단사업손익' 한계
2 최초치 vs 지금 값(영업이익·지배순이익·매출액·세전계속사업이익 잠정): 둘 다 있는 행, 같은 행, 상대 차이 → README 'DataGuide 최근 수정치' 한계
3 이자비용(M000906020) 빈칸인데 세전이익이 있는 행: 금융비용·순이자비용·이자발생부채 값이 있는지, 0인지 → README '이자비용 빈칸' 한계
4 01 MF 보유 종목 중 중단사업이익이 0 아닌 수
공통/에서 PYTHONPATH=. 로 실행 → _검증/추가자료_확인_결과.txt"""
import numpy as np
import pandas as pd
import 데이터읽기 as 읽기

e = 읽기.연간재무()
e = e[e["회계연도"].between(1987, 2025)]
print("연간 행", len(e), "/ 회계연도", e["회계연도"].min(), "~", e["회계연도"].max())

print("\n## 1. 중단사업이익 M000907005")
x = e["M000907005"]
print("값 있음", int(x.notna().sum()), "/ 0 아님", int((x.fillna(0) != 0).sum()), "/ 0", int((x == 0).sum()))
print("회계연도별 0 아닌 행:", (x.fillna(0) != 0).groupby(e["회계연도"]).sum().loc[lambda v: v > 0].to_dict())
print("01 기간 회계연도 2003~2020에서 0 아닌 행:", int(((x.fillna(0) != 0) & e["회계연도"].between(2003, 2020)).sum()))

print("\n## 2. 최초치 vs 지금 값(같은 회계연도 행)")
rows = {}
for 지금, 최초, 이름 in [("M000906001", "FP56000250", "영업이익"), ("M000908004", "FP56000650", "지배순이익"), ("M000904001", "FP56000150", "매출액"), ("M000908001", "FP56000450", "당기순이익"),
                       ("M000907001", "FP56000300", "세전계속사업이익(잠정)")]:
    if 최초 not in e:
        print(이름, 최초, "파일 없음"); continue
    a, b = e[지금], e[최초]
    both = a.notna() & b.notna()
    rel = ((b - a).abs() / a.abs()).where(both & (a != 0))
    rows[이름] = {"지금 값 있음": int(a.notna().sum()), "최초치 있음": int(b.notna().sum()), "둘 다": int(both.sum()),
                "같음(차이 0)": int((both & (a == b)).sum()), "상대 차이 > 1%": int((rel > 0.01).sum()), "상대 차이 > 10%": int((rel > 0.1).sum()),
                "최초/지금 비 중앙값": float((b / a).where(both & (a != 0)).median()), "최초치 첫 회계연도": int(e.loc[b.notna(), "회계연도"].min())}
print(pd.DataFrame(rows).T.to_string())

print("\n## 3. 이자비용 빈칸 + 세전이익 있음")
m = e["M000906020"].isna() & e["M000907001"].notna()
print("행", int(m.sum()))
for c, n in [("M000992009", "금융비용"), ("M000911010", "순이자비용"), ("M000991040", "이자발생부채")]:
    if c in e:
        v = e.loc[m, c]
        print(f"{n} {c}: 값 있음 {int(v.notna().sum())}, 그중 0 {int((v == 0).sum())} / 전체 행에서 0 {int((e[c] == 0).sum())}")
    else:
        print(n, c, "파일 없음")

print("\n## 4. 01 MF(본문, 상위 30 동일) 보유 종목 중 그때 쓴 회계연도에 중단사업이익이 0 아닌 수")
import 포트폴리오 as 포
cfg = {**포.우동호2023, "기간": ("2004-04", "2022-03"), "끝": "마지막거래일"}
W = 포.실행(cfg)["보유"][("동일", "상위30")]
n = {t.year: int((포.재무(t, cfg["재무시점"])["M000907005"].reindex(w.index).fillna(0) != 0).sum()) for t, w in sorted(W.items())}
print("리밸런싱 연도별:", n, "/ 합", sum(n.values()), "/ 보유 종목-해", sum(len(w) for w in W.values()))
