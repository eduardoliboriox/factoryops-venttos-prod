@echo off
setlocal

echo Ativando ambiente...

:: (opcional) ativar venv se existir
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set HOJE=%%i
for /f %%i in ('powershell -NoProfile -Command "(Get-Date).AddDays(1).ToString('yyyy-MM-dd')"') do set AMANHA=%%i

set SAIDA=%~dp0coletas\dados_%HOJE%_%AMANHA%.json

echo ============================================================
echo  Venttos - Coletor de Producao
echo  Data: %HOJE% ate %AMANHA%
echo  Saida: %SAIDA%
echo ============================================================

cd /d "%~dp0"

python coletor.py --de %HOJE% --ate %AMANHA% --json "%SAIDA%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Coleta concluida. Arquivo salvo em: %SAIDA%
) else (
    echo.
    echo [ERRO] Coleta falhou. Codigo de saida: %ERRORLEVEL%
)

echo.
pause
endlocal