# 05:55 공통 고침 확인: 금융업 이름='원문'·변동성_원문·우동호2023 master 정의
import sys, pandas as pd
sys.path.insert(0, r"D:\26-2_데이터기반투자전략\과제02\과제02_백테스트\공통")
import 데이터읽기 as 읽기, 지표, 포트폴리오 as 포, 종목거르기
t = pd.Timestamp("2010-04-01")
s = 포.재료(t, 포.우동호2023)
c = 종목거르기.시장(s, s["codes"], ["KS", "KQ"])
넓, 원 = 종목거르기.금융업(s, c), 종목거르기.금융업(s, c, 이름="원문")
print("금융업 넓게 남음", len(넓), "원문 남음", len(원), "원문에서만 남는 종목", list(원.difference(넓))[:20])
assert 넓.isin(원).all() and len(원) >= len(넓)
v0, v1 = 지표.변동성(s), 지표.변동성_원문(s)
print("변동성 값 있음", v0.notna().sum(), "변동성_원문", v1.notna().sum())
assert (v0.dropna() - v1[v0.dropna().index]).abs().max() < 1e-12  # 상장 조건 통과 종목은 같은 값
w = 지표.변동성_창(s, 12, "일", 상장조건=False)
assert ((w - v1).abs().max() < 1e-12) or (w.notna() == v1.notna()).all()
print("변동성_창(상장조건=False) vs 변동성_원문 최대차", (w - v1).abs().max(), "값 있음", w.notna().sum())
assert "재무연도" not in 포.우동호2023 and 포.우동호2023_원문["재무연도"] == "직전년도" and "투자기구" not in 포.우동호2023_원문["제외"]
print("ok")
