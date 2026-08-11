@echo off
REM Build monolith_query.exe — standalone SQLite query tool
REM Run from VS Developer Command Prompt, or let it find cl.exe via vswhere

REM Compute a SHA256 of the source and inject its first 16 hex chars as
REM /DSOURCE_HASH so --version reports a hash the staleness guard can match.
REM certutil is built into Windows; its second output line is the bare hash.
REM Statements are kept un-nested so plain (non-delayed) %VAR% expansion works.
set SOURCE_HASH=dev
set SRCHASH_RAW=
for /f "skip=1 tokens=*" %%H in ('certutil -hashfile monolith_query.cpp SHA256') do if not defined SRCHASH_RAW set SRCHASH_RAW=%%H
if not defined SRCHASH_RAW goto :hashdone
REM Strip spaces certutil may insert between hex byte groups, take first 16 chars.
set SRCHASH_NOSPACE=%SRCHASH_RAW: =%
set SOURCE_HASH=%SRCHASH_NOSPACE:~0,16%
:hashdone
echo Source hash: %SOURCE_HASH%

where cl >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Building with cl.exe...
    cl /EHsc /std:c++17 /O2 /MT /I ThirdParty /I ..\MonolithProxy\ThirdParty /DSQLITE_ENABLE_FTS5 /DSOURCE_HASH=\"%SOURCE_HASH%\" monolith_query.cpp ThirdParty\sqlite3.c /Fe:monolith_query.exe
    if %ERRORLEVEL% equ 0 goto :copy
    echo Build failed.
    exit /b 1
)

echo cl.exe not found in PATH.
echo Run from a Visual Studio Developer Command Prompt, or add cl.exe to PATH.
exit /b 1

:copy
if not exist ..\..\Binaries mkdir ..\..\Binaries
copy /Y monolith_query.exe ..\..\Binaries\monolith_query.exe
echo.
echo Built: Plugins\Monolith\Binaries\monolith_query.exe
