r"""합치기 확인(추가 지시 04:58): 저장소 노트북 짧은 시험 결과(_검증\1106\시험결과) ↔ 제출 노트북 짧은 시험 결과(<제출 시험 결과 폴더>).
같음·결과대조 = _제출작업\숫자대조.py에서 글자 그대로 복사(추가 지시 05:26: 기존 스크립트 import·exec 금지).
pkl은 git 기록 칸(커밋·변경) 빼고 값, csv는 값, png는 값 비교 안 함. 저장소 시험결과에는 예전 시험 파일도 있어 '한쪽만 있음'은 따로 셈.
출력 파일이 이미 있으면 멈춤(덮어쓰기 금지).
쓰는 법: python 시험대조2.py <제출 시험 결과 폴더> --출력 <새 txt>"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


# ---- 아래 두 함수: _제출작업\숫자대조.py 25~73줄 복사 ----
def 같음(a, b, 길=""):
    """다른 곳 목록."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{길}: 키 다름 {sorted(set(map(str, a)) ^ set(map(str, b)))[:5]}"] if set(a) != set(b) else []
        for k in a:
            if k in b and k not in ("커밋", "변경"):
                out += 같음(a[k], b[k], f"{길}/{k}")
        return out
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return [f"{길}: 길이 {len(a)} ≠ {len(b)}"]
        return sum((같음(x, y, f"{길}[{i}]") for i, (x, y) in enumerate(zip(a, b))), [])
    if isinstance(a, (pd.DataFrame, pd.Series)):
        if type(a) is not type(b) or not a.equals(b):
            try:
                n = int((~((a == b) | (a.isna() & b.isna()))).values.sum()) if a.shape == b.shape else "모양 다름"
            except Exception:
                n = "비교 불가"
            return [f"{길}: 표 다름(다른 칸 {n})"]
        return []
    try:
        if isinstance(a, float) and isinstance(b, float) and np.isnan(a) and np.isnan(b):
            return []
        return [] if a == b or bool(np.all(a == b)) else [f"{길}: {a!r} ≠ {b!r}"]
    except Exception:
        return [] if repr(a) == repr(b) else [f"{길}: repr 다름"]


def 결과대조(A, B, 이름):
    줄, 다름 = [f"\n### 결과 파일: {이름}"], 0
    for k in sorted(set(A) | set(B)):
        if k not in A or k not in B:
            줄.append(f"  한쪽만 있음: {k} ({'제출본' if k in A else '참조본'})"); 다름 += 1; continue
        a, b = A[k], B[k]
        if a.suffix == ".pkl":
            d = 같음(pd.read_pickle(a), pd.read_pickle(b))
        elif a.read_bytes() == b.read_bytes():
            d = []
        elif a.suffix == ".csv":
            d = 같음(pd.read_csv(a, encoding="utf-8-sig"), pd.read_csv(b, encoding="utf-8-sig"))
        else:
            d = ["바이트 다름(그림 등)"] if a.suffix != ".png" else []  # png는 글꼴 렌더 바이트가 실행마다 같다는 보장이 없어 값 비교 안 함
            if a.suffix == ".png":
                줄.append(f"  그림(값 비교 안 함): {k}")
                continue
        다름 += bool(d)
        줄.append(f"  {'같음' if not d else '다름!'} {k}" + ("".join(f"\n      {x}" for x in d[:8])))
    return 줄, 다름


# ---- 복사 끝 ----


ap = argparse.ArgumentParser(); ap.add_argument("제출", type=Path); ap.add_argument("--출력", type=Path, required=True)
a = ap.parse_args()
assert not a.출력.exists(), f"이미 있음(덮어쓰지 않음): {a.출력}"
파일 = lambda r: {str(f.relative_to(r)): f for f in r.rglob("*") if f.is_file() and f.suffix in (".pkl", ".csv", ".png")}
A, B = 파일(a.제출), 파일(HERE / "시험결과")
공통 = set(A) & set(B)
줄, 다름 = 결과대조({k: A[k] for k in 공통}, {k: B[k] for k in 공통}, "양쪽에 있는 파일")
줄 += ["", f"제출 시험에만: {sorted(set(A) - set(B))}", f"저장소 시험에만(예전 시험 파일 포함): {sorted(set(B) - set(A))}",
       f"\n요약: 양쪽 {len(공통)}개 중 다름 {다름}개, 제출에만 {len(set(A) - set(B))}, 저장소에만 {len(set(B) - set(A))}"]
a.출력.write_text("\n".join(줄), encoding="utf-8")
print("\n".join(줄[-3:]))
