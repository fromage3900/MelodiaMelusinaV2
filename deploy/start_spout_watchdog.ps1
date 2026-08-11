# start_spout_watchdog.ps1
# Monitors Spout stream health between TouchDesigner and Unreal Engine
# Branch: feature/touchdesigner-mcp-integration

param(
    [int]$IntervalSeconds = 5
)

$ProjectRoot = "G:\EnvironmentPortfolio"
$AuditDir = "$ProjectRoot\BS_GodFile\Saved\Audit"
$StateFile = "$AuditDir\spout_stream_state.json"

New-Item -ItemType Directory -Force -Path $AuditDir | Out-Null

Write-Host "[SPOUT] Watchdog started — checking streams every ${IntervalSeconds}s"

$streams = @(
    @{Name="TD_NikkiPreview"; Direction="TD_to_UE"; Resolution="1920x1080"; Format="RGBA8"},
    @{Name="UE_RenderTarget"; Direction="UE_to_TD"; Resolution="Variable"; Format="RGBA16F"}
)

while ($true) {
    if (Test-Path "$AuditDir\td_loop_STOP") { 
        Write-Host "[SPOUT] STOP signal received. Exiting."
        break 
    }
    
    $streamStatus = foreach ($s in $streams) {
        # In production: query Envoy MCP for Spout TOP status
        # For now: mark as active if TD process is presumed running
        @{
            name = $s.Name
            direction = $s.Direction
            resolution = $s.Resolution
            format = $s.Format
            status = "active"  # TODO: actual MCP query
            fps = 60           # TODO: actual measurement
            dropped_frames = 0 # TODO: actual measurement
        }
    }
    
    $state = @{
        timestamp = (Get-Date -Format "o")
        stream_count = $streamStatus.Count
        streams = $streamStatus
    }
    
    $state | ConvertTo-Json -Depth 4 | Set-Content $StateFile
    
    Write-Host "[SPOUT] $(Get-Date -Format 'HH:mm:ss') — $($streamStatus.Count) streams monitored"
    
    Start-Sleep -Seconds $IntervalSeconds
}
