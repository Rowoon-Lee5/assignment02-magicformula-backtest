# 원본 파일(data\ 아래 전부 + 바탕 화면 1990~1999 파일)의 크기·수정시각을 기록하고, 두 번째 실행부터는 처음 기록과 비교한다.
import sys, glob, os
import numpy as np, pandas as pd
from pathlib import Path

H = Path(__file__).parent
FILES = [p for p in glob.glob(r"D:\26-2_데이터기반투자전략\과제02\data\**\*", recursive=True) if os.path.isfile(p)] \
      + glob.glob(r"C:\Users\benef\OneDrive\바탕 화면\*1990~1999*")
now = pd.DataFrame([(p, os.path.getsize(p), os.path.getmtime(p)) for p in FILES], columns=["파일", "크기", "수정시각"]).set_index("파일")
first = H / "원본_처음.csv"
if not first.exists():
    now.to_csv(first, encoding="utf-8-sig"); print(f"처음 기록: {len(now)}개 파일"); sys.exit()
old = pd.read_csv(first, index_col=0, encoding="utf-8-sig")
j = old.join(now, rsuffix="_지금", how="outer")
# 수정시각은 csv 왕복 오차(1e-7초)가 있어 1밀리초까지 같으면 같다고 본다.
bad = j[(j["크기"] != j["크기_지금"]) | ~np.isclose(j["수정시각"], j["수정시각_지금"], rtol=0, atol=1e-3)]
kind = np.where(bad["크기"].isna(), "새 파일", np.where(bad["크기_지금"].isna(), "없어짐", "바뀜"))
when = pd.to_datetime(bad["수정시각_지금"].fillna(bad["수정시각"]), unit="s", utc=True).dt.tz_convert("Asia/Seoul")
lines = [f"{k}\t{t:%Y-%m-%d %H:%M}\t{p}" for k, t, p in zip(kind, when, bad.index)]
msg = f"{pd.Timestamp.now():%Y-%m-%d %H:%M:%S} 처음 {len(old)}개 / 지금 {len(now)}개 / 다른 파일 {len(bad)}개(바뀜 {(kind == '바뀜').sum()}, 새 파일 {(kind == '새 파일').sum()}, 없어짐 {(kind == '없어짐').sum()})"
print(msg, *lines, sep="\n")
with open(H / "원본확인_로그.txt", "a", encoding="utf-8") as f:
    print(msg, *lines, sep="\n", file=f)
