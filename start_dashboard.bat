@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "MODEL_QUANT=q6_k"

echo ============================================
echo  FishS2 - Avvio backend + dashboard
echo ============================================

echo.
echo [1/2] Avvio backend (--model-quant %MODEL_QUANT%)...
start "FishS2 Backend" cmd /k call "%PROJECT_DIR%run.bat" --model-quant %MODEL_QUANT%

echo Attendo che il backend risponda su http://localhost:8020 ...
set "ATTEMPTS=0"
:wait_backend
set /a ATTEMPTS+=1
if %ATTEMPTS% GEQ 90 (
    echo.
    echo ATTENZIONE: il backend non ha risposto entro il timeout.
    echo Controlla la finestra "FishS2 Backend" per eventuali errori.
    goto start_dashboard
)
timeout /t 2 >nul
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'http://localhost:8020/health' -UseBasicParsing -TimeoutSec 8 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto wait_backend

echo Backend pronto.

:start_dashboard
echo.
echo [2/2] Avvio dashboard Angular...
start "FishS2 Dashboard" cmd /k call "%PROJECT_DIR%dashboard\_serve.bat"

echo.
echo Fatto. Due finestre sono state aperte: backend e dashboard.
echo Chiudile per fermare i rispettivi processi.
endlocal
