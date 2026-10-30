# Runs the RenderZ card collector (called by the "FMM RenderZ Collector" scheduled task).
# Log: E:\Claude\FMM\output\collect.log
Set-Location "E:\Claude\FMM"
$log = "E:\Claude\FMM\output\collect.log"
New-Item -ItemType Directory -Force "E:\Claude\FMM\output" | Out-Null
"=== $(Get-Date -Format 'yyyy-MM-dd HH:mm') ===" | Add-Content $log
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
& $py -m fmm.collect *>&1 | Out-File -Append -Encoding utf8 $log
# keep the log small
if ((Get-Item $log).Length -gt 512KB) { Get-Content $log -Tail 300 | Set-Content $log }
