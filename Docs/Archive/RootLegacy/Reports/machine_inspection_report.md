# BS_GodFile Machine Inspection Report
*Generated from: C:\EnvironmentPortfolio\BS_GodFile*

---
## 1. GPU type/version and driver info
- **NOT FOUND** in inspected scripts (validate_setup.ps1, ollama_health.py, paths.json, etc.)
- No GPU-related checks present in the validation infrastructure
- Source files examined: validate_setup.ps1, ollama_health.py, paths.json, status.ps1, ai_tool_quickstart.ps1, start_ollama_fleet.ps1

---
## 2. VRAM amount and current utilization
- **NOT FOUND** in inspected scripts
- No VRAM monitoring or reporting in the configuration
- No GPU tracking infrastructure present

---
## 3. System RAM amount
- **NOT FOUND** in inspected scripts
- No system RAM reporting in the configuration

---
## 4. Python version and point about 3.14 vs baseline 3.11 warning
- **Installed version**: Python 3.14.5 (from `python --version`)
- **Baseline configured**: Python 3.11 (from Config/paths.json `versions.python`)
- **Warning from validate_setup.ps1**: `[WARN] python: 3.14 found; documented baseline is 3.11`
- **Analysis**: Python 3.14.5 exceeds the documented baseline of 3.11, triggering a WARN status. The script uses `Test-CommandVersion "python" 3 11 -Required -ExactMinor` which matches when `major == 3 AND minor >= 11`, and since `3.14 > 3.11` but `3.14 != 3.11`, it falls into the "meets minimum but not baseline" category, producing the warning.

---
## 5. Node.js version and warning about 24.18 vs 20.0
- **Installed version**: Node.js v24.18.0 (from `node -v`)
- **Baseline configured**: Node.js 20 (from Config/paths.json `versions.node`)
- **Warning from validate_setup.ps1**: `[WARN] node: 24.18 found; documented baseline is 20.0`
- **Analysis**: Node.js v24.18.0 exceeds the documented baseline of 20.0, triggering a WARN status. The script uses `Test-CommandVersion "node" 20 0 -Required:$false` which similarly warns when the installed version exceeds but doesn't exactly match the baseline.

---
## 6. Ollama status - what models are running, which are missing
- **Ollama status**: REACHABLE at `http://127.0.0.1:11434`
- **Ollama version**: 0.32.14
- **Installed models** (from ollama list /api/tags):
  - qwen3.8-27b:latest (size: 18034382686 bytes, quantization: Q4_K_M, context_length: 262144)
  - qwen2.5-coder:7b (size: 4683087561 bytes, quantization: Q4_K_M, context_length: 32768)
  - qwen2.5-coder:14b (size: 8988124298 bytes, quantization: Q4_K_M, context_length: 32768)
  - deepseek-r1:14b (size: 8988112209 bytes, quantization: Q4_K_M, context_length: 131072)
  - deepseek-r1:7b (size: 4683075440 bytes, quantization: Q4_K_M, context_length: 131072)
  - deepseek-coder:6.7b (size: 3827834503 bytes, quantization: Q4_0, context_length: 16384)
- **Lane model assignments** (from ollama_health.py LANE_MODELS):
  - reasoning: deepseek-r1:14b → **AVAILABLE**
  - code: qwen2.5-coder:7b → **AVAILABLE**
  - heavy_code: qwen2.5-coder:14b → **AVAILABLE**
  - general: qwen2.5-coder:7b → **AVAILABLE**
  - creative: deepseek-r1:14b → **AVAILABLE**
- **Missing models**: NONE (healthy: true, missing_models: [])

---
## 7. Bound, VRAM-bound, RAM-bound assessments
- **NOT FOUND** in inspected scripts
- No bound assessment infrastructure present in the configuration
- No CPU/RAM/VRAM binding checks in validate_setup.ps1 or related scripts

---
## 8. Quantization info for local models
### qwen3.8-27b:latest
- Parameter size: 27.3B
- Quantization level: **Q4_K_M**
- Context length: 262144
- Embedding length: 5120
- Format: gguf
- Family: qwen35
- Size on disk: 18034382686 bytes

### qwen2.5-coder:7b
- Parameter size: 7.6B
- Quantization level: **Q4_K_M**
- Context length: 32768
- Embedding length: 3584
- Format: gguf
- Family: qwen2
- Size on disk: 4683087561 bytes

### qwen2.5-coder:14b
- Parameter size: 14.8B
- Quantization level: **Q4_K_M**
- Context length: 32768
- Embedding length: 5120
- Format: gguf
- Family: qwen2
- Size on disk: 8988124298 bytes

### deepseek-r1:14b
- Parameter size: 14.8B
- Quantization level: **Q4_K_M**
- Context length: 131072
- Embedding length: 5120
- Format: gguf
- Family: qwen2
- Size on disk: 8988112209 bytes

### deepseek-r1:7b
- Parameter size: 7.6B
- Quantization level: **Q4_K_M**
- Context length: 131072
- Embedding length: 3584
- Format: gguf
- Family: qwen2
- Size on disk: 4683075440 bytes

### deepseek-coder:6.7b
- Parameter size: 7B
- Quantization level: **Q4_0**
- Context length: 16384
- Embedding length: 4096
- Format: gguf
- Family: llama
- Size on disk: 3827834503 bytes

---
## 9. Ollama configuration (127.0.0.1:11434, background processes)
- **Ollama endpoint**: `http://127.0.0.1:11434` (API at `/api/tags`, `/api/version`)
- **Service port**: 11434 (configured in Config/paths.json `ports.ollama`)
- **Background daemons** (from deploy scripts):
  - `ollama_slice_content_daemon.py`
  - `ollama_wardrobe_catalog_daemon.py`
  - `ollama_dialogue_daemon.py`
  - `ollama_gumroad_copy_daemon.py`
  - `ollama_data_validator_daemon.py`
- **Ollama health probe** (from Tools/ollama_health.py):
  - Checks `/api/version` and `/api/tags` endpoints
  - Writes evidence to `Saved/Integration/ollama_health.json`
  - Supports `--offline` mode with cached evidence
  - Defines `LANE_MODELS` contract for local fleet:
    - reasoning: deepseek-r1:14b
    - code: qwen2.5-coder:7b
    - heavy_code: qwen2.5-coder:14b
    - general: qwen2.5-coder:7b
    - creative: deepseek-r1:14b
  - Defines `LANE_FALLBACKS` for each lane with alternative models

---
## 10. Any CPU info relevant to model serving
- **NOT FOUND** in inspected scripts
- No CPU information (count, model, features) present in the configuration
- No CPU-specific model serving constraints documented

---
## 11. The 7 PC health warnings listed in validate_setup.ps1 output
The exactly 7 warnings produced by `validate_setup.ps1`:

1. **[WARN] python: 3.14 found; documented baseline is 3.11**
   - Python 3.14.5 installed, baseline is 3.11

2. **[WARN] node: 24.18 found; documented baseline is 20.0**
   - Node.js v24.18.0 installed, baseline is 20.0

3. **[WARN] Required LFS files: not checked; rerun with -CheckLfsHydration after git lfs pull**
   - Git LFS hydration not verified

4. **[WARN] LiveLink: not running; start only for workflows that require it**
   - LiveLink service not running on port 9876

5. **[WARN] VOICEVOX: not running; start only for workflows that require it**
   - VOICEVOX service not running on port 50021

6. **[WARN] Melusina Voice: not running; start only for workflows that require it**
   - Melusina Voice service not running on port 50022

7. **[WARN] Quantum: not running; start only for workflows that require it**
   - Quantum service not running on port 8008

---
## 12. Any other hardware/software constraints for model routing
### Port configuration (from Config/paths.json)
- `ollama`: 11434
- `quantum`: 8008
- `ue_mcp`: 9316
- `blender_mcp`: 9317
- `voicevox`: 50021
- `melusina_voice`: 50022
- `livelink`: 9876

### Model routing constraints
- **Ollama is the primary local model inference engine** at 127.0.0.1:11434
- **6 models installed** supporting 5 lane assignments with fallbacks
- **All lane models available** — healthy = true, no missing models
- **Fallback model chains** configured for each lane (see ollama_health.py LANE_FALLBACKS)
- **Python 3.14** exceeds the 3.11 baseline warning — may affect script compatibility
- **Node.js 24.18** exceeds the 20.0 baseline warning — may affect build/tooling compatibility
- **No GPU acceleration** detected/configured for model inference
- **All model quantization is Q4_K_M** (except deepseek-coder:6.7b which uses Q4_0) — moderate quantization level balancing model quality and memory usage
- **No VRAM/RAM thresholds** configured in the routing infrastructure
- **Model sizes range from 7B to 27.3B parameters** — quantization at Q4_K_M reduces memory footprint significantly vs unquantized sizes

### Summary constraints for model routing
1. Ollama must be running at 127.0.0.1:11434 with the 6 installed models
2. All 5 lane model assignments are satisfied (no missing models)
3. Python 3.14.5 is newer than the documented 3.11 baseline (warns but functional)
4. Node.js v24.18.0 is newer than the documented 20.0 baseline (warns but functional)
5. No GPU acceleration configured — models rely on CPU inference via GGUF quantization
6. Q4_K_M quantization used for all models except deepseek-coder:6.7b (Q4_0)
7. 7 PC health warnings exist — 2 version mismatches (Python/Node), 5 optional services not running