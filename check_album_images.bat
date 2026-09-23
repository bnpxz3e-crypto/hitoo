@echo off
cd /d "%~dp0"
echo Checking card images...
for /L %%i in (1,1,17) do (
  if not exist "img.joypop.gg\uploads\images\card\18\goods%%i.webp" echo MISSING goods%%i.webp
)
echo Done. If no MISSING lines appeared, all 17 images exist.
pause
