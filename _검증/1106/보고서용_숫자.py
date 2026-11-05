r"""B4 보고서용 숫자 모음(md). 숫자는 결과 파일에서 읽기만(csv 칸 글자 그대로, 표시만 유효숫자 6자리로 반올림).
성과 칸(누적·연환산·SD·샤프·MDD·IR·CAPM/FF3/Carhart α와 t(OLS))은 결과 pkl의 R·F에 공통 `평가.성과`(노트북과 같은 함수)를 그대로 씀.
NW 칸('NW'가 이름에 든 칸)은 쓰지 않는다. 리밸런싱 주기 비교는 뺀다(회원 결정 2026-11-06 03:46: 표6은 자리만, 비용 표는 기준 주기 줄만).
묶음(조정자 지시 03:53): ①01 ②02 ③03 ④04 ⑤확장연구(비중·지표·순서·거래비용) ⑥기간별·요약표. 묶음마다 조각 md(<조각>\묶음N.md), --합치기로 보고서 표 순서대로 한 md.
보고서 표 순서: 표0 MF·IMF 원문 대조, 표1 문헌별 주장, 표2·3 성과, 표4 기간별, 표5 비중, 표6 주기(뺌), 표7 지표 4×4, 표8 고르는 기간/검증 기간, 표9 순서, 표10·11 분위·롱숏 Carhart, 부록(거래비용 등).
쓰는 법: python 보고서용_숫자.py <결과 폴더(결과_월수익률·결과_전략수익률이 든 곳)> <출력 md> [--노트북 <제출 ipynb>] [--공통 <공통 폴더>] [--조각 <폴더>] [--묶음 N | --합치기]
  --묶음 N = 그 묶음 조각만 씀, --합치기 = 있는 조각을 합쳐 <출력 md>, 둘 다 없으면 6묶음 모두 + 합치기. 조각 폴더 기본 = <출력 md 폴더>\보고서용_숫자_조각
  예) 제출본: python 보고서용_숫자.py ..\제출_원문대로\결과 ..\제출_원문대로\보고서용_숫자.md --노트북 ..\제출_원문대로\과제02.ipynb --묶음 1"""
import argparse, csv, datetime, json, re, sys
from pathlib import Path

import pandas as pd


def 새파일(p):
    """이미 있으면 덮어쓰지 않고 _2, _3 …(추가 지시 05:26)."""
    q, i = p, 2
    while q.exists():
        q, i = p.with_name(f"{p.stem}_{i}{p.suffix}"), i + 1
    return q

ap = argparse.ArgumentParser()
ap.add_argument("결과", type=Path)
ap.add_argument("출력", type=Path)
ap.add_argument("--노트북", type=Path)
ap.add_argument("--공통", type=Path, default=Path(__file__).resolve().parents[2] / "공통")
ap.add_argument("--조각", type=Path)
ap.add_argument("--묶음", type=int, choices=range(1, 7))
ap.add_argument("--합치기", action="store_true")
a = ap.parse_args()
조각폴더 = a.조각 or a.출력.parent / "보고서용_숫자_조각"
sys.path.insert(0, str(a.공통))
import 평가  # noqa: E402

월, 전략 = a.결과 / "결과_월수익률", a.결과 / "결과_전략수익률"
NW = re.compile(r"NW")
표이름 = {0: "표0. MF·IMF 원문 대조 (우동호 외 2023 표 2~7)", 1: "표1. 문헌별 원문 주장·대조", 2: "표2. 01 MF·IMF·KOSPI 성과 (월수익률)",
        3: "표3. 04 성과 (월수익률)", 4: "표4. 기간별 성과", 5: "표5. 확장연구: 비중", 6: "표6. 확장연구: 리밸런싱 주기", 7: "표7. 확장연구: 지표 4×4",
        8: "표8. 확장연구: 조합 고르는 기간 / 검증 기간", 9: "표9. 확장연구: 요인 순서", 10: "표10. 02 분위·롱숏 성과와 Carhart α·t(OLS)",
        11: "표11. 03 분위·롱숏 성과와 Carhart α·t(OLS)", 90: "부록. 확장연구 나머지 표(거래비용 등)"}

# 노트북 절 찾기
칸들 = []
if a.노트북:
    큰, 작은 = "", ""
    for i, c in enumerate(json.load(open(a.노트북, encoding="utf-8"))["cells"]):
        s = "".join(c["source"])
        if c["cell_type"] == "markdown":
            for l in s.splitlines():
                if re.match(r"#\s", l):
                    큰, 작은 = l.lstrip("# ").strip(), ""
                elif re.match(r"#{2,4}\s", l):
                    작은 = l.lstrip("# ").strip()
        else:
            칸들.append((i, 큰, 작은, s, c.get("outputs", [])))


def 절(f):
    for 열쇠 in (f'"{f.name}"', f'"{f.stem}"', f.name, f.stem, f.parent.name):  # 따옴표 든 이름(저장 칸: to_csv(… "x.csv"), 평가.저장(…, "x")) → 이름 → 폴더(이름을 f-string으로 만드는 칸)
        for i, 큰, 작은, s, _ in 칸들:
            if 열쇠 in s:
                return f"노트북 칸 {i} · {큰} > {작은}"
    return "노트북 절 못 찾음" if 칸들 else ""


조각 = []  # (표 번호, 글 줄들)
쓴파일 = set()


def 출처(f):
    쓴파일.add(f)
    return f"출처: `{f.relative_to(a.결과)}`" + (f" ← {절(f)}" if 칸들 else "")


def 수(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "" if x is None else str(x).replace("|", "/")
    return "" if v != v else (str(x) if re.fullmatch(r"-?\d+", str(x)) else f"{v:.6g}")


def md(rows):
    n = max(map(len, rows))
    rows = [list(r) + [""] * (n - len(r)) for r in rows]
    return ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * n] + ["| " + " | ".join(r) + " |" for r in rows[1:]] + [""]


def csv표(f, 줄거르기=None):
    """csv 글자 그대로. 머리 줄(둘째 줄이 '원문/우리' 같은 두 번째 머리면 그것도)에 NW가 든 칸은 뺌."""
    r = list(csv.reader(open(f, encoding="utf-8-sig")))
    머리수 = 2 if len(r) > 1 and r[1] and r[1][0] == "" and not any(re.fullmatch(r"-?[\d.e+-]+", x) for x in r[1] if x) else 1
    뺄 = {j for j in range(len(r[0])) if any(NW.search(r[h][j]) for h in range(머리수) if j < len(r[h]))}
    본 = [x for x in r[머리수:] if 줄거르기 is None or 줄거르기(dict(zip(r[0], x)))]
    머리 = [" / ".join(dict.fromkeys(r[h][j] for h in range(머리수) if r[h][j])) for j in range(len(r[0])) if j not in 뺄]
    return md([머리] + [[수(v) for j, v in enumerate(x) if j not in 뺄] for x in 본]), len(r) - 머리수 - len(본), sorted(r[0][j] for j in 뺄)


def 표넣기(번호, f, 제목, 줄거르기=None, 뺀줄이유=""):
    if not f.exists():
        조각.append((번호, [f"#### {제목}", "", f"(파일 없음: `{f.relative_to(a.결과)}`)", ""]))
        return
    t, 뺀줄, 뺀칸 = csv표(f, 줄거르기)
    조각.append((번호, [f"#### {제목}", "", 출처(f) + (f" · NW 칸 {len(뺀칸)}개 뺌" if 뺀칸 else "") + (f" · {뺀줄이유} {뺀줄}줄 뺌" if 뺀줄 else ""), ""] + t))


성과칸 = ["개월", "누적", "연환산", "표준편차(연)", "샤프", "MDD", "정보비율", "CAPM α(월)", "CAPM t(OLS)", "FF3 α(월)", "FF3 t(OLS)", "Carhart α(월)", "Carhart t(OLS)",
        "Carhart β:MKT", "Carhart β:SMB", "Carhart β:HML", "Carhart β:MOM", "Carhart adj R²"]


def 성과md(표, 머리="전략 · 가중"):
    칸 = [c for c in 성과칸 if any(c in o for o in 표.values())]
    return md([[머리] + 칸] + [[k] + [수(o.get(c)) for c in 칸] for k, o in 표.items()])


def 이름(k):
    return " ".join(map(str, k)) if isinstance(k, tuple) else str(k)


def 성과표(번호, f, 제목, 시장추가=False):
    if f is None or not f.exists():
        조각.append((번호, [f"#### {제목}", "", "(결과 pkl 없음)", ""]))
        return
    try:
        d = pd.read_pickle(f)
        if d["F"] is None:  # 따라하기 02·03: 요인은 옮김 노트북이 결과_월수익률/요인/<같은 이름>.pkl 에(평가.요약과 같은 규칙)
            d["F"] = pd.read_pickle(f.parent / "요인" / f.name)
        표 = {이름(k): 평가.성과(d["R"][k], d["F"], k in d["롱숏"]) for k in d["R"]}
        if 시장추가 and "시장" in d["F"]:
            표["KOSPI(F '시장' 열 = 이 노트북 설정의 시장지수)"] = 평가.성과(d["F"]["시장"].reindex(d["R"].dropna(how="all").index), d["F"])
        글 = 성과md(표)
    except Exception as e:  # 새 노트북에서 F 칸 이름이 바뀌는 등: 멈추지 말고 적음
        글 = [f"(평가.성과 계산 실패: {type(e).__name__} {e})", ""]
    조각.append((번호, [f"#### {제목}", "", 출처(f) + " → 공통 `평가.성과`(R·F 그대로; 롱숏 열은 초과수익 = 수익률, 나머지는 수익률 − RF)", ""] + 글))


pkl = lambda p: next(iter(sorted(월.glob(p))), None)
csv들 = lambda p: sorted(월.glob(p))


def 묶음1():
    표넣기(0, 월 / "01_원문대조.csv", "01_원문대조 (원문 숫자·우리 숫자)")
    for f in csv들("01_*.csv"):
        if f.name != "01_원문대조.csv":
            표넣기(1, f, f.stem)
    성과표(2, pkl("01_*.pkl"), "01 결과 pkl 전 열 + KOSPI (원문 단위로 잰 값은 표0)", 시장추가=True)


def 묶음234(n, 표번호):
    for f in csv들(f"0{n}_*.csv") + (csv들("2차_*.csv") if n == 4 else []):
        표넣기(1, f, f.stem)
    성과표(표번호, pkl(f"0{n}_*.pkl"), f"0{n} 결과 pkl 전 열")


def 묶음5():
    기준주기 = set()
    if (전략 / "1_비중.csv").exists():
        기준주기 = set(pd.read_csv(전략 / "1_비중.csv", encoding="utf-8-sig")["주기"].astype(str)) - {"0"}
    표넣기(5, 전략 / "1_비중.csv", "1_비중")
    조각.append((6, ["회원 결정으로 뺌(2026-11-06 03:46, 리밸런싱 주기 비교는 보고서에서 뺀다). 결과 파일 `결과_전략수익률\\2_주기.csv`·`.png`는 지우지 않고 둠.", ""]))
    f = 전략 / "3_지표.csv"
    표넣기(7, f, "3_지표 (전체 표)")
    if f.exists():
        t = pd.read_csv(f, encoding="utf-8-sig")
        t = t[t["전략"].str.contains(r"\+")]
        쪽 = t["전략"].str.replace(" 순위합산", "").str.split("+", n=1)
        for c in ("연환산", "샤프", "Carhart α(월)", "Carhart t(OLS)"):
            if c in t:
                p = t.assign(가치=쪽.str[0], 질=쪽.str[1]).pivot_table(index="가치", columns="질", values=c, aggfunc="first", sort=False)
                조각.append((7, [f"#### 지표 4×4: {c} (행 = 가치, 열 = 질, 같은 `3_지표.csv`의 '{c}' 칸을 모양만 바꿈)", ""] +
                             md([["가치 \\ 질"] + list(p.columns)] + [[i] + [수(v) for v in r] for i, r in p.iterrows()])))
    f = pkl("연구_이로운_지표바꾸기.pkl")
    if f:
        d = pd.read_pickle(f)
        기간 = {"고르는 기간": 평가.구간들["2004-04~2017-03"], "검증 기간": 평가.구간들["2017-04~"]}
        글 = [출처(f) + " → 평가.구간(보유 월로 자름) + 평가.성과, 이로운 지표바꾸기 노트북 10·11절과 같은 계산(고르는 기간 2004-04~2017-03, 검증 기간 2017-04~)", ""]
        샤프 = {}
        for 이름k, (s, e) in 기간.items():
            표 = {이름(k): 평가.성과(평가.구간(d["R"][k].dropna(), s, e), d["F"]) for k in d["R"]}
            샤프[이름k] = pd.Series({k: o["샤프"] for k, o in 표.items() if k.endswith(" 동일")})
            글 += [f"##### {이름k}", ""] + 성과md(표, "조합 · 가중")
        고른 = 샤프["고르는 기간"].idxmax()
        글 += [f"- 고르는 기간 동일가중 샤프 1등(위 표에서 고름): {고른} {수(샤프['고르는 기간'][고른])} → 검증 기간 샤프 {수(샤프['검증 기간'][고른])}, 순위 {int(샤프['검증 기간'].rank(ascending=False)[고른])}/{len(샤프['검증 기간'])}", ""]
        조각.append((8, 글))
    else:
        조각.append((8, ["(결과_월수익률\\연구_이로운_지표바꾸기.pkl 없음)", ""]))
    표넣기(9, 전략 / "4_순서.csv", "4_순서")
    for f in sorted(전략.glob("*.csv")):
        if re.match(r"[1-4]_|.*(주기|기간)", f.stem):
            continue
        if "비용" in f.stem and 기준주기:
            표넣기(90, f, f"{f.stem} (기준 주기 {sorted(기준주기)}와 벤치마크 줄만)", lambda x: x.get("주기") in 기준주기 | {"0"}, "주기 비교 줄(기준 주기 아님)")
        else:
            표넣기(90, f, f.stem)


def 묶음6():
    for f in sorted(전략.glob("*기간*.csv")):
        표넣기(4, f, f.stem + " (확장연구 기준 전략과 벤치마크)")
    표넣기(4, 월 / "요약표.csv", "요약표 (따라하기 01~04, 전략 × 가중 × 기간, 평가.요약)", lambda x: bool(re.match(r"0[1-4]_", x.get("파일", ""))), "연구 노트북 줄")


묶음들 = {1: 묶음1, 2: lambda: 묶음234(2, 10), 3: lambda: 묶음234(3, 11), 4: lambda: 묶음234(4, 3), 5: 묶음5, 6: 묶음6}


def 조각쓰기(n):
    조각.clear(); 쓴파일.clear()
    묶음들[n]()
    조각폴더.mkdir(parents=True, exist_ok=True)
    글 = [f"<!-- 쓴파일: {json.dumps(sorted(str(p.relative_to(a.결과)) for p in 쓴파일), ensure_ascii=False)} -->"]
    for 번호, 줄들 in 조각:
        글 += [f"<!-- 표: {번호} -->"] + 줄들
    새파일(조각폴더 / f"묶음{n}.md").write_text("\n".join(글), encoding="utf-8")
    print(f"조각 {조각폴더 / f'묶음{n}.md'} (표 {sorted({b for b, _ in 조각})})")


def 합치기():
    모음, 쓴 = {}, set()
    있는 = sorted(조각폴더.glob("묶음*.md"))
    for f in 있는:
        s = f.read_text(encoding="utf-8")
        쓴 |= set(json.loads(re.search(r"<!-- 쓴파일: (.*) -->", s).group(1)))
        for m in re.finditer(r"<!-- 표: (\d+) -->\n(.*?)(?=\n<!-- 표: |\Z)", s, re.S):
            모음.setdefault(int(m.group(1)), []).append(f"_({f.stem})_\n\n" + m.group(2))
    줄 = ["# 보고서용 숫자 모음", "",
          f"- 만든 때: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}, 스크립트 `_검증\\1106\\보고서용_숫자.py`, 조각 {[f.name for f in 있는]} (조각 폴더 `{조각폴더}`)",
          f"- 결과 폴더: `{a.결과}`" + (f", 노트북: `{a.노트북}`" if a.노트북 else ", 노트북: (안 줌 → 절 표시 없음)"),
          "- 숫자: csv는 파일 칸 글자 그대로(표시만 유효숫자 6자리로 반올림). 성과 표는 결과 pkl의 월수익률 R·요인 F에 공통 `평가.성과`(노트북과 같은 함수)를 그대로 적용한 값.",
          "- t는 OLS만(NW 칸은 파일에 있어도 쓰지 않음). 리밸런싱 주기 비교는 회원 결정으로 뺌(파일은 그대로 있음).", ""]
    for 번호 in sorted(set(표이름) | set(모음)):
        줄 += [f"## {표이름.get(번호, f'표{번호}')}", ""] + (모음.get(번호) or ["(이 표를 만드는 묶음 조각이 아직 없음)", ""]) + [""]
    줄 += ["## 그림", "", "### 결과 폴더의 그림 파일", ""]
    그림 = sorted(a.결과.rglob("*.png"))
    줄 += [f"- `{p}`" + (" (주기 비교: 보고서에서 뺌)" if "주기" in p.stem else "") + (f" ← {절(p)}" if 칸들 else "") for p in 그림] or ["(없음)"]
    if 칸들:
        줄 += ["", "### 노트북 안 그림(출력 칸, 파일로 저장 안 됨 — 로그 축 누적 등)", ""]
        for i, 큰, 작은, s, o in 칸들:
            n = sum("image/png" in x.get("data", {}) for x in o)
            if n:
                로그 = re.search(r"누적그림\(", s) and "로그=False" not in s
                줄.append(f"- 칸 {i} · {큰} > {작은}: 그림 {n}장" + (" (평가.누적그림, 로그 축)" if 로그 else "") + (" (주기 비교: 보고서에서 뺌)" if "주기" in 작은 else ""))
    남은 = [p for p in sorted(a.결과.rglob("*")) if p.is_file() and p.suffix in (".csv", ".pkl") and str(p.relative_to(a.결과)) not in 쓴]
    줄 += ["", "## 이 문서에 안 쓴 결과 파일(있는 그대로 둠)", ""] + ([f"- `{p.relative_to(a.결과)}`" for p in 남은] or ["(없음)"]) + [""]
    a.출력.parent.mkdir(parents=True, exist_ok=True)
    새파일(a.출력).write_text("\n".join(줄), encoding="utf-8")
    print(f"합침 {a.출력} ({len(줄)}줄, 조각 {len(있는)}개)")


if a.묶음:
    조각쓰기(a.묶음)
if a.합치기:
    합치기()
if not a.묶음 and not a.합치기:
    for n in 묶음들:
        조각쓰기(n)
    합치기()
