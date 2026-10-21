# Installs the Nous shim to %USERPROFILE%\.claude\nous-shim and puts it first on the USER PATH.
# Restart Unreal (and any open terminals) afterwards so they inherit the new PATH.
$dest = Join-Path $env:USERPROFILE '.claude\nous-shim'
New-Item -ItemType Directory -Force $dest | Out-Null
foreach ($f in 'claude.cmd', 'claude.ps1', 'ensure_proxy.ps1', 'nous_anthropic_proxy.py') { Copy-Item (Join-Path $PSScriptRoot $f) $dest -Force }
$user = [Environment]::GetEnvironmentVariable('Path', 'User') -split ';' | Where-Object { $_ -and $_ -ne $dest }
[Environment]::SetEnvironmentVariable('Path', (@($dest) + $user) -join ';', 'User')
Write-Host "Installed to $dest. Restart Unreal Editor, then click the Claireon Claude Code button."
