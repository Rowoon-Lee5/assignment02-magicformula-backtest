# B2 진행을 보며 B3 대조·B4 숫자를 묶음별로 동시에(지시 03:53). 묶음 1~5 = 7.5.4 끝(옮김 파일까지 다 생긴 뒤), 묶음 6 = B2 끝.
cd "D:/26-2_데이터기반투자전략/과제02/과제02_백테스트/_검증/1106"
S=../../../제출_원문대로; PY=/c/Users/benef/AppData/Local/Python/pythoncore-3.11-64/python.exe; log=../../_진행기록_20261106c.md
export PYTHONIOENCODING=utf-8
둘() { $PY 대조_B3.py $S/결과 --묶음 $1 > 실행출력/B3_$1.log 2>&1; echo "B3 $1 $?" >> 실행출력/B34.txt
       $PY 보고서용_숫자.py $S/결과 $S/보고서용_숫자.md --노트북 $S/과제02.ipynb --묶음 $1 > 실행출력/B4_$1.log 2>&1; echo "B4 $1 $?" >> 실행출력/B34.txt; }
until [ -n "$(find $S/결과 -name '옮김04_12절_K1-K5.csv' 2>/dev/null)" ] || [ -f 실행출력/B2_full.끝 ]; do sleep 60; done
echo "- $(date +%H:%M) B2 7.5절 끝 확인 → B3·B4 묶음 1~5 동시 시작" >> $log
빈() { powershell -NoProfile -c "[int](Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue"; }
for n in 1 2 3 4 5; do until [ "$(빈 | tr -d '')" -ge 4000 ]; do sleep 30; done; 둘 $n & sleep 45; done; wait  # 빈 메모리 4GB 이상일 때만 하나씩 더 띄움(B2 커널 최대 약 21GB)
until [ -f 실행출력/B2_full.끝 ]; do sleep 60; done
echo "- $(date +%H:%M) B2 끝(종료코드 $(tr -d '\r\n ' < 실행출력/B2_full.끝)) → B3·B4 묶음 6, 합치기" >> $log
둘 6
$PY 대조_B3.py $S/결과 --합치기 > 실행출력/B3_합.log 2>&1; echo "B3 합 $?" >> 실행출력/B34.txt
$PY 보고서용_숫자.py $S/결과 $S/보고서용_숫자.md --노트북 $S/과제02.ipynb --합치기 > 실행출력/B4_합.log 2>&1; echo "B4 합 $?" >> 실행출력/B34.txt
echo "- $(date +%H:%M) B3·B4 묶음 6·합치기 끝: $(tr '\n' ' ' < 실행출력/B34.txt)" >> $log
