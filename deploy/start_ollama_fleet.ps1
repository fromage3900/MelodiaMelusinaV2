# Launch the full local-model content fleet (detached). Stop everything: create deploy\STOP_ALL
# Individual stops: OLLAMA_SLICE_STOP / OLLAMA_WARDROBE_STOP / OLLAMA_DIALOGUE_STOP / OLLAMA_GUMROAD_STOP / OLLAMA_VALIDATOR_STOP
$root = Split-Path $PSScriptRoot -Parent
Remove-Item "$PSScriptRoot\STOP_ALL" -ErrorAction SilentlyContinue
$daemons = @(
    "ollama_slice_content_daemon.py",
    "ollama_wardrobe_catalog_daemon.py",
    "ollama_dialogue_daemon.py",
    "ollama_gumroad_copy_daemon.py",
    "ollama_data_validator_daemon.py"
)
foreach ($d in $daemons) {
    Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "`"$PSScriptRoot\$d`"" -WorkingDirectory $root
    Write-Output "launched $d"
}
Write-Output "Fleet up. Halt all with: New-Item $PSScriptRoot\STOP_ALL"
