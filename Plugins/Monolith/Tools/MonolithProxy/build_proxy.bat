@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if %ERRORLEVEL% neq 0 (
    echo FAILED: vcvars64.bat not found or failed
    exit /b 1
)
echo VCVARS loaded, compiling...
cd /d "%~dp0"
echo CWD: %CD%
dir monolith_proxy.cpp
cl /EHsc /std:c++17 /O2 /MT /I ThirdParty monolith_proxy.cpp winhttp.lib /Fe:monolith_proxy.exe
if %ERRORLEVEL% neq 0 (
    echo FAILED: Compilation failed
    exit /b 1
)
if not exist "..\..\Binaries" mkdir "..\..\Binaries"
copy /Y monolith_proxy.exe "..\..\Binaries\monolith_proxy.exe"
echo SUCCESS: Built monolith_proxy.exe
