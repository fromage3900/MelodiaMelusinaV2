# start_osc_monitor.ps1
# Monitors OSC bridge health between TouchDesigner and Unreal Engine
# Branch: feature/touchdesigner-mcp-integration

param(
    [int]$IntervalSeconds = 10
)

$ProjectRoot = "G:\EnvironmentPortfolio"
$AuditDir = "$ProjectRoot\BS_GodFile\Saved\Audit"
$StateFile = "$AuditDir\osc_monitor_state.json"

New-Item -ItemType Directory -Force -Path $AuditDir | Out-Null

$ports = @(
    @{Port=8000; Description="UE OSC Listener"},
    @{Port=9000; Description="Blender OSC Listener"}
)

Write-Host "[OSC] Monitor started — checking ports every ${IntervalSeconds}s"

while ($true) {
    if (Test-Path "$AuditDir\td_loop_STOP") { 
        Write-Host "[OSC] STOP signal received. Exiting."
        break 
    }
    
    $portStatus = @()
    
    foreach ($p in $ports) {
        # Check if port is open via UDP probe (best-effort)
        $testResult = "unknown"
        try {
            $udp = New-Object System.Net.Sockets.UdpClient
            $udp.Client.ReceiveTimeout = 500
            $udp.Connect("127.0.0.1", $p.Port)
            $sendBytes = [Text.Encoding]::ASCII.GetBytes("/osc/ping")
            $udp.Send($sendBytes, $sendBytes.Length) | Out-Null
            $udp.Close()
            $testResult = "reachable"
        }
        catch {
            $testResult = "unreachable"
        }
        
        $portStatus += @{
            port = $p.Port
            description = $p.Description
            status = $testResult
            timestamp = (Get-Date -Format "o")
        }
    }
    
    $state = @{
        timestamp = (Get-Date -Format "o")
        ports = $portStatus
        active_routes = @(
            "/melusina/pitch",
            "/melusina/amp",
            "/material/toon",
            "/material/preset",
            "/time/cycle"
        )
    }
    
    $state | ConvertTo-Json -Depth 4 | Set-Content $StateFile
    
    $reachable = ($portStatus | Where-Object { $_.status -eq "reachable" }).Count
    Write-Host "[OSC] $(Get-Date -Format 'HH:mm:ss') — $reachable/$($portStatus.Count) ports reachable"
    
    Start-Sleep -Seconds $IntervalSeconds
}
