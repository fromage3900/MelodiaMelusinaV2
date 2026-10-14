# Persist GEMINI_API_KEY for the Claireon/Claude Code gemini upstream.
# Hidden input. Never prints or logs the key value - only lengths and HTTP status.
# Writes: user-scope env var GEMINI_API_KEY + %LOCALAPPDATA%\hermes\gemini_api_key.txt
# Then smoke-tests Google's OpenAI-compatible surface (the exact one the proxy uses).
$ErrorActionPreference = 'Stop'
$secure = Read-Host 'Enter GEMINI_API_KEY (input is hidden)' -AsSecureString
if (-not $secure -or $secure.Length -eq 0) {
    Write-Host 'SET_KEY=not_run reason=no_key_entered'
    exit 2
}
$ptr = [IntPtr]::Zero
try {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $apiKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        Write-Host 'SET_KEY=failed reason=empty_key'
        exit 2
    }
    $apiKey = $apiKey.Trim()

    # Smoke: list models on the OpenAI-compatible surface (Authorization: Bearer).
    $listed = $false
    try {
        $resp = Invoke-RestMethod -Uri 'https://generativelanguage.googleapis.com/v1beta/openai/models' `
            -Headers @{ Authorization = "Bearer $apiKey" } -TimeoutSec 60
        $ids = @($resp.data | ForEach-Object { $_.id })
        $listed = $ids -contains 'gemini-4-argon'
        Write-Host ("OPENAI_COMPAT=success models_listed={0} gemini-4-argon={1}" -f $ids.Count, ($(if ($listed) { 'yes' } else { 'NO' })))
        if (-not $listed -and $ids.Count -gt 0) {
            $argonish = $ids | Where-Object { $_ -match 'argon' }
            if ($argonish) { Write-Host ("ARGON_VARIANTS=" + ($argonish -join ',')) }
        }
    } catch {
        $status = 0
        try { if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode } } catch {}
        Write-Host ("OPENAI_COMPAT=blocked http_status={0}" -f $status)
        $detail = [string]$_.ErrorDetails.Message
        if ($detail -match 'API_KEY_INVALID|UNAUTHENTICATED|PERMISSION_DENIED') {
            Write-Host 'category=API_KEY_INVALID_or_permission'
            Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
            exit 3
        }
        # Key may still be valid even if the models listing is unavailable; ask before persisting.
        $cont = Read-Host 'Models listing failed. Persist the key anyway? (y/N)'
        if ($cont -notmatch '^[Yy]') { exit 3 }
    }

    # Persist: user-scope env (for Tools/model_router.py, gemini_video_qa.py, new shells)
    [Environment]::SetEnvironmentVariable('GEMINI_API_KEY', $apiKey, 'User')
    $env:GEMINI_API_KEY = $apiKey

    # Persist: hermes key file (for the translating proxy, which re-reads per request)
    $hermesDir = Join-Path $env:LOCALAPPDATA 'hermes'
    if (-not (Test-Path $hermesDir)) { New-Item -ItemType Directory -Force -Path $hermesDir | Out-Null }
    [System.IO.File]::WriteAllText((Join-Path $hermesDir 'gemini_api_key.txt'), $apiKey, (New-Object System.Text.UTF8Encoding $false))

    Write-Host ("SET_KEY=persisted env=User file=hermes\\gemini_api_key.txt key_len={0}" -f $apiKey.Length)
    Write-Host 'New shells inherit the user env var; already-running processes (e.g. the proxy) read the key file.'
} finally {
    if ($ptr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
    if ($secure) { $secure.Dispose() }
    $apiKey = $null
}
