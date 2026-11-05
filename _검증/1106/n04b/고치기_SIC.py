# V04b MEDIUM: Novy-Marx p.8 'excludes financial firms (those with one-digit SIC codes of six)' = SIC Division H 60~67(금융·보험·부동산, 6770 blank checks = 스팩, 6798 리츠, 67 투자회사)
# → 04 따라하기는 금융업 넓은 이름 규칙(리츠·스팩·지주$ 포함) + 투자기구(리츠·선박·부동산투자) 거르기가 원문대로(회원 원칙 '원문에 있으면 원문대로'). 판정 csv의 Panel A·B 줄은 원문 문장 주장 없음 표시.
import json
꼴 = lambda 원래, s: s.splitlines(keepends=True) if isinstance(원래, list) else s  # 원래 꼴(줄 목록/문자열) 지킴
옛 = '("금융업", {"이름": "원문"})'
새 = '"금융업", "투자기구"'
주석 = '  # 비금융 = 원문 p.8 SIC 첫 자리 6(금융·보험·부동산 60~67: 리츠 6798·스팩 6770·투자회사 67 포함, OSHA SIC 편람) → 금융업 넓은 이름 규칙 + 투자기구'
for f, cs in [("따라하기/04_신마법공식.ipynb", [6]), ("연구/따라하기에서_옮김_04.ipynb", [18, 20])]:
    nb = json.load(open(f, encoding="utf-8"))
    for i in cs:
        s = "".join(nb["cells"][i]["source"])
        assert s.count(옛) == 1, (f, i)
        s = s.replace(옛, 새)
        줄 = s.split("\n")
        k = next(j for j, l in enumerate(줄) if 새 in l)
        줄[k] += 주석
        nb["cells"][i]["source"] = "\n".join(줄)
    if f.startswith("따라하기"):
        c = nb["cells"][10]
        s = "".join(c["source"])
        a = '판정["판정(방향)"] = np.where(판정.pop("같은 방향"), "같음", "다름")\n'
        assert a in s
        s = s.replace(a, a + '판정["원문 문장 주장"] = np.where(판정.index.str.startswith("Panel "), "없음(표 7 부호만 나란히, 참고)", "있음")  # V04b: Panel A·B는 p.21 \'for comparison\'뿐\n')
        c["source"] = 꼴(c["source"], s)
    json.dump(nb, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(f, "a", encoding="utf-8").write("\n")
print("ok")
