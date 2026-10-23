# Wedge-proof Houdini license probe - run this BEFORE any hython work (plan B0).
# Background: on 2026-08-28 a bare "hython --version" in a shared console hung >60s
# and wedged the whole shell session. This probe isolates every invocation with
# Start-Process + a hard timeout + forced kill, so a license-server hang can never
# take the console down again.

$ErrorActionPreference = "Continue"
$hython = "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe"
$hserver = "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hserver.exe"
$timeoutSec = 45

function Invoke-Isolated {
    param([string]$Exe, [string[]]$ArgList, [string]$Tag)
    $out = Join-Path $env:TEMP "$Tag`_out.txt"
    $err = Join-Path $env:TEMP "$Tag`_err.txt"
    Remove-Item $out, $err -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $Exe -ArgumentList $ArgList `
         -RedirectStandardOutput $out -RedirectStandardError $err `
         -PassThru -WindowStyle Hidden
    if ($p.WaitForExit($timeoutSec * 1000)) {
        $text = (Get-Content $out -Raw -ErrorAction SilentlyContinue) + `
                (Get-Content $err -Raw -ErrorAction SilentlyContinue)
        return @{ status = "OK"; output = $text.Trim() }
    }
    try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {}
    return @{ status = "HANG (killed after ${timeoutSec}s)"; output = "" }
}

Write-Host "=== B0 Houdini license verdict (isolated probes) ==="

$r1 = Invoke-Isolated $hserver @("-l") "hserver_list"
Write-Host "hserver -l : $($r1.status)"
Write-Host $r1.output

# hou import via temp file: Start-Process mangles spaced -c strings, so never pass them
$probe_py = Join-Path $env:TEMP "hou_probe.py"
Set-Content -LiteralPath $probe_py -Value "import hou; print('HOU', hou.applicationVersionString())" -Encoding ASCII
$r2 = Invoke-Isolated $hython @($probe_py) "hython_probe"
Write-Host "hython hou : $($r2.status)"
Write-Host $r2.output

if ($r1.status -eq "OK" -and $r2.status -eq "OK") {
    if ($r1.output -match "No licenses|None") {
        Write-Host "VERDICT: hython runs but NO Engine license - HDA-in-UE stays blocked; Apprentice hython cooks (geometry/COP) are the lane."
    } else {
        Write-Host "VERDICT: license server answering and hython imports hou - check above lines for 'Houdini Engine' entry; if present, HDA lane may proceed."
    }
} else {
    Write-Host "VERDICT: RED - hython/hserver hang persists. All hython cooks stay parked; PIL/Blender fallbacks carry the texture lane (they need nothing from Houdini)."
    Write-Host "Next: open License Administrator (hkey) / sesictrl manually, then rerun this probe."
}
