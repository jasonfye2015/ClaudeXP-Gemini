@echo off
rem Builds dist\Claude Entertainment System.scr. The first run makes .venv-build (its own Python with PySide6 and
rem PyInstaller, kept apart from ClaudeXP's) - that needs the internet once.
cd /d "%~dp0"
if not exist ".venv-build\Scripts\python.exe" (
    py -3.13 -m venv .venv-build || python -m venv .venv-build || goto :fail
    ".venv-build\Scripts\python.exe" -m pip install --upgrade pip
    ".venv-build\Scripts\python.exe" -m pip install PySide6-Essentials pyinstaller || goto :fail
)
".venv-build\Scripts\python.exe" build_scr.py || goto :fail
echo.
echo Built: dist\Claude Entertainment System.scr  (right-click it and choose Install)
exit /b 0
:fail
echo Build failed.
exit /b 1
