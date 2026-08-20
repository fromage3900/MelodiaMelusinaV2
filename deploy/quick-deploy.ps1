param(
    [string]$Message = "Sync site updates"
)

Write-Host ""
Write-Host "  Melodia -- Quick Deploy"
Write-Host "  =========================="
& "$PSScriptRoot\sync_site_to_github.ps1" -Message $Message