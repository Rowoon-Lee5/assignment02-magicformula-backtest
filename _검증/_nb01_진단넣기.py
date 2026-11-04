import json
p = "따라하기/01_우동호2023.ipynb"
nb = json.load(open(p, encoding="utf-8"))
C = nb["cells"]
src = lambda i: "".join(C[i]["source"])

md = '''## 15. 원문 차이 진단 (2026-11-04)
값을 원문에 맞추려고 고르지 않는다. 원인 후보마다 그 원인만 바꾼 숫자를 원문 숫자(표 1 p.512, 표 2·3 p.514)와 나란히 둔다.
- **(1) 표준편차·샤프·정보비율 정의**: 원문은 정의를 적지 않았다. KOSPI는 누적(2.1239)이 원문과 같아 자료 문제가 아니므로, KOSPI의 원문 숫자가 나오는 정의를 후보마다 계산해 찾았다(`_검증/01_정의역산.py`): **일간 수익률, 표준편차 × √(일 수 N = 4,452), 샤프 = 일 초과수익(국고 3년 금리/365) 평균/표준편차 × √N** → KOSPI 0.8348·1.3418(원문 0.8349·1.34). 이 정의를 MF·IMF 일간 가치(4절과 같은 보유 비중)에 그대로 쓴다. 4절 표의 '표준편차(연)'·'샤프'는 월간 × √12라 원문과 단위가 다르다.
- **(2)~(4) 표본 수·시총 1분위·설정**: `_검증/01_진단.py`를 그대로 돌린다(같은 공통 코드). 거르기 단계를 하나씩 끈 판, 시총 분위를 나누는 모집단 3가지, 설정 판 5가지.
- **본문을 바꾸지 않은 이유**: 원문 p.512 '분석대상의 기간은 매년 4월 첫 거래일부터 다음연도 3월 마지막 거래일까지로 구분'은 표 1의 해마다 기간을 나누는 문장이라, 3월 말~4월 첫 거래일 하루를 보유하지 않는다는 뜻인지 문장만으로 알 수 없다. 거래비용 문장(p.512 '증권거래수수료 0.015%, 증권거래세 0.25%, 매수매도 거래 시마다 추가 거래비용(Slippage) 0.5%')도 '매수매도 거래 시마다'가 슬리피지에만 걸리는지 거래세에도 걸리는지 문장만으로 알 수 없다. 두 판 모두 진단으로만 둔다.'''

code1 = '''# (1) 원문 표 2 정의(일간, √N)로 다시 잰 MF·IMF·KOSPI
import numpy as np, runpy
시작, 끝 = "2004-04-01", "2022-03-31"
x = pd.read_excel(next(읽기.XLSX.glob("X02_*.xlsx")), header=None)  # X02 E11.02.011.001 국고 3년 일간(연 %), 원문 무위험 p.513
국고일 = pd.Series(x.iloc[14:, 1].astype(float).to_numpy(), pd.to_datetime(x.iloc[14:, 0])).dropna()
날 = 읽기.상장가격(읽기.수정주가).loc[시작:끝].index
Rd = 포.기간수익률(읽기.상장가격(읽기.수정주가), 날)
일 = {"KOSPI": 읽기.지수()["I.001"].reindex(날).pct_change().dropna()}
for k in ["MF", "IMF"]:
    일[k] = 포.보유(Rd, 결과[k]["보유"][("동일", "상위30")], 설정[k]["거래비용"], 설정[k]["전량교체"]).loc[:끝].dropna()
def 일정의(r, b):
    N, w = len(r), (1 + r).cumprod()
    e = r - 국고일.reindex(r.index.union(국고일.index)).ffill().reindex(r.index).shift(1) / 100 / 365
    a = r - b.reindex(r.index)
    return {"일 수 N": N, "누적": w.iloc[-1] - 1, "MDD": (w / w.cummax().clip(lower=1) - 1).min(), "SD": r.std() * np.sqrt(N),
            "Sharpe": e.mean() / e.std() * np.sqrt(N), "IR": a.mean() / a.std() * np.sqrt(N) if a.std() else 0.0}
정의표 = pd.concat({"원문 표 2": 원문표.loc["전체"][["Return", "MDD", "SD", "Sharpe", "IR"]].set_axis(["누적", "MDD", "SD", "Sharpe", "IR"], axis=1),
                 "우리(일간 정의)": pd.DataFrame({k: 일정의(r, 일["KOSPI"]) for k, r in 일.items()}).T.drop(columns="일 수 N"),
                 "우리(4절 월간 × √12)": 표.loc[["MF_동일", "IMF_동일", "KOSPI"], ["누적", "MDD", "표준편차(연)", "샤프", "정보비율"]]
                     .set_axis(["MF", "IMF", "KOSPI"]).set_axis(["누적", "MDD", "SD", "Sharpe", "IR"], axis=1)}, axis=1)
정의표'''

code2 = '''# (2)~(4) 표본 수·시총 1분위·설정: _검증/01_진단.py (출력 전부, 표는 _검증/01_진단_*.csv)
진단 = runpy.run_path(str(Path.cwd().parent / "_검증" / "01_진단.py"))'''

code3 = '''# 원인별 요약: 숫자는 위 출력에서 가져옴
A, B, Cc, 정의 = 진단["A"], 진단["B"], 진단["Cc"], 정의표
판 = [c for c in A.columns if c != "원문 Number"]
가까운판 = (A[판].sub(A["원문 Number"], axis=0)).abs().mean().idxmin()
f = lambda v: f"{v:.4f}"
요약 = pd.DataFrame([
    ["표준편차·샤프 정의", "원문에 정의 없음. KOSPI 원문 숫자(표 2 p.514)가 일간 √N 정의에서만 나옴(역산)",
     f"MF SD {f(정의.loc['MF', ('우리(일간 정의)', 'SD')])}·샤프 {f(정의.loc['MF', ('우리(일간 정의)', 'Sharpe')])}, IMF SD {f(정의.loc['IMF', ('우리(일간 정의)', 'SD')])}·샤프 {f(정의.loc['IMF', ('우리(일간 정의)', 'Sharpe')])}",
     "MF 0.9479·2.42, IMF 0.8857·2.58", "정의는 맞춤(KOSPI 같음). MF·IMF 차이는 수익률 자체 차이"],
    ["표본 수(표 1 Number)", "p.512 표 1, 3.1절 거르기 조건",
     f"2004년 순위 매긴 수: 본문 {A.loc[2004, '기본']}, 유가증권만 {A.loc[2004, '기본 (유가증권만)']}, 단계 하나씩 끔 {A.loc[2004, [c for c in 판 if '안 거름' in c]].min()}~{A.loc[2004, [c for c in 판 if '안 거름' in c]].max()}. 해마다 차이 절대값 평균이 가장 작은 판: {가까운판}",
     "2004년 850 (2021년 1,955)", f"본문 해마다 차이 평균 {(A['원문 Number'] - A['기본']).mean():.1f}. 끄면 모두 늘어나 원문이 더 거름(원문 조건 중 우리에 없는 것이 있음, 확인 안 함)"],
    ["시총 1분위 모집단", "p.514 표 3: 시총 5분위로 나눈 뒤 분위마다 상위 30(나누는 모집단은 원문에 없음)",
     ", ".join(f"{k[1]} {v:.1f}배" for k, v in B["누적"].items() if k[0] == "MF"),
     "MF 44.2427배", "모집단 3가지 모두 원문보다 큼. 1분위 MF 해마다 +100% 넘은 종목 수 최대: " + ", ".join(f"{t}년 {int(n)}개" for t, n in 진단["Y"]["+100% 넘은 종목"].nlargest(2).items())],
] + [[f"설정: {k}", "p.512 문장(위 '본문을 바꾸지 않은 이유')" if k in ("3월 말→4월 첫 거래일 하루 비보유", "거래세 매수에도") else "원문 p.512(가격 = 수정주가, 재무 = 3월 말까지 공시, 비용)",
      f"MF {Cc.loc[k, 'MF']:.4f}, IMF {Cc.loc[k, 'IMF']:.4f}", "MF 9.8035, IMF 10.2791",
      f"MF {Cc.loc[k, 'MF'] - 9.8035:+.4f}, IMF {Cc.loc[k, 'IMF'] - 10.2791:+.4f}"] for k in Cc.index if k != "원문 누적(표 2)"],
    columns=["원인", "근거", "바꾼 뒤 숫자", "원문", "남은 차이"])
요약'''

md2 = '''### 원문 차이 진단 정리
- 숫자는 위 표가 정본이다. 정의(표준편차·샤프)는 원문 KOSPI 숫자로 찾았고, 그 정의로 다시 재도 MF·IMF의 누적·표준편차가 원문과 다른 것은 정의가 아니라 수익률 차이다.
- 설정 판마다 MF·IMF가 원문 쪽으로 움직이는지는 위 요약표 '남은 차이' 칸(부호가 MF·IMF 반대면 한 설정으로 둘을 함께 맞출 수 없음). 표본 수는 앞 해들은 원문이 우리보다 적고 뒤 해들(2018·2019년 등)은 많다(해마다 숫자는 (2) 출력 A1). 앞 해들은 거르기를 끄면 더 벌어진다 → 원문에 적힌 조건 밖의 거르기 또는 TS2000 자료 범위 차이일 수 있으나 원문으로 확인할 수 없다(확인 안 함).
- 시총 1분위 차이는 분위 모집단을 바꿔도 줄지 않는다((2) 출력 B1). 어느 해의 큰 수익률 종목이 차이를 만드는지는 B2·B3 출력(연도별·종목 기여).
- 원문 안에서도 다른 곳: p.512 본문 '2020년 … 평균 96.69%' 대 표 1의 2020년 98.69%.'''

new = [{"cell_type": "markdown", "metadata": {}, "source": md.splitlines(keepends=True)}] + \
      [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": c.splitlines(keepends=True)} for c in (code1, code2, code3)] + \
      [{"cell_type": "markdown", "metadata": {}, "source": md2.splitlines(keepends=True)}]
assert src(28).startswith("## 15. 요약표용 저장")
C[28]["source"] = src(28).replace("## 15. 요약표용 저장", "## 16. 요약표용 저장", 1).splitlines(keepends=True)
C[28:28] = new
json.dump(nb, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(p, "a", encoding="utf-8").write("\n")
print("ok", len(C))
