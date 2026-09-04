@echo off
setlocal
cd /d "%~dp0frontend"

if not exist "node_modules" (
  echo [PrepPilot] Frontend-Abhaengigkeiten fehlen.
  echo Fuehre im Ordner frontend zuerst npm install aus.
  pause
  exit /b 1
)

echo [PrepPilot] Frontend startet auf http://127.0.0.1:5173
call npm run dev -- --host 127.0.0.1 --port 5173 --strictPort

if errorlevel 1 (
  echo.
  echo [PrepPilot] Frontend wurde mit einem Fehler beendet.
  pause
)
