"""N04 마지막 단계(조정자가 M04 끝났다고 알린 뒤에만 실행): 04 따라하기에서 신마법 1.0·2.0·우동호IMF 칸과 감사표 2번 칸을 빼고 Novy-Marx 결합 전략만 남김.
옮긴 곳 = 연구/따라하기에서_옮김_04.ipynb(M04). 고치기_04.py를 먼저 돌린 판에만 씀."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
F = Path(__file__).resolve().parents[3] / "따라하기" / "04_신마법공식.ipynb"
nb = json.loads(F.read_text(encoding="utf-8"))
칸 = {c["id"]: c for c in nb["cells"]}
assert "4b7c0e21" in 칸, "고치기_04.py를 먼저 돌려야 함"


def 글(i):
    return "".join(칸[i]["source"])


def 넣기(i, s):
    칸[i]["source"] = s.splitlines(keepends=True)
    if 칸[i]["cell_type"] == "code":
        칸[i]["outputs"], 칸[i]["execution_count"] = [], None


def 바꾸기(i, a, b):
    s = 글(i)
    assert s.count(a) == 1, (i, a[:60])
    넣기(i, s.replace(a, b))


# 빼는 칸(옮긴 곳 M04): 신마법 설정·실행·그림·기록(3~6절), 11절 진단·부호 규칙, 10절 신마법 저장, 12절 K1-K5
뺄칸 = ["23e1fc95", "f144993e", "d2872f2f", "645203cb", "215bf784", "5ab3378b", "e8563b2b", "a429294e",
       "70a16c69", "e9b3c54e", "f7200be1", "3f22543a", "f38a8bce", "cc43a23b", "16dc1391"]

# 0절: Novy-Marx 결합 전략만. 원문 문장·설정은 3절 머리(964f5a0e)에서 가져옴
머리 = 글("964f5a0e").split("\n", 1)[1]
넣기("91e5a12d", """# 04 Novy-Marx(2013) 결합 전략 (GP/A + B/M)

## 0. 원문 정리
원문: Novy-Marx, R., "The Other Side of Value: Good Growth and the Gross Profitability Premium", NBER Working Paper 15940(2010년 4월판, 파일 `참고논문\\2_수익성_NovyMarx_2013_TheOtherSideOfValue_NBERw15940.pdf`, 파일 이름은 2013이지만 표지는 April 2010. 학술지판 2013 JFE의 표 번호·숫자는 확인 안 함). 쪽은 논문에 찍힌 쪽. 원문 확인 기록 `_검증/1106/원문사양_04.md`.

> 회원 결정(2026-11-06): 04 따라하기 = Novy-Marx(2013) 결합 전략(원문 있음)만. 강환국 신마법공식 1.0·2.0은 책 원문을 확인 못 해 확장연구 `연구/따라하기에서_옮김_04.ipynb`로 옮김 — Novy-Marx 결합 전략을 국내 실무에서 바꾼 판, 책 원문 미확인, 2차 자료 intelliquant 573·578로 구현. 같은 노트북 설정으로 돌리던 우동호 IMF 나란히 보기, 시가총액가중 판, 연환산 등 원문에 없는 성과 칸, 이상값 칸, 로그 축 그림, 기록 표, 예전 판 → 원문 규칙 단계별 진단(부호 판정 규칙), 2차 자료 확인판 K1-K5도 같은 곳으로 옮김.
> 한국 근거(참고문헌 후보): 윤보현·유원석(Yoon·Liu, 2015), 유통과학연구 13(9), 37-45, GP/A × B/M 5×5(이 노트북에서 돌리지 않음).

""" + 머리)
넣기("964f5a0e", "## 3. 설정과 실행\n원문 정의대로(0절). 원문에 없어 기본 방법으로 정한 칸은 6절 표.\n")

# 2절 기간: Novy-Marx만
바꾸기("72e15d0a", '기간 = ("2004-04", "2022-03")  # 01(우동호 p.512)과 같은 기간, 마지막 구간은 2022-03 마지막 거래일에서 끊음\n', "")
바꾸기("72e15d0a", '    기간, 기간NM = ("2004-04", "2006-03"), ("2004-06", "2006-06")', '    기간NM = ("2004-06", "2006-06")')
바꾸기("72e15d0a", '"/ 기간:", 기간, "/ Novy-Marx 기간:", 기간NM', '"/ 기간:", 기간NM')
바꾸기("72e15d0a", "# 7절 Novy-Marx: 6월 말 시작", "# Novy-Marx: 6월 말 시작")

# 3절 실행: 동일가중만, 원문에 없는 성과표·기록 표시 뺌
바꾸기("1162853b", '"비중": ["동일", "시총"]', '"비중": ["동일"]')
바꾸기("1162853b", 'N["동일_H-L"], N["시총_H-L"] = N["동일_Q1"] - N["동일_Q3"], N["시총_Q1"] - N["시총_Q3"]', 'N["동일_H-L"] = N["동일_Q1"] - N["동일_Q3"]')
바꾸기("1162853b", '표N = 평가.성과표(N, Fn, ["동일_H-L", "시총_H-L"])\ndisplay(표N)\ndisplay(o["기록"].T)\n', '표N = 평가.성과표(N, Fn, ["동일_H-L"])  # 대조표(4절)가 쓰는 칸: 초과평균·FF3 α와 t(OLS), 샤프\n')

# 4·5·6절 머리
i = next(j for j, c in enumerate(nb["cells"]) if c["id"] == "4b7c0e21")
if "4b7c0e20" not in 칸:
    nb["cells"].insert(i, {"cell_type": "markdown", "id": "4b7c0e20", "metadata": {},
                           "source": ["## 4. 원문 대조: 표 7 Panel C(p.22)와 p.21·23 문장 숫자\n",
                                      "원문 = 미국 1963-07~2009-12, 우리 = 한국 2절 기간. 시장·기간·요인이 달라 크기를 그대로 견줄 수 없다(5절). 판정 규칙은 원문에 없어 이 노트북에 두지 않음.\n"]})
바꾸기("914fbdd5", "## 8. 차이 이유 후보", "## 5. 차이 이유 후보")
s = 글("914fbdd5")
넣기("914fbdd5", "\n".join(l for l in s.split("\n") if not l.startswith("- **신마법공식**")).replace("(11절)", "(단계별 진단은 `연구/따라하기에서_옮김_04.ipynb`로 옮김)"))
바꾸기("914fbdd5", "- **벤치마크**: 신마법공식은 수정주가(배당 미포함)라 코스피 가격지수와 정의가 맞다. Novy-Marx 판도", "- **벤치마크**: Novy-Marx 판은")
바꾸기("7a9f22d6", "## 9. 원문과 다르게 한 것", "## 6. 원문과 다르게 한 것")
s = 글("7a9f22d6")
넣기("7a9f22d6", "\n".join(l for l in s.split("\n") if not (l.startswith("| 책 원문(강환국") or l.startswith("| PBR 순위"))))

nb["cells"] = [c for c in nb["cells"] if c["id"] not in 뺄칸]
F.write_text(json.dumps(nb, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print("남은 칸", [c["id"] for c in nb["cells"]])
