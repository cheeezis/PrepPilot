@echo off
setlocal
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
  echo [PrepPilot] Backend-Umgebung fehlt: backend\.venv
  echo Hinweise zur Einrichtung stehen in docs\development.md.
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [PrepPilot] Frontend-Abhaengigkeiten fehlen: frontend\node_modules
  echo Hinweise zur Einrichtung stehen in docs\development.md.
  pause
  exit /b 1
)

where docker.exe >nul 2>&1
if errorlevel 1 (
  echo [PrepPilot] Docker wurde nicht gefunden. Bitte Docker Desktop installieren und starten.
  pause
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo [PrepPilot] Docker Desktop ist nicht erreichbar. Bitte Docker Desktop starten.
  pause
  exit /b 1
)

call "%~dp0stop-preppilot.bat"

echo [PrepPilot] PostgreSQL wird gestartet ...
docker compose up -d postgres
if errorlevel 1 (
  echo [PrepPilot] PostgreSQL konnte nicht gestartet werden.
  pause
  exit /b 1
)

for /l %%A in (1,1,30) do (
  docker compose exec -T postgres pg_isready -U preppilot -d preppilot >nul 2>&1 && goto database_ready
  timeout /t 1 /nobreak >nul
)

echo [PrepPilot] PostgreSQL war nach 30 Sekunden noch nicht bereit.
pause
exit /b 1

:database_ready
echo [PrepPilot] Datenbankschema wird aktualisiert ...
pushd backend
".venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
  popd
  echo [PrepPilot] Datenbankmigration ist fehlgeschlagen.
  pause
  exit /b 1
)
popd

echo [PrepPilot] Backend und Frontend werden in eigenen Fenstern gestartet.
start "PrepPilot Backend" cmd /k call "%~dp0start-backend.bat"
start "PrepPilot Frontend" cmd /k call "%~dp0start-frontend.bat"

echo [PrepPilot] Warte auf das Frontend und oeffne danach den Browser ...
powershell.exe -NoProfile -Command "$url='http://127.0.0.1:5173/'; for ($attempt=1; $attempt -le 30; $attempt++) { try { $response=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1; if ($response.StatusCode -eq 200) { Start-Process $url; exit 0 } } catch {}; Start-Sleep -Seconds 1 }; Write-Host '[PrepPilot] Frontend war nach 30 Sekunden noch nicht erreichbar.'; exit 1"

if errorlevel 1 (
  echo [PrepPilot] Bitte pruefe die beiden Serverfenster auf Fehlermeldungen.
  pause
)
