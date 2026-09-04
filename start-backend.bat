@echo off
setlocal
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
  echo [PrepPilot] Backend-Umgebung fehlt: backend\.venv
  echo Bitte zuerst die Python-Abhaengigkeiten installieren.
  pause
  exit /b 1
)

echo [PrepPilot] Backend startet auf http://127.0.0.1:8000
".venv\Scripts\python.exe" -m uvicorn preppilot_api.main:app --host 127.0.0.1 --port 8000

if errorlevel 1 (
  echo.
  echo [PrepPilot] Backend wurde mit einem Fehler beendet.
  pause
)
