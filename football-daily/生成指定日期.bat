@echo off
chcp 65001 >nul
cd /d "%~dp0"

set /p DAY=请输入日期 YYYY-MM-DD（例如 2025-12-14）: 
if "%DAY%"=="" (
  echo 未输入日期。
  pause
  exit /b 1
)

python -m pip install -r requirements.txt -q
python -m football_daily --date %DAY% --open
echo.
echo HTML 在: %cd%\reports\daily_big5_%DAY%.html
pause