param(
    [Parameter(Mandatory = $true)]
    [string]$ArchiveDir,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$')]
    [string]$Bucket,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._/\\-]*$')]
    [string]$Prefix,
    [string]$Region = "ca-central-1",
    [string]$Profile,
    [string]$KmsKeyId,
    [string]$EvidencePath,
    [switch]$ConfirmPublish
)

$ErrorActionPreference = "Stop"

function Invoke-AwsJson {
    param([string[]]$Arguments)
    $output = & aws @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI failed: $($output -join [Environment]::NewLine)"
    }
    return ($output -join [Environment]::NewLine)
}

$resolvedArchive = (Resolve-Path -LiteralPath $ArchiveDir).Path
if (-not (Test-Path -LiteralPath $resolvedArchive -PathType Container)) {
    throw "Archive directory does not exist: $ArchiveDir"
}
if ($ConfirmPublish -and -not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI is required for a confirmed publish."
}

$normalisedPrefix = ($Prefix -replace '\\', '/').Trim('/')
$destination = "s3://$Bucket/$normalisedPrefix"
$baseArgs = @("--region", $Region)
if ($Profile) { $baseArgs += @("--profile", $Profile) }

$manifest = Join-Path $resolvedArchive "melodia_artifact_manifest.json"
$plan = [ordered]@{
    schema = "melodia.aws_artifact_publish_plan.v1"
    status = if ($ConfirmPublish) { "publish" } else { "plan_only" }
    source = $resolvedArchive
    destination = $destination
    region = $Region
    profile = if ($Profile) { $Profile } else { "default-resolution" }
    encryption = if ($KmsKeyId) { "aws:kms" } else { "bucket-default" }
    delete_semantics = "none"
    manifest_present = (Test-Path -LiteralPath $manifest -PathType Leaf)
}

if (-not $ConfirmPublish) {
    $plan | ConvertTo-Json -Depth 5
    Write-Output "Plan only. Re-run with -ConfirmPublish and an explicit -KmsKeyId to publish; no AWS write occurred."
    exit 0
}

if (-not $KmsKeyId) {
    throw "Confirmed publication requires -KmsKeyId so the artifact is explicitly encrypted with SSE-KMS."
}
if (-not $plan.manifest_present) {
    throw "Refusing to publish an archive without melodia_artifact_manifest.json: $manifest"
}

$identityJson = Invoke-AwsJson (@("sts", "get-caller-identity", "--output", "json") + $baseArgs)
$identity = $identityJson | ConvertFrom-Json
$plan["caller_account"] = [string]$identity.Account
$plan["caller_arn"] = [string]$identity.Arn

$copyArgs = @(
    "s3", "cp", $resolvedArchive, $destination,
    "--recursive", "--only-show-errors", "--no-progress",
    "--sse", "aws:kms", "--sse-kms-key-id", $KmsKeyId
) + $baseArgs
& aws @copyArgs
if ($LASTEXITCODE -ne 0) {
    throw "Artifact publication failed with exit code $LASTEXITCODE."
}

$plan["status"] = "published"
$plan["published_at_utc"] = (Get-Date).ToUniversalTime().ToString("o")
$plan["objects"] = "recursive copy without delete"
$planJson = $plan | ConvertTo-Json -Depth 8
$planJson

if ($EvidencePath) {
    $repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
    $evidenceTool = Join-Path $repoRoot "Tools\evidence_envelope.py"
    $subjectJson = $plan | ConvertTo-Json -Compress -Depth 8
    & python $evidenceTool create `
        --kind build --status pass --producer aws-artifact-publisher `
        --check-name s3_artifact_publish --check-status pass `
        --gate-id aws_artifact_publish `
        --note "Published BuildGraph artifact to $destination with SSE-KMS; recursive copy used without delete semantics." `
        --subject-json $subjectJson `
        --artifact $manifest `
        --artifact $destination `
        --output $EvidencePath
    if ($LASTEXITCODE -ne 0) {
        throw "Artifact published, but evidence envelope creation failed with exit code $LASTEXITCODE."
    }
}
