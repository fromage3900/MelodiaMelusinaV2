# Session Handoff — 2026-08-20 (Claireon lane)

Read this first next session. Written against disk state, not conversation memory.

## TL;DR

| Workstream | State |
|---|---|
| Claireon prep | Declared in `.uproject`, launch config + isolated worktree ready. **NOT built. Never run.** |
| Claireon probe harness | Working. 2 valid model results, 1 invalid (corrupt model), 5 unscored. |
| Ollama | Root-caused and fixed (config). One model found corrupt. |
| Email drafts | 6 send-ready bodies. **Removed a live over-claim** — see §4. |
| Echo pipeline | `claireon_bringup` stage + 4 non-blocking gates added. |
| T3D dashboards | Rebuilt 13:23. |
| Melusina Claireon plan | Written — 5 boundaries, 5 phases. |

---

## 1. Git state

Branch `main`, HEAD `2a691b1d` at time of writing. **Concurrent lanes are active
in this repo** — another agent committed 7 times during my session and twice
reverted my `.uproject`/`.gitignore` edits. Always `git log` before assuming state.

My commits today:

| SHA | What |
|---|---|
| `2eb04dcc` | Claireon in `.uproject` (+12 deps), prep doc, probe harness |
| `119d492c` | `.claireon/launch_editor.json`, `Scripts/LaunchEditor.ps1`, prep ledger |
| `6bd08286` | Probe results ledger |
| `2a691b1d` | Emails, withdrawn-metric correction, Echo gates, Melusina plan |

### UNCOMMITTED at session end — commit these first

| File | State |
|---|---|
| `Docs/OLLAMA_SETUP_FIX_2026-08-20.md` | new — full root-cause writeup |
| `Tools/fix_ollama_setup.ps1` | new — applied and verified working |
| `Tools/test_claireon_toolcalls.py` | modified — timeout 1200s, sweep resilience |
| `Scripts/LaunchEditor.ps1` | modified — **syntax fix, was broken** |
| `Docs/CLAIREON_PROBE_RESULTS_2026-08-20.md` | modified — 14b marked INVALID |
| `.gitignore` | **owner-protected, needs your sign-off** |

`.gitignore` adds `Plugins/Claireon/` (nested clone of `believer-oss/Claireon.git`
@ `ed0b457`, not project source). The pre-commit hook blocks it. Use
`SKIP_PROTECTION=1 git commit` if you agree. A peer lane also left
`Docs/GITIGNORE_UNION_PROPOSAL_2026-08-20.md` untracked — reconcile both together.

---

## 2. Claireon — where it actually stands

**Nothing has been built or executed.** All prep, no bring-up.

Done:
- `Claireon` + 12 engine-bundled deps declared in `BS_GodFile.uproject` (72 plugins)
- `.claireon/launch_editor.json` — proxy `launch_editor` contract
- `Scripts/LaunchEditor.ps1` — build + launch with `-StartMCPServer` (syntax now valid)
- Isolated worktree: `C:\EnvironmentPortfolio\Melodia_ClaireonTest`, branch
  `claireon-test`, pinned at `010d8f50`
- Echo stage `claireon_bringup` with gates `claireon_build`,
  `claireon_server_bind`, `claireon_tool_discovery`, `claireon_python_roundtrip`
  (all non-blocking; the four completion gates still PASS)

Deterministic ports (SHA-256 of canonical root → 49152-65535):

| Worktree | Port |
|---|---|
| `BS_GodFile` (main) | 64998 |
| `Melodia_ClaireonTest` (test) | **57818** |
| Proxy registration (fixed) | 43017 |

### Next action — exactly this, in the test worktree only

```powershell
cd C:\EnvironmentPortfolio\Melodia_ClaireonTest
# 1. Set UEBlueprintMCP to "Enabled": false in BS_GodFile.uproject  (see §5)
# 2. Build
& Plugins\Claireon\Scripts\Utilities\Invoke-EditorBuild.ps1
# 3. Record the outcome either way
python Tools\echo_run.py record claireon_build pass|fail --note "UE 5.8 build result"
```

**A build failure is a legitimate, valuable outcome.** Upstream has open bugs for
UE 5.7+ builds (issue #6) and `bp_compile` hangs (issue #7), and there is no
public record of any UE 5.8 Claireon build. File the result upstream. Do not
work around a failure to force a green.

---

## 3. Ollama — fixed, with one caveat

### What was wrong
Not crashes. `%LOCALAPPDATA%\Ollama\server.log` shows
`timed out waiting for llama-server to start: context canceled`.
`F:\OllamaModels` reads at **32 MB/s** (HDD). Cold loads: 6.7B = 98s,
7B = 251s, 14B = 284s. The harness used a 180s timeout. Everything larger "failed."

The `NTSTATUS 0xffffffff` string I chased earlier was a *symptom*, not the cause.
**Always read `server.log` first.**

### What was applied
`Tools/fix_ollama_setup.ps1` (USER scope, persistent, no admin):
`OLLAMA_LOAD_TIMEOUT=30m`, `OLLAMA_KEEP_ALIVE=30m`,
`OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_FLASH_ATTENTION=1`.
`OLLAMA_MODELS` untouched. Ollama was restarted; settings are live.

Verified after restart:

| Model | load | output |
|---|---|---|
| `qwen2.5-coder:7b` | 250.6s | `"OK"` — coherent, `done_reason: stop` |
| `qwen2.5-coder:14b` | 284.5s | `"8888888..."` — **garbage** |

### CAVEAT: qwen2.5-coder:14b is corrupt
Separate defect, not the timeout. It loads then emits repeated-token garbage for
every prompt (0/8, all unparsed). Isolated to that model — 7b on identical
config/store is coherent, and the two tags don't share exclusive blobs.

`Saved/Audit/claireon_probe_qwen2.5-coder_14b_2026-08-20.json` is flagged
`INVALID: true` / `do_not_cite: true`. **Do not cite it as a model result.**

Fix: `ollama rm qwen2.5-coder:14b && ollama pull qwen2.5-coder:14b`, then smoke
test coherence *before* benchmarking. If it still emits `8888...`, run `chkdsk F:`.

### Not fixed: the disk
Config makes loads survive, not fast. A full `--all` sweep is ~45-60 min, almost
all disk I/O. Durable fix is moving the store to an SSD — blocked: C: 22G free,
F: 32G, G: 0G, store is 66G of blobs.

**Correction to an earlier claim of mine:** I said deleting a duplicate Muse tag
frees ~42GB. That is wrong. Reading the manifests, `muse-glimmer-30b:latest` and
`hf.co/bartowski/Muse-Glimmer-30B-GGUF:Q4_K_M` share **all 5 blobs** — deleting
either frees zero bytes. To reclaim you must remove all three Muse tags (~17-21GB
total). `ollama list` sizes are misleading; verify with `du -sh`.

---

## 4. Emails — a live over-claim was removed

Two drafts (`EMAIL_DRAFTS_2026-08-20.md`, `STUDIO_NOUS_RESEARCH_DRAFT.md:87`) led
with:
```
Hermes 3 8B: 98.8% TCA, 100% PAR, 95.5% SCR, 91.0% RCF, 85% token reduction
LongCat 14B: 99.2% TCA, 97.5% SCR
```
Those were **formally withdrawn on 2026-08-19** by your own whitepaper
(`Docs/melusina-agent-harness.html:468-478`): *"withdrawn and unpublished — it was
never backed by a committed run log."* They were still the headline aimed at a
research lab that would ask for the log.

Replaced with numbers that each have a file in `Saved/Audit/`:

| Claim | Evidence |
|---|---|
| Self-eval 31/32, TCA 100% | `math_run_latest.json` |
| qwen2.5-coder:7b 21/32, TCA 90.3% | `math_run_qwen2.5-coder_7b_2026-08-20.json` |
| qwen3.8-27b 21/32, TCA 81.2%, TER 3.18 | `math_run_qwen3.8-27b_2026-08-19.json` |
| muse-glimmer-30b 0/32 | `math_run_muse-glimmer-30b_2026-08-19.json` |
| Ledger 41 rows (32 pass, 9 fail) | `Saved/gate_ledger.json` |

Send-ready bodies now exist for: Nous, NVIDIA, OpenCode, Certain Affinity,
Infold, Velan. Only `[[...]]` fields need your input. **Nothing was sent** — per
the outreach skill, drafts require your explicit approval.

⏰ **NVIDIA JR2023172 deadline was Aug 21** — check whether that has passed.

---

## 5. Open decisions for you

1. **`.gitignore`** — owner-protected, still unstaged. Ignores `Plugins/Claireon/`.
2. **UEBlueprintMCP is still enabled** in `.uproject`. Your own docs
   (`OPENCODE_TECHNICAL_OBSERVATIONS.md:24`) record it as permanently disabled
   (untrusted); Claireon's README says never run both — two unsandboxed Python
   execution surfaces. Must be off before Claireon's first launch. I did not
   change it; it's a policy call.
3. **Disk space** — every drive effectively full. Blocks the real Ollama fix and
   will block UE builds soon.

---

## 6. Files created/modified today (my lane)

New:
```
.claireon/launch_editor.json
Scripts/LaunchEditor.ps1
Tools/test_claireon_toolcalls.py
Tools/fix_ollama_setup.ps1
Docs/CLAIREON_PREP_2026-08-20.md
Docs/CLAIREON_PROBE_RESULTS_2026-08-20.md
Docs/MELUSINA_CLAIREON_INTEGRATION_PLAN.md
Docs/OLLAMA_SETUP_FIX_2026-08-20.md
Docs/Handoffs/SESSION_HANDOFF_CLAIREON_2026-08-20.md   (this file)
```

Modified:
```
BS_GodFile.uproject          +12 Claireon deps
specs/echo_pipeline.json     +claireon_bringup stage
Docs/Career/EMAIL_DRAFTS_2026-08-20.md
Docs/Career/STUDIO_NOUS_RESEARCH_DRAFT.md
.gitignore                   (uncommitted — owner-protected)
```

Regenerated (gitignored, not committed): `Saved/t3d-catalog.html`,
`Saved/agent-dashboard-t3d.html`, `wix/` copies of both, `Saved/Echo/state.txt`.

---

## 7. Recommended order next session

1. Commit the 5 uncommitted files (§1). Decide on `.gitignore`.
2. `ollama rm qwen2.5-coder:14b && ollama pull qwen2.5-coder:14b`; smoke-test
   coherence before any benchmark.
3. Coherence smoke test on every other large tag — the corruption may not be
   isolated. One `"say OK"` call each, ~5 min per cold load.
4. `python Tools/test_claireon_toolcalls.py --all --timeout 1200` in background
   with `notify_on_complete` (~45-60 min).
5. Disable UEBlueprintMCP in the test worktree, then attempt the Claireon build.
   Record `claireon_build` pass **or fail**.

## 8. Lessons worth keeping

- Read the service's own log before trusting an API error string. `NTSTATUS
  0xffffffff` sent me down a driver rabbit hole; `server.log` said "timed out" in
  plain English.
- A model that loads is not a model that works. Smoke-test coherence before
  scoring — otherwise you file storage corruption as a capability result.
- `ollama list` sizes are per-tag, not per-blob. Read manifests for disk math.
- PowerShell: `"C: has..."` in double quotes is a parse error, and a stray
  backtick-quote in an array silently breaks the whole script. Syntax-check
  generated `.ps1` with `[Parser]::ParseFile` before committing — I shipped a
  broken `LaunchEditor.ps1` in `119d492c` and only caught it on review.
- This repo has concurrent agent lanes. Re-check `git log`/`git status` before
  every commit; re-apply your own edits idempotently rather than clobbering.

