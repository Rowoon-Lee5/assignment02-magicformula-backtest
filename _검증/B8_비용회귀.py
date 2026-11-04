"""한계 15·21·40번 고침 회귀(2026-11-04): `포.보유` 예전(첫 달에만 비용, 폐지 종목 굳은 비중에도 매도비용) 대 새.
비용이 있는 기준 전략만(01 MF·IMF 전량교체, 확장 기준 부분교체 1·12개월, 02 현실판 월비용). 공통/에서 PYTHONPATH=."""
import pandas as pd
import 데이터읽기 as 읽기
import 포트폴리오 as 포

새보유 = 포.보유


def 예전보유(R, W, 비용, 전량=False, 회전=None):
    out, old, dates = [], pd.Series(dtype=float), sorted(W)
    for t0, t1 in zip(dates, dates[1:] + [R.index[-1]]):
        w = W[t0]
        r = R.loc[(R.index > t0) & (R.index <= t1), w.index]
        g = (1 + r.fillna(0)).cumprod()
        v = g.shift(1, fill_value=1) * w
        pr = (1 + (v * r).sum(axis=1) / v.where(r.notna()).sum(axis=1)) * (1 - 비용.get("월비용", 0)) - 1
        c = 포.거래비용(old, w[:0], 비용) + 포.거래비용(w[:0], w, 비용) if 전량 else 포.거래비용(old, w, 비용)
        if 회전 is not None:
            회전[t0] = w.sub(old, fill_value=0).clip(lower=0).sum()
        pr.iloc[0] = (1 - c) * (1 + pr.iloc[0]) - 1
        old = g.iloc[-1] * w / (g.iloc[-1] * w).sum()
        out.append(pr)
    return pd.concat(out)


기간 = ("2004-04", "2022-03")
월비용 = dict(수수료=0, 거래세=0, 슬리피지=0, 월비용=0.002)
설정 = {"01 MF": {**포.우동호2023, "기간": 기간, "끝": "마지막거래일"},
        "01 IMF": {**포.우동호2023, "이름": "IMF", "기간": 기간, "끝": "마지막거래일", "지표": [("GPA", "높게"), ("EY", "높게")]},
        "확장 기준 12개월(부분교체)": {**포.우동호2023, "기간": ("1990-04", "2026-09"), "가격": 읽기.TR, "재무시점": ("발표일", 150), "무위험": "CD1m", "전량교체": False},
        "확장 기준 1개월(부분교체)": {**포.우동호2023, "기간": ("1990-04", "2026-09"), "가격": 읽기.TR, "재무시점": ("발표일", 150), "무위험": "CD1m", "전량교체": False, "리밸런싱": 1},
        "02 현실판(월비용 0.2%)": {**포.기본설정, "이름": "현실", "시장": ["KS"], "기간": ("2009-01", "2018-05"), "기준일": "마지막거래일", "리밸런싱": 1,
                              "재무시점": ("발표일", 150), "제외": [("거래정지", {"아이템": 읽기.정지여부}), "관리종목", ("시총상위", {"n": 300}), ("거래대금", {"창": "월"})],
                              "지표": [(m, "높게") for m in ["BP", "EP", "SP", "CFP", "EBITDA_EV"]], "합산": "z합산", "고르기": ("분위", 5), "비중": ["동일"], "거래비용": 월비용}}
for 이름, cfg in 설정.items():
    out = {}
    for 판, f in {"예전": 예전보유, "새": 새보유}.items():
        포.보유 = f
        out[판] = 포.실행(cfg)
    포.보유 = 새보유
    for k in out["새"]["수익률"]:
        r0, r1 = out["예전"]["수익률"][k].dropna(), out["새"]["수익률"][k].dropna()
        d = (r1 - r0).reindex(r0.index.union(r1.index))
        print(f"{이름} {k}: 누적 {(1 + r0).prod() - 1:.4f} → {(1 + r1).prod() - 1:.4f}, 다른 달 {int(d.abs().gt(1e-12).sum())}, "
              f"빈칸 위치 다름 {int(r0.index.symmetric_difference(r1.index).size)}, 차이 최대 {d.abs().max():.5f}")
