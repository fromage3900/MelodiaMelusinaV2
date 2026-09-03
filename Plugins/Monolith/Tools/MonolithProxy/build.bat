@echo off
REM Try direct cl.exe first (run from VS Developer Command Prompt)
where cl >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Building with cl.exe...
    cl /EHsc /std:c++17 /O2 /MT /I ThirdParty monolith_proxy.cpp winhttp.lib /Fe:monolith_proxy.exe
    if %ERRORLEVEL% equ 0 goto :copy
)
echo cl.exe not found, trying CMake...
if not exist build mkdir build
cd build
cmake .. -A x64
cmake --build . --config Release
cd ..
copy /Y build\Release\monolith_proxy.exe monolith_proxy.exe

:copy
if not exist ..\..\Binaries mkdir ..\..\Binaries
copy /Y monolith_proxy.exe ..\..\Binaries\monolith_proxy.exe
echo Built: Plugins\Monolith\Binaries\monolith_proxy.exe
