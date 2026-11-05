# N01b 작은 확인: 01 요인 F의 SMB·HML·MOM = DataGuide 지수 비율 그대로인지, 우동호2023_원문 거르기 단계, 옮김_01 칸 14·22 새 줄이 도는지 (기간 1년)
import sys
from pathlib import Path
ROOT = Path(r"D:\26-2_데이터기반투자전략\과제02\과제02_백테스트")
sys.path.insert(0, str(ROOT / "공통"))
import pandas as pd
import 데이터읽기 as 읽기, 포트폴리오 as 포, 평가

cfg = {**포.우동호2023_원문, "기간": ("2004-04", "2005-03"), "끝": "마지막거래일"}
g = 포.기준일(cfg)
F = 평가.요인(g, cfg)
r = 읽기.지수().reindex(g).pct_change(fill_method=None)
for a, b in [("SMB", "3FM.2B3.SMB"), ("HML", "3FM.2B3.HML"), ("MOM", "3FM.2M3.MOM")]:
    print(a, "= DataGuide", b, ":", F[a].equals(r[b]), "/ 값 있는 달", int(F[a].notna().sum()), "/ 첫 값", F[a].dropna().iloc[0])
t0 = g[0]
s, c, n = 포.거르기(t0, cfg)
print(t0.date(), "단계별 남은 수:", n)
print("투자기구 이름에 걸림(안 거름):", len(c) - len(포.종목거르기.투자기구(s, c)))
ex = [x for f in cfg["제외"] for x in ([f, "투자기구"] if isinstance(f, tuple) and f[0] == "금융업" else [f])]
print("투자기구 거름 판 제외 목록:", ex)
print("투자기구 거름 판 단계별:", 포.거르기(t0, {**cfg, "제외": ex})[2])
