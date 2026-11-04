"""추가 지시 F(2026-11-04) 분기(3개월) 재무 xlsx → parquet. 감독 변환기(data\\DataGuide_추가_202611\\_tools\\_to_parquet.py)의 읽기·검사 함수와
독립 검사기(_audit\\a1_verify.py)를 그대로 쓰고, 저장만 저장소 안 `_캐시/분기/`에 한다(data 폴더에 쓰지 않음, 원본 xlsx는 읽기만).
감독 변환 루프가 돌지 않아(14:2x 확인) 대신 바꾼다. 감독 루프처럼: 저장 잠금이 없고 마지막 수정 뒤 10분 지난 파일만, 이미 있으면 건너뜀.
실행: 3.11 python(python_calamine 있음) _검증/분기_변환.py (한 번에 한 파일씩 전부)"""
import json, subprocess, sys, time
from pathlib import Path

TOOLS = Path(r"D:\26-2_데이터기반투자전략\과제02\data\DataGuide_추가_202611\_tools")
SRC = Path(r"D:\26-2_데이터기반투자전략\과제02\data\DataGuide_전체_202611")
DATA = Path(r"D:\26-2_데이터기반투자전략\과제02\data\통합_전체_202611")
OUT = Path(__file__).resolve().parent.parent / "_캐시" / "분기"
sys.path.insert(0, str(TOOLS))
from _to_parquet import read_rows, to_frame  # noqa: E402

OUT.mkdir(parents=True, exist_ok=True)
for f in sorted(x for x in SRC.glob("R*_분기3M_I00P_일간_*.xlsx") if not x.name.startswith("~$")):  # 엑셀 잠금 파일(~$...) 빼기
    name = f.name.split("_I00P_")[0]
    if list(DATA.glob(f"통합_일간_*_{name}.parquet")) or list(OUT.glob(f"통합_일간_*_{name}.parquet")):
        print("건너뜀(있음)", name, flush=True)
        continue
    if (TOOLS / "_save.lock").exists() or time.time() - f.stat().st_mtime < 600:
        print("건너뜀(저장 중일 수 있음)", name, flush=True)
        continue
    t0 = time.time()
    item, df = to_frame(read_rows(f))
    out = OUT / f"통합_일간_{item}_{name}.parquet"
    tmp = out.with_name(out.stem + ".tmp.parquet")
    df.to_parquet(tmp)
    del df
    res = OUT / f"res_{name}.json"
    r = subprocess.run([sys.executable, "-B", "-X", "utf8", str(TOOLS / "_audit" / "a1_verify.py"), str(f), str(tmp), str(res)],
                       capture_output=True, text=True, encoding="utf-8")
    verdict = json.load(open(res, encoding="utf-8")).get("RESULT") if res.exists() else None
    if r.returncode != 0 or verdict != "PASS":
        print(f"FAIL {name}: 독립 검사 {verdict}, 종료코드 {r.returncode} / {r.stderr[-300:]}", flush=True)
        continue
    tmp.rename(out)
    print(f"{out.name}: 독립 검사 PASS, {time.time() - t0:.0f}초", flush=True)
