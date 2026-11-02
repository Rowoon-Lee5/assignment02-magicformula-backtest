"""'쓰지 말 것' 칸(예전 데이터로 찾은 것)이 새 일간 파일에서도 같은 모양인지 확인. 값은 안 고침."""
import sys
sys.path.insert(0, r"D:\26-2_데이터기반투자전략\과제02\과제02_백테스트\공통")
import pandas as pd
import 데이터읽기 as 읽기

d = 읽기.DATA.parent / "DataGuide_추가_202610"
p, tr = 읽기.일간(읽기.수정주가), 읽기.일간(읽기.TR)
m = pd.read_csv(d / "수정주가_병합미반영_7칸.csv", encoding="utf-8-sig", parse_dates=["날짜(월말)"])
pm = p.resample("ME").last()
m["새 수정주가 월수익률"] = [pm[c].pct_change(fill_method=None).get(x + pd.offsets.MonthEnd(0)) for c, x in zip(m["코드"], m["날짜(월말)"])]
print("D27 7칸:\n", m[["코드", "날짜(월말)", "수정주가 월수익률", "새 수정주가 월수익률"]].round(4).to_string())
a = pd.read_csv(d / "수정주가TR_이상칸.csv", encoding="utf-8-sig", parse_dates=["날짜", "앞_날짜"])
a = a[a["날짜"] <= p.index[-1]]
f = lambda q, c, x, y: q.at[y, c] / q.at[x, c] - 1 if c in q else float("nan")
a["새 TR수익률"] = [f(tr, c, x, y) for c, x, y in zip(a["코드"], a["앞_날짜"], a["날짜"])]
a["새 가격수익률"] = [f(p, c, x, y) for c, x, y in zip(a["코드"], a["앞_날짜"], a["날짜"])]
same = ((a["새 TR수익률"] - a["TR수익률"]).abs() < 1e-3) & ((a["새 가격수익률"] - a["가격수익률"]).abs() < 1e-3)
print(f"TR 이상칸 {len(a)}칸 중 새 데이터에서 TR·가격 수익률이 예전과 같음(차 < 0.001) {int(same.sum())}칸")
print(a.loc[~same, ["코드", "이름", "날짜", "TR수익률", "새 TR수익률", "가격수익률", "새 가격수익률", "유형"]].round(4).to_string())
x = p.loc["2004-01":"2013-09", "A008080"].pct_change(fill_method=None)
print(f"A008080 2004-01~2013-09 새 수정주가 일간수익률: 값 {x.count()}개, |r|>50% {int((x.abs() > 0.5).sum())}개, 최대 {x.max():.3f}, 최소 {x.min():.3f}")
