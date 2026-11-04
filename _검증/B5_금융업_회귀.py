"""금융업 WICS 보조 판정(2026-11-04) 회귀 검사: 예전(이름 규칙만) 대 새(이름 규칙 또는 WICS 금융). 바뀐 보유 종목이 모두 새로 빠진 종목(업종 빈칸·WICS 금융)인지. 공통/에서 PYTHONPATH=."""
import pandas as pd
import 데이터읽기 as 읽기
import 포트폴리오 as 포
import 종목거르기

새 = 종목거르기.금융업
def 예전(s, c, 낱말=("은행", "보험", "증권", "금융", "금고")):
    krx = 종목거르기.그날(읽기.업종, s["t"], c)
    name = 읽기.종목정보()["코드명"].reindex(c).str.replace(r"\(주\)|㈜", "", regex=True).str.strip()
    return c[~(krx.str.contains("|".join(낱말), na=False) | (krx.isna() & name.str.contains("은행|보험|증권|금융|금고|캐피탈|카드|저축|신금|리츠|스팩|지주$", na=False)))]

빠진 = set(pd.read_csv("../_검증/B5_금융업이름_목록_첫거래일.csv")["코드"]) if False else None
for name, cfg in {"01 MF": {**포.우동호2023, "기간": ("2004-04", "2022-03"), "끝": "마지막거래일"},
                  "01 IMF": {**포.우동호2023, "기간": ("2004-04", "2022-03"), "끝": "마지막거래일", "지표": [("GPA", "높게"), ("EY", "높게")]},
                  "확장 기준(EY+ROC, TR, 1990-04~, 12개월)": {**포.우동호2023, "기간": ("1990-04", "2026-09"), "가격": 읽기.TR, "재무시점": ("발표일", 150), "무위험": "CD1m", "전량교체": False}}.items():
    종목거르기.금융업 = 예전; a = 포.실행(cfg)
    종목거르기.금융업 = 새; b = 포.실행(cfg)
    d = a["기록"]["금융업"] - b["기록"]["금융업"]
    print(f"===== {name}\n금융업 단계 뒤 종목 수 (예전 − 새), 0 아닌 기준일 {int((d != 0).sum())}개, 합 {int(d.sum())}, 최대 {int(d.max())}")
    바뀐 = 0
    for k in a["보유"]:
        for t in a["보유"][k]:
            x, y = set(a["보유"][k][t].index), set(b["보유"][k][t].index)
            if x != y:
                바뀐 += 1
                print(f"  보유 바뀜 {k} {t:%Y-%m-%d}: 빠짐 {sorted(x - y)} 들어옴 {sorted(y - x)}")
    print("보유 바뀐 리밸런싱 수:", 바뀐, "/ 누적 예전:", ((1 + a["수익률"]).prod() - 1).round(4).to_dict(), "새:", ((1 + b["수익률"]).prod() - 1).round(4).to_dict())
