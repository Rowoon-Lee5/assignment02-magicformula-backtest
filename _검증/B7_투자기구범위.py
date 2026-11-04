"""한계 26번(투자기구 이름 규칙 범위): 금융업·투자기구를 거친 뒤에도 남는 '펀드·투자회사·인프라·스팩·리츠·선박·부동산' 이름 종목을
01(우동호 MF, 2004-04~) 리밸런싱일마다, 그리고 그중 ROC·EY가 있어 순위에 드는 것·상위 30에 든 것을 센다. 코드는 바꾸지 않음. 공통/에서 PYTHONPATH=."""
import numpy as np
import pandas as pd
import 데이터읽기 as 읽기
import 지표
import 포트폴리오 as 포

pat = "펀드|투자회사|인프라|스팩|기업인수목적|리츠|선박|부동산|뮤추얼"
name = 읽기.종목정보()["코드명"].astype(str)
for 이름, 기간 in {"01 MF(2004-04~2022-03)": ("2004-04", "2022-03"), "확장 기준(1990-04~2026-09)": ("1990-04", "2026-09")}.items():
    cfg = {**포.우동호2023, "기간": 기간}
    o = 포.실행(cfg)
    보유 = o["보유"][("동일", "상위30")]
    rows = []
    for t in 포.기준일(cfg)[:-1][::12]:
        s, c, _ = 포.거르기(t, cfg)
        hit = c[name.reindex(c).str.contains(pat, na=False).to_numpy()]
        v = pd.DataFrame({m: getattr(지표, m)(s).reindex(hit) for m in ["ROC", "EY"]}).replace([np.inf, -np.inf], np.nan).dropna()
        held = [k for k in hit if t in 보유 and k in 보유[t].index]
        rows.append({"기준일": t.date(), "거른 뒤 남은 이름 걸린 종목": len(hit), "순위 매김": len(v), "상위 30 보유": len(held),
                     "보유 종목": ", ".join(f"{k} {name[k]}" for k in held), "남은 종목 예": ", ".join(f"{k} {name[k]}" for k in hit[:6])})
    r = pd.DataFrame(rows).set_index("기준일")
    print(f"===== {이름}\n", r.to_string())
    print("합: 남은", int(r.iloc[:, 0].sum()), "/ 순위", int(r["순위 매김"].sum()), "/ 보유", int(r["상위 30 보유"].sum()))
