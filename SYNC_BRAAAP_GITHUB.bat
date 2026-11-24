@echo off
chcp 65001 >nul
cd /d "%~dp0"
title SYNC BRAAAP - GitHub
:MENU
cls
echo ===================================================
echo         SINCRONIZZAZIONE BRAAAP (GITHUB)
echo ===================================================
echo.
echo   [1] INVIA modifiche di questo PC su GitHub
echo   [2] SCARICA aggiornamenti da GitHub su questo PC
echo   [3] SINCRONIZZA tutto (Scarica + Invia)
echo   [0] Esci
echo.
set /p SCELTA="Scegli un numero (1, 2, 3 o 0): "
if "%SCELTA%"=="1" goto INVIA
if "%SCELTA%"=="2" goto SCARICA
if "%SCELTA%"=="3" goto TUTTO
if "%SCELTA%"=="0" exit
goto MENU

:INVIA
echo.
echo --- Salvataggio e invio su GitHub ---
git add .
git commit -m "Sync Braaap %date% %time:~0,5%"
git push
echo.
pause
goto MENU

:SCARICA
echo.
echo --- Scaricamento aggiornamenti da GitHub ---
git pull --rebase
echo.
pause
goto MENU

:TUTTO
echo.
echo --- Sincronizzazione completa ---
git add .
git commit -m "Sync Braaap %date% %time:~0,5%"
git pull --rebase
git push
echo.
pause
goto MENU
