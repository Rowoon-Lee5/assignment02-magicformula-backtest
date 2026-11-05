"""05:50-3: 늦게 나온 옛 기간 보고서가 새 보고서를 덮는 경우 건수(계산은 안 바꿈, 세기만).
규칙은 공통 `포.발표재무(t)` 그대로: 월말까지 가능일이 든 보고서를 (가능일, 분기말) 순으로 정렬해 마지막 = 고른 보고서.
덮임 = 고른 보고서의 분기말 < 그때까지 발표된 그 종목 보고서 중 가장 늦은 분기말.
리밸런싱일 = 그 달 마지막 거래일(02·03 따라하기). 셀 종목 = 그날 상장 가격(수정주가) 있는 종목(포.재료의 codes와 같음).
출력: _검증/1106/늦은보고서_건수.txt (이미 있으면 _2, _3 …)."""
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "공통"))
import 데이터읽기 as 읽기  # noqa: E402
import 포트폴리오 as 포  # noqa: E402

f = 포.발표행()[["코드", "분기말", "가능일", "보고서"]]
p = 읽기.상장가격(읽기.수정주가)
d = p.index.to_series()
월끝 = d.groupby(d.dt.to_period("M")).max()  # 달마다 마지막 거래일

# 포.발표재무와 같은 정렬. 종목마다 (가능일, 분기말) 순 누적 최대 분기말과 비교.
f = f.sort_values(["코드", "가능일", "분기말"]).reset_index(drop=True)
f["앞최대"] = f.groupby("코드")["분기말"].cummax()
f["덮임"] = f["분기말"] < f["앞최대"]
# 월말 t에서 고른 행 = 가능일이 t가 든 달 말 이하인 행 중 마지막 → (코드, 가능일의 달)마다 마지막 행이 그 달부터 다음 행의 달 전까지 쓰인다.
f["달"] = f["가능일"].dt.to_period("M")
끝행 = f.groupby(["코드", "달"]).tail(1)

rows = []
for m, t in 월끝.items():
    g = 끝행[끝행["달"] <= m].groupby("코드").tail(1)  # 끝행은 코드·가능일 순이라 tail(1) = 그 달까지 마지막
    listed = p.columns[p.loc[t].notna()]
    g = g[g["코드"].isin(listed)]
    rows.append(dict(달=m, t=t, 종목=len(g), 덮임=int(g["덮임"].sum()), 보통주KS=0, 덮임_보통주KS=0, 예=g[g["덮임"]]))
# 보통주·KS(02·03 유니버스 근사: 관리·정지 거르기 전)
시장 = 읽기.일간(읽기.시장구분)
for r in rows:
    g = r["예"]
    ks = 시장.loc[r["t"]].reindex(g["코드"]).eq("KS").to_numpy() & g["코드"].str.endswith("0").to_numpy()
    r["덮임_보통주KS"] = int(ks.sum())

def 합(a, b):
    sel = [r for r in rows if pd.Period(a, "M") <= r["달"] <= pd.Period(b, "M")]
    return len(sel), sum(r["종목"] for r in sel), sum(r["덮임"] for r in sel), sum(r["덮임_보통주KS"] for r in sel)

out = []
out.append("늦게 나온 옛 기간 보고서가 새 보고서를 덮는 종목-월 (규칙 = 공통 포.발표재무, 상한 없음)")
out.append(f"발표행 {len(f):,}행, 그 가운데 발표될 때 이미 더 늦은 기간 보고서가 나와 있던 행(덮임 행) {int(f['덮임'].sum()):,}행 "
           f"(분기 {int(f.loc[f['덮임'] & (f['보고서'] == '분기')].shape[0]):,} · 연간 {int(f.loc[f['덮임'] & (f['보고서'] == '연간')].shape[0]):,})")
for 이름, a, b in [("전체", str(월끝.index[0]), str(월끝.index[-1])), ("02 따라하기 기간", "2002-03", "2018-05"), ("03 따라하기 기간", "2002-03", "2018-09")]:
    n, 전, 덮, ks = 합(a, b)
    out.append(f"{이름} {a}~{b}: 월말 {n}개, 상장 종목-월(보고서 있음) {전:,}, 덮임 {덮:,} ({덮 / 전:.4%}), 그 가운데 KS 보통주 {ks:,}")
# 예시 3개: 덮임 행 가운데 앞 최대 분기말과 차이가 큰 것부터가 아니라, 기간 안 처음 나온 순서로(고르는 잣대 없이)
예 = pd.concat([r["예"].assign(t=r["t"]) for r in rows if r["덮임"]])
예 = 예[(예["t"] >= "2002-03-01") & (예["t"] <= "2018-09-30")].drop_duplicates(["코드", "분기말", "가능일"])
이름표 = 읽기.종목정보()["코드명"]
out.append("예시(02·03 기간 안, 덮임 행이 처음 쓰인 월말 순 앞 3개):")
for _, r in 예.sort_values("t").head(3).iterrows():
    out.append(f"  {r['코드']} {이름표.get(r['코드'], '')}: 월말 {r['t']:%Y-%m-%d}에 고른 보고서 = {r['보고서']} 분기말 {r['분기말']:%Y-%m-%d} (발표 {r['가능일']:%Y-%m-%d}), "
               f"이미 발표된 가장 늦은 기간 끝 {r['앞최대']:%Y-%m-%d}")
txt = "\n".join(out)
print(txt)
base = os.path.join(ROOT, "_검증", "1106", "늦은보고서_건수")
path, k = base + ".txt", 2
while os.path.exists(path):
    path, k = f"{base}_{k}.txt", k + 1
open(path, "w", encoding="utf-8").write(txt + "\n")
print("저장:", path)
