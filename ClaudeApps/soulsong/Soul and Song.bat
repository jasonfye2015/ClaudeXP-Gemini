@echo off
rem Soul and Song on its own (outside the Timeline's computers), with the Timeline's portable Python.
cd /d "%~dp0.."
start "" "%~dp0..\..\Python\pythonw.exe" -m soulsong
