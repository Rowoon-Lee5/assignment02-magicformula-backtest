# run.ps1을 작업 스케줄러 작업으로 바로 띄운다(앱·Claude Code가 죽어도 계속 돎).
# launch.ps1 -Name t01 -Notebook 따라하기\01_우동호2023.ipynb -EnvVars "FOLLOW_TEST=1"
# 끝났는지: _검증\1106\실행출력\<Name>.끝 이 생기면 끝(안의 숫자 = 종료코드). 로그 = <Name>.log
param([string]$Name, [string]$Notebook = "", [string]$Script = "", [string]$ScriptArgs = "", [string]$EnvVars = "")
$done = Join-Path $PSScriptRoot "실행출력\$Name.끝"
if (Test-Path $done) { Remove-Item $done }
$arg = "-NoProfile -ExecutionPolicy Bypass -File `"$(Join-Path $PSScriptRoot 'run.ps1')`" -Name $Name"
if ($Notebook) { $arg += " -Notebook `"$Notebook`"" }
if ($Script) { $arg += " -Script `"$Script`"" }
if ($ScriptArgs) { $arg += " -ScriptArgs `"$ScriptArgs`"" }
if ($EnvVars) { $arg += " -EnvVars `"$EnvVars`"" }
$task = "kwaje02_$Name"
$a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg -WorkingDirectory (Split-Path (Split-Path $PSScriptRoot))
Register-ScheduledTask -TaskName $task -Action $a -Force | Out-Null
Start-ScheduledTask -TaskName $task
"launched $task"
