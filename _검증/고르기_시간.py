"""추가 지시 J: 고르기 고침(종목 < 분위 수 → 빈 묶음) 전·후 같은 입력의 값과 시간. 옛 = 커밋 ffaa4b3 전 판(0종목만 빈 묶음, 나머지 qcut).
입력: 종목 0·3·500·1,500개 점수(난수, 고정 seed), 분위 5, 각 2,000번. 공통/에서 PYTHONPATH=. 로 실행 → _검증/고르기_시간_결과.txt"""
import time
import numpy as np
import pandas as pd
import 포트폴리오 as 포


def 옛(sc, how):
    kind, n = how
    if sc.empty:
        return {f"Q{i}": sc.index for i in range(1, n + 1)}
    q = pd.qcut(sc.rank(method="first", ascending=False), n, labels=[f"Q{i}" for i in range(1, n + 1)])
    return {g: sc.index[q == g] for g in q.cat.categories}


rng = np.random.default_rng(0)
for m in (0, 3, 500, 1500):
    sc = pd.Series(rng.normal(size=m), [f"A{i}" for i in range(m)])
    t = {}
    for 이름, f in (("옛", 옛), ("새", 포.고르기)):
        t0 = time.time()
        for _ in range(2000):
            try:
                r = f(sc, ("분위", 5))
            except ValueError:
                r = "오류"
        t[이름] = (time.time() - t0, r)
    a, b = t["옛"][1], t["새"][1]
    같음 = a != "오류" and all(list(a[k]) == list(b[k]) for k in b)
    print(f"종목 {m}: 옛 {t['옛'][0]:.3f}초, 새 {t['새'][0]:.3f}초 / 묶음 같음 {같음}" + ("" if 같음 else f" (옛 {'오류' if a == '오류' else {k: len(v) for k, v in a.items()}}, 새 { {k: len(v) for k, v in b.items()} })"))
