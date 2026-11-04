"""2026-11-04: 종목거르기.그날을 reindex(ffill) → 위치 찾기로 바꿈(02 실행 중 py-spy로 느린 곳 확인). 값이 같은지와 시간.
공통/에서 PYTHONPATH=. 로 실행 → _검증/그날_속도_결과.txt"""
import time, pandas as pd, 데이터읽기 as 읽기, 종목거르기 as 거
옛 = lambda item, t, c: 읽기.일간(item).reindex([t], method="ffill").iloc[0].reindex(c)  # 고치기 전 코드 그대로
c = pd.Index(읽기.일간(읽기.시장구분).columns.tolist() + ["A없음000"])
ts = [pd.Timestamp(x) for x in ["1987-12-31", "1988-01-04", "1995-06-15", "2004-04-01", "2010-01-01", "2018-05-31", "2026-09-30", "2027-01-01"]]
n = 0
for item in [읽기.시장구분, 읽기.업종, 읽기.WICS, 읽기.관리여부, 읽기.정지여부, 읽기.종가, 읽기.주식수]:
    for t in ts:
        a, b = 옛(item, t, c), 거.그날(item, t, c)
        assert a.index.equals(b.index) and ((a.astype(object) == b.astype(object)) | (a.isna() & b.isna())).all(), (item, t)
        n += 1
t0 = time.time(); [옛(읽기.업종, t, c) for t in ts]; t1 = time.time(); [거.그날(읽기.업종, t, c) for t in ts]; t2 = time.time()
print(f"같음 {n}개 조합(항목 7 × 날짜 8, 범위 밖 날짜·없는 종목 포함). 업종 8번: 옛 {t1 - t0:.2f}초, 새 {t2 - t1:.2f}초")
