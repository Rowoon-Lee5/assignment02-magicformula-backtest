"""연구 노트북 NW 참조 고치기(R-NW, 2026-11-06). _제출작업\\NW제외_고치기.py 규칙 재사용, 출력은 그대로 둠(코드·마크다운 source만).
바꾼 칸과 줄 전후를 R_NW_고치기_로그.txt에."""
import difflib, json, re
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "연구"
LOG = Path(__file__).with_name("R_NW_고치기_로그.txt")
줄임 = "NW는 회원 결정(2026-11-06)으로 뺌, t는 OLS"
뉴이 = "NW(뉴이-웨스트: 자기상관·이분산을 감안한 t)"
CT = '"Carhart t(NW)"'

# 파일: [(칸, 앞, 뒤, 개수)]
할일 = {
    "연구_틀.ipynb": [(0, 뉴이, 줄임, 1), (16, CT, '"Carhart t(OLS)"', 1)],
    "이로운_비중바꾸기.ipynb": [(1, 뉴이, 줄임, 1), (17, CT, '"Carhart t(OLS)"', 1)],
    "이로운_지표바꾸기.ipynb": [(1, 뉴이, 줄임, 1), (17, CT, '"Carhart t(OLS)"', 1), (23, CT, '"Carhart t(OLS)"', 1)],
    "이로운_팩터순서.ipynb": [(1, 뉴이, 줄임, 1), (17, CT, '"Carhart t(OLS)"', 1)],
    "요약표.ipynb": [(0, "**평균 t(NW)**: 그 평균의 뉴이-웨스트 t.", "**평균 t(OLS)**: 그 평균의 OLS t.", 1),
                     (0, "**α t(NW)**: 그 t.", "**α t(OLS)**: 그 t.", 1),
                     (0, 뉴이, 줄임, 1)],
    "확장연구_20261103.ipynb": [
        (0, "NW(뉴이-웨스트 t)", 줄임, 1),
        (8, "각 t(OLS·NW)", "각 t(OLS)", 1),
        (9, ', "CAPM t(NW)", "CAPM t(NW보정)"', "", 1),
        (9, ', "FF3 t(NW)", "FF3 t(NW보정)"', "", 1),
        (9, ', "Carhart t(NW)", "Carhart t(NW보정)"', "", 1),
        (11, CT, '"Carhart t(OLS)"', 1),
        (26, "Carhart α·t(NW)", "Carhart α·t(OLS)", 1),
        (27, CT, '"Carhart t(OLS)"', 2),
    ],
    "결과요약_20261103.ipynb": [
        (0, "NW(뉴이-웨스트 t)", 줄임, 1),
        (2, "1-1절의 'Carhart t(NW)'는 뉴이-웨스트 t다.", "1-1절의 'Carhart t(OLS)'도 OLS t다(회원 결정(2026-11-06)으로 NW를 뺌).", 1),
        (5, CT, '"Carhart t(OLS)"', 1),
        (11, CT, '"Carhart t(OLS)"', 1),
        (23, CT, '"Carhart t(OLS)"', 1),
    ],
    # 따라하기에서_옮김_01: 코드에 NW 없음. 0칸 마크다운 표의 NW 줄은 "회원 결정으로 뺌(NW)" 기록이라 그대로.
}

로그 = []
for f, ops in 할일.items():
    p = D / f
    raw = p.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    nb = json.loads(raw)
    old = [("".join(c["source"])) for c in nb["cells"]]
    for i, a, b, n in ops:
        s = "".join(nb["cells"][i]["source"])
        assert s.count(a) == n, (f, i, a, s.count(a))
        nb["cells"][i]["source"] = s.replace(a, b).splitlines(keepends=True)
    로그.append(f"##### {f}")
    for i, c in enumerate(nb["cells"]):
        sa, sb = old[i], "".join(c["source"])
        if sa != sb:
            로그.append(f"=== 칸 {i} ({c['cell_type']}) ===")
            로그 += [l for l in difflib.unified_diff(sa.splitlines(), sb.splitlines(), lineterm="", n=0) if not l.startswith(("---", "+++", "@@"))]
    t = json.dumps(nb, ensure_ascii=False, indent=1) + "\n"
    p.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))

LOG.write_text("\n".join(로그) + "\n", encoding="utf-8")
print("\n".join(로그))
