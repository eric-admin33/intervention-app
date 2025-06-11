taskkill /F /IM python.exe >nul 2>nul
@echo off
cd /d "%~dp0backend"
echo.
echo --- (Re)démarrage du serveur Flask ---
REM Facultatif : tuer les anciens python (si besoin) :
REM taskkill /F /IM python.exe >nul 2>nul

python app.py

echo.
echo Appuyez sur une touche pour fermer...
pause >nul
