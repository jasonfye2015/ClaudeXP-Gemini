@echo off
setlocal
cd /d "%~dp0.."
py -3.13 -m pip install -r win7_2011\requirements.txt
if errorlevel 1 (
  echo PySide6 installation failed.
  pause
  exit /b 1
)
echo Setup complete. Run win7_2011\run_windows.bat to start the simulator.
pause
