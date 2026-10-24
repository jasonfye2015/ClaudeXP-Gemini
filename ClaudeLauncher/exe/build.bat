@echo off
rem Builds "Claude Timeline.exe" in the Claude Timeline folder: the icon from the SYSTEC emblem, then the C# starter,
rem with the C# compiler that comes with Windows (.NET Framework 4). Nothing to download.
cd /d "%~dp0"
"%~dp0..\..\Python\python.exe" make_icon.py || goto failed
"%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:winexe /optimize+ /win32icon:systec.ico /reference:System.Windows.Forms.dll /out:"%~dp0..\..\Claude Timeline.exe" ClaudeTimeline.cs || goto failed
echo Built Claude Timeline.exe
exit /b 0
:failed
echo Build failed.
exit /b 1
