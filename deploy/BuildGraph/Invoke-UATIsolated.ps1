param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("CookPackage", "Gauntlet")]
    [string]$Task,
    [Parameter(Mandatory = $true)]
    [string]$ProjectFile,
    [Parameter(Mandatory = $true)]
    [string]$UATBat,
    [Parameter(Mandatory = $true)]
    [string]$ArchiveDir,
    [string]$ProjectRoot = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$archive = (Resolve-Path -LiteralPath $ArchiveDir -ErrorAction SilentlyContinue)
if (-not $archive) {
    New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null
    $archive = Resolve-Path -LiteralPath $ArchiveDir
}
$archivePath = $archive.Path
$resolvedProject = (Resolve-Path -LiteralPath $ProjectFile).Path
$resolvedUAT = (Resolve-Path -LiteralPath $UATBat).Path

# UE 5.8's AutomationTool singleton is controlled by this environment switch.
$env:uebp_UATMutexNoWait = "1"

$logRoot = Join-Path $root "Saved\Integration\BuildGraph"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$stdoutPath = Join-Path $logRoot ("{0}_{1}.stdout.log" -f $Task, $stamp)
$stderrPath = Join-Path $logRoot ("{0}_{1}.stderr.log" -f $Task, $stamp)

if ($Task -eq "CookPackage") {
    $uatArguments = @(
        "BuildCookRun", "-NoMutex", "-project=$resolvedProject", "-noP4",
        "-platform=Win64", "-clientconfig=Development", "-cook", "-build",
        "-stage", "-pak", "-archive", "-archivedirectory=$archivePath", "-utf8output"
    )
} else {
    $uatArguments = @(
        "RunUnreal", "-NoMutex", "-project=$resolvedProject", "-platform=Win64",
        "-configuration=Development", "-test=UE.TargetAutomation",
        "-Build=$archivePath\Windows", "-packaged", "-RunTest=Project",
        "-skipdeploy", "-unattended", "-log", "-MaxDuration=120"
    )
}

# RunUAT is a .bat file. Redirecting its complete stream keeps BuildGraph's
# LogEventParser out of the high-volume UE output path; the node receives only
# a compact completion line and the child exit code remains authoritative.
$quotedUAT = '"' + $resolvedUAT + '"'
$commandLine = '/d /c call ' + $quotedUAT + ' ' + ($uatArguments -join ' ')
$child = Start-Process -FilePath "cmd.exe" -ArgumentList $commandLine -WorkingDirectory $root `
    -WindowStyle Hidden -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru -Wait

Write-Output ("{0} UAT exit code: {1}" -f $Task, $child.ExitCode)
Write-Output ("{0} stdout: {1}" -f $Task, $stdoutPath)
Write-Output ("{0} stderr: {1}" -f $Task, $stderrPath)
if ($child.ExitCode -ne 0) {
    $tail = Get-Content -LiteralPath $stdoutPath -Tail 40 -ErrorAction SilentlyContinue
    if ($tail) { $tail | Write-Output }
    throw ("{0} UAT failed with exit code {1}" -f $Task, $child.ExitCode)
}
