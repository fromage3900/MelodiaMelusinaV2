# Ollama tuning for a slow model store (F: HDD @ ~32 MB/s) on a 12GB RTX 4070 SUPER.
#
# Root cause this addresses: models load from F: at ~32 MB/s, so a 9-21GB model
# needs 5-11 minutes to page in. Ollama's default load window expires first and
# reports "timed out waiting for llama-server to start: context canceled" —
# which surfaces to callers as an opaque runtime error, NOT an OOM or a bad GGUF.
#
# Sets USER-level vars (persistent, no admin needed). Restart Ollama afterward.

$settings = @{
  # Give slow-disk loads room. 30 min covers a 21GB model at 32 MB/s (~11 min)
  # with generous headroom for cold NTFS cache.
  'OLLAMA_LOAD_TIMEOUT'  = '30m'

  # Keep a model resident for 30 min so a benchmark sweep pays the load cost
  # ONCE instead of per-task. This was the single biggest cause of mid-run
  # failures: each task re-paged the model from the HDD.
  'OLLAMA_KEEP_ALIVE'    = '30m'

  # 12GB VRAM cannot hold two models. Serialize to avoid eviction thrash,
  # which on a slow disk is catastrophic (evict = another 10-min reload).
  'OLLAMA_MAX_LOADED_MODELS' = '1'
  'OLLAMA_NUM_PARALLEL'      = '1'

  # Do not unload/reload across requests in a sweep.
  'OLLAMA_FLASH_ATTENTION' = '1'
}

Write-Output "Applying Ollama environment settings (User scope)..."
foreach ($k in $settings.Keys) {
  [Environment]::SetEnvironmentVariable($k, $settings[$k], 'User')
  Write-Output ("  {0} = {1}" -f $k, $settings[$k])
}

Write-Output ""
Write-Output "Preserved (not modified):"
Write-Output ("  OLLAMA_MODELS = {0}" -f [Environment]::GetEnvironmentVariable('OLLAMA_MODELS','User'))

Write-Output ""
Write-Output "Verify after restarting Ollama:"
Write-Output "  1. Quit Ollama from the system tray (or: taskkill /IM 'ollama app.exe' /F)"
Write-Output "  2. Relaunch Ollama"
Write-Output "  3. python BS_GodFile/Tools/test_claireon_toolcalls.py --model qwen2.5-coder:7b"
Write-Output ""
Write-Output 'NOTE: these are load/VRAM settings only. They do NOT make the HDD faster.'
Write-Output 'The durable fix is moving OLLAMA_MODELS to an SSD -- blocked today because'
Write-Output 'C: has 22G free, F: 32G, G: 0G and the store is 84G.'
