@echo off
rem Shim: the Claireon editor button runs `claude --mcp-config ... --strict-mcp-config`.
rem Only that launch is routed to Nous Portal; every other `claude` call passes straight through.
setlocal
set "REAL=%USERPROFILE%\.local\bin\claude.exe"
echo %* | findstr /C:"--strict-mcp-config" >nul
if errorlevel 1 goto passthrough
if defined NOUS_PROXY_DISABLE goto passthrough
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0claude.ps1" %*
exit /b %ERRORLEVEL%

:passthrough
"%REAL%" %*
