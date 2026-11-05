r"""B3 대조: 새 제출본(제출_원문대로) 실행 결과 ↔ (a) 저장소 노트북(고친 판) 결과, (b) 어제 제출본 결과.
예전 대조 스크립트를 그대로 가져다 씀(저장소 밖 D:\…\과제02\_제출작업\대조_NW제외.py의 비교·표대조: 칸 이름마다, 한쪽에만 있는 칸,
NW → OLS 이름 바뀐 칸). 줄(index)이 다르면 같은 줄만 비교하도록 감쌈, 줄마다 적는 차이는 칸당 5줄까지. (a)의 파일 짝 규칙은 대조_전체.py의 저장소짝을 넓힌 것.
pkl은 git 기록 칸('커밋'·'변경') 빼고 값 비교, csv는 값 비교, png는 바이트 SHA-256(값 비교 아님, '그림만 다름'으로 따로 셈).
묶음(조정자 지시 03:53): ①01 ②02 ③03 ④04(+2차_07) ⑤확장연구(결과_전략수익률·이로운·확장연구·연구_*, 기간 표 빼고) ⑥기간별·요약표(*기간*·요약표) — 파일 이름으로 나눔.
쓰는 법: python 대조_B3.py <새 결과 폴더> [--저장소 <저장소>] [--어제 <어제 결과 폴더>] [--대조폴더 <폴더>] [--출력 <txt>] [--묶음 N | --합치기]
  --묶음 N = <대조폴더>\절N.txt만, --합치기 = 있는 절1~6.txt를 합쳐 <출력>, 둘 다 없으면 6묶음 모두 + 합치기.
  기본: 저장소 = 이 파일의 저장소, 어제 = _제출작업\전체실행결과\결과, 대조폴더 = <새 결과 폴더>\..\대조, 출력 = <새 결과 폴더>\..\대조_결과.txt"""
import argparse, datetime, hashlib, re, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
W = Path(r"D:\26-2_데이터기반투자전략\과제02\_제출작업")
ap = argparse.ArgumentParser()
ap.add_argument("새", type=Path)
ap.add_argument("--저장소", type=Path, default=Path(__file__).resolve().parents[2])
ap.add_argument("--어제", type=Path, default=W / "전체실행결과" / "결과")
ap.add_argument("--대조폴더", type=Path)
ap.add_argument("--출력", type=Path)
ap.add_argument("--묶음", type=int, choices=range(1, 7))
ap.add_argument("--합치기", action="store_true")
a = ap.parse_args()
출력 = a.출력 or a.새.parent / "대조_결과.txt"
대조폴더 = a.대조폴더 or a.새.parent / "대조"
REPO = a.저장소
묶음이름 = {1: "01 우동호", 2: "02 NH 밸류", 3: "03 NH 퀄리티·로우볼", 4: "04 (+2차_07)", 5: "확장연구(비중·지표·순서·거래비용, 이로운·확장연구 파일)", 6: "기간별·요약표"}

# ---- 예전 대조 함수: _제출작업\대조_NW제외.py의 'NW칸 = re.compile' ~ 'sha = lambda' 앞까지 글자 그대로 복사(추가 지시 05:26: 기존 스크립트 exec 금지) ----
NW칸 = re.compile(r"t\(NW")
새이름 = lambda c: re.sub(r"t\(NW\)", "t(OLS)", c) if isinstance(c, str) else c


def 값줄(v):
    return "빈칸" if np.ndim(v) == 0 and pd.isna(v) else str(v)


def 표대조(a, b, 길):
    """a = 어제, b = 새. 칸 이름마다."""
    out = []
    if isinstance(a, pd.Series):
        a, b = a.to_frame(), b.to_frame()
    if not a.index.equals(b.index):
        out.append(f"{길}: 줄(index) 다름 — 어제 {len(a)}줄, 새 {len(b)}줄")
        return out
    ca, cb = list(a.columns), list(b.columns)
    공통 = [c for c in ca if c in cb]
    어제만, 새만 = [c for c in ca if c not in cb], [c for c in cb if c not in ca]
    for c in 공통:
        if not a[c].equals(b[c]):
            x, y = a[c], b[c]
            틀 = ~((x == y) | (x.isna() & y.isna()))
            out.append(f"{길}: 칸 {c!r} 값 다름 {int(틀.sum())}줄")
            out += [f"      줄 {k!r}: 어제 {값줄(x[k])} → 새 {값줄(y[k])}" for k in x.index[틀]]
    if 어제만 or 새만:
        out.append(f"{길}: 어제만 있는 칸 {len(어제만)}개 {어제만}")
        out.append(f"{길}: 새로만 있는 칸 {len(새만)}개 {새만}")
        for c in 새만:  # NW → OLS 이름 바꾼 칸: 값 전부
            짝 = [o for o in 어제만 if 새이름(o) == c]
            if 짝:
                out.append(f"{길}: 칸 {짝[0]!r} → {c!r} (이름 바뀜, 값은 NW → OLS) 줄마다:")
                out += [f"      줄 {k!r}: 어제 {값줄(a.at[k, 짝[0]])} → 새 {값줄(b.at[k, c])}" for k in b.index]
        남은 = [c for c in 어제만 if 새이름(c) not in 새만 and not NW칸.search(str(c))]
        if 남은:
            out.append(f"{길}: !! NW가 아닌데 없어진 칸 {남은}")
        덤 = [c for c in 새만 if not any(새이름(o) == c for o in 어제만)]
        if 덤:
            out.append(f"{길}: !! 어제 짝이 없는 새 칸 {덤}")
    return out


def 비교(a, b, 길=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{길}: 키 다름 {sorted(set(map(str, a)) ^ set(map(str, b)))}"] if set(a) != set(b) else []
        for k in a:
            if k in b and k not in ("커밋", "변경"):
                out += 비교(a[k], b[k], f"{길}/{k}")
        return out
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return [f"{길}: 길이 {len(a)} ≠ {len(b)}"]
        return sum((비교(x, y, f"{길}[{i}]") for i, (x, y) in enumerate(zip(a, b))), [])
    if isinstance(a, (pd.DataFrame, pd.Series)):
        if type(a) is not type(b):
            return [f"{길}: 형식 다름"]
        return [] if a.equals(b) else 표대조(a, b, 길)
    try:
        if isinstance(a, float) and isinstance(b, float) and np.isnan(a) and np.isnan(b):
            return []
        return [] if a == b or bool(np.all(a == b)) else [f"{길}: {a!r} ≠ {b!r}"]
    except Exception:
        return [] if repr(a) == repr(b) else [f"{길}: repr 다름"]
# ---- 복사 끝 ----


def 새파일(p):
    """이미 있으면 덮어쓰지 않고 _2, _3 …(추가 지시 05:26)."""
    q, i = p, 2
    while q.exists():
        q, i = p.with_name(f"{p.stem}_{i}{p.suffix}"), i + 1
    return q
_표대조 = 표대조


def 표대조(x, y, 길):  # noqa: F811  비교()가 부르는 이름을 덮어씀
    if isinstance(x, pd.Series):
        x, y = x.to_frame(), y.to_frame()
    out = []
    if not x.index.equals(y.index):
        공 = x.index.intersection(y.index)
        out.append(f"{길}: 줄(index) 다름 — 어제 {len(x)}줄, 새 {len(y)}줄, 같은 줄 {len(공)}; 어제만 {list(x.index.difference(y.index))[:3]}…, 새만 {list(y.index.difference(x.index))[:3]}…")
        if not (x.index.is_unique and y.index.is_unique) or not len(공):
            return out
        x, y, 길 = x.loc[공], y.loc[공], f"{길} [같은 줄만]"
    n, 짧게 = 0, []
    for l in _표대조(x, y, 길):
        n = n + 1 if l.startswith("      줄 ") else 0
        if n <= 5:
            짧게.append(l)
        elif n == 6:
            짧게.append("      … (칸당 5줄까지만 적음)")
    return out + 짧게


sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
파일들 = lambda d: {str(f.relative_to(d)): f for f in sorted(d.rglob("*")) if f.is_file()} if d.exists() else {}


def 묶음(rel):
    n = Path(rel).name
    if m := re.match(r"0([1-4])_", n):
        return int(m.group(1))
    if n.startswith("2차_"):
        return 4
    if "기간" in Path(rel).stem or n.startswith("요약표"):
        return 6
    return 5


def 저장소짝(rel):  # 대조_전체.py 저장소짝을 넓힌 것
    p = Path(rel)
    후보 = []
    if p.parts[0] in ("결과_월수익률", "결과_전략수익률"):
        후보.append(REPO / p)
    if p.name.startswith("이로운_"):  # 저장소는 같은 이름이 있으면 _1·_2·…를 붙여 저장 → 가장 나중에 쓴 것
        후보 += sorted((REPO / "연구/결과").glob(p.stem + "*" + p.suffix), key=lambda f: f.stat().st_mtime, reverse=True)
    후보 += [d / p.name for d in (REPO / "연구/결과", REPO / "따라하기/결과", REPO / "_검증", REPO / "결과_월수익률", REPO / "결과_전략수익률")]
    return next((f for f in 후보 if f.exists()), None)


def 차이(p, q):
    """p = 기준(어제/저장소), q = 새. 다른 곳 목록(같으면 빈 목록)."""
    if p.suffix == ".png":
        return [] if sha(p) == sha(q) else ["그림 바이트 다름(SHA-256, 값 비교 아님)"]
    if p.read_bytes() == q.read_bytes():
        return []
    if p.suffix == ".pkl":
        return 비교(pd.read_pickle(p), pd.read_pickle(q))
    if p.suffix == ".csv":
        return 비교(pd.read_csv(p, encoding="utf-8-sig", low_memory=False), pd.read_csv(q, encoding="utf-8-sig", low_memory=False))
    return ["바이트 다름"]


def 파일줄(k, d, 기준):
    return f"  {'같음' if not d else ('그림만 다름' if k.endswith('.png') else '값 다름')} {k}" + "".join(f"\n    {l.replace('어제', 기준)}" for l in d)


def 대조(n):
    새 = {k: v for k, v in 파일들(a.새).items() if 묶음(k) == n}
    어제 = {k: v for k, v in 파일들(a.어제).items() if 묶음(k) == n}
    줄 = [f"# 절{n}. {묶음이름[n]} ({datetime.datetime.now():%Y-%m-%d %H:%M:%S})", f"새 = {a.새} ({len(새)}개) / 저장소 = {REPO} / 어제 = {a.어제} ({len(어제)}개)", ""]
    # (a) 새 ↔ 저장소
    짝 = {k: 저장소짝(k) for k in 새}
    없음 = sorted(k for k, v in 짝.items() if v is None)
    B = {k: v for k, v in 짝.items() if v}
    da = {k: 차이(B[k], 새[k]) for k in B}
    다름a = sum(bool(d) for k, d in da.items() if not k.endswith(".png"))
    그림a = sum(bool(d) for k, d in da.items() if k.endswith(".png"))
    쓴 = {v.resolve() for v in B.values()}
    남 = [f for d in ("결과_월수익률", "결과_전략수익률") for f in sorted((REPO / d).glob("*.*")) if f.resolve() not in 쓴 and 묶음(f.name) == n]
    줄 += [f"## (a) 저장소 노트북(고친 판) 결과 → 새: 짝 {len(B)}개, 저장소 짝 없음 {len(없음)}개, 값 다름 {다름a}개, 그림 바이트 다름 {그림a}개, 새에 없는 저장소 파일 {len(남)}개"]
    줄 += [파일줄(k, d, "저장소") for k, d in da.items()]
    줄 += [f"  짝: {k} ↔ {v.relative_to(REPO)}" for k, v in B.items() if str(v.relative_to(REPO)) != k]
    줄 += [f"  (저장소 짝 없음) {k}" for k in 없음] + [f"  (새에 없는 저장소 결과 파일) {f.relative_to(REPO)}" for f in 남]
    # (b) 어제 → 새
    공통 = sorted(set(어제) & set(새))
    없어짐, 생김 = sorted(set(어제) - set(새)), sorted(set(새) - set(어제))
    db = {k: 차이(어제[k], 새[k]) for k in 공통}
    바뀜 = sum(bool(d) for d in db.values())
    줄 += ["", f"## (b) 어제 제출본 → 새: 양쪽 {len(공통)}개 중 바뀜 {바뀜}개(그림 {sum(bool(d) for k, d in db.items() if k.endswith('.png'))}개 포함), 없어짐 {len(없어짐)}개, 생김 {len(생김)}개"]
    줄 += [f"  없어진 파일(어제만) {k}" for k in 없어짐] + [f"  생긴 파일(새만) {k}" for k in 생김] + [파일줄(k, d, "어제") for k, d in db.items()]
    # 원문 대조표·판정 칸 전후(글자 그대로)
    줄 += ["", "## 원문 대조표·판정 칸 전후 (어제 → 새, 파일 글자 그대로)"]
    for k in sorted(set(어제) | set(새)):
        if Path(k).suffix == ".csv" and re.search(r"원문|대조|판정|주장", Path(k).stem):
            for 이름, d in (("어제", 어제), ("새", 새)):
                f = d.get(k)
                줄 += [f"\n### {k} — {이름}", pd.read_csv(f, encoding="utf-8-sig").to_string() if f else "(파일 없음)"]
    요약 = f"절{n} {묶음이름[n]}: (a) 값 다름 {다름a}·그림 다름 {그림a}·저장소 짝 없음 {len(없음)}·새에 없는 저장소 파일 {len(남)} / (b) 바뀜 {바뀜}·없어짐 {len(없어짐)}·생김 {len(생김)}"
    대조폴더.mkdir(parents=True, exist_ok=True)
    새파일(대조폴더 / f"절{n}.txt").write_text(f"요약: {요약}\n" + "\n".join(줄) + "\n", encoding="utf-8")
    print(f"썼음 {대조폴더 / f'절{n}.txt'} — {요약}")


def 합치기():
    있는 = [대조폴더 / f"절{n}.txt" for n in 묶음이름 if (대조폴더 / f"절{n}.txt").exists()]
    글 = [f.read_text(encoding="utf-8") for f in 있는]
    머리 = [f"B3 대조 결과 (합친 때 {datetime.datetime.now():%Y-%m-%d %H:%M:%S}, 스크립트 {Path(__file__)}, 조각 폴더 {대조폴더})",
            f"새 = {a.새} / 저장소 = {REPO} / 어제 = {a.어제}", f"묶음 {len(있는)}/6개" + (f", 없는 묶음 {[n for n in 묶음이름 if not (대조폴더 / f'절{n}.txt').exists()]}" if len(있는) < 6 else ""), "",
            "## 요약"] + [g.splitlines()[0] for g in 글] + [""]
    출력.parent.mkdir(parents=True, exist_ok=True)
    새파일(출력).write_text("\n".join(머리) + "\n" + "\n\n".join(글), encoding="utf-8")
    print(f"합침 {출력} (절 {len(있는)}개)")


if a.묶음:
    대조(a.묶음)
if a.합치기:
    합치기()
if not a.묶음 and not a.합치기:
    for n in 묶음이름:
        대조(n)
    합치기()
