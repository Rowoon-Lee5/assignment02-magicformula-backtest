"""02 셀 14 '분기, 최근 분기 × 4' Multi-Metric에서 qcut 오류가 난 기준일과 그때 점수 있는 종목 수를 찾는다(진단만)."""
import pandas as pd
import 데이터읽기 as 읽기
import 포트폴리오 as 포
옛고르기 = 포.고르기
def 고르기(sc, how):
    try:
        return 옛고르기(sc, how)
    except ValueError:
        print("오류: 종목 수", len(sc), "값 수", sc.notna().sum(), sc.head(), flush=True); raise
포.고르기 = 고르기
옛거르기 = 포.거르기
def 거르기(t, cfg):
    out = 옛거르기(t, cfg); print(t.date(), len(out[1]), flush=True) if t.month == 1 else None; 거르기.t = t; return out
포.거르기 = 거르기
기본 = {**포.기본설정, "이름": "NH밸류", "시장": ["KS"], "기간": ("2002-03", "2018-05"), "기준일": "마지막거래일", "리밸런싱": 1,
       "재무시점": ("발표일", 150), "재무주기": ("분기", "최근분기x4"), "제외": [("거래정지", {"아이템": 읽기.정지여부}), "관리종목"],
       "고르기": ("분위", 5), "비중": ["동일"], "거래비용": dict(수수료=0, 거래세=0, 슬리피지=0)}
try:
    포.실행({**기본, "지표": [(m, "높게") for m in ["BP", "EP", "SP", "CFP", "EBITDA_EV"]], "합산": "z합산"})
    print("오류 없음")
except ValueError:
    print("기준일", 거르기.t)
