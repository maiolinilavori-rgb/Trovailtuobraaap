@echo off
title BRAAAP - Portatile (Python 3.14 Ufficiale)
set "BRAAAP_DATA_DIR=%~dp0dati"
set "PYTHONPATH=%~dp0_internal"
py -3.14 "%~dp0_internal\app.py"
pause
