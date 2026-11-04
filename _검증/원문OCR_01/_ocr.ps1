param($dir)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(-1) | Out-Null; $task.Result }
[void][Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
[void][Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$lang = New-Object Windows.Globalization.Language 'ko'
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
if (-not $eng) { throw "no engine" }; "max " + [Windows.Media.Ocr.OcrEngine]::MaxImageDimension
Get-ChildItem $dir -Filter *.png | % {
  $f = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($_.FullName)) ([Windows.Storage.StorageFile])
  $s = Await ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $r = Await ($eng.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
  $out = ($r.Lines | % { $_.Text }) -join "`n"
  [IO.File]::WriteAllText(($_.FullName -replace '\.png$','.txt'), $out, [Text.Encoding]::UTF8)
  "$($_.Name) $($r.Lines.Count)"
}
