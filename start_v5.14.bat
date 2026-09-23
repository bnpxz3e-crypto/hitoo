@echo off
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python server_v5_14.py
) else (
  py server_v5_14.py
)
pause
