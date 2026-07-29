@echo off
REM Atlas Chat Startup launcher (more reliable than .lnk -> powershell args)
set SCRIPT=%~dp0atlas-chat-startup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%SCRIPT%" -OpenUrl "http://127.0.0.1:8765/"
