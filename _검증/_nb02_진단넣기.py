import json
p = "따라하기/02_NH_밸류.ipynb"
nb = json.load(open(p, encoding="utf-8"))
C = nb["cells"]
src = lambda i: "".join(C[i]["source"])
def put(i, s): C[i]["source"] = s.splitlines(keepends=True)

# 7절: 벤치마크를 원문대로 I.401
s = src(15); o = "원문 벤치마크(KOSPI 200 동일가중지수)는 데이터에 없어 코스피(I.001)를 놓는다."
assert o in s; put(15, s.replace(o, "벤치마크는 원문대로 KOSPI 200 동일가중지수(X01 `I.401` '코스피 200 동일가중지수', 종가지수, 값은 2009-01-02부터)를 놓는다(2026-11-04 고침, 예전엔 '데이터에 없음'으로 잘못 보고 코스피 I.001). 배당 포함 여부는 X01에 적혀 있지 않다(확인 안 함). 코스피(I.001)는 참고로 함께 둔다."))
s = src(16); o = '평가.성과표(pd.DataFrame({k: o["수익률"][("동일", "Q1")] for k, o in 현실.items()} | {"KOSPI": F["시장"]}).dropna(how="all"), F)'
assert o in s
put(16, s.replace(o, '''F200 = 평가.요인(포.기준일(기본), {**기본, "시장지수": "I.401"})  # 원문 벤치마크(p.26). 정보비율·CAPM α가 이 지수 기준
현실표 = pd.DataFrame({k: o["수익률"][("동일", "Q1")] for k, o in 현실.items()} | {"KOSPI200 동일가중(I.401)": F200["시장"], "KOSPI(I.001, 참고)": F["시장"]})
평가.성과표(현실표.loc["2009-02":], F200.loc["2009-02":])  # I.401 첫 값 2009-01-02 → 첫 수익률 달 = 2009-02 말'''))
s = src(24); o = "| 현실판 벤치마크 | KOSPI 200 동일가중지수 | 코스피(I.001) | 데이터에 없음 |"
assert o in s; put(24, s.replace(o, "| 현실판 벤치마크 | KOSPI 200 동일가중지수 | 같음: X01 `I.401`(2026-11-04 고침. 예전엔 I.001) | 예전 '데이터에 없음'은 틀림(X01에 있음) |"))

md = '''## 14. 원문 차이 진단 (2026-11-04)
값을 원문에 맞추려고 고르지 않는다. 원인 후보마다 그 원인만 바꿔 돌린 숫자를 원문 숫자(그림 19, p.16)와 나란히 둔다. 판정 기준은 돌리기 전에 아래처럼 정했다.
- **'경계'**: 두 전략의 위험조정수익률(월평균/월표준편차) 차이를 Jobson·Korkie(1981) 식을 Memmel(2003)이 고친 식으로 검정해 p > 0.05이면, 순위가 '같음/다름'이 아니라 '경계'(순위를 가를 만큼 차이가 크지 않음). 누적·평균 차이는 두 월수익률 차이의 평균을 NW t로 검정(같은 기준). 두 논문 원문은 확인 안 함(식은 `평가.샤프차이` 설명).
- **옮기지 않은 원문 결론**(0단계 대조 28줄): 문장마다 판정 기준을 표에 같이 적는다. '월등'·'다소 부진'처럼 숫자 기준이 없는 말은 우리가 읽은 기준을 적는다.
- **원인 바꾸기**: (가) 재무 반영 180일, (나) 발표 당일부터 쓰기(원문 '발표 월의 월말'에 더 가까운 쪽: 발표일이 그 달 마지막 거래일이어도 그날 씀), (다) 지표를 원문처럼 배수 그대로(P/B 등 낮은 쪽이 1분위 → 적자·자본잠식 종목이 '싼 쪽'에 섞임). 분기 재무는 받지 않아(`_검증/추가로_받을것.md` 7절) 바꿔 볼 수 없다.'''

code1 = '''# (1) '경계': Multi-Metric과 단일 지표 1분위의 위험조정수익률 차이(원문 주장 3), LS 누적 상위 2와 3위 차이(원문 주장 2)
q1 = Q1.drop(columns="KOSPI")
경계 = pd.DataFrame({f"Multi-Metric 대 {n}": 평가.샤프차이(q1["Multi-Metric"], q1[n]) for n in 지표명}).T
경계["판정"] = np.where(경계["p"] > 0.05, "경계", np.where(경계["차이"] > 0, "Multi가 높음", "Multi가 낮음"))
display(경계.style.set_caption("Multi-Metric 대 단일 지표 1분위: 월평균/월표준편차 차이 검정").format(precision=4))
순 = 누적LS.sort_values(ascending=False)
ls경계 = pd.DataFrame({f"{a} 대 {순.index[2]}": 평가.평균차이(LS[a], LS[순.index[2]]) for a in 순.index[:2]}).T
ls경계["판정"] = np.where(ls경계["p"] > 0.05, "경계", "차이 있음")
display(ls경계.style.set_caption(f"LS 누적 상위 2({', '.join(순.index[:2])}) 대 3위: 월 LS 차이 평균 검정").format(precision=4))'''

code2 = '''# (2) 옮기지 않은 원문 결론 판정(원문 쪽·그림 번호, 판정 기준)
누적Q1 = (1 + q1).prod() - 1
최고단일 = 누적Q1.drop("Multi-Metric").idxmax()
월등 = 평가.평균차이(q1["Multi-Metric"], q1[최고단일])
ls10 = (1 + LS.loc["2010":]).prod() - 1
pe전, pe후 = [(1 + x).prod() ** (12 / len(x)) - 1 for x in (LS["P/E"].loc[:"2014"].dropna(), LS["P/E"].loc["2015":].dropna())]
주기 = {k: 포.실행({**기본, "지표": [("BP", "높게")], "리밸런싱": k}) for k in (1, 3, 6, 12)}
주기LS = pd.DataFrame({f"{k}개월": o["수익률"]["동일"]["Q1"] - o["수익률"]["동일"]["Q5"] for k, o in 주기.items()})
주기누적 = (1 + 주기LS).prod() - 1
본현실 = 현실표["현실판_비용월0.2%(본)"].loc["2009-02":].dropna()
벤치 = F200["시장"].reindex(본현실.index)
초과 = 평가.평균차이(본현실, 벤치)
판정 = lambda ok, p: "같음" if ok and p <= 0.05 else ("경계" if ok else "다름")
더주장 = pd.DataFrame([
    ["p.15 그림 18", "Multi-Metric 1분위 누적이 단일 지표 1분위보다 '월등하게 우수'", "Multi 누적이 단일 최고보다 크고, 월 차이 평균 p ≤ 0.05(크기만 크고 p > 0.05면 경계)",
     f"Multi {누적Q1['Multi-Metric']:.3f}, 단일 최고 {최고단일} {누적Q1[최고단일]:.3f}, p = {월등['p']:.3f}", 판정(누적Q1.idxmax() == "Multi-Metric", 월등["p"])],
    ["p.14 그림 17", "2010년 이후로 한정해도 P/B·P/E가 가장 효과적", "2010-01 말~ LS 누적 상위 2가 P/B·P/E",
     ", ".join(f"{k} {v:.3f}" for k, v in ls10.sort_values(ascending=False).items()), "같음" if set(ls10.nlargest(2).index) == {"P/B", "P/E"} else "다름"],
    ["p.14", "P/E는 2015년 이후 다소 부진", "(우리가 읽은 기준) P/E LS 연환산이 2015년 이후 < 2014년까지",
     f"~2014 {pe전:.4f}, 2015~ {pe후:.4f}", "같음" if pe후 < pe전 else "다름"],
    ["p.18 그림 23·24", "P/B LS는 1개월 리밸런싱이 가장 좋음(1·3·6·12개월 비교)", "LS 누적이 1개월에서 가장 큼",
     ", ".join(f"{k} {v:.3f}" for k, v in 주기누적.items()), "같음" if 주기누적.idxmax() == "1개월" else "다름"],
    ["p.26 그림 36", "현실판(비용 월 0.2%)이 KOSPI 200 동일가중지수를 Outperform", "같은 달 누적이 I.401보다 크고, 월 차이 평균 p ≤ 0.05(크기만 크면 경계)",
     f"현실판 {(1 + 본현실).prod() - 1:.3f}, I.401 {(1 + 벤치).prod() - 1:.3f}, p = {초과['p']:.3f}", 판정((1 + 본현실).prod() > (1 + 벤치).prod(), 초과["p"])],
    ["p.19~24", "애널리스트 추정 밸류·시총·유동성·코스닥 결론", "—", "안 함: 애널리스트 추정치는 받지 않음, 나머지는 원문 기본 실험 밖", "안 함"],
], columns=["원문 쪽·그림", "원문 결론", "판정 기준", "우리", "판정"])
더주장'''

code3 = '''# (3) 원인 하나씩 바꾼 뒤 그림 19 숫자(Q1 월평균/월표준편차)와 LS 누적
for n, m in 지표명.items():  # 원문 꼴 '배수 그대로'(진단용): P/B = 1 / (B/P), 낮을수록 1분위
    setattr(지표, m + "_배수", lambda s, m=m: 1 / getattr(지표, m)(s))
def 판돌리기(d, 꼴):
    res = {n: 포.실행({**기본, **d, "지표": [(m + 꼴[0], 꼴[1])]}) for n, m in 지표명.items()}
    res["Multi-Metric"] = 포.실행({**기본, **d, "지표": [(m + 꼴[0], 꼴[1]) for m in 지표명.values()], "합산": "z합산"})
    return res
판 = {"기본(본문)": 결과, "재무 180일": 판돌리기(dict(재무시점=("발표일", 180)), ("", "높게")),
     "발표 당일부터": 판돌리기(dict(재무시점=("발표당일", 150)), ("", "높게")), "배수 그대로": 판돌리기({}, ("_배수", "낮게"))}
q = lambda o: o["수익률"]["동일"]["Q1"]
rows = {}
for k, res in 판.items():
    r19 = pd.Series({n: q(o).mean() / q(o).std() for n, o in res.items()})[그림19.index]
    ls = pd.Series({n: (1 + q(o) - o["수익률"]["동일"][숏.get(n, "Q5")]).prod() - 1 for n, o in res.items() if n != "Multi-Metric"})
    rows[k] = {("그림19", n): v for n, v in r19.items()} | {("LS 누적", n): v for n, v in ls.items()} | {
        ("요약", "그림19와 차이 절대값 평균"): (r19 - 그림19).abs().mean(), ("요약", "Multi가 1위"): r19.idxmax() == "Multi-Metric",
        ("요약", "LS 상위 2 = P/B·P/E"): set(ls.nlargest(2).index) == {"P/B", "P/E"}}
원인표 = pd.DataFrame(rows)
원인표["원문"] = pd.Series({("그림19", n): v for n, v in 그림19.items()})
원인표'''

md2 = '''### 원문 차이 진단 요약
| 원인 | 근거 | 바꾼 뒤 숫자 | 원문 | 남은 차이 |
|---|---|---|---|---|
| 재무 반영 늦춤(180일) | 원문 p.14 '발표 월의 월말'. 150·180일은 원문에 없음 | (3) 표 '재무 180일' 열 | 그림 19 6칸 | (3) 표 '그림19와 차이 절대값 평균' |
| 발표 당일부터 | 원문 p.14 '발표 월의 월말'(발표일이 그 달 안이면 그 달 말에 반영) | (3) 표 '발표 당일부터' 열 | 그림 19 6칸 | 같은 칸 |
| 지표 꼴(배수 그대로) | 원문 p.14 P/B·P/E 등 배수 이름. 정렬 꼴은 원문에 없음 | (3) 표 '배수 그대로' 열 | 그림 19 6칸 | 같은 칸 |
| 분기 재무 없음 | 원문 p.14 '분기/연간' | 바꿔 볼 수 없음(자료 없음) | — | 남음 |
| Multi 대 단일 지표 순위 | 원문 그림 19 Multi 0.39 > P/B 0.34 | (1) 표 p | — | p > 0.05면 '경계' |
| 현실판 벤치마크 | 원문 p.26 KOSPI 200 동일가중지수 | 본문을 I.401로 고침(7절), (2) 표 | Outperform | (2) 표 판정 |

숫자는 위 코드 출력이 정본이다. 본문(기본) 설정은 원문 문장이 받치는 것(현실판 벤치마크 I.401)만 바꾸고, (3)의 세 판은 진단으로만 둔다(재무 반영은 원문 문장을 우리 자료로 그대로 할 수 없고, 정렬 꼴은 원문에 없음).'''

new = [{"cell_type": "markdown", "metadata": {}, "source": md.splitlines(keepends=True)}] + \
      [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": c.splitlines(keepends=True)} for c in (code1, code2, code3)] + \
      [{"cell_type": "markdown", "metadata": {}, "source": md2.splitlines(keepends=True)}]
assert src(25).startswith("## 13. 요약표용 저장")
C[25:25] = new
s = src(2); assert "import pandas as pd\n" in s and "numpy" not in s
put(2, s.replace("import pandas as pd\n", "import numpy as np\nimport pandas as pd\n"))
json.dump(nb, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(p, "a", encoding="utf-8").write("\n")
print("ok", len(C))
