# B34_감시.sh 다음 판(09:04 B2 1차 멈춤 뒤): B2_full2 가 종료코드 0으로 끝난 뒤에만 B3·B4 묶음 1~6, 합치기를 차례로. 0이 아니면 아무것도 안 돌림.
cd "D:/26-2_데이터기반투자전략/과제02/과제02_백테스트/_검증/1106"
S=../../../제출_원문대로; PY=/c/Users/benef/AppData/Local/Python/pythoncore-3.11-64/python.exe; log=../../_진행기록_20261106c.md; K=실행출력/B34_2.txt
export PYTHONIOENCODING=utf-8
until [ -f 실행출력/B2_full2.끝 ]; do sleep 60; done
코드=$(tr -d '\r\n ' < 실행출력/B2_full2.끝)
echo "- $(date +%H:%M) B2(B2_full2) 끝, 종료코드 $코드" >> $log
[ "$코드" = 0 ] || exit 1
for n in 1 2 3 4 5 6; do
  $PY 대조_B3.py $S/결과 --묶음 $n > 실행출력/B3b_$n.log 2>&1; echo "B3 $n $?" >> $K
  $PY 보고서용_숫자.py $S/결과 $S/보고서용_숫자.md --노트북 $S/과제02.ipynb --묶음 $n > 실행출력/B4b_$n.log 2>&1; echo "B4 $n $?" >> $K
done
$PY 대조_B3.py $S/결과 --합치기 > 실행출력/B3b_합.log 2>&1; echo "B3 합 $?" >> $K
$PY 보고서용_숫자.py $S/결과 $S/보고서용_숫자.md --노트북 $S/과제02.ipynb --합치기 > 실행출력/B4b_합.log 2>&1; echo "B4 합 $?" >> $K
echo "- $(date +%H:%M) B3·B4 묶음 1~6·합치기 끝: $(tr '\n' ' ' < $K)" >> $log
