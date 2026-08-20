# Enables Epic Live Link plugins in BS_GodFile.uproject for Rokoko Studio Live.
# Does NOT install the Rokoko Smartsuit plugin — grab that from Fab / GitHub for UE 5.8.

$ErrorActionPreference = 'Stop'
$UProject = 'C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject'
$json = Get-Content $UProject -Raw | ConvertFrom-Json

$needed = @('LiveLink', 'LiveLinkHub', 'LiveLinkControlRig')
$existing = @($json.Plugins | ForEach-Object { $_.Name })
$added = @()
foreach ($name in $needed) {
  if ($existing -contains $name) {
    $plugin = $json.Plugins | Where-Object { $_.Name -eq $name } | Select-Object -First 1
    if (-not $plugin.Enabled) {
      $plugin.Enabled = $true
      $added += "$name (re-enabled)"
    }
    continue
  }
  $json.Plugins += [pscustomobject]@{ Name = $name; Enabled = $true }
  $added += $name
}

($json | ConvertTo-Json -Depth 20) | Set-Content -Path $UProject -Encoding utf8
Write-Host "UProject updated."
if ($added.Count) {
  Write-Host "Plugins touched: $($added -join ', ')"
} else {
  Write-Host "Live Link plugins already present."
}
Write-Host ""
Write-Host "Next (manual):"
Write-Host "  1. Install Rokoko Studio Live for UE 5.8 (Fab or github.com/Rokoko/rokoko-studio-live-unreal-engine)."
Write-Host "  2. Copy Smartsuit plugin into Plugins\ (or enable from Fab)."
Write-Host "  3. Restart editor — Window > Virtual Production > Live Link."
Write-Host "  4. Read Docs\ROKOKO_MELUSINA_MOCAP.md"
