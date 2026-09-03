@echo off
:: Monolith MCP Proxy launcher
:: Finds Python automatically and runs the proxy.
:: Usage in .mcp.json:
::   {"mcpServers": {"monolith": {"command": "Plugins/Monolith/Scripts/monolith_proxy.bat"}}}

setlocal

:: Try system Python first
where python >nul 2>&1
if %errorlevel% equ 0 (
    python "%~dp0monolith_proxy.py" %*
    exit /b %errorlevel%
)

:: Try python3 (common on some setups)
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    python3 "%~dp0monolith_proxy.py" %*
    exit /b %errorlevel%
)

:: Try py launcher (Windows Python launcher)
where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 "%~dp0monolith_proxy.py" %*
    exit /b %errorlevel%
)

echo [monolith-proxy] ERROR: Python 3 not found. Install Python 3.8+ from https://python.org 1>&2
exit /b 1
