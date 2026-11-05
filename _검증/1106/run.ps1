# 작업 스케줄러로 띄우는 실행기(2026-11-06 c). Claude Code·앱과 떨어져 돈다.
# run.ps1 -Name <짧은이름> -Notebook <ipynb> [-EnvVars "FOLLOW_TEST=1;X=Y"]  또는 -Script <py> [-ScriptArgs "..."]
# 노트북은 _검증\1106\실행출력\<Name>.ipynb 사본으로 저장(원본 노트북 안 바꿈). 끝나면 <Name>.끝 파일에 종료코드.
param([string]$Name, [string]$Notebook = "", [string]$Script = "", [string]$ScriptArgs = "", [string]$EnvVars = "")
$root = Split-Path (Split-Path $PSScriptRoot)
Set-Location $root
$out = Join-Path $PSScriptRoot "실행출력"
New-Item -ItemType Directory -Force $out | Out-Null
$env:PYTHONIOENCODING = "utf-8"; [Console]::OutputEncoding = [Text.Encoding]::UTF8
foreach ($kv in ($EnvVars -split ";")) { if ($kv -match "=") { $k, $v = $kv -split "=", 2; Set-Item "env:$k" $v } }
$log = Join-Path $out "$Name.log"
"시작 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 환경=$EnvVars" | Out-File $log -Encoding utf8
if ($Notebook) {
  & "C:\Users\benef\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m jupyter nbconvert --to notebook --execute $Notebook --output-dir $out --output "$Name.ipynb" --ExecutePreprocessor.kernel_name=magicformula-py311 --ExecutePreprocessor.timeout=-1 2>&1 | Out-File $log -Append -Encoding utf8
} else {
  & "C:\Users\benef\AppData\Local\Python\pythoncore-3.11-64\python.exe" $Script ($ScriptArgs -split " " | ? { $_ }) 2>&1 | Out-File $log -Append -Encoding utf8
}
$c = $LASTEXITCODE
"끝 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 종료코드 $c" | Out-File $log -Append -Encoding utf8
"$c" | Out-File (Join-Path $out "$Name.끝") -Encoding ascii
