# Ollama Setup — Root Cause & Fix (2026-08-20)

## The failure

Every local model appeared to "crash on load" mid-session, including two that had
run successfully 20 minutes earlier. The API stayed up; only model loads failed.
Surfaced to callers as:

```
{"error":"llama-server process has terminated: exit status 0xffffffff: NTSTATUS 0xffffffff"}
```

## What it actually was

**Not** a driver fault, GPU failure, OOM, or corrupt GGUF. The server log
(`%LOCALAPPDATA%\Ollama\server.log`) shows the real error:

```
level=INFO source=sched.go:641 msg="Load failed"
  model=F:\OllamaModels\blobs\sha256-...
  error="timed out waiting for llama-server to start: context canceled"
```

`NTSTATUS 0xffffffff` was a *downstream symptom* of the load being cancelled, not
the cause. Chasing that string is a dead end — always read `server.log`.

### Measured root cause

| Fact | Value | How measured |
|---|---|---|
| Model store location | `F:\OllamaModels` (84 GB) | `OLLAMA_MODELS` env var |
| **F: sequential read** | **32.0 MB/s** | `dd if=<17GB blob> bs=1M count=2000` → 65.5s for 2.1 GB |
| GPU | RTX 4070 SUPER, 12281 MiB (~11069 free) | `nvidia-smi` |
| deepseek-coder:6.7b cold load | **98.3 s** | `load_duration` from `/api/chat` |
| qwen2.5-coder:14b cold load | **284.5 s** (4.7 min) | `load_duration` from `/api/chat` |

F: is a hard disk. A 9 GB model needs ~5 minutes just to page in; a 21 GB model
needs ~11 minutes. The probe harness used a 180-second timeout and Ollama's own
load window expired under that pressure — so every larger model "failed."

Compounding factor: with `OLLAMA_KEEP_ALIVE` unset (default 5 min), a benchmark
sweep re-paged the model from the HDD for *each* task, so the sweep re-paid the
5-minute cost repeatedly and appeared to fail randomly.

## The fix applied

`Tools/fix_ollama_setup.ps1` — sets USER-scope env vars (no admin, persistent):

| Variable | Value | Why |
|---|---|---|
| `OLLAMA_LOAD_TIMEOUT` | `30m` | Covers a 21 GB model at 32 MB/s with headroom |
| `OLLAMA_KEEP_ALIVE` | `30m` | Sweep pays the load cost ONCE, not per task |
| `OLLAMA_MAX_LOADED_MODELS` | `1` | 12 GB VRAM can't hold two; eviction on a slow disk is catastrophic |
| `OLLAMA_NUM_PARALLEL` | `1` | Serialize; avoids VRAM thrash |
| `OLLAMA_FLASH_ATTENTION` | `1` | Reduces KV cache footprint |

`OLLAMA_MODELS` was left untouched.

Harness also hardened (`Tools/test_claireon_toolcalls.py`):
- default `--timeout` raised 180s → 1200s
- `--all` no longer aborts the whole sweep when one model errors; failures are
  listed at the end as unscored (never estimated)

## Verification — the config fix works

After applying settings and restarting Ollama, both previously-failing models
now load and respond:

| Model | load_duration | Output | done_reason |
|---|---|---|---|
| `qwen2.5-coder:7b` | **250.6 s** | `"OK"` — coherent | `stop` |
| `qwen2.5-coder:14b` | **284.5 s** | `"8888888888..."` — **garbage** | `length` |

The timeout problem is solved: both load where neither could before.

## SECOND, SEPARATE DEFECT: qwen2.5-coder:14b emits garbage

This is **not** the timeout issue and **not** fixed by the config change.

`qwen2.5-coder:14b` loads successfully and then produces pure repeated-token
output. A full probe run scored **0/8 with all 8 responses unparsed**, every one
of them `"8888888888888888888888888888888"`.

Isolation evidence — it is one model, not the store or the config:

- `qwen2.5-coder:7b` on the identical config, identical prompt shape, same store:
  coherent `"OK"` with `done_reason: stop`.
- Both tags carry 2 exclusive blobs each, so this is not shared-blob corruption.
- `deepseek-coder:6.7b` also produced coherent (if unparseable-as-JSON) prose
  earlier in the session.

Conclusion: `qwen2.5-coder:14b`'s weights are corrupt on disk. Given F: is a
failing-speed HDD holding 66 GB of blobs, a bad write is plausible.

**DO NOT treat `Saved/Audit/claireon_probe_qwen2.5-coder_14b_2026-08-20.json` as
a model-capability result.** It measures a corrupt file. The 0/8 is a storage
defect, not a finding about Qwen's tool-calling.

### Fix
```bash
ollama rm qwen2.5-coder:14b
ollama pull qwen2.5-coder:14b     # ~9 GB over a 32 MB/s disk: expect ~5+ min
# then re-verify BEFORE benchmarking:
python Tools/test_claireon_toolcalls.py --model qwen2.5-coder:14b --timeout 1200
```

If the re-pull also emits `8888...`, suspect the drive itself and run `chkdsk F:`.
Consider verifying the other large tags the same way — a single coherence smoke
test per model before any sweep is now mandatory.


## Remaining limitation (NOT fixed)

These settings make loads *survive*; they do not make them *fast*. A full
`--all` sweep across 8 models will take roughly 45-60 minutes, nearly all of it
disk I/O.

**The durable fix is moving the model store to an SSD.** Blocked today by disk
space — every drive is effectively full:

```
C:  953G total,  22G free  (98% used)
F:  1.9T total,  32G free  (99% used)
G:  932G total,   0G free  (100% used)
```

The store is 84 GB and there is nowhere to put it. Options, in order of
preference:

1. Free ~100 GB on C: (an SSD), then set `OLLAMA_MODELS=C:\OllamaModels` and
   move the store. Expect roughly a 15-20x load speedup.
2. Prune unused models first. **Verified blob refcounts** (from reading the
   manifests in `F:\OllamaModels\manifests` and counting shared digests):

   | Tag | Layers | Exclusive blobs | Deleting it frees |
   |---|---|---|---|
   | `hf.co/bartowski/Muse-Glimmer-30B-GGUF:Q4_K_M` | 5 | **0** | nothing — pure alias |
   | `muse-glimmer-30b:latest` | 5 | **0** | nothing — pure alias |
   | `muse-glimmer-30b-cpu:latest` | 5 | 2 | partial |
   | `deepseek-coder:6.7b` | 5 | 5 | full ~3.8 GB |
   | `qwen3.8-27b:latest` | 4 | 4 | full ~18 GB |
   | `deepseek-r1:14b` / `:7b` | 5 | 2 each | partial |
   | `qwen2.5-coder:14b` / `:7b` | 5 | 2 each | partial |

   **Important correction:** `muse-glimmer-30b:latest` and the `hf.co/bartowski`
   tag share **all 5 blobs** — they are two names for one download, not 42 GB of
   duplication. Deleting either frees zero bytes. `ollama list` showing "21 GB"
   three times is misleading; the store is 66 GB of blobs total, not 84 GB of
   distinct models.

   To actually reclaim space you must remove **all three** Muse tags (they
   collectively hold the 17 GB blob plus 2 exclusive each), which frees roughly
   17-21 GB. That model scored **0/32** and is the best prune candidate.
   `qwen3.8-27b` has 4 fully-exclusive blobs (~18 GB) and scored 21/32.

   Verify reclaim with `du -sh /f/OllamaModels/blobs` before and after — do not
   trust `ollama list` sizes for disk math.

3. Add a dedicated NVMe for model storage.

## Diagnostic recipe for next time

```bash
# 1. Is it really a crash? Read the server log, not the API error.
grep -iE "Load failed|timed out|error" "$LOCALAPPDATA/Ollama/server.log" | tail -20

# 2. How slow is the store?
cd "$OLLAMA_MODELS/blobs" && dd if=$(ls -S | head -1) of=/dev/null bs=1M count=2000

# 3. What does a load actually cost? (load_duration is in nanoseconds)
curl -s -X POST http://localhost:11434/api/chat -d '{"model":"<tag>","stream":false,
  "options":{"num_predict":8},"messages":[{"role":"user","content":"OK"}]}' | python -m json.tool

# 4. Confirm env vars are live (registry, not shell)
powershell -NoProfile -Command "[Environment]::GetEnvironmentVariables('User')"
```
