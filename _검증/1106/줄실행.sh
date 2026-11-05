# 노트북을 하나씩 차례로 제자리 실행(작업 스케줄러). 띄우기 전 빈 메모리 8GB 이상 기다림.
# bash 줄실행.sh 이름=노트북 ...  (ENVV=FOLLOW_TEST=1 이면 짧은 시험·사본 저장, 없으면 전체 기간 제자리)
cd "D:/26-2_데이터기반투자전략/과제02/과제02_백테스트"
log=_진행기록_20261106c.md
for pair in "$@"; do
  n=${pair%%=*}; nb=${pair#*=}
  until [ "$(powershell -NoProfile -c "[int](Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue")" -ge 8000 ]; do sleep 60; done
  if [ -n "$ENVV" ]; then powershell.exe -NoProfile -ExecutionPolicy Bypass -File _검증/1106/launch.ps1 -Name "$n" -Notebook "$nb" -EnvVars "$ENVV"; else powershell.exe -NoProfile -ExecutionPolicy Bypass -File _검증/1106/launch.ps1 -Name "$n" -Notebook "$nb" -InPlace; fi
  echo "- $(date +%H:%M) $n 시작(${ENVV:-전체 기간, 제자리}): $nb" >> $log
  sleep 20
  until [ -f "_검증/1106/실행출력/$n.끝" ]; do sleep 30; done
  c=$(tr -d '\r\n ' < "_검증/1106/실행출력/$n.끝")
  echo "- $(date +%H:%M) $n 끝 종료코드 $c" >> $log
  echo "$n $c"
done
