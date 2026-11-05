"""N04 (2026-11-06): 따라하기/04_신마법공식.ipynb Novy-Marx 판을 원문대로 + 짧은 시험 모드. 칸 ID로 찾아 고침(신마법 칸 지우기는 마지막에 따로)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
F = Path(__file__).resolve().parents[3] / "따라하기" / "04_신마법공식.ipynb"
nb = json.loads(F.read_text(encoding="utf-8"))
칸 = {c["id"]: c for c in nb["cells"]}


def 글(i):
    return "".join(칸[i]["source"])


def 넣기(i, s):
    칸[i]["source"] = s.splitlines(keepends=True)
    if 칸[i]["cell_type"] == "code":
        칸[i]["outputs"], 칸[i]["execution_count"] = [], None


def 바꾸기(i, a, b):
    s = 글(i)
    assert s.count(a) == 1, (i, a[:60])
    넣기(i, s.replace(a, b))


# 0절: 인용 문구(감사표 04-2, 1x)
바꾸기("91e5a12d", "Novy-Marx(NBER w15940) pp.21-22는 7절.",
     "Novy-Marx(NBER w15940)의 결합 전략은 원문 p.21(4.3.1)·p.22 표 7 Panel C(아래 '7절'은 이 노트북의 절 번호, 원문 7절은 p.40 'Explaining anomalies').")
바꾸기("91e5a12d", "참고(7절): Novy-Marx, NBER Working Paper 15940(2010년 4월판, 파일 이름은 2013이지만 표지는 April 2010. 학술지판 2013 JFE의 표 번호는 확인 안 함) 4.3.1절·표 7 Panel C 설정",
     "참고(이 노트북 7절): Novy-Marx, NBER Working Paper 15940(2010년 4월판, 파일 이름은 2013이지만 표지는 April 2010. 학술지판 2013 JFE의 표 번호는 확인 안 함) p.21(4.3.1)·p.22 표 7 Panel C 설정")

# 1절: 짧은 시험 모드(공통 지침)
바꾸기("ef7481c1", "import sys\n", "import os\nimport sys\n")
넣기("ef7481c1", 글("ef7481c1") + """
시험 = os.environ.get("FOLLOW_TEST") == "1"  # 짧은 시험(2026-11-06 공통 지침): 기간 약 2년, 결과는 _검증/1106/시험결과/에 씀(실제 결과 파일을 덮지 않음)
if 시험:
    평가.결과폴더 = Path.cwd().parent / "_검증" / "1106" / "시험결과"
    평가.결과폴더.mkdir(parents=True, exist_ok=True)
""")

# 2절: 기간(시험이면 약 2년)
바꾸기("72e15d0a", 'print("데이터:", 읽기.DATA, "/ 기간:", 기간)',
     '기간NM = ("2004-06", "2022-04")  # 7절 Novy-Marx: 6월 말 시작(원문 p.21 \'At the end of each June\'). 원문 기간 1963-07~2009-12(p.22)은 한국 자료로 불가. 끝 2022-04는 원문 근거 없음(기본 방법)\n'
     'if 시험:\n    기간, 기간NM = ("2004-04", "2006-03"), ("2004-06", "2006-06")\n'
     'print("데이터:", 읽기.DATA, "/ 기간:", 기간, "/ Novy-Marx 기간:", 기간NM, "/ 시험:", 시험)')

# 7절 머리
넣기("964f5a0e", """## 7. Novy-Marx(NBER w15940, 2010년 4월판) p.21(4.3.1)·p.22 표 7 Panel C 결합 전략
원문(PDF에서 글자를 뽑아 2026-11-06 다시 확인, 쪽은 논문에 찍힌 쪽):
- p.21(4.3.1) "The strategy I consider is constructed within the 500 largest non-financial stocks for which gross profits-to-assets and book-to-market are both available. Each year I rank these stocks … At the end of each June the strategy buys one dollar of each of the 150 stocks with the highest average of the profitability and value ranks, and shorts one dollar of each of the 150 stocks with the lowest average ranks."
- p.21 "average excess returns of 0.64 percent per month, and has a realized annual Sharpe ratio of 0.76", "These large firms returned on average 0.41 percent per month …, so the strategy makes 58 percent of its profits on the long side, and 42 percent on the short side". p.23 "Only one-third of each side of the strategy turns over each year."
- p.22 표 7 설명 "the sum of the firms' GPA and BM ranks within the sample (Panel C) … time-series average portfolio characteristics (portfolio GPA, portfolio BM, average firm size (ME, in $10^6), and number of firms (n)). The sample covers July 1963 to December 2009."
- p.11 각주 3 "market equity is lagged six months … Book equity is shareholder equity, plus deferred taxes, minus preferred stock, when available." 각주 4 "I lag accounting data to the end of June of the following year". p.12 표 2 설명 GP = "revenues minus cost of goods sold, Compustat REVT - COGS … scaled by assets (AT)". 비금융 = "one-digit SIC codes of six"(p.8·p.11). 무위험·FF3 요인의 출처는 4.3.1·표 7에 문장 없음(p.41 "Ken French's data library"는 원문 7절 표 15 요인 이야기, `_검증/1106/원문사양_04.md`).

우리(2026-11-06 원문대로 고침): 6월 마지막 거래일, **보통주만**(회원 결정) → 비금융(`금융업`·`투자기구`) → 그날 거래정지 아님(원문에 없음, 기본 방법 ①) → GP/A·B/M 둘 다 있음 → 시총 상위 500, 위 150 / 가운데 200 / 아래 150(`상하N`), 순위합산(평균과 순서 같음), 동일가중.
- GP/A = 매출총이익 M000904007 / 자산총계 M000901001(`지표.GPA`).
- B/M = **원문 장부가** `BP_장부원문_6개월`: (자본총계(지배) + 이연법인세부채 M000911019 − 우선주자본금 M000903008) / 6개월 전 시가총액. 이연법인세·우선주가 빈 종목은 그 항만 뺌('when available').
- 재무 = 결산 후 5개월이 지났고 결산일이 전 해인 회계연도(`재무시점=("결산후개월",5)`, `재무연도="직전년도"`: 각주 4 '다음 해 6월 말부터'. 전 해 결산이 없으면 그 종목은 그해 빠짐 = 기본 방법 ①).
- 수익률 가격 = 수정주가 S410000700(회원 결정, 배당 없음). 거래비용 0(원문에 없음, 기본 방법 ②), 무위험 = 콜금리(E11.02.003.001, 원문에 출처 없음 → 기본설정 그대로), 요인 = DataGuide 한국 요인(3FM.2B3), t = OLS(회원 결정). 원문에 없어 기본 방법으로 정한 칸은 9절 표.
- 원문 표 7의 Panel A(GPA만)·Panel B(BM만)는 결합 전략이 아니라 돌리지 않음(회원 결정 '결합 전략만'). ME는 원문 단위가 백만 달러라 대조하지 않음.
""")

# 7절 코드: 원문대로
넣기("1162853b", """nm = {**포.기본설정, "이름": "NovyMarx2013_표7C", "시장": ["KS", "KQ"], "기간": 기간NM, "기준일": "마지막거래일",
      "리밸런싱": 12, "재무시점": ("결산후개월", 5), "재무연도": "직전년도", "가격": 읽기.수정주가,
      "제외": ["보통주", "금융업", "투자기구", "거래정지", ("지표있음", {"지표들": ["GPA", "BP_장부원문_6개월"]}), ("시총상위", {"n": 500})],
      "지표": [("GPA", "높게"), ("BP_장부원문_6개월", "높게")], "합산": "순위합산", "고르기": ("상하N", 150),
      "비중": ["동일", "시총"], "거래비용": dict(수수료=0, 거래세=0, 슬리피지=0)}
assert {"M000911019", "M000903008"} <= set(읽기.재무항목()), "원문 장부가에 쓰는 이연법인세부채·우선주자본금 파일이 없음"
o = 포.실행(nm)
Fn = 평가.요인(포.기준일(nm), nm)
N = pd.DataFrame({f"{b}_{g}": o["수익률"][(b, g)] for b, g in o["수익률"]})
N["동일_H-L"], N["시총_H-L"] = N["동일_Q1"] - N["동일_Q3"], N["시총_Q1"] - N["시총_Q3"]
N = N.dropna(how="all")
표N = 평가.성과표(N, Fn, ["동일_H-L", "시총_H-L"])
display(표N)
display(o["기록"].T)
""")

# 원문 대조표(표 7 Panel C 전 칸 중 ME 뺌, p.21 Sharpe)와 p.21·23 문장 숫자: 새 칸 두 개를 1162853b 뒤에
대조 = """# 표 7 Panel C(p.22, 미국 1963-07~2009-12)와 p.21 Sharpe. Low = 아래 150(Q3), 2 = 가운데 200(Q2), High = 위 150(Q1), H-L = High − Low(동일가중)
묶음 = {"Low": "동일_Q3", "2": "동일_Q2", "High": "동일_Q1", "H-L": "동일_H-L"}
원문 = pd.DataFrame({"월 초과수익(%)": [0.15, 0.57, 0.78, 0.64], "t": [0.59, 2.89, 3.68, 5.21],
                   "FF3 α(%)": [-0.22, 0.10, 0.16, 0.39], "FF3 t": [-2.43, 1.90, 2.69, 3.77],
                   "MKT": [1.13, 1.01, 1.08, -0.05], "MKT t": [52.5, 85.3, 75.1, -1.92],
                   "SMB": [0.01, 0.03, 0.15, 0.15], "SMB t": [0.26, 1.53, 7.72, 4.38],
                   "HML": [-0.27, 0.10, 0.30, 0.56], "HML t": [-8.27, 5.31, 13.8, 15.6],
                   "GPA": [0.22, 0.38, 0.45, np.nan], "BM": [0.45, 0.68, 1.20, np.nan], "n": [150, 200, 150, np.nan],
                   "연 Sharpe": [np.nan, np.nan, np.nan, 0.76]}, index=list(묶음))
ff3 = {k: 평가.회귀(N[c] - (0 if k == "H-L" else Fn["RF"]), Fn[["MKT", "SMB", "HML"]])[2] for k, c in 묶음.items()}  # 성과()의 FF3 회귀와 같은 식, 적재값·t를 꺼내려고
특성 = []  # 포트폴리오 GPA·BM: 리밸런싱일마다 보유 종목 값의 평균 → 시점 평균(원문 'time-series average portfolio characteristics', 종목 평균인지 가중인지는 원문에 없음 → 동일 평균)
for t in sorted(o["보유"][("동일", "Q1")]):
    s = 포.재료(t, o["설정"])
    v = pd.DataFrame({"GPA": 지표.GPA(s), "BM": 지표.BP_장부원문_6개월(s)})
    특성 += [{"묶음": k, **v.reindex(o["보유"][("동일", 묶음[k][3:])][t].index).mean()} for k in ("Low", "2", "High")]
특성 = pd.DataFrame(특성).groupby("묶음").mean()
우리 = pd.DataFrame({k: {"월 초과수익(%)": 표N.loc[c, "초과평균 α(월)"] * 100, "t": 표N.loc[c, "초과평균 t(OLS)"],
                       "FF3 α(%)": 표N.loc[c, "FF3 α(월)"] * 100, "FF3 t": 표N.loc[c, "FF3 t(OLS)"],
                       **{x: ff3[k].params[x] for x in ("MKT", "SMB", "HML")}, **{f"{x} t": ff3[k].tvalues[x] for x in ("MKT", "SMB", "HML")},
                       "GPA": 특성["GPA"].get(k, np.nan), "BM": 특성["BM"].get(k, np.nan),
                       "n": o["기록"][f"편입:{c[3:]}"].mean() if k != "H-L" else np.nan,
                       "연 Sharpe": 표N.loc[c, "샤프"] if k == "H-L" else np.nan} for k, c in 묶음.items()}).T  # Sharpe = 월 평균/표준편차 × √12(원문 'realized annual' 계산법 없음 → 가장 단순)
NM대조 = pd.concat({"원문(미국 1963-07~2009-12)": 원문, "우리": 우리}, axis=1).swaplevel(axis=1)[list(원문)]
NM대조.to_csv(평가.결과폴더 / "04_NovyMarx대조.csv", encoding="utf-8-sig")  # 결과요약 노트북이 읽음(열 2단: 항목 × 원문/우리)
NM대조
"""
문장 = """# p.21·p.23 문장의 숫자. '500종목 평균'은 세 묶음 월 초과수익률 평균을 종목 수(n)로 가중한 값(500종목 동일가중 포트폴리오를 따로 돌리지 않은 근사)
a = 우리.loc[["Low", "2", "High"]]
전체 = (a["월 초과수익(%)"] * a["n"]).sum() / a["n"].sum()
롱 = (우리.loc["High", "월 초과수익(%)"] - 전체) / 우리.loc["H-L", "월 초과수익(%)"]
회전 = o["회전율"][[("동일", "Q1"), ("동일", "Q3")]].iloc[1:].mean()  # 한쪽 회전율 = 리밸런싱 때 산 비중 합, 첫 매수(=1) 뺌
NM문장 = pd.DataFrame({"원문": [8, 0.41, 0.58, 0.42, 1 / 3, 1 / 3], "우리": [우리.loc["H-L", "월 초과수익(%)"] * 12, 전체, 롱, 1 - 롱, 회전.iloc[0], 회전.iloc[1]],
                     "원문 쪽": ["p.21 'almost eight percent per year'", "p.21", "p.21", "p.21", "p.23", "p.23"]},
                    index=["H-L 연 초과수익(%, 월 × 12)", "500종목 평균 월 초과수익(%)", "롱 쪽 이익 비중", "숏 쪽 이익 비중", "롱 쪽 한 해 회전율", "숏 쪽 한 해 회전율"])
NM문장.to_csv(평가.결과폴더 / "04_NovyMarx문장대조.csv", encoding="utf-8-sig")
NM문장
"""
i = next(j for j, c in enumerate(nb["cells"]) if c["id"] == "1162853b")
새 = [{"cell_type": "code", "id": cid, "metadata": {}, "execution_count": None, "outputs": [], "source": src.splitlines(keepends=True)}
     for cid, src in (("4b7c0e21", 대조), ("4b7c0e22", 문장))]
if not any(c["id"] == "4b7c0e21" for c in nb["cells"]):
    nb["cells"][i + 1:i + 1] = 새

# 8절 차이 이유: Novy-Marx·벤치마크 줄
바꾸기("914fbdd5", "- **Novy-Marx 참고판**: 시장·기간(미국 1963~2009 vs 한국), 장부가 정의(원문은 자본 + 이연법인세 − 우선주, 우리는 자본총계(지배)). B/M 6개월 전 시가·150/200/150·재무 시점은 2026-11-04 원문대로 고침(11절).",
     "- **Novy-Marx 결합 전략**: 시장·기간(미국 1963~2009 vs 한국), 비금융 판정(SIC 대신 거래소 업종), 요인·무위험(원문 4.3.1·표 7에 출처 문장 없음, 미국 자료일 것)은 한국 자료(DataGuide 요인·콜금리)로 대신해 바꿀 수 없음. 장부가(각주 3)·보통주·Low·2 줄은 2026-11-06 원문대로 고침, B/M 6개월 전 시가·150/200/150·재무 시점은 2026-11-04 고침(11절).")
바꾸기("914fbdd5", "Novy-Marx 참고판은 TR 가격이라 정보비율·CAPM α가 배당만큼 높게 나온다.",
     "Novy-Marx 판도 2026-11-06부터 수정주가(회원 결정; 원문 4.3.1·표 7에는 수익률 가격 문장 없음).")

# 9절 표: Novy-Marx 줄 고치고 더함
바꾸기("7a9f22d6", "| Novy-Marx 대형주 500 | GP/A·BM 둘 다 있는 비금융 500 | 비금융 → GPA·BP 둘 다 있음(`지표있음`) → 시총 500 | 2026-11-04 원문 순서대로 고침(전에는 시총 500을 먼저 고른 뒤 빈칸 제외) |",
     "| Novy-Marx 대형주 500 | GP/A·BM 둘 다 있는 비금융 500(p.21) | 보통주 → 비금융 → 거래정지 아님 → GPA·BP 둘 다 있음(`지표있음`) → 시총 500 | 2026-11-04 원문 순서대로 고침(전에는 시총 500을 먼저 고른 뒤 빈칸 제외) |\n"
     "| Novy-Marx 우선주 | 원문 문장 못 찾음 | 보통주만(코드 끝자리 0, `보통주`) | 회원 결정 2026-11-06 '보통주만 해'(전에는 거르기 없어 우선주가 500 안에 따로 들 수 있었음) |\n"
     "| Novy-Marx 장부가 | 자본 + 이연법인세 − 우선주, 'when available'(각주 3, p.11). Compustat 계층: SEQ → CEQ+PSTX → AT−LT, TXDITC → TXDB/ITCB, PSTKR → PSTKRL → PSTK | 자본총계(지배) + 이연법인세부채(M000911019) − 우선주자본금(M000903008), 빈 항은 뺌(`BP_장부원문_6개월`, 2026-11-06 본문으로) | 한국 항목 하나씩으로 대신. 자본총계(지배)가 빈 종목은 원문이면 AT−LT로 채우지만 우리는 그 종목이 빠짐 |\n"
     "| Novy-Marx GP/A | (REVT − COGS)/AT(표 2 설명, p.12) | 매출총이익(M000904007)/자산총계(M000901001) | 매출총이익 항목 = 매출액 − 매출원가. 두 값이 같은지는 숫자로 대조 안 함 |\n"
     "| Novy-Marx 재무 연도 | 다음 해 6월 말부터(각주 4) | 결산 후 5개월이 지났고 결산일이 전 해인 회계연도(`재무연도='직전년도'`, 2026-11-06) | 전 해 결산이 없으면 그해 빠짐(기본 방법 ①). 전에는 2년 안 가장 최근 행 |\n"
     "| Novy-Marx 시장 | 미국(4.3.1에 거래소 문장 없음) | 유가증권 + 코스닥(KS·KQ) | 원문에 없음 → 기본 방법 ②(상장 전체) |\n"
     "| Novy-Marx 거래정지 | 원문 없음 | 리밸런싱일에 거래정지인 종목 제외(`거래정지`) | 원문에 없음 → 기본 방법 ①(그날 거래 가격이 없음 → 그 종목을 그해 뺌, `_검증/1106/원문사양_04.md`) |\n"
     "| Novy-Marx 시총 500의 날짜 | 원문 없음 | 리밸런싱일(6월 마지막 거래일) 시가총액 | 원문에 없음 → 기본 방법 ② |\n"
     "| Novy-Marx 기간 | 1963-07~2009-12(p.22 표 7) | 2004-06~2022-04(6월 말 18번) | 한국 자료. 시작 = 우동호와 같은 해 6월, **끝 달 2022-04는 원문 근거 없음**(기본 방법으로 둠) |\n"
     "| Novy-Marx 수익률 가격 | 4.3.1·표 7에 문장 없음 | 수정주가 S410000700 | 회원 결정 2026-11-06(전에는 TR) |\n"
     "| Novy-Marx 거래비용 | 원문 없음(p.23 회전율만) | 0 | 원문에 없음 → 기본 방법 ② |\n"
     "| Novy-Marx 같은 순위 | 원문 없음 | 순위 평균(pandas 기본), 같은 점수는 정렬 순서 | 원문에 없음 → 기본 방법 ② |\n"
     "| Novy-Marx Sharpe 연율화·t | 'realized annual Sharpe ratio'(p.21), t 계산법 문장 없음 | 월 평균/표준편차 × √12, t = OLS | Sharpe는 기본 방법 ②, OLS는 회원 결정(NW 뺌) |\n"
     "| Novy-Marx 특성 GPA·BM·n | 시점 평균 포트폴리오 특성(표 7) | 리밸런싱일마다 보유 종목 평균 → 시점 평균, n = 편입 수 평균. ME는 단위(백만 달러)가 달라 대조 안 함 | 포트폴리오 평균 방식은 원문에 없음 → 기본 방법 ②(동일 평균) |\n"
     "| Novy-Marx 500종목 평균·롱 쪽 비중 | 0.41%, 58%/42%(p.21) | 세 묶음 월 초과수익을 종목 수로 가중한 평균으로 계산 | 500종목 포트폴리오를 따로 돌리지 않은 근사 |")

바꾸기("7a9f22d6", "| Novy-Marx 요인·무위험 | Ken French 미국 요인·미국 금리 | DataGuide 한국 요인(3FM.2B3)·콜금리 | 시장이 다름 |",
     "| Novy-Marx 요인·무위험 | 4.3.1·표 7에 출처 문장 없음(p.41 'Ken French' 문장은 원문 7절 표 15 요인 이야기, 2026-11-06 원문사양_04로 바로잡음) | DataGuide 한국 요인(3FM.2B3)·콜금리(E11.02.003.001) | 미국 자료일 것이라 한국 자료로 대신(바꿀 수 없음). 무위험은 기본설정 그대로(기본 방법 ②) |")

바꾸기("7a9f22d6", "| Novy-Marx B/M 시가 | 6개월 전 시가(각주 3) | 같음(`BP_6개월`, 2026-11-04 고침. 예전 그날 시가) | — |",
     "| Novy-Marx B/M 시가 | 6개월 전 시가(각주 3) | 같음(2026-11-04 고침. 예전 그날 시가. 2026-11-06부터 장부가도 원문 정의 `BP_장부원문_6개월`) | — |")
바꾸기("7a9f22d6", "| 12월 결산 → 5월 말부터라 6월 마지막 거래일에 씀. 1월 결산은 6월 30일이 거래일인 해만 그해 회계연도가 들어감(한국에 거의 없음, 확인 안 함) |",
     "| 12월 결산 → 5월 말부터라 6월 마지막 거래일에 씀. 2026-11-06부터 결산일이 전 해인 회계연도만 써서(위 '재무 연도' 줄) 1월 결산도 원문처럼 전 해 결산을 씀 |")

# 11절 진단: 바탕을 7절 본문으로(보통주·수정주가·직전년도), 본문 = 장부가 원문 줄
바꾸기("e9b3c54e", "# 예전 판 → 원문 규칙을 하나씩 더함. 마지막 줄 = 7절 본문",
     "# 예전 판 → 원문 규칙을 하나씩 더함. 마지막 줄 = 7절 본문(2026-11-06: 모든 줄에 7절 본문의 보통주·수정주가·직전년도 재무를 깔았음)")
바꾸기("e9b3c54e", '"+ 재무 결산 후 5개월(= 7절 본문)"', '"+ 재무 결산 후 5개월"')
바꾸기("e9b3c54e", '단계["+ 장부가 = 자본 + 이연법인세 − 우선주(각주 3)"]', '단계["+ 장부가 = 자본 + 이연법인세 − 우선주(각주 3, = 7절 본문)"]')
바꾸기("e9b3c54e", '"제외": ["금융업", "투자기구", ("지표있음"', '"제외": ["보통주", "금융업", "투자기구", "거래정지", ("지표있음"')
바꾸기("70a16c69", "| B/M | 장부가 = 자본 + 이연법인세 − 우선주, 시가는 6개월 전(각주 3, p.11) | 자본총계(지배)/6개월 전 시가총액(장부가 정의는 다름: 이연법인세·우선주 따로 받지 않음) |",
     "| B/M | 장부가 = 자본 + 이연법인세 − 우선주, 시가는 6개월 전(각주 3, p.11) | (자본총계(지배) + 이연법인세부채 − 우선주자본금)/6개월 전 시가총액(2026-11-06 본문으로) |")
바꾸기("70a16c69", "| 대형주 500 | 비금융, GP/A·B/M 둘 다 있는 종목 중 시총 상위 500(p.21·22) | 금융업·투자기구 제외 → 둘 다 있음 → 시총 상위 500(유가+코스닥) |",
     "| 대형주 500 | 비금융, GP/A·B/M 둘 다 있는 종목 중 시총 상위 500(p.21·22) | 보통주 → 금융업·투자기구 제외 → 둘 다 있음 → 시총 상위 500(유가+코스닥) |")
바꾸기("70a16c69", "| 리밸런싱·재무 | 6월 말 연 1회, 다음 해 6월 말부터(각주 4) | 6월 마지막 거래일, 결산 후 5개월 |",
     "| 리밸런싱·재무 | 6월 말 연 1회, 다음 해 6월 말부터(각주 4) | 6월 마지막 거래일, 결산 후 5개월·결산일이 전 해 |")
바꾸기("f7200be1", "| 장부가 정의 | 각주 3 자본 + 이연법인세 − 우선주('when available') | 위 표 '+ 장부가' 줄(이연법인세부채 M000911019·우선주자본금 M000903008 파일이 있을 때만, 없으면 출력에 빠졌다고 나옴) | — | 그 줄과 본문 줄 차이 |",
     "| 장부가 정의 | 각주 3 자본 + 이연법인세 − 우선주('when available') | 위 표 '+ 장부가' 줄 = 7절 본문(2026-11-06부터) | — | — |")
바꾸기("f7200be1", "숫자는 위 코드 출력이 정본이다. 7절 본문은 원문 문장이 받치는 세 규칙(150/200/150, 6개월 전 시가, 다음 해 6월 말)으로 바꿨다.",
     "숫자는 위 코드 출력이 정본이다. 7절 본문은 원문 문장이 받치는 네 규칙(150/200/150, 6개월 전 시가, 다음 해 6월 말, 장부가 정의)으로 바꿨다.")

# 12절: 시험 때 결과폴더가 바뀌어도 csv 경로는 저장소 _검증
바꾸기("16dc1391", '평가.결과폴더.parent / "_검증" / "2차_07_신마법.csv"', 'Path.cwd().parent / "_검증" / "2차_07_신마법.csv"')

F.write_text(json.dumps(nb, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print("고침", F)
