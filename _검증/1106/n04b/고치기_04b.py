"""N04b (2026-11-06 05:5x): 04 따라하기에 표 7 Panel A·B, 금융업 '원문'·투자기구 뺌, AT−LT 한계 줄, 무위험 '우리가 고른 값'. 옮김_04 nm 맞춤·원문요인 줄 뺌.
칸 출력은 건드리지 않음. 바꿀 글이 정확히 한 번 있어야 바꿈(assert)."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]


def 고치기(파일, 바꿈):
    p = root / 파일
    nb = json.loads(p.read_text(encoding="utf-8"))
    칸 = {c["id"]: c for c in nb["cells"]}
    for cid, 옛, 새 in 바꿈:
        s = "".join(칸[cid]["source"])
        assert s.count(옛) == 1, (파일, cid, s.count(옛), 옛[:80])
        s = s.replace(옛, 새)
        칸[cid]["source"] = s if isinstance(칸[cid]["source"], str) else s.splitlines(keepends=True)  # 원래 꼴(문자열/줄 목록) 유지
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


제외_옛 = '"제외": ["보통주", "금융업", "투자기구", '
제외_새 = '"제외": ["보통주", ("금융업", {"이름": "원문"}), '

# ---------------- 따라하기 04 ----------------
칸6_옛끝 = '''o = 포.실행(nm)
Fn = 평가.요인(포.기준일(nm), nm)
N = pd.DataFrame({f"{b}_{g}": o["수익률"][(b, g)] for b, g in o["수익률"]})
N["동일_H-L"] = N["동일_Q1"] - N["동일_Q3"]
N = N.dropna(how="all")
표N = 평가.성과표(N, Fn, ["동일_H-L"])  # 대조표(4절)가 쓰는 칸: 초과평균·FF3 α와 t(OLS), 샤프'''
칸6_새끝 = '''o전체 = 포.실행(nm)  # 표 7 Panel A(GPA만)·B(BM만)·C(순위합) = 같은 거르기 결과(같은 500종목)에서 한 번에(`전략들`, 열 = (판, 비중, 그룹)). 유니버스 시총 열은 안 씀


def 판(p):  # Panel p만 꺼내 전략 하나로 돌린 것과 같은 꼴로(열 (비중, 그룹), 기록 '편입:Q1' 등)
    return {**o전체, "수익률": o전체["수익률"][p], "회전율": o전체["회전율"][p],
            "보유": {k[1:]: w for k, w in o전체["보유"].items() if k[0] == p},
            "기록": o전체["기록"].rename(columns=lambda x: x.replace(f":{p}:", ":"))}


Fn = 평가.요인(포.기준일(nm), nm)
판들, Ns, 표들 = {}, {}, {}
for p in "ABC":
    판들[p] = 판(p)
    N = pd.DataFrame({f"{b}_{g}": 판들[p]["수익률"][(b, g)] for b, g in 판들[p]["수익률"]})
    N["동일_H-L"] = N["동일_Q1"] - N["동일_Q3"]
    Ns[p] = N.dropna(how="all")
    표들[p] = 평가.성과표(Ns[p], Fn, ["동일_H-L"])  # 대조표(4절)가 쓰는 칸: 초과평균·FF3 α와 t(OLS), 샤프
o, N, 표N = 판들["C"], Ns["C"], 표들["C"]  # 결합 전략(Panel C) = 아래 문장 대조·판정·저장의 본체'''

칸6 = [("1162853b", 제외_옛, 제외_새),
       ("1162853b", '"지표": [("GPA", "높게"), ("BP_장부원문_6개월", "높게")], "합산": "순위합산", "고르기": ("상하N", 150),\n      "비중": ["동일"], "거래비용": dict(수수료=0, 거래세=0, 슬리피지=0)}',
        '"지표": [("GPA", "높게"), ("BP_장부원문_6개월", "높게")], "합산": "순위합산", "고르기": ("상하N", 150),\n      "비중": ["동일"], "거래비용": dict(수수료=0, 거래세=0, 슬리피지=0),\n'
        '      "전략들": {"A": dict(지표=[("GPA", "높게")], 합산="순위합산"), "B": dict(지표=[("BP_장부원문_6개월", "높게")], 합산="순위합산"),\n'
        '               "C": dict(지표=[("GPA", "높게"), ("BP_장부원문_6개월", "높게")], 합산="순위합산")}}  # p.21 \'similarly constructed strategies based on profitability and value individually\''),
       ("1162853b", 칸6_옛끝, 칸6_새끝)]

칸8_옛 = '''# 표 7 Panel C(p.22, 미국 1963-07~2009-12)와 p.21 Sharpe. Low = 아래 150(Q3), 2 = 가운데 200(Q2), High = 위 150(Q1), H-L = High − Low(동일가중)
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
NM대조'''
칸8_새 = '''# 표 7(p.22, 미국 1963-07~2009-12) Panel A(GPA만)·B(BM만)·C(순위합)와 p.21 Sharpe(C만). Low = 아래 150(Q3), 2 = 가운데 200(Q2), High = 위 150(Q1), H-L = High − Low(동일가중)
묶음 = {"Low": "동일_Q3", "2": "동일_Q2", "High": "동일_Q1", "H-L": "동일_H-L"}
열 = ["월 초과수익(%)", "t", "FF3 α(%)", "FF3 t", "MKT", "MKT t", "SMB", "SMB t", "HML", "HML t", "GPA", "BM", "n"]
na = np.nan
원문표7 = {  # PDF 24쪽(논문 p.22)에서 옮김(2026-11-06 pymupdf 글자로 다시 확인). 줄 = Low·2·High·H-L, 열 = 위 `열`(re·[t]·α·[t]·MKT·[t]·SMB·[t]·HML·[t]·GPA·BM·n). ME는 단위($10^6)가 달라 뺌
    "A": [[0.34, 1.70, -0.17, -2.18, 1.02, 54.1, -0.03, -1.25, 0.23, 8.07, 0.13, 1.02, 150],
          [0.54, 2.37, -0.00, -0.01, 1.13, 72.7, 0.11, 5.12, 0.08, 3.48, 0.31, 0.85, 200],
          [0.63, 2.90, 0.25, 3.80, 1.03, 66.6, 0.08, 3.78, -0.17, -7.53, 0.64, 0.41, 150],
          [0.28, 2.38, 0.42, 3.90, 0.00, 0.05, 0.11, 3.20, -0.40, -10.5, na, na, na]],
    "B": [[0.35, 1.40, 0.07, 1.05, 1.10, 68.0, 0.04, 1.91, -0.49, -19.9, 0.51, 0.25, 150],
          [0.49, 2.33, -0.01, -0.22, 1.07, 78.7, 0.07, 3.66, 0.09, 4.33, 0.34, 0.58, 200],
          [0.68, 3.49, 0.02, 0.28, 1.02, 71.9, 0.06, 3.06, 0.53, 24.9, 0.22, 1.54, 150],
          [0.34, 2.22, -0.06, -0.72, -0.08, -4.49, 0.02, 0.68, 1.02, 37.0, na, na, na]],
    "C": [[0.15, 0.59, -0.22, -2.43, 1.13, 52.5, 0.01, 0.26, -0.27, -8.27, 0.22, 0.45, 150],
          [0.57, 2.89, 0.10, 1.90, 1.01, 85.3, 0.03, 1.53, 0.10, 5.31, 0.38, 0.68, 200],
          [0.78, 3.68, 0.16, 2.69, 1.08, 75.1, 0.15, 7.72, 0.30, 13.8, 0.45, 1.20, 150],
          [0.64, 5.21, 0.39, 3.77, -0.05, -1.92, 0.15, 4.38, 0.56, 15.6, na, na, na]]}
판이름 = {"A": "A GPA만", "B": "B BM만", "C": "C 순위합"}
특성값 = {}  # 포트폴리오 GPA·BM: 리밸런싱일마다 보유 종목 값의 평균 → 시점 평균(원문 'time-series average portfolio characteristics', 종목 평균인지 가중인지는 원문에 없음 → 동일 평균). 재료는 세 판이 같아 한 번만
for t in sorted(o["보유"][("동일", "Q1")]):
    s = 포.재료(t, o["설정"])
    특성값[t] = pd.DataFrame({"GPA": 지표.GPA(s), "BM": 지표.BP_장부원문_6개월(s)})
대조 = {}
for p in "ABC":
    op, Np, 표p = 판들[p], Ns[p], 표들[p]
    원문 = pd.DataFrame(원문표7[p], index=list(묶음), columns=열).assign(**{"연 Sharpe": [na, na, na, 0.76 if p == "C" else na]})
    ff3 = {k: 평가.회귀(Np[c] - (0 if k == "H-L" else Fn["RF"]), Fn[["MKT", "SMB", "HML"]])[2] for k, c in 묶음.items()}  # 성과()의 FF3 회귀와 같은 식, 적재값·t를 꺼내려고
    특성 = pd.DataFrame([{"묶음": k, **v.reindex(op["보유"][("동일", 묶음[k][3:])][t].index).mean()} for t, v in 특성값.items() for k in ("Low", "2", "High")]).groupby("묶음").mean()
    우리 = pd.DataFrame({k: {"월 초과수익(%)": 표p.loc[c, "초과평균 α(월)"] * 100, "t": 표p.loc[c, "초과평균 t(OLS)"],
                           "FF3 α(%)": 표p.loc[c, "FF3 α(월)"] * 100, "FF3 t": 표p.loc[c, "FF3 t(OLS)"],
                           **{x: ff3[k].params[x] for x in ("MKT", "SMB", "HML")}, **{f"{x} t": ff3[k].tvalues[x] for x in ("MKT", "SMB", "HML")},
                           "GPA": 특성["GPA"].get(k, np.nan), "BM": 특성["BM"].get(k, np.nan),
                           "n": op["기록"][f"편입:{c[3:]}"].mean() if k != "H-L" else np.nan,
                           "연 Sharpe": 표p.loc[c, "샤프"] if k == "H-L" else np.nan} for k, c in 묶음.items()}).T  # Sharpe = 월 평균/표준편차 × √12(원문 'realized annual' 계산법 없음 → 가장 단순)
    대조[판이름[p]] = pd.concat({"원문(미국 1963-07~2009-12)": 원문, "우리": 우리}, axis=1).swaplevel(axis=1)[list(원문)]
우리 = 대조["C 순위합"].xs("우리", axis=1, level=1)  # 아래 문장 대조·판정이 쓰는 결합 전략 값
NM대조 = pd.concat(대조, names=["판", "묶음"])
NM대조.loc["C 순위합"].rename_axis(None).to_csv(평가.결과폴더 / "04_NovyMarx대조.csv", encoding="utf-8-sig")  # 결과요약 노트북이 읽음(열 2단: 항목 × 원문/우리, 줄 = 묶음). 예전과 같은 꼴 = Panel C만
NM대조.to_csv(평가.결과폴더 / "04_NovyMarx대조_표7.csv", encoding="utf-8-sig")  # Panel A·B·C 다(줄 2단: 판 × 묶음)
NM대조'''

칸10_옛 = '''                   ("롱 쪽 이익 비중 > 숏 쪽(0.5 초과)", "p.21(58% 대 42%)", 0.58, 롱, 롱 > 0.5)],'''
칸10_새 = '''                   ("롱 쪽 이익 비중 > 숏 쪽(0.5 초과)", "p.21(58% 대 42%)", 0.58, 롱, 롱 > 0.5)]
                  + [(f"Panel {p} H-L {x} {'>' if v > 0 else '<'} 0", f"표 7 Panel {p}", v, 대조[판이름[p]].loc["H-L", (x, "우리")], (대조[판이름[p]].loc["H-L", (x, "우리")] > 0) == (v > 0))
                     for p in "AB" for x in ("월 초과수익(%)", "FF3 α(%)") for v in [대조[판이름[p]].loc["H-L", (x, "원문(미국 1963-07~2009-12)")]]],  # 표 7 Panel A·B의 부호(p.21 'for comparison', 문장 주장은 없음. B의 α −0.06은 t −0.72)'''

칸11_옛 = '''R = pd.DataFrame({(f"NovyMarx_{k}", "동일"): N[c] for k, c in 묶음.items()})
평가.저장(R, Fn, "04_NovyMarx", 롱숏=[("NovyMarx_H-L", "동일")])'''
칸11_새 = '''R = pd.DataFrame({(f"NovyMarx{'' if p == 'C' else '_' + {'A': 'GPA', 'B': 'BM'}[p]}_{k}", "동일"): Ns[p][c] for p in "CAB" for k, c in 묶음.items()})  # C = 예전 이름 그대로, Panel A·B = NovyMarx_GPA_*·NovyMarx_BM_*
평가.저장(R, Fn, "04_NovyMarx", 롱숏=[(f"NovyMarx{x}_H-L", "동일") for x in ("", "_GPA", "_BM")])'''
칸11 = [("4b7c0e24", "# 요약표용 저장: 동일가중 Low(Q3)·2(Q2)·High(Q1)·H-L 월수익률, 요인 Fn, H-L은 롱숏(초과수익 = 그대로)",
         "# 요약표용 저장: 동일가중 Low(Q3)·2(Q2)·High(Q1)·H-L 월수익률(표 7 Panel C 결합 + Panel A GPA만·B BM만), 요인 Fn, H-L은 롱숏(초과수익 = 그대로)"),
        ("4b7c0e24", 칸11_옛, 칸11_새)]

칸0 = [("91e5a12d", "비금융(`금융업`·`투자기구`) → GP/A·B/M 둘 다 있음 → 시총 상위 500, 위 150 / 가운데 200 / 아래 150(`상하N`), 순위합산(평균과 순서 같음), 동일가중.",
        "비금융(`(\"금융업\", {\"이름\": \"원문\"})`) → GP/A·B/M 둘 다 있음 → 시총 상위 500, 위 150 / 가운데 200 / 아래 150(`상하N`), 순위합산(평균과 순서 같음), 동일가중. 같은 500종목에서 GP/A 순위만(Panel A)·B/M 순위만(Panel B)으로도 같은 방법으로 고른다(p.21 \"The table also shows, for comparison, the performance of similarly constructed strategies based on profitability and value individually\", p.22 표 7 Panel A·B)."),
       ("91e5a12d", "무위험 = 콜금리(E11.02.003.001, 원문에 출처 없음 → 기본설정 그대로)",
        "무위험 = 콜금리(E11.02.003.001, 원문에 출처 없음 → 우리가 고른 값, 기존 기본설정 그대로)"),
       ("91e5a12d", "- 원문 표 7의 Panel A(GPA만)·Panel B(BM만)는 결합 전략이 아니라 돌리지 않음(회원 결정 '결합 전략만'). ME는 원문 단위가 백만 달러라 대조하지 않음.",
        "- 원문 표 7의 Panel A(GPA만)·Panel B(BM만)도 원문에 있어 같은 표본·방법으로 돌려 대조함(05:47 지시, 원문 p.21 'for comparison'). ME는 원문 단위가 백만 달러라 대조하지 않음.")]

칸7 = [("4b7c0e20", "## 4. 원문 대조: 표 7 Panel C(p.22)와 p.21·23 문장 숫자", "## 4. 원문 대조: 표 7 Panel A·B·C(p.22)와 p.21·23 문장 숫자")]

칸13 = [("7a9f22d6", "| Novy-Marx 장부가 음수 |",
         "| Novy-Marx 장부가 AT−LT | 각주 3 'or else total assets minus total liabilities (AT - LT)' | 자본총계(지배)가 빈칸이면 자산총계 − 부채총계 | 원문 글자대로(계산 그대로). 한계: AT−LT에는 비지배지분이 들어 지배 기준(자본총계(지배))과 섞일 수 있음 |\n| Novy-Marx 장부가 음수 |"),
        ("7a9f22d6", "| Novy-Marx 비금융 | SIC 첫 자리 6 제외 | 거래소 업종 낱말·이름 규칙(`금융업`) + `투자기구` | 한국 자료에 SIC 없음 |",
         "| Novy-Marx 비금융 | 'non-financial'(p.21·p.22 표 7 설명), 'The sample excludes financial firms (those with one-digit SIC codes of six)'(p.8) | `(\"금융업\", {\"이름\": \"원문\"})`: 거래소 업종(CP10001090)에 은행·보험·증권·금융·금고, 업종이 빈 날은 이름에 은행·보험·증권·금융·금고·캐피탈·카드·저축·신금 또는 그날 WICS '금융' | 한국 자료에 SIC 없음. 한계: SIC 첫 자리 6(SIC 분류표의 금융·보험·부동산, 원문에는 '6'만 적힘)에는 부동산·투자회사도 드는데 우리 판정은 금융 낱말뿐이라 리츠·선박투자·부동산투자회사·지주회사가 표본에 남을 수 있음. 원문에 따로 없는 '투자기구' 거르기는 뺌(회원 05:57) |"),
        ("7a9f22d6", "| DataGuide 한국 요인(3FM.2B3)·콜금리(E11.02.003.001) | 미국 자료일 것이라 한국 자료로 대신(바꿀 수 없음). 무위험은 기본설정 그대로(기본 방법 ②) |",
         "| DataGuide 한국 요인(3FM.2B3)·콜금리(E11.02.003.001) | 미국 자료일 것이라 한국 자료로 대신(바꿀 수 없음). 요인은 과제 공지대로 DataGuide. 무위험 콜금리는 우리가 고른 값(기존 기본설정 그대로, 기본 방법 ② 아님) |"),
        ("7a9f22d6", "| Novy-Marx 묶음 크기 | 150/200/150 | 같음(`상하N`, 2026-11-04 고침. 예전 3등분) | — |",
         "| Novy-Marx 묶음 크기 | 150/200/150 | 같음(`상하N`, 2026-11-04 고침. 예전 3등분) | — |\n| Novy-Marx 표 7 Panel A·B | 'similarly constructed strategies based on profitability and value individually'(p.21), 표 7 Panel A(GPA)·B(BM), 같은 500 표본(p.22 표 설명 'Portfolios are tertile sorted on GPA (Panel A), BM (Panel B)') | 같은 거르기 결과(같은 500종목)에서 지표 하나 순위로 150/200/150, 동일가중(`포.실행`의 `전략들`). 대조는 4절 `04_NovyMarx대조_표7.csv`, 부호 판정은 `04_NovyMarx판정.csv` | 원문대로(05:47 지시) |")]

고치기("따라하기/04_신마법공식.ipynb", 칸0 + 칸6 + 칸7 + [("4b7c0e21", 칸8_옛, 칸8_새), ("4b7c0e23", 칸10_옛, 칸10_새)] + 칸11 + 칸13)

# ---------------- 옮김 04 ----------------
옮김 = [("fd7e8b71", '\nF = F.drop(columns=["SMB", "HML", "MOM"]).join(포.원문요인(설정["신마법공식"]))', ""),
        ("1d043c03", "요인 SMB·HML·MOM = `포.원문요인`(우동호 p.513 30/30, 01 따라하기와 같음)", "요인 = DataGuide SMB·HML·MOM(`평가.요인`, 과제 공지 05:35: 요인은 DataGuide, `포.원문요인`은 부르지 않음)"),
        ("1ae4b16e", '신마법·우동호IMF = `포.우동호2023`(재무 `"재무연도": "직전년도"`), 요인 SMB·HML·MOM = `포.원문요인`(01 따라하기와 같음, 우동호 p.513 30/30).',
         "신마법·우동호IMF = `포.우동호2023`(확장연구 기준, master 때와 같은 동작), 요인 = DataGuide SMB·HML·MOM(과제 공지 05:35, `포.원문요인`은 부르지 않음)."),
        ("94b3ab7c", 제외_옛, 제외_새),
        ("ba880694", 제외_옛, 제외_새),
        ("3e362575", "| 보통주·금융업·투자기구 제외 → 둘 다 있음 → 시총 상위 500(유가+코스닥) |", "| 보통주·금융업(`이름=\"원문\"`) 제외 → 둘 다 있음 → 시총 상위 500(유가+코스닥) |"),
        ("3e362575", "| 거래소 업종 낱말·이름 규칙 + `투자기구` |", "| 거래소 업종 낱말·이름 규칙(`(\"금융업\", {\"이름\": \"원문\"})`, 투자기구 거르기 없음: 05:57) |")]
고치기("연구/따라하기에서_옮김_04.ipynb", 옮김)
print("끝")
