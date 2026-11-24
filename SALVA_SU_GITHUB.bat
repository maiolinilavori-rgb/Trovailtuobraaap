@echo off
cd /d "%~dp0"
git add .
git commit -m "Aggiornamento Braaap %date% %time%"
git push
pause
