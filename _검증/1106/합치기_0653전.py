r"""B1: 제출용 단일 노트북 만들기(2026-11-06 c). 예전 제출본을 만든 `_제출작업\만들기.py`와 같은 방식:
공통/*.py 6개는 글자 그대로 `%%모듈` 칸(경로 줄만 바꿈), 각 절은 저장소 노트북 칸 그대로 맨 위에 `%%절 번호`, 칸마다 metadata['출처'] = 원본 파일#칸.
예전과 다른 점: ① 따라하기 4개·'따라하기에서 옮김' 4개는 노트북 칸을 전부 옮김(고치는 중이라 칸 번호를 못 박음. 맨 위 import 칸에서 0·1절이 대신하는 줄만 뺌)
② 확장연구에 7.5절 '따라하기에서 옮김' ③ 저장소 노트북의 FOLLOW_TEST 시험 모드 → 0절 `시험_기간`(기본 None = 본 실행)
④ 저장소 연구 노트북에 'NW' 칸 이름이 남아 있으면 OLS로 바꿈(공통에서 NW t를 뺐으므로, 예전 제출_NW제외와 같은 규칙).
쓰는 법(파이썬은 nbformat 있는 3.14):
  python 합치기.py          → 제출_원문대로\과제02.ipynb (진짜 출력, 조정자가 따라하기 수정 끝난 뒤)
  python 합치기.py --시험   → _검증\1106\합치기_시험\과제02.ipynb (지금 판으로 시험)
점검(남은 저장소 경로·data에 없는 파일·시험 줄 없음 등) = _검증\1106\합치기_점검[_시험].txt, 예전 제출본과 절·칸 수 비교 = 합치기_비교[_시험].md.
점검에 '고칠 것'이 있으면 종료 코드 1(노트북은 씀)."""
import json, re, subprocess, sys
from collections import Counter, OrderedDict
from pathlib import Path

import nbformat as nbf


def 새파일(p):
    """이미 있으면 덮어쓰지 않고 _2, _3 …(추가 지시 05:26)."""
    q, i = p, 2
    while q.exists():
        q, i = p.with_name(f"{p.stem}_{i}{p.suffix}"), i + 1
    return q

시험 = "--시험" in sys.argv
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO.parent  # 과제02
OUT = 새파일(HERE / "합치기_시험" / "과제02.ipynb" if 시험 else ROOT / "제출_원문대로" / "과제02.ipynb")  # 이미 있으면 새 이름(추가 지시 05:26)
DATA = ROOT / "제출_원문대로" / "data"
OLD = ROOT / "제출" / "과제02.ipynb"
꼬리 = "_시험" if 시험 else ""
git = lambda *a: subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True, encoding="utf-8").stdout.strip()
커밋, 브랜치 = git("rev-parse", "--short", "HEAD"), git("branch", "--show-current")
변경 = git("status", "--porcelain", "--", "공통", "따라하기", "연구")

nb = nbf.v4.new_notebook()
nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}, "language_info": {"name": "python"}}
cells = nb.cells
기록 = []  # 바꾼 것(점검 파일에)
고칠 = []  # 사람이 봐야 할 것(있으면 종료 코드 1)


def md(s, 출처=None):
    c = nbf.v4.new_markdown_cell(s)
    if 출처:
        c.metadata["출처"] = 출처
    cells.append(c)


def code(s, 출처=None):
    c = nbf.v4.new_code_cell(s)
    if 출처:
        c.metadata["출처"] = 출처
    cells.append(c)


원본 = {}


def 칸들(rel):
    if rel not in 원본:
        원본[rel] = json.load(open(REPO / rel, encoding="utf-8"))["cells"]
    return 원본[rel]


def 칸(rel, i):
    c = 칸들(rel)[i]
    return c["cell_type"], "".join(c["source"])


def 낮춤(s):  # 제목 한 단계 낮춤(# → ##): 노트북 하나 안의 절이 되게
    return re.sub(r"(?m)^(#{1,5}) ", lambda m: "#" + m.group(1) + " ", s)


def 바꿈(s, 바꿀):
    for a, b in 바꿀:
        assert s.count(a) == 1, (a, s[:200])
        s = s.replace(a, b)
    return s


# ───────── 모든 노트북 칸에 쓰는 바꾸기(규칙이 맞을 때만, 바꾼 것은 기록) ─────────
NW_md = [("NW(뉴이-웨스트: 자기상관·이분산을 감안한 t), ", ""), ("NW(뉴이-웨스트 t), ", ""), (", NW(뉴이-웨스트 t)", ""),
         ("각 t(OLS·NW)", "각 t(OLS)"), ("α·t(NW)", "α·t(OLS)"), ("NW t로 검정해", "OLS t로 검정해"),
         ("1-1절의 'Carhart t(NW)'는 뉴이-웨스트 t다.", "1-1절의 'Carhart t(OLS)'도 OLS t다."),
         ("**평균 t(NW)**: 그 평균의 뉴이-웨스트 t.", "**평균 t(OLS)**: 그 평균의 OLS t."), ("**α t(NW)**: 그 t.", "**α t(OLS)**: 그 t.")]


def NW정리(s, t, 출처):
    """공통 평가에서 NW t를 뺐으므로(칸 이름 t(OLS)만) 저장소 노트북에 남은 NW 칸 이름을 OLS로(예전 _제출작업\\NW제외_고치기.py와 같은 규칙)."""
    s0 = s
    if t == "markdown":
        for a, b in NW_md:
            s = s.replace(a, b)
    else:
        s = re.sub(r', "(CAPM|FF3|Carhart) t\(NW보정\)"', "", s)
        for m in ("CAPM", "FF3", "Carhart"):
            s = s.replace(f', "{m} t(NW)"', "") if f'"{m} t(OLS)"' in s else s.replace(f'"{m} t(NW)"', f'"{m} t(OLS)"')
    if s != s0:
        기록.append(f"NW → OLS: {출처}")
    return s


시험식 = re.compile(r"""os\.environ\.get\(\s*["']FOLLOW_TEST["']\s*(?:,\s*[^)]*)?\)\s*==\s*["']1["']""")
시험경로 = re.compile(r"""(?:Path\.cwd\(\)\.parent|평가\.결과폴더\.parent|Path\(__file__\)\.resolve\(\)\.parents?\[?\d*\]?(?:\.parent)*|REPO|ROOT|저장소)\s*/\s*["']_검증["']\s*/\s*["']1106["']\s*/\s*["']시험결과["']""")


runpy식 = re.compile(r"""runpy\.run_path\(\s*str\(\s*[^\n]*?/\s*["']_검증["']\s*/\s*["']([^"']+\.py)["']\s*\)\s*\)""")
# 저장소 _검증 안의 자료 파일(원문 표 숫자 등)을 읽는 줄 → data/저장소_검증/(data_추가.py로 복사, 없으면 점검에 명령을 적음)
검증읽기식 = re.compile(r"""(?:Path\.cwd\(\)\.parent|평가\.결과폴더\.parent)\s*/\s*["']_검증["']\s*/\s*["']([^"'/]+\.(?:csv|xlsx|json|txt))["']""")
검증파일 = set()
# 연구 노트북이 쓰는 폴더: 저장소 연구/결과 → 노트북 옆 결과/, 시험이면 결과/시험결과
연구결과식 = [(re.compile(r"""Path\.cwd\(\)\.parent\s*/\s*\(\s*["']_검증/1106/(시험결과[^"']*)["']\s+if\s+시험\s+else\s+["']연구/결과/([^"']*)["']\s*\)"""), r'Path("결과") / ("\1" if 시험 else "\2")'),
           (re.compile(r"""Path\.cwd\(\)\.parent\s*/\s*["']연구["']\s*/\s*["']결과["']"""), 'Path("결과")'),
           (re.compile(r"""Path\.cwd\(\)\.parent\s*/\s*["']연구/결과["']"""), 'Path("결과")'),
           (re.compile(r"""Path\.cwd\(\)\.parent\s*/\s*["']_검증/1106/시험결과["']"""), 'Path("결과") / "시험결과"')]


def runpy넣기(s, 출처):
    """저장소 칸이 runpy.run_path(_검증/X.py)로 스크립트를 돌리면: 제출본에는 그 파일이 없으므로 스크립트 글자 그대로를 칸 안에 넣고 새 이름 공간에서 돌림(runpy와 같음).
    스크립트의 __file__ = 노트북 옆 결과/X.py → 스크립트가 Path(__file__).parent에 쓰는 csv는 결과/에."""
    이름들 = runpy식.findall(s)
    if not 이름들:
        return s
    머리 = ["# (제출본에서 바꿈) 저장소 칸은 runpy.run_path(저장소 _검증/스크립트). 제출본에는 그 파일이 없어 같은 코드(글자 그대로)를 아래 글자로 넣고 새 이름 공간에서 돌림(runpy와 같음). 스크립트가 쓰는 csv는 노트북 옆 결과/에"]
    for n in dict.fromkeys(이름들):
        t = (REPO / "_검증" / n).read_text(encoding="utf-8")
        assert "'''" not in t and not t.rstrip().endswith("\\"), n
        머리.append(f"_스크립트_{n[:-3]} = r'''{t.rstrip()}\n'''")
    s = runpy식.sub(lambda m: f'(lambda g: exec(compile(_스크립트_{m.group(1)[:-3]}, "_검증/{m.group(1)}", "exec"), g) or g)({{"__name__": "<run_path>", "__file__": str(Path("결과") / "{m.group(1)}")}})', s)
    기록.append(f"runpy _검증 스크립트 → 칸 안에 글자 그대로({', '.join(이름들)}): {출처}")
    return "\n".join(머리) + "\n" + s


def 코드바꿈(s, 출처):
    s = runpy넣기(s, 출처)
    s0 = s
    s = 시험식.sub("bool(시험_기간)", s)  # 저장소 노트북의 시험 모드 = 0절 시험_기간(기본 None → 본 실행)
    s = 시험경로.sub('Path("결과") / "시험결과"', s)  # 시험 결과는 노트북 옆 결과/시험결과(저장소 _검증 폴더 대신)
    s = s.replace('Path.cwd().parent / "결과_전략수익률"', 'Path.cwd() / "결과" / "결과_전략수익률"')  # 저장소 결과_전략수익률/ → 노트북 옆 결과/
    for a, b in 연구결과식:
        s = a.sub(b, s)
    검증파일.update(검증읽기식.findall(s))
    s = 검증읽기식.sub(lambda m: f'읽기.새목록.parent / "저장소_검증" / "{m.group(1)}"', s)
    if s != s0:
        s += "\n# (제출본에서 바꿈) 이 칸의 " + "·".join(x for x, y in [("FOLLOW_TEST 시험 모드 → 0절 시험_기간", 시험식.search(s0)), ("시험 결과 폴더 → 결과/시험결과", 시험경로.search(s0)),
                                                          ("결과_전략수익률 폴더 → 결과/결과_전략수익률", 'Path.cwd().parent / "결과_전략수익률"' in s0),
                                                          ("저장소 연구/결과 폴더 → 결과/", any(a.search(s0) for a, _ in 연구결과식)),
                                                          ("저장소 _검증 자료 파일 → data/저장소_검증/", 검증읽기식.search(s0))] if y)
        기록.append(f"경로·시험: {출처}")
    return s


공통이름 = {"데이터읽기", "지표", "종목거르기", "포트폴리오", "평가", "점검"}
영절 = {"import sys", "import json", "import time", "import types", "import numpy as np", "import pandas as pd", "from pathlib import Path"}


def import정리(s):
    """저장소 노트북 맨 위 import 칸에서 0·1절이 대신하는 줄(sys.path에 공통 넣기, 공통 모듈 import, 0절에 있는 import, pandas 표시 설정)만 뺌. 나머지(시험 모드 줄 등)는 둠."""
    남 = []
    for l in s.splitlines():
        x = l.split("#")[0].strip()
        if x in 영절 or x.startswith("pd.set_option(") or ("sys.path.insert" in x and "공통" in x):
            continue
        if x.startswith("import ") and all(p.strip().split(" as ")[0].strip() in 공통이름 for p in x[7:].split(",")):
            continue
        남.append(l)
    return "\n".join(남).strip("\n")


import표 = 'sys.path.insert(0, str(Path.cwd().parent / "공통"))'
s7 = (REPO / "_검증" / "2차_07_신마법.py").read_text(encoding="utf-8")
s7 = s7[s7.index("T0 = time.time()"):].rstrip("\n")
s7 = 바꿈(s7, [('짧게 = "--짧게" in sys.argv', '짧게 = bool(시험_기간)  # (제출본에서 바꿈) 스크립트의 --짧게 = 0절 시험_기간(앞 2년 + 뒤 2년)'),
               ('    T.to_csv(Path(__file__).resolve().parent / "2차_07_신마법.csv", encoding="utf-8-sig")',
                '    T.to_csv(평가.결과폴더 / "2차_07_신마법.csv", encoding="utf-8-sig")  # (제출본에서 바꿈) 저장소는 _검증/2차_07_신마법.csv')])
쓰는파일 = OrderedDict()  # 절 → 노트북이 쓰는 결과 파일 이름(0절 표·점검)


def 노트북전부(rel, 번호):
    """rel 노트북 칸을 전부 차례로 옮김(맨 위 '불러오기' 제목 칸은 빼고, import 칸은 import정리). 코드 칸 맨 위 '%%절 번호'."""
    for i, c in enumerate(칸들(rel)):
        t, s = c["cell_type"], "".join(c["source"])
        출처 = f"{rel}#{i}"
        if t == "markdown":
            if re.match(r"#+\s*1\.\s*불러오기", s.strip()) and len(s.strip().splitlines()) == 1:
                기록.append(f"뺌(불러오기 제목 칸): {출처}")
                continue
            md(낮춤(NW정리(s, t, 출처)), 출처)
            continue
        if import표 in s:
            s = import정리(s)
            기록.append(f"import 칸 정리(0·1절이 대신하는 줄 뺌, 남은 줄 {len(s.splitlines())}): {출처}")
            if not s.strip():
                continue
            s = "# (제출본) 저장소 import 칸에서 0·1절이 대신하는 줄(sys.path·공통 import·0절 import·pandas 표시 설정)을 뺀 나머지\n" + s
        if "2차_07_신마법.csv" in s and "read_csv" in s:  # 예전 제출본처럼 csv를 읽는 대신 스크립트 코드를 그대로 돌림
            md("> (제출본) 아래 칸은 저장소 노트북의 csv 읽기 대신 `_검증/2차_07_신마법.py`의 코드를 그대로 돌려 표를 찍고, 전체 기간이면 `결과/결과_월수익률/2차_07_신마법.csv`에 쓴다(`시험_기간`이면 스크립트의 `--짧게`처럼 앞·뒤 2년만 돌리고 csv는 안 씀).")
            code(f"%%절 {번호}\n# 저장소 _검증/2차_07_신마법.py(맨 위 설명 글·import 줄 뺀 나머지 글자 그대로). 저장소 노트북의 이 칸은 그 스크립트가 쓴 csv를 읽었음\n" + s7 +
                 '\npd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)  # (제출본에서 더함) 위 스크립트 줄이 바꾼 표시 설정을 다른 절과 같게 되돌림(표시만)',
                 f"_검증/2차_07_신마법.py#T0~ (대신: {출처})")
            기록.append(f"2차_07 csv 읽기 칸 → 스크립트 코드: {출처}")
            continue
        code(f"%%절 {번호}\n" + 코드바꿈(NW정리(s, t, 출처), 출처), 출처)


def 옮김(rel, idx, 번호, 바꿀={}, 칸수=None):
    """예전 만들기.py와 같음: rel 노트북의 칸 idx를 차례로 옮김(고정 칸 번호, 연구 노트북용). 칸수가 다르면 멈춤(노트북이 바뀌었으면 칸 번호를 다시 봐야 함)."""
    if 칸수 is not None:
        assert len(칸들(rel)) == 칸수, f"{rel} 칸 수 {len(칸들(rel))} ≠ 예전 {칸수}: 칸 번호를 다시 봐야 함"
    for i in idx:
        if isinstance(i, str):
            md(i)
            continue
        t, s = 칸(rel, i)
        s = NW정리(바꿈(s, 바꿀.get(i, [])), t, f"{rel}#{i}")
        if t == "markdown":
            md(낮춤(s), f"{rel}#{i}")
        else:
            code(f"%%절 {번호}\n" + 코드바꿈(s, f"{rel}#{i}"), f"{rel}#{i}")


def 제목(rel):
    s = 칸(rel, 0)[1].strip().splitlines()[0]
    return re.sub(r"^#+\s*(\d+\s+)?", "", s)


따라 = [("3", "①", "따라하기/01_우동호2023.ipynb"), ("4", "②", "따라하기/02_NH_밸류.ipynb"),
       ("5", "③", "따라하기/03_NH_퀄리티로우볼.ipynb"), ("6", "④", "따라하기/04_신마법공식.ipynb")]
옮김들 = sorted(p.relative_to(REPO).as_posix() for p in (REPO / "연구").glob("따라하기에서_옮김_0*.ipynb"))
for n in "1234":
    if f"연구/따라하기에서_옮김_0{n}.ipynb" not in 옮김들:
        고칠.append(f"연구/따라하기에서_옮김_0{n}.ipynb 없음(아직 안 만들어짐) → 7.5.{n}절 빠짐")

# ───────────── 0절 ─────────────
표줄 = "\n".join(f"| {번호} | {기호} {제목(rel)} | `{rel}` |" for 번호, 기호, rel in 따라)
옮김줄 = "\n".join(f"| 7.5.{rel[-7]} | 따라하기에서 옮김 {rel[-8:-6]}: {제목(rel)} | `{rel}` |" for rel in 옮김들)
md(f"""# 과제02 백테스트 — 제출 코드 (한 파일, 원문대로 판)

## 0. 안내
**이 노트북 하나가 과제 코드 전부다.** 같은 폴더의 `data` 폴더만 있으면 처음부터 끝까지 그대로 돈다. 절대 경로는 쓰지 않는다(바로 아래 칸의 `DATA = Path("data")`).

**어디서 왔나**: 팀 저장소(커밋 `{커밋}`, 브랜치 `{브랜치}`)의 `공통/` 모듈 6개와 노트북(`따라하기/01~04`, `연구/확장연구_20261103`, `연구/이로운_*` 3개, `연구/따라하기에서_옮김_01~04`, `연구/결과요약_20261103`·`요약표`), `_검증/2차_07_신마법.py`를 **계산 줄은 바꾸지 않고** 옮겨 합쳤다(만든 스크립트: 저장소 `_검증/1106/합치기.py`). 바꾼 것은 ① 파일 경로(모두 `data` 폴더·노트북 옆 `결과` 폴더 기준), ② 저장소 노트북 맨 위 import 칸에서 0·1절이 대신하는 줄(나머지 줄은 둠), ③ 짧은 시험: 따라하기 노트북의 시험 모드 줄(`FOLLOW_TEST`)은 0절 `시험_기간`으로 잇고, 연구 노트북에는 `if 시험_기간:` 줄을 더함, ④ 표시·기록용 몇 줄(각 줄 주석에 '(제출본에서 바꿈/더함)'), ⑤ 마크다운 제목을 한 단계씩 내림, ⑥ 저장소 연구 노트북에 남은 Newey-West 칸 이름을 OLS로(공통에서 NW t를 뺐음)뿐이다. 칸마다 원본 위치는 칸 metadata '출처'.

**원문대로 판에서 바뀐 것(2026-11-06 회원 결정)**: 따라하기 4개는 원문에 있는 것만(원문에 없는 추가 분석·확인판·진단은 7.5절 '따라하기에서 옮김'으로), 보통주만, 수익률 가격 = 수정주가, 분기 재무 = 발표된 값 그대로, t는 OLS만(Newey-West 뺌). 리밸런싱 주기 비교(7.1절)는 결과를 지우지 않고 그대로 둔다.

**실행 순서**: 위에서 아래로 한 번(Jupyter '모두 실행' 또는 `jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 과제02.ipynb`). 커널은 기본 `python3`(아래 패키지가 깔린 Python 3.11).
| 절 | 내용 | 원래 노트북 |
|---|---|---|
| 1 | 공통 함수(데이터 읽기·종목 거르기·지표·포트폴리오·평가·점검) | `공통/*.py` |
| 2 | 엑셀 → parquet 다시 만들기(기본은 끔) | 원래 data 폴더의 감독 변환기 `DataGuide_추가_202611\\_tools\\_to_parquet.py`(쓰는 함수 세 개를 글자 그대로) |
{표줄}
| 7.1 | 확장 연구(비중·주기·지표·순서·비용·기간·무위험) | `연구/확장연구_20261103.ipynb` |
| 7.2~7.4 | 이로운 연구(비중 바꾸기·지표 바꾸기·팩터 순서) | `연구/이로운_*.ipynb` |
| 7.5 | 따라하기에서 옮김(원문에 없는 우리 추가) | `연구/따라하기에서_옮김_0N.ipynb` |
{옮김줄}
| 8 | 원문 대조 요약표(3~7절이 남긴 파일만 읽음) | `연구/결과요약_20261103.ipynb`, `연구/요약표.ipynb` |

- **결과 파일**: 이 노트북은 옆에 `결과` 폴더를 만들어 쓴다(`결과/결과_월수익률`, `결과/결과_전략수익률`, `결과/` 바로 아래에 확장연구·이로운 csv). `data` 폴더의 파일은 읽기만 한다.
- **8절은 3~7절이 남긴 파일을 읽는다.** 3~7절은 1절만 공유한다(7.5절이 앞 절 결과를 읽는지는 그 절 칸 참고).
- **실행 시간·메모리**: 이 판의 전체 기간 실행 기록은 같은 폴더 `대조_결과.txt`(실행 뒤 씀). 예전 제출본은 한 커널 '전부' 실행에 약 2시간 34분, 커널 메모리 최대 RSS 약 21GB였다(2026-11-05). 메모리가 작은 PC면 `실행할_절`을 "3", "4", …처럼 하나씩 주고 절마다 커널을 다시 시작해 돌린다(8절은 마지막).
- **필요한 패키지**: Python 3.11, pandas, numpy, scipy, statsmodels, matplotlib, scikit-learn, pyarrow, (2절을 켤 때만) python-calamine. 아래 칸이 지금 버전을 찍는다. 글꼴 'Malgun Gothic'(그림 한글).

줄임말: EW(동일가중), VW(시가총액가중), LS(롱숏), MDD(최대 낙폭), IR(정보비율), CAPM·FF3·Carhart(요인 모형), OLS(보통최소제곱), TR(배당 포함 수정주가).""")

code('''# 실행 설정: 이 칸만 바꾼다. 교수님 실행은 기본값 그대로(전부, 원래 기간)
from pathlib import Path
DATA = Path("data")    # 제출한 data 폴더. 노트북과 같은 폴더에 둔다(절대 경로 안 씀)
실행할_절 = "전부"      # "전부" 또는 "3,7.1"처럼 절 번호(쉼표로 여럿). 고른 절만 돌고 나머지 칸은 '건너뜀'을 찍는다. 1절(공통 함수)은 늘 돈다
시험_기간 = None        # None = 원문·저장소와 같은 전체 기간(본 실행). True로 바꾸면 절마다 짧은 기간만 돌린다(오류 확인용, 숫자는 본문이 아님)''')

code('''# 공통 준비: 패키지 불러오기, 표시 설정, 결과 폴더, 칸 매직 두 개
import json, os, sys, time, types
import numpy as np
import pandas as pd
from IPython.core.magic import register_cell_magic

pd.set_option("display.float_format", "{:.4f}".format)  # 따라하기 노트북과 같은 표시 설정(표시만)
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 300)
for d in ["결과", "결과/결과_월수익률", "결과/결과_전략수익률"]:  # 결과는 노트북 옆 '결과' 폴더에만 씀(data 폴더는 읽기만)
    Path(d).mkdir(parents=True, exist_ok=True)


@register_cell_magic
def 모듈(line, cell):
    """칸 맨 위 '%%모듈 이름 별칭': 그 칸의 코드를 '이름'이라는 모듈(코드 묶음)로 실행하고 노트북에서는 '별칭'으로 부른다.
    왜: 저장소에서는 공통/의 파일 6개가 서로 `import 데이터읽기 as 읽기`처럼 불러 쓴다. 파일 하나로 내야 해서 그 코드를 칸에 그대로 넣고,
    이 매직이 칸 코드를 모듈로 만들어 sys.modules에 올려 그 import 줄이 그대로 돌게 한다(계산 코드는 한 글자도 안 바꿈)."""
    이름, *별칭 = line.split()
    m = types.ModuleType(이름)
    sys.modules[이름] = m
    exec(compile(cell, f"<{이름}>", "exec"), m.__dict__)
    get_ipython().user_ns[별칭[0] if 별칭 else 이름] = m


@register_cell_magic
def 절(line, cell):
    """칸 맨 위 '%%절 번호': 맨 위 칸의 실행할_절에 그 번호가 있으면(또는 '전부') 칸 코드를 그대로 실행, 없으면 건너뜀.
    왜: 저장소 노트북 칸을 글자 그대로 옮기면서 절마다 따로 돌릴 수 있게 하려고(칸 코드를 if 안에 넣으면 들여쓰기가 바뀜). 오류는 그대로 멈춤."""
    번호 = line.split()[0]
    if 실행할_절 == "전부" or any(번호 == s.strip() or 번호.startswith(s.strip() + ".") for s in str(실행할_절).split(",")):
        get_ipython().run_cell(cell).raise_error()
    else:
        print(f"{번호}절 건너뜀(실행할_절 = {실행할_절!r})")


import importlib.metadata as md
print("Python", sys.version.split()[0], "/", ", ".join(f"{p} {md.version(p)}" for p in ["pandas", "numpy", "scipy", "statsmodels", "matplotlib", "scikit-learn", "pyarrow"]))
print("data 폴더:", DATA.resolve(), "있음" if DATA.is_dir() else "없음 → 노트북 옆에 data 폴더를 두세요")''')

# ───────────── 1절 공통 함수 (예전 만들기.py와 같은 바꾸기) ─────────────
md("""## 1. 공통 함수 (저장소 `공통/` 모듈 6개, 글자 그대로)
계산은 모두 여기 함수가 한다. 3~8절은 설정(dict)을 정하고 `포.실행(설정)`을 불러 결과를 본다. 순서: 데이터읽기(원본 파일 읽기) → 지표 → 종목거르기 → 포트폴리오(기준일 → 거르기 → 지표 → 점수 → 고르기 → 비중 → 매수보유 → 월수익률) → 평가(성과표·요인 회귀, t는 OLS) → 점검(손으로 답을 아는 작은 예로 계산 확인, 'ok'가 찍혀야 함).
- 각 칸 맨 위 `%%모듈 이름 별칭`은 0절 칸 매직(그 칸을 모듈로 실행). 함수마다 무엇을 왜 하는지는 그 함수의 설명 글(docstring)과 줄 끝 주석에 있다. 원문에 말이 없어 정한 기본값과 그 영향은 저장소 `_검증/기본값_영향_20261106.md`.
- 제출본에서 바꾼 줄: `데이터읽기`의 파일 경로 줄(→ `data` 폴더 아래 같은 이름 하위 폴더. 저장소 안 `_검증/새목록`은 `data/저장소_목록`으로 복사, 저장소 `_캐시/변환`은 같은 파일이 `data/통합_전체_202611`에 있어 `변환캐시 = DATA`), `평가`의 결과 폴더 줄(→ 노트북 옆 `결과/결과_월수익률`)과 git 기록 줄(`import shutil`을 더해 git이 없는 컴퓨터에서도 돌게, 기록 칸에만 쓰임). 나머지는 저장소와 같다.
- data에는 이 노트북이 읽는 파일을 넣었다(`data_파일목록.csv`). 이 노트북에서 쓰지 않는 거래량·상장주식수(`종목거르기.회전율`) 파일은 없으므로, 회전율 거르기를 켜려면 그 파일을 더 받아야 한다.""")

경로 = [
    ('DATA = Path(r"D:\\26-2_데이터기반투자전략\\과제02\\data\\통합_전체_202611")',
     'from __main__ import DATA as 뿌리  # (제출본에서 바꿈) 노트북 맨 위 칸의 DATA = Path("data")\nDATA = 뿌리 / "통합_전체_202611"'),
    ('XLSX = Path(r"D:\\26-2_데이터기반투자전략\\과제02\\data\\DataGuide_전체_202611")', 'XLSX = 뿌리 / "DataGuide_전체_202611"'),
    ('RF_FILE = Path(r"D:\\26-2_데이터기반투자전략\\과제02\\data\\DataGuide_1990s_202610\\무위험이자율후보_DataGuide_시장금리전체아이템35종_월간_19880101-20260930.xlsx")',
     'RF_FILE = 뿌리 / "DataGuide_1990s_202610" / "무위험이자율후보_DataGuide_시장금리전체아이템35종_월간_19880101-20260930.xlsx"'),
    ('FACTOR_FILE = Path(r"D:\\26-2_데이터기반투자전략\\과제02\\data\\DataGuide_추가_202610\\요인_팩터모델과시장지수_일간_1990-2026.xlsx")',
     'FACTOR_FILE = 뿌리 / "DataGuide_추가_202610" / "요인_팩터모델과시장지수_일간_1990-2026.xlsx"'),
    ('새목록 = Path(__file__).resolve().parent.parent / "_검증" / "새목록"  # B2(2026-11-04): 예전 데이터로 만든 목록을 새 데이터에서 같은 규칙으로 다시 만든 것(저장소 안)',
     '새목록 = 뿌리 / "저장소_목록"  # B2(2026-11-04): 예전 데이터로 만든 목록을 새 데이터에서 같은 규칙으로 다시 만든 것(저장소 _검증/새목록에서 data/저장소_목록으로 복사)'),
    ('CD_FILE = Path(r"D:\\26-2_데이터기반투자전략\\과제02\\data\\교수제공\\08.[액셀실습]TSMom(K200).xlsx")', 'CD_FILE = 뿌리 / "교수제공" / "08.[액셀실습]TSMom(K200).xlsx"'),
    ('KRX_FILE = Path(r"D:\\26-2_데이터기반투자전략\\과제02\\data\\DataGuide_추가_202611\\R12_통합지수_KRXTMI_KRX300_KRX300TR_KRX100_코스닥TR_I31000040F_일별_19991228-20260930.xlsx")',
     'KRX_FILE = 뿌리 / "DataGuide_추가_202611" / "R12_통합지수_KRXTMI_KRX300_KRX300TR_KRX100_코스닥TR_I31000040F_일별_19991228-20260930.xlsx"'),
    ('변환캐시 = Path(__file__).resolve().parent.parent / "_캐시" / "변환"  # data 폴더에 parquet가 없는 xlsx(분기 R40~, 결산 R32~)를 감독 변환기 함수로 바꾼 것(`_검증/추가_변환.py`, data 폴더에 안 씀)',
     '변환캐시 = DATA  # (제출본에서 바꿈) 저장소에서는 data에 parquet가 없던 분기 R40~·결산 R32~를 저장소 _캐시/변환에 두었으나, 지금은 같은 이름 파일이 data\\통합_전체_202611에 모두 있고 SHA-256도 같아(2026-11-05) 같은 폴더를 가리킴'),
]
평가바꿈 = [
    ('결과폴더 = Path(__file__).resolve().parent.parent / "결과_월수익률"', '결과폴더 = Path("결과") / "결과_월수익률"  # (제출본에서 바꿈) 노트북 옆 결과 폴더'),
    ('    git = lambda *a: subprocess.run(["git", *a], cwd=결과폴더.parent, capture_output=True, text=True, encoding="utf-8").stdout.strip()  # 한글 파일 이름(utf-8)을 cp949로 읽다 깨지지 않게',
     '    git = lambda *a: subprocess.run(["git", *a], cwd=결과폴더.parent, capture_output=True, text=True, encoding="utf-8").stdout.strip() if shutil.which("git") else ""  # 한글 파일 이름(utf-8)을 cp949로 읽다 깨지지 않게. (제출본에서 더함) git이 없는 컴퓨터면 빈칸(기록용 칸, 계산 안 씀)'),
    ('import subprocess\n', 'import shutil  # (제출본에서 더함) git 있는지 보기\nimport subprocess\n'),
]
for 파일, 별칭, 바꿀 in [("데이터읽기", "읽기", 경로), ("지표", "지표", []), ("종목거르기", "종목거르기", []), ("포트폴리오", "포", []), ("평가", "평가", 평가바꿈), ("점검", "점검", [])]:
    s = (REPO / "공통" / f"{파일}.py").read_text(encoding="utf-8")
    code(f"%%모듈 {파일} {별칭}\n" + 바꿈(s, 바꿀).rstrip("\n"), f"공통/{파일}.py")

# ───────────── 2절 엑셀 → parquet (예전과 같음) ─────────────
tp = (ROOT / "data" / "DataGuide_추가_202611" / "_tools" / "_to_parquet.py").read_text(encoding="utf-8")
함수 = tp[tp.index("def labels(rows):"):tp.index("def convert(f):")].rstrip("\n")
md("""## 2. 엑셀 → parquet 다시 만들기 (기본은 끔)
3~8절은 `data\\통합_전체_202611`의 parquet(엑셀을 빠르게 읽으려고 바꾼 파일)를 읽는다. 그 parquet는 `data\\DataGuide_전체_202611`의 DataGuide 원본 엑셀에서 아래 함수(데이터를 받은 원래 data 폴더의 감독 변환기 `DataGuide_추가_202611\\_tools\\_to_parquet.py`의 `labels`·`read_rows`·`to_frame`, 글자 그대로. 변환기 파일은 제출 data에 없음)로 만들었다.
- `엑셀_변환 = True`로 바꾸면 원본 엑셀마다 parquet를 다시 만들어 노트북 옆 `다시만든_parquet` 폴더에 쓰고(data 폴더는 안 건드림), data의 parquet와 값이 칸마다 같은지(`DataFrame.equals`: 날짜·종목·값·빈칸 위치·형식 모두) 찍는다. 엑셀이 커서(파일당 0.2~0.4GB) 파일당 수 분, 전체 수 시간 걸린다.
- 원래 변환기는 저장 뒤 독립 검사기(xlsx XML 직접 읽기)로 한 번 더 대조했다(PASS인 파일만 씀, 기록은 원래 data 폴더의 `DataGuide_추가_202611\\_tools\\_audit`, 제출 data에는 없음). 여기서는 다시 만든 것을 data의 parquet와 값으로 대조한다.
- 읽는 규칙(값은 원본 그대로): '코드' 줄이 있는 시트 중 줄이 가장 많은 시트, 코드 줄 빈칸·중복·날짜 중복·역순·숫자 글자 섞임이면 멈춤, 마지막 날짜 뒤 날짜 없는 줄의 값은 빼고 알림(R24·R25 A015890 한 칸).""")
code("%%절 2\n" + f'''엑셀_변환 = False  # True로 바꾸면 원본 엑셀에서 parquet를 다시 만들어 data의 parquet와 같은지 확인(오래 걸림)
import datetime as dt  # 아래 to_frame이 날짜 칸 형식을 볼 때 씀

# ↓ 감독 변환기 _to_parquet.py의 읽기 함수 세 개(글자 그대로). 원본 엑셀(행 = 날짜, 열 = 종목)을 표로 읽는다.
{함수}


if 엑셀_변환:
    from python_calamine import CalamineWorkbook  # 엑셀을 빨리 읽는 패키지(read_rows가 씀). 이 칸을 켤 때만 필요
    다시 = Path("다시만든_parquet")
    다시.mkdir(exist_ok=True)
    for f in sorted((DATA / "DataGuide_전체_202611").glob("*_I00P_일간_*.xlsx")):  # 일간 아이템 엑셀(X01~X04는 3~8절이 엑셀을 바로 읽음)
        name = f.name.split("_I00P_")[0]  # 예: R08_부채총계_M000902001_결산 (원래 변환기와 같은 이름 규칙)
        (old,) = list((DATA / "통합_전체_202611").glob(f"통합_일간_*_{{name}}.parquet"))
        t0 = time.time()
        item, df = to_frame(read_rows(f))
        new = 다시 / f"통합_일간_{{item}}_{{name}}.parquet"
        df.to_parquet(new)
        같음 = pd.read_parquet(new).equals(pd.read_parquet(old))
        print(f"{{'같음' if 같음 else '다름!'}} {{new.name}}: {{df.shape}}, {{time.time() - t0:.0f}}초", flush=True)
else:
    print("엑셀 → parquet 다시 만들기: 꺼짐(엑셀_변환 = False). 3~8절은 data\\\\통합_전체_202611의 parquet를 읽음")''', "data/DataGuide_추가_202611/_tools/_to_parquet.py#labels·read_rows·to_frame")

# ───────────── 3~6절 따라하기 4개 (칸 전부) ─────────────
for 번호, 기호, rel in 따라:
    md(f"# {번호}. {기호} {제목(rel)}\n저장소 `{rel}`의 칸 전부(맨 위 import 칸은 0·1절이 대신하는 줄만 뺌). 아래 'n절'은 그 노트북의 절 번호.")
    노트북전부(rel, 번호)

# ───────────── 7.1절 확장연구 (예전과 같음) ─────────────
E = "연구/확장연구_20261103.ipynb"
md("# 7. 확장 연구와 이로운 연구\n## 7.1 확장 연구\n저장소 `연구/확장연구_20261103.ipynb`의 칸(원래 import 칸과 7절 기록 표만 뺌). 리밸런싱 주기 비교도 결과를 지우지 않고 그대로 둔다.")
옮김(E, [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
         "> 원래 7절(리밸런싱마다 단계별 종목 수 표)은 옮기지 않았다 → 저장소 `연구/확장연구_20261103.ipynb` 7절 참고.", 30], "7.1",
     {5: [('기간 = ("1990-04", "2026-09")\n', '기간 = ("1990-04", "2026-09")\n'
           'if 시험_기간: 기간 = ("2009-04", "2015-03")  # (제출본에서 더함) 0절 시험_기간일 때만 6년. 아래 표들이 24개월 넘는 줄만 남기므로: 코스피TR·코스닥TR 지수가 2011-01부터 있고, \'공통\' 기간은 최소분산(직전 36개월)에 수익률이 생긴 달부터라 둘 다 24개월 넘게 남도록. 기본은 위 기간\n')],
      7: [('결과, 수익 = {}, {}\n', '포.최소분산기록.clear()  # (제출본에서 더함) 다른 절이 남긴 기록을 지움: 아래 \'최소분산 SLSQP\' 횟수가 이 절 것만 되게(계산에는 안 씀)\n결과, 수익 = {}, {}\n')]},
     칸수=31)

# ───────────── 7.2~7.4 이로운 (예전과 같음) ─────────────
for 번호, 이름, 시험기간, n칸 in [("7.2", "이로운_비중바꾸기", '("1993-04", "1996-03")', 26), ("7.3", "이로운_지표바꾸기", '("2014-04", "2019-03")', 28), ("7.4", "이로운_팩터순서", '("1990-04", "1993-03")', 26)]:
    F_ = f"연구/{이름}.ipynb"
    s9 = 칸(F_, 9)[1]
    추가 = f"if 시험_기간: 설정[\"기간\"] = {시험기간}  # (제출본에서 더함) 0절 시험_기간일 때만 짧게{'(고르는 기간 ~2017-03 35개월, 검증 기간 2017-04~ 24개월이 들어가게)' if 번호 == '7.3' else ''}. 기본은 위 기간\n"
    md(f"## {번호} {이름.replace('_', ': ', 1)}\n저장소 `{F_}`의 칸(원래 1·2절 import 칸과 8절 기록 표만 뺌).")
    idx = [1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, f"> 원래 8절(리밸런싱마다 단계별 종목 수 표)은 옮기지 않았다 → 저장소 `{F_}` 8절 참고.", 20, 21, 22, 23, 24, 25] + ([26, 27] if 이름.endswith("지표바꾸기") else [])
    닫힘 = "\n}\n" if "\n}\n" in s9 else "\n}"
    바꿀 = {9: [(닫힘, 닫힘.rstrip("\n") + "\n" + 추가 if 닫힘.endswith("\n") else 닫힘 + "\n" + 추가.rstrip("\n"))]}
    if 이름.endswith("비중바꾸기"):
        바꿀[13] = [("결과 = 포.실행(설정)\n", "포.최소분산기록.clear()  # (제출본에서 더함) 다른 절(7.1)이 남긴 기록을 지움: 11절 '최소분산 SLSQP' 횟수가 이 실험 것만 되게(계산에는 안 씀)\n결과 = 포.실행(설정)\n")]
    옮김(F_, idx, 번호, 바꿀, 칸수=n칸)

# ───────────── 7.5절 따라하기에서 옮김 (새) ─────────────
md("## 7.5 따라하기에서 옮김 (원문에 없는 우리 추가)\n2026-11-06 회원 결정 \"원문에 말이 없으면 빼. 원문에 있으면 원문대로 해\"에 따라 따라하기 노트북(3~6절)에서 뺀 추가 분석·검정·확인판·민감도·그림·표. 저장소 `연구/따라하기에서_옮김_0N.ipynb`의 칸 전부(맨 위 import 칸은 0·1절이 대신하는 줄만 뺌). 각 노트북 맨 앞 마크다운에 옮긴 목록(무엇·원래 따라하기 몇 절)이 있다.")
for rel in 옮김들:
    n = rel[-7]
    md(f"## 7.5.{n} 따라하기에서 옮김 0{n}: {제목(rel)}\n저장소 `{rel}`.")
    노트북전부(rel, f"7.5.{n}")

# ───────────── 8절 결과요약 (예전과 같음) ─────────────
G = "연구/결과요약_20261103.ipynb"
md("# 8. 원문 대조 요약표 (3~7절이 남긴 파일만 읽음)\n저장소 `연구/결과요약_20261103.ipynb`(대표 노트북)와 `연구/요약표.ipynb`의 칸. 그 노트북의 '먼저 실행할 노트북'은 이 파일의 3~7절이고, 파일 위치는 `결과/` 폴더다(저장소 `결과_월수익률/` → `결과/결과_월수익률/`, `연구/결과/` → `결과/`, `결과_전략수익률/` → `결과/결과_전략수익률/`).")
assert len(칸들(G)) == 25 and len(칸들("연구/요약표.ipynb")) == 3, "결과요약·요약표 칸 수가 예전과 다름: 칸 번호를 다시 봐야 함"
g1 = 칸(G, 1)[1]
뺄 = ["import sys\n", "from pathlib import Path\n", 'sys.path.insert(0, str(Path.cwd().parent / "공통"))\n', "import pandas as pd\n", "import 평가\n"]
옮김(G, [0], "8")
code("%%절 8\n# (제출본) 저장소 칸의 import 줄은 0·1절이 대신해 뺐다\n" + 바꿈(g1, [(x, "") for x in 뺄]).strip("\n"), f"{G}#1")
옮김(G, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], "8")
옮김("연구/요약표.ipynb", [0], "8")
code("%%절 8\n" + NW정리(칸("연구/요약표.ipynb", 2)[1], "code", "연구/요약표.ipynb#2"), "연구/요약표.ipynb#2")
옮김(G, [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], "8")

nbf.validate(nb)
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUT)

# ───────────── 점검 ─────────────
def 코드부분(l):
    return re.sub(r"""(["'])(?:(?!\1).)*\1""", '""', l).split("#")[0]  # 글자 안 # 은 무시


남은경로 = []
for i, c in enumerate(cells):
    if c.cell_type != "code":
        continue
    src = re.sub(r"_스크립트_\w+ = r'''.*?\n'''", "", c.source, flags=re.S)  # 칸 안에 넣은 스크립트 글자는 빼고 봄
    for l in src.splitlines():
        x, raw = 코드부분(l), l.split("#")[0]
        if re.search(r"Path\.cwd\(\)\.parent|os\.environ|runpy\.run_path\(|__file__", x) \
                or re.search(r"""["'](?:[A-Za-z]:\\|[A-Za-z]:/)""", raw) or re.search(r"""["']_검증["']""", raw):
            남은경로.append(f"칸 {i} ({c.metadata.get('출처', '')}): {l.strip()[:160]}")
for x in 남은경로:
    고칠.append("저장소 경로·환경 변수 남음 → " + x)
NW남음 = [f"칸 {i} ({c.metadata.get('출처', '')}): {l.strip()[:120]}" for i, c in enumerate(cells) if c.metadata.get("출처") and not c.metadata["출처"].startswith("공통/")
         for l in c.source.splitlines() if re.search(r"t\(NW|NW보정|HAC|뉴이|NW\(", l) and not re.search(r"뺌|뺐|빼고", l)]  # 공통(글자 그대로)·이 스크립트가 쓴 안내 칸·'NW를 뺌' 기록 줄은 빼고
for n in sorted(검증파일):
    if not (DATA / "저장소_검증" / n).is_file():
        고칠.append(f"저장소 _검증/{n}을 읽는 칸이 있음 → data/저장소_검증/에 복사 필요: python data_추가.py \"{REPO / '_검증' / n}|저장소_검증/{n}|(어느 절)\"")
for x in NW남음:
    고칠.append("NW 남음 → " + x)
# 시험 모드 줄이 있는지(따라하기 4개·옮김 4개)
for 번호, _, rel in 따라 + [(f"7.5.{r[-7]}", "", r) for r in 옮김들]:
    src = "".join("".join(c["source"]) for c in 칸들(rel))
    if "FOLLOW_TEST" not in src:
        고칠.append(f"{rel}: FOLLOW_TEST 시험 줄 없음 → 0절 시험_기간=True여도 이 절은 짧아지지 않음(본 실행에는 영향 없음)")
# data에 없는 파일 이름(글자로 쓴 것만): 노트북이 쓰지도 않는 것
data이름 = {p.name for p in DATA.rglob("*") if p.is_file()} if DATA.is_dir() else set()
코드 = [c.source for c in cells if c.cell_type == "code"]
쓰기식, 읽기식 = r"to_csv\(|to_pickle\(|savefig\(|to_parquet\(|write_text\(|평가\.저장\(", r"read_csv\(|read_pickle\(|read_parquet\(|read_excel\(|open\("
쓴 = set()
for s in 코드:  # 쓰는 칸(여러 줄에 걸친 to_pickle 등)에서 읽기 줄이 아닌 줄의 파일 이름
    if re.search(쓰기식, s):
        쓴 |= {n for l in s.splitlines() if not re.search(읽기식, l) for n in re.findall(r'"([^"/\\{}]+\.(?:csv|pkl|png|parquet|txt))"', l)}
        쓴 |= {f"{n}.pkl" for n in re.findall(r'평가\.저장\(.*?"([^"]+)"', s)}
읽는 = set()
for s in 코드:
    for l in s.splitlines():
        x = l.split("#")[0]
        if re.search(쓰기식, x):
            continue
        읽는 |= set(re.findall(r'"([^"/\\{}*.][^"/\\{}*]*\.(?:csv|pkl|xlsx|parquet))"', x))
없는파일 = sorted(n for n in 읽는 - 쓴 - data이름)
for n in 없는파일:
    고칠.append(f"코드가 글자로 부르는 파일인데 data에도 없고 노트북이 쓰지도 않음(확인 필요): {n}")
# 8절이 읽는 결과 파일 ↔ 앞 절이 쓰는 파일
파일식 = r'"([^"/\\{}]+\.(?:csv|pkl|png))"'
절칸 = {}
for c in cells:
    if c.cell_type == "code" and c.source.startswith("%%절 "):
        절칸.setdefault(c.source.split()[1], []).append(c.source)

# ───────────── 예전 제출본과 절·칸 수 비교 ─────────────
def 절나누기(cs):
    지금, n = "0", OrderedDict()
    for c in cs:
        s = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
        if c["cell_type"] == "markdown" and not c.get("metadata", {}).get("출처"):
            h = re.findall(r"(?m)^#{1,2} (\d+(?:\.\d+)*)\.?\s", s)
            if h:
                지금 = h[-1]
        n.setdefault(지금, Counter())[c["cell_type"]] += 1
    return n


옛 = 절나누기(json.load(open(OLD, encoding="utf-8"))["cells"])
새 = 절나누기(json.load(open(OUT, encoding="utf-8"))["cells"])
키 = list(옛) + [k for k in 새 if k not in 옛]
키 = sorted(키, key=lambda k: [int(x) for x in k.split(".")])
줄 = [f"# 합치기 비교{' (시험: 따라하기 고치는 중인 지금 판)' if 시험 else ''}: 예전 제출본 ↔ 새 노트북, 절·칸 수",
      f"예전 = `{OLD}`, 새 = `{OUT}` (저장소 커밋 {커밋}, 브랜치 {브랜치}, 공통·따라하기·연구 커밋 안 된 변경 {len(변경.splitlines())}개 파일)", "",
      "| 절 | 예전 칸 | 예전 코드 | 예전 마크다운 | 새 칸 | 새 코드 | 새 마크다운 | 칸 차이 |", "|---|---|---|---|---|---|---|---|"]
for k in 키:
    a, b = 옛.get(k, Counter()), 새.get(k, Counter())
    줄.append(f"| {k} | {sum(a.values())} | {a['code']} | {a['markdown']} | {sum(b.values())} | {b['code']} | {b['markdown']} | {sum(b.values()) - sum(a.values()):+d} |")
ta, tb = sum((v for v in 옛.values()), Counter()), sum((v for v in 새.values()), Counter())
줄.append(f"| 합 | {sum(ta.values())} | {ta['code']} | {ta['markdown']} | {sum(tb.values())} | {tb['code']} | {tb['markdown']} | {sum(tb.values()) - sum(ta.values()):+d} |")
새파일(HERE / f"합치기_비교{꼬리}.md").write_text("\n".join(줄) + "\n", encoding="utf-8")

점검 = [f"합치기 점검{' (시험)' if 시험 else ''}: 출력 {OUT}", f"칸 {len(cells)}, 코드 {sum(c.cell_type == 'code' for c in cells)}, 저장소 커밋 {커밋} ({브랜치})",
        f"공통·따라하기·연구 커밋 안 된 변경:\n{변경 or '(없음)'}", f"7.5절 옮김 노트북: {옮김들 or '(없음)'}", "",
        f"## 고칠 것·확인할 것 {len(고칠)}개 (있으면 종료 코드 1)"] + 고칠 + ["", f"## 바꾼 것 {len(기록)}개"] + 기록 + \
       ["", "## 절마다 코드가 쓰는 결과 파일(글자로 쓴 이름만)"] + [f"{k}: {sorted(set(re.findall(파일식, chr(10).join(v))) & 쓴)}" for k, v in 절칸.items()]
새파일(HERE / f"합치기_점검{꼬리}.txt").write_text("\n".join(점검) + "\n", encoding="utf-8")
print("\n".join(점검[:6]))
print(f"고칠 것 {len(고칠)}개 → {HERE / f'합치기_점검{꼬리}.txt'}, 비교 → {HERE / f'합치기_비교{꼬리}.md'}")
sys.exit(1 if 고칠 else 0)
