@echo off
cd /d "%~dp0"
title JOYPOP Local V5.12
echo Starting JOYPOP Local V5.12...
where python >nul 2>nul
if %errorlevel%==0 (
  python server_v5_12.py
  goto :end
)
where py >nul 2>nul
if %errorlevel%==0 (
  py server_v5_12.py
  goto :end
)
echo.
echo ERROR: Python was not found.
echo Install Python or add python.exe to PATH.
:end
pause
