"""G02 셀(G02_그림25_26_셀.py)을 02 노트북 1~3절과 같은 준비(2026-11-06 노트북 칸 2·4·6 그대로)로 짧게 돌려 오류만 본다.
실행: FOLLOW_TEST=1 이면 기간 2002-03~2004-02, 결과 csv·그림은 _검증\\1106\\시험결과\\. 인자 '2010'을 주면 2010-01~2011-12,
'2014'를 주면 2013-11~2014-10을 본 실행 갈래(시험=False)로(저장은 시험결과\\)."""
import os, sys, time
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
여기 = Path(__file__).resolve().parent
os.chdir(여기.parents[1] / "따라하기")  # 노트북과 같은 cwd
sys.path.insert(0, str(Path.cwd().parent / "공통"))
import numpy as np, pandas as pd
import 데이터읽기 as 읽기, 종목거르기, 지표, 포트폴리오 as 포, 평가
display = print
T = time.time()
시험 = os.environ.get("FOLLOW_TEST") == "1"
assert 시험, "FOLLOW_TEST=1 로만 돌린다(결과_월수익률\\ 덮어쓰기 막기)"
평가.결과폴더 = 여기 / "시험결과"
평가.결과폴더.mkdir(parents=True, exist_ok=True)
기간 = ("2010-01", "2011-12") if "2010" in sys.argv else ("2002-03", "2004-02")
if "2014" in sys.argv:  # 본 실행 갈래(시험=False: 그림 25 2010-02부터 자르기·2014년 이후 판정)를 짧은 기간으로. 저장은 그대로 시험결과\
    기간, 시험 = ("2013-11", "2014-10"), False
기본 = {**포.기본설정, "이름": "NH밸류", "시장": ["KS"], "가격": 읽기.수정주가, "기간": 기간, "기준일": "마지막거래일", "리밸런싱": 1,
       "재무주기": ("발표값",), "재무시점": ("발표월말", 0), "제외": [("거래정지", {"아이템": 읽기.정지여부}), "관리종목", "보통주"],
       "고르기": ("분위", 5), "비중": ["동일"], "거래비용": dict(수수료=0, 거래세=0, 슬리피지=0)}
코드 = [c for c in (여기 / "G02_그림25_26_셀.py").read_text(encoding="utf-8").split("# %%") if not c.startswith(" [markdown]")]
for i, c in enumerate(코드):
    if c.strip():
        exec(compile(c, f"셀{i}", "exec"), globals())
print(대조25_26.to_string())
for n, f in zip(("그림25", "그림26"), plt.get_fignums()):
    plt.figure(f).savefig(평가.결과폴더 / f"G02_{n}_{기간[0]}.png", dpi=80)
print("월수익률 LS3 첫·끝", LS3.dropna(how="all").index[[0, -1]].strftime("%Y-%m").tolist(), "개월", len(LS3.dropna(how="all")))
print(f"끝 {time.time() - T:.0f}초")
