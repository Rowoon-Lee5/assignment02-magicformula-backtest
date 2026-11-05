# 추가 지시 06:53: 합치기.py에 '제출본에서만 요인 직접 구성 코드 빼기' 넣기(한 번만 돌림, 전 사본 합치기_0653전.py)
from pathlib import Path

p = Path(__file__).with_name("합치기.py")
s = p.read_text(encoding="utf-8")
assert "요인직접빼기" not in s
줄 = s.split("\n")
i = next(n for n, l in enumerate(줄) if l.startswith("for ") and '("포트폴리오", "포", [])' in l)
assert 줄[i + 1].strip().startswith("s = (REPO") and 줄[i + 2].strip().startswith("code(")
함수 = '''def 요인직접빼기(s, 파일):
    """(추가 지시 06:53) 제출본에서만: 과제 공지 '요인은 직접 만들지 말 것' → 부르는 곳 0인 `원문요인`과 그것만 쓰는 보조(지표.시가총액·모멘텀11, 고르기 '상하비율')를 뺌. 저장소 공통/은 그대로."""
    def 뺌(s, 처음, 끝):
        i = s.index(처음)
        j = s.index(끝, i)
        기록.append(f"(제출본에서 뺌) 공통/{파일}.py: {처음.strip().splitlines()[0][:40]} … (요인 직접 구성, 부르는 곳 0)")
        return s[:i] + s[j:]
    if 파일 == "포트폴리오":
        s = 뺌(s, "\\n\\ndef 원문요인(", "\\n\\n\\ndef 큰수익률(")
        s = 뺌(s, '    if kind == "상하비율":', "    if len(sc) < n:")
    if 파일 == "지표":
        s = 뺌(s, "# 우동호 외(2023) p.513 요인", "# 애널리스트 추정치")
    return s

'''.split("\n")
줄 = 줄[:i] + 함수 + 줄[i:i + 2] + ["    s = 요인직접빼기(s, 파일)"] + 줄[i + 2:]
p.write_text("\n".join(줄), encoding="utf-8")
print("ok", i)
