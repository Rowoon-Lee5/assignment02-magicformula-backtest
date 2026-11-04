"""감사 2 H1: '분위' 고르기를 쓰는 설정마다 리밸런싱일에 점수 있는 종목이 1~(분위 수 − 1)개인 날을 센다(그날은 옛 코드 = 이상한 묶음, 지금 코드 = 빈 묶음).
노트북의 설정 칸(첫 포.실행 앞 코드 칸)을 그대로 실행해 설정을 가져온다. 백테스트(보유·수익률)는 안 돌림.
공통/에서 PYTHONPATH=. 로 실행 → _검증/분위_적은날_결과.txt"""
import json
import pandas as pd
import 포트폴리오 as 포


def 설정칸(nb):
    g = {}
    for c in json.load(open(nb, encoding="utf-8"))["cells"]:
        s = "".join(c["source"])
        if c["cell_type"] != "code" or "포.실행" in s:
            if c["cell_type"] == "code" and "포.실행" in s:
                break
            continue
        s = "\n".join(l for l in s.splitlines() if not l.startswith(("%", "!")))
        try:
            exec(s, g)
        except Exception as e:  # 표 그리기 등 설정과 무관한 칸
            print("  (설정 칸 하나 건너뜀:", type(e).__name__, str(e)[:80], ")")
    return g


def 세기(이름, cfg, 지표묶음, n):
    cfg = {**포.기본설정, **cfg}
    grid = 포.기준일(cfg)
    rows = []
    for t in grid[:-1][::cfg["리밸런싱"]]:
        s, c, _ = 포.거르기(t, cfg)
        ms = list(dict.fromkeys(m[0] for e in 지표묶음.values() for m in e[0]))
        v = pd.DataFrame({m: getattr(포.지표, m)(s).reindex(c) for m in ms}).replace([float("inf"), -float("inf")], float("nan"))
        rows.append({k: len(포.점수(v[[m[0] for m in 지표]], 지표, how)) for k, (지표, how) in 지표묶음.items()} | {"기준일": t})
    d = pd.DataFrame(rows).set_index("기준일")
    적은 = d[(d > 0) & (d < n)]
    print(f"\n## {이름}: 리밸런싱일 {len(d)}, 분위 {n}")
    for k in d:
        x = 적은[k].dropna()
        print(f"  {k}: 1~{n - 1}종목인 날 {len(x)}" + (f" → {', '.join(f'{t:%Y-%m-%d}({int(m)})' for t, m in x.items())}" if len(x) else "") +
              f" / 0종목인 날 {int((d[k] == 0).sum())}")


if __name__ == "__main__":  # 분위_적은날_04.py가 세기()만 가져다 씀
    g2 = 설정칸("../따라하기/02_NH_밸류.ipynb")
    단 = {n: ([(m, "높게")], "순위합산") for n, m in g2["지표명"].items()} | {"Multi-Metric": ([(m, "높게") for m in g2["지표명"].values()], "z합산")}
    for 판, d in {"본문(분기, 4분기 합)": {}, "분기, 최근 분기 × 4": dict(재무주기=("분기", "최근분기x4")), "연간": dict(재무주기=("연간",))}.items():
        세기("02 " + 판, {**g2["기본"], **d}, 단, 5)

    g3 = 설정칸("../따라하기/03_NH_퀄리티로우볼.ipynb")
    단 = {n: ([m], "순위합산") for n, m in g3["지표들"].items()} | {"ROE_양자본": ([("ROE_양자본", "높게")], "순위합산"), "부채비율_양자본": ([("부채비율_양자본", "낮게")], "순위합산")}
    for 판, d in {"본문(분기, 4분기 합)": {}, "분기, 최근 분기 × 4": dict(재무주기=("분기", "최근분기x4")), "연간": dict(재무주기=("연간",)),
                 "연간 180일": dict(재무주기=("연간",), 재무시점=("발표일", 180)), "연간 발표 당일부터": dict(재무주기=("연간",), 재무시점=("발표당일", 150))}.items():
        for k in ((1, 3, 6, 12) if 판 == "본문(분기, 4분기 합)" else (3,)):
            세기(f"03 {판} 리밸런싱 {k}", {**g3["기본"], **d, "리밸런싱": k}, 단, 5)

    g1 = 설정칸("../따라하기/01_우동호2023.ipynb")
    for k in ["MF", "IMF"]:
        c = g1["설정"][k]
        세기(f"01 {k} 분위(14절)", c, {k: (c["지표"], c["합산"])}, 5)

    # 재감사(라운드 2) M1: 처음에 빠뜨린 '분위' 설정(02 7절 현실판 두 기간·13절 배수 그대로·9절 연간 180일·13절 EV 확인판, 03 8절 로우볼 보통주만)
    print("\n# 처음에 빠뜨린 설정(재감사 M1로 더함)")
    멀티 = lambda ms: {"Multi-Metric": ([(m, "높게") for m in ms], "z합산")}
    현실 = {**g2["기본"], "지표": [], "합산": "z합산", "제외": g2["기본"]["제외"] + [("시총상위", {"n": 300}), ("거래대금", {"창": "월"})]}
    세기("02 현실판 2009-01~(7절 본)", {**현실, "기간": ("2009-01", g2["기간"][1])}, 멀티(g2["지표명"].values()), 5)
    세기("02 확장: 현실판 2002-03부터(7절)", 현실, 멀티(g2["지표명"].values()), 5)
    for n, m in g2["지표명"].items():  # 02 셀 28과 같은 정의
        setattr(포.지표, m + "_배수", lambda s, m=m: 1 / getattr(포.지표, m)(s))
    세기("02 배수 그대로(13절)", g2["기본"], {n: ([(m + "_배수", "낮게")], "순위합산") for n, m in g2["지표명"].items()} | {"Multi-Metric": ([(m + "_배수", "낮게") for m in g2["지표명"].values()], "z합산")}, 5)
    세기("02 연간 180일(9절)", {**g2["기본"], "재무주기": ("연간",), "재무시점": ("발표일", 180)}, {n: ([(m, "높게")], "순위합산") for n, m in g2["지표명"].items()}, 5)
    차 = [("EBITDA_EV_차입금" if m == "EBITDA_EV" else m, "높게") for m in g2["지표명"].values()]
    세기("02 연간, EV 확인판(13절)", {**g2["기본"], "재무주기": ("연간",)}, {"EV/EBITDA": ([("EBITDA_EV_차입금", "높게")], "순위합산"), "Multi-Metric": (차, "z합산")}, 5)
    세기("03 로우볼 보통주만(8절)", {**g3["기본"], "제외": ["보통주"] + g3["기본"]["제외"]}, {"로우볼": ([g3["지표들"]["로우볼"]], "순위합산")}, 5)
    print("\n04 '예전 판' 3분위(시총 상위 500·두 지표 있는 종목)는 이 스크립트로 세지 않음(재감사자가 따로 세어 0일).")
