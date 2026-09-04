@echo off
setlocal

echo [PrepPilot] Beende Prozesse, die auf Port 8000 oder 5173 lauschen ...
powershell.exe -NoProfile -Command "$ports=@(8000,5173); $found=$false; for ($round=1; $round -le 5; $round++) { $listeners=Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in $ports }; foreach ($listener in $listeners) { $found=$true; $targetPid=$listener.OwningProcess; $current=Get-CimInstance Win32_Process -Filter ('ProcessId = {0}' -f $targetPid) -ErrorAction SilentlyContinue; if (-not $current) { $orphans=Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $targetPid -and $_.CommandLine -match 'multiprocessing\.spawn' }; foreach ($orphan in $orphans) { Write-Host ('[PrepPilot] Stoppe verwaisten Worker PID {0} auf Port {1}' -f $orphan.ProcessId,$listener.LocalPort); taskkill.exe /PID $orphan.ProcessId /T /F 2>$null | Out-Null } }; while ($current) { $parent=Get-CimInstance Win32_Process -Filter ('ProcessId = {0}' -f $current.ParentProcessId) -ErrorAction SilentlyContinue; if ($parent -and $parent.CommandLine -match '(fastapi\.exe.+dev|uvicorn.+--reload)') { $targetPid=$parent.ProcessId; $current=$parent } else { break } }; if (Get-Process -Id $targetPid -ErrorAction SilentlyContinue) { Write-Host ('[PrepPilot] Stoppe Prozessbaum PID {0} auf Port {1}' -f $targetPid,$listener.LocalPort); taskkill.exe /PID $targetPid /T /F 2>$null | Out-Null } }; Start-Sleep -Milliseconds 500 }; if (-not $found) { Write-Host '[PrepPilot] Keine laufenden Server auf Port 8000 oder 5173 gefunden.' }"

where docker.exe >nul 2>&1
if not errorlevel 1 (
  docker compose stop postgres >nul 2>&1
  if not errorlevel 1 echo [PrepPilot] PostgreSQL wurde beendet.
)

echo [PrepPilot] Fertig.
