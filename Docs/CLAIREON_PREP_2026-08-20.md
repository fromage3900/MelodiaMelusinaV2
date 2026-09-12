# Claireon Prep & Test Ledger — 2026-08-20

Evidence-backed record of Claireon integration prep. Every claim below has a
verifying command. Nothing here asserts Claireon is running — it is not built yet.

## 1. Baseline: what Claireon actually was on disk

| Check | Result | Verified by |
|---|---|---|
| Plugin present | `Plugins/Claireon/`, v2.1.0, 1738 files, 74M | `find Plugins/Claireon -type f \| wc -l` |
| Nested git repo | YES — clone of `believer-oss/Claireon.git` @ `ed0b457` | `git -C Plugins/Claireon log --oneline -1` |
| `Installed` flag | `false` in `Claireon.uplugin` | `read Claireon.uplugin:12` |
| Built binaries | NONE in `Binaries/Win64/` | `ls Binaries/Win64 \| grep -i claireon` |
| Server ever started | NO — `Saved/Claireon/` does not exist | `ls Saved/Claireon` |
| Launch config | NO — `.claireon/` did not exist | `ls .claireon` |
| In `.uproject` | NO | `grep Claireon BS_GodFile.uproject` |

Verdict: source-only checkout, never built, never run.

## 2. Deterministic ports (SHA-256 of canonical root, folded into 49152-65535)

| Worktree | Port |
|---|---|
| `C:\EnvironmentPortfolio\BS_GodFile` (main) | **64998** |
| `C:\EnvironmentPortfolio\Melodia_ClaireonTest` (test) | **57818** |
| Proxy registration (fixed, per-machine singleton) | 43017 |

Reproduce: `python Tools/test_claireon_toolcalls.py` prints the port for its own worktree.

## 3. Dependency audit

Claireon declares 17 plugin deps. 12 were missing from `.uproject`; all 12 resolve
to engine-bundled plugins under `C:\Program Files\Epic Games\UE_5.8\Engine\Plugins`.
Nothing needs downloading.

Added to `.uproject`: Claireon, GameplayAbilities, Chooser, ModularGameplay,
ModelViewViewModel, MotionWarping, Niagara, NNERuntimeORT, PCG,
PropertyBindingUtils, SQLiteCore, StateTree.
(Metasound was already added by a concurrent lane; PythonScriptPlugin and
GameplayStateTree were already present.)

Optional deps NOT installed and not required: `Untested`, `BlueprintAssist`,
`GameplayCameras`, `LyraGame`.

## 4. Concurrent-lane collision (recorded, not hidden)

Mid-session another agent lane staged 517 files and rewrote `BS_GodFile.uproject`,
reverting my first pass. Rather than clobber it, I diffed and re-applied only the
still-missing entries.

- Other lane's additions, preserved and asserted intact: `EnhancedInput`,
  `MelodiaNPR`, `MelodiaWardrobe`, `Metasound`, `Oceanology_Plugin`.
- Main's HEAD moved `010d8f50` → `caee6389` during the session.
- The same lane also reverted my `.gitignore` edit; re-applied.

If `.uproject` loses Claireon again, that lane is the cause. The re-apply script is
idempotent — rerun it, do not hand-edit.

## 5. Git prep for testing

Per Claireon's own SECURITY.md (`python_execute` is unsandboxed, full filesystem
and network access), testing does not happen in the main checkout.

```
git branch claireon-test HEAD
git worktree add ../Melodia_ClaireonTest claireon-test
```

| Worktree | Commit | Branch |
|---|---|---|
| `BS_GodFile` | caee6389 | main (untouched by Claireon tests) |
| `Melodia_ClaireonTest` | 010d8f50 | claireon-test |

`.gitignore` additions: `Plugins/Claireon/` (vendored upstream clone, not project
source). `Saved/Claireon/` was already covered by the existing `Saved/` rule.

## 6. Files created / modified

| Path | Action |
|---|---|
| `BS_GodFile.uproject` | Modified — +12 Claireon deps (72 plugins total) |
| `.gitignore` | Modified — ignore `Plugins/Claireon/` |
| `.claireon/launch_editor.json` | Created — proxy `launch_editor` contract |
| `Scripts/LaunchEditor.ps1` | Created — build + launch with `-StartMCPServer` |
| `Tools/test_claireon_toolcalls.py` | Created — 2-tool discovery probe |
| `Docs/CLAIREON_PREP_2026-08-20.md` | This ledger |

## 7. CONFLICT: UEBlueprintMCP still enabled

`.uproject` has `UEBlueprintMCP` enabled (unauthenticated TCP, port 55558, ~60
tools including `load_blueprint_class` / `get_default_object` from Python).
Claireon's `python_execute` is the same class of surface.

Project precedent: `Docs/Career/OPENCODE_TECHNICAL_OBSERVATIONS.md:24` records
UEBlueprintMCP as "permanently disabled in `.mcp.json` (flagged as untrusted)".
Claireon's own guidance says never run it alongside UEBlueprintMCP.

**Action required before first Claireon run:** set `UEBlueprintMCP` to
`"Enabled": false`, or accept two unsandboxed Python execution surfaces on one
project. Not changed here — that is a project-policy call, not a prep step.

## 8. Remaining manual steps

1. Register in `C:/Users/froma/.mcp.json` (test worktree port):
   ```json
   "claireon": { "type": "http", "url": "http://127.0.0.1:57818/mcp" }
   ```
2. Build in the TEST worktree:
   `& Plugins/Claireon/Scripts/Utilities/Invoke-EditorBuild.ps1`
3. Launch with `-StartMCPServer`, or start proxy-first:
   `& Plugins/Claireon/Scripts/Utilities/Start-MCPProxy.ps1`
4. Confirm `Saved/Claireon/MCPServer.json` appears with a live port + PID.

## 9. Known upstream issues (from the project's own research doc)

`Docs/Research/UE_AGENT_BENCHMARK_DESIGN_2026-08-19.md` records two open
community bugs: `bp_compile` hangs (issue #7), and UE 5.7+ build errors (issue #6).
This project is UE **5.8** — no public record of a successful 5.8 Claireon build
exists. A build failure here is an expected outcome, and filing it upstream is a
real contribution rather than a setback.
