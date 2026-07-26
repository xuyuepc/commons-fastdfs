@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] 检查依赖...
python -m pip install -r requirements.txt -q
if errorlevel 1 (
  echo 请先安装 Python 3.10+，并确保命令 "python" 可用。
  pause
  exit /b 1
)

echo [2/3] 生成今日五大联赛 HTML...
python -m football_daily --open
if errorlevel 1 (
  echo 生成失败，请把上方报错发我。
  pause
  exit /b 1
)

echo [3/3] 完成。HTML 在 reports 文件夹里。
echo 路径: %cd%\reports\
pause