# Start ngrok tunnel for Cursor Agent to use local Ollama models
# Run this before using Cursor Agent with local models (for remote access)
# For local access, no tunnel needed - just ensure Ollama is running

# Verify Ollama is running locally first
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
    Write-Host "Ollama is running with $($response.models.Count) models available" -ForegroundColor Green
    Write-Host "Recommended model: qwen2.5-coder:14b (for web development)" -ForegroundColor Cyan
} catch {
    Write-Host "WARNING: Ollama not responding on localhost:11434" -ForegroundColor Red
    Write-Host "Start Ollama first with: ollama serve" -ForegroundColor Yellow
    exit 1
}

# Check if ngrok is running
$ngrokStatus = & ngrok status 2>&1
if ($ngrokStatus -match "tunnel") {
    Write-Host "ngrok already running" -ForegroundColor Green
} else {
    Write-Host "Starting ngrok tunnel on port 11434..." -ForegroundColor Yellow
    Start-Process -WindowStyle Hidden -FilePath "ngrok" -ArgumentList "http", "11434"
    Start-Sleep -Seconds 3
}

# Get the public URL
$ngrokAPI = & ngrok http://localhost:4040/api/tunnels 2>&1 | Select-String -Pattern "public_url"
if ($ngrokAPI) {
    $url = $ngrokAPI -match 'https://[\w.-]+ngrok.io' | Out-Null
    $tunnelUrl = $matches[0]
    Write-Host "Tunnel ready: $tunnelUrl" -ForegroundColor Green
    
    # Save tunnel config for Cursor Agent use
    $tunnelConfig = @{
        OLLAMA_HOST = $tunnelUrl -replace 'https', 'http'
        created = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    $configPath = Join-Path $PSScriptRoot "cursor_ollama_tunnel_config.json"
    $tunnelConfig | ConvertTo-Json | Set-Content $configPath
    Write-Host "Saved tunnel config to: $configPath" -ForegroundColor Cyan
    Write-Host "For remote Cursor Agent, set OLLAMA_HOST=$($tunnelConfig.OLLAMA_HOST)" -ForegroundColor Yellow
}