$ErrorActionPreference = 'Stop'
$src = 'C:\EnvironmentPortfolio\BS_GodFile\deploy\cascadeur\csc_mcp_exec.py'
$dstDir = 'C:\Program Files\Cascadeur\resources\scripts\python\commands\externals'
$dst = Join-Path $dstDir 'csc_mcp_exec.py'
New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
Copy-Item -LiteralPath $src -Destination $dst -Force
$marker = Join-Path $env:TEMP 'csc_mcp_install_ok.txt'
Set-Content -LiteralPath $marker -Value (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -Encoding utf8