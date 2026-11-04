"""README 한계 '거래정지 날 수익률 0'(감독 #16): 확장연구 위험균형도 03 로우볼(_검증/로우볼_거래정지.py)과 같은 확인.
거래정지(S410002600) 날 일간수익률을 빈칸으로 본 변동성으로 위험균형 비중을 다시 매겨 본문과 비교. 공통 코드는 바꾸지 않음. 공통/에서 PYTHONPATH=."""
import pandas as pd
import 데이터읽기 as 읽기
import 포트폴리오 as 포

정지 = 읽기.일간(읽기.정지구분).eq("거래정지")
본문 = 포.위험균형
def 정지빼기(c, s, cfg):
    r = 포.이력(c, s)
    sd = r.mask(정지.reindex(index=r.index, columns=r.columns, fill_value=False)).std()
    iv = 1 / sd.where(sd > 0)
    return iv / iv.sum()
포.위험균형정지빼기 = 정지빼기
설정 = {**포.우동호2023, "이름": "확장 기준 EY+ROC", "기간": ("1990-04", "2026-09"), "가격": 읽기.TR, "재무시점": ("발표일", 150),
        "무위험": "CD1m", "전량교체": False, "비중": ["위험균형", "위험균형정지빼기"]}  # 확장연구 설정(EY+ROC 순위합산·상위 30)
for k in [12, 1]:
    o = 포.실행({**설정, "리밸런싱": k})
    R = o["수익률"].xs("상위30", axis=1, level=1)
    print(f"===== 리밸런싱 {k}개월: 누적", ((1 + R).prod() - 1).round(4).to_dict(), "연환산", ((1 + R).prod() ** (12 / R.notna().sum()) - 1).round(4).to_dict())
    rows = {}
    for t, w in o["보유"][("위험균형", "상위30")].items():
        w2 = o["보유"][("위험균형정지빼기", "상위30")][t]
        창 = 정지.loc[t - pd.DateOffset(years=1):t].reindex(columns=w.index, fill_value=False).iloc[1:].sum()
        rows[t] = {"직전 1년 정지 20일 이상 종목": int((창 >= 20).sum()), "그 종목 비중 합(본문)": float(w[창 >= 20].sum()),
                   "그 종목 비중 합(정지 빼기)": float(w2.reindex(w.index)[창 >= 20].sum()), "비중 차이 합(절대값/2)": float(w.sub(w2, fill_value=0).abs().sum() / 2)}
    r = pd.DataFrame(rows).T
    print(r.describe().loc[["mean", "max"]].round(4).to_string())
    print("리밸런싱", len(r), "회 중 정지 20일 이상 종목을 담은 회:", int((r["직전 1년 정지 20일 이상 종목"] > 0).sum()))
    print("가장 큰 비중 차이 5회:\n", r.nlargest(5, "비중 차이 합(절대값/2)").round(4).to_string())
