# CI reality audit — 2026-08-14

Read-only audit of GitHub Actions reality for this repo. Nothing was modified.
All facts below were pulled live from the GitHub API via `gh` (authenticated),
except where noted as local filesystem state.

**Verdict up front: the CI lane has never produced runtime evidence. Zero of
128 workflow runs in repo history has concluded `success`.**

---

## 1. Runner

Registered: **yes**, exactly one runner.

| Field | Value |
|---|---|
| Name | `melodia-v2-win` |
| Labels | `self-hosted`, `Windows`, `X64`, `UE58` |
| Status | **offline** (busy: false) |

The runner picked up jobs earlier (its logs show checkouts at
`C:\actions-runner\_work\MelodiaMelusinaV2\...` — it is this machine). The last
completed job ran ~06:08Z on 2026-08-14. Since ~16:51Z the same day, 24+24 runs
have sat **queued** because the runner is offline. A queued run means "no
matching runner", not "workflow bug".

## 2. Run history — the whole repo

`GET /actions/runs?per_page=100` (2 pages) → `total_count = 128`, all dumped.

**Aggregated conclusions: 78 `failure`, 2 `cancelled`, 48 `queued` (empty
conclusion). `success`: 0.**

| Workflow (registered id) | Runs | Green | Notes |
|---|---|---|---|
| Echo Static Gates — `echo_gates.yml` (332212214) | 65 | **0** | 40 fail, 1 cancelled, 24 queued |
| Unreal Build + Tests — `unreal_build.yml` (332186401) | 63 | **0** | 38 fail, 1 cancelled, 24 queued |
| Release Tag (on demand) — `release_tag.yml` (332212215) | **0** | **0** | `gh run list --workflow=332212215` returns `[]` — never dispatched |
| Melodia BuildGraph / Gauntlet — `melodia_buildgraph.yml` | **0** | **0** | **not on the remote** — untracked local file (`git status` = `??`), never pushed |
| Melodia AWS artifact publish — `melodia_aws_publish.yml` | **0** | **0** | **not on the remote** — untracked local file, never pushed |

The remote `.github/workflows/` contains exactly three files
(`GET /contents/.github/workflows`): `echo_gates.yml`, `release_tag.yml`,
`unreal_build.yml`. The two "Gauntlet/ AWS" workflows exist only in this
working tree.

### Sample failure evidence (run logs)

- Run 31774815839 (Unreal Build, 2026-08-14T06:00Z, `feature/repo-lockin-20260813`):
  failed at `actions/checkout@v4` —
  `fatal: unable to access 'https://github.com/fromage3900/MelodiaMelusinaV2/': Failed to connect to github.com port 443`
  (3 retries, 20s/14s backoff). Build/LFS/pytest/ruff steps all skipped.
- Run 31774815783 (Echo Gates, same commit): failed at "Static gate sweep
  (headless)"; the ledger upload step then warned
  `No files were found with the provided path: Saved/gate_ledger.json` —
  **CI has never uploaded a gate ledger artifact.** Therefore
  `release_tag.yml`'s `dawidd6/action-download-artifact` step can never find
  one, and even a green echo run would never have written one (the record step
  is skipped when the sweep fails).

### What the ledger rows in AGENTS.md are NOT

`runtime`, `save_load`, `package_launch` "pass" rows come from local
owner-verified editor runs (`Saved/gate_ledger.json` on this machine). They are
not CI evidence and no workflow has ever produced or uploaded them.

## 3. The Gauntlet node — what it actually does

`BuildGraph/MelodiaBuildGraph.xml:32-35` runs the `Gauntlet` node, which spawns:

```
powershell -NoProfile -ExecutionPolicy Bypass -File deploy\BuildGraph\Invoke-UATIsolated.ps1
  -Task Gauntlet -ProjectFile <root>\BS_GodFile.uproject
  -UATBat "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat"
  -ArchiveDir <root>\Products\Builds\BuildGraph -ProjectRoot <root>
```

`Invoke-UATIsolated.ps1` (Task=Gauntlet branch, lines 40-47) then runs:

```
RunUAT.bat RunUnreal -NoMutex -project=<root>\BS_GodFile.uproject -platform=Win64
  -configuration=Development -test=UE.TargetAutomation
  -Build=<ArchiveDir>\Windows -packaged -RunTest=Project
  -skipdeploy -unattended -log -MaxDuration=120
```

- **Executes:** `UE.TargetAutomation` test controller, `Project` test group,
  against the packaged Development build staged at
  `Products\Builds\BuildGraph\Windows` (depends on the `CookPackage` node
  having run first, which is `BuildCookRun ... -cook -build -stage -pak -archive`).
- **Emits:** nothing structured. The complete UAT stream is redirected
  (lines 54-55) to
  `Saved\Integration\BuildGraph\Gauntlet_<UTCstamp>.{stdout,stderr}.log` inside
  the **runner workspace** — these logs are not part of any CI artifact.
  Node success = UAT exit code 0 only (lines 57-63).
- **Where artifacts land:** `PublishArtifact` (XML:37-43) tags
  `$(ArchiveDir)\**\*.*` = `Products\Builds\BuildGraph` (cooked/staged package
  + `melodia_artifact_manifest.json`). The workflow's upload step
  (`melodia_buildgraph.yml`) uploads only `Products/Builds/BuildGraph`.
  Gauntlet's test results are **not** in it.

## 4. Gauntlet → gate row linkage

**None. Confirmed by grep, not by assumption.**

- `grep -ri gauntlet Tools/` → no matches (any file type).
- `grep -r TargetAutomation|Integration\BuildGraph|melodia_artifact_manifest|Saved\Automation` over all `*.py` → no matches.
- Only `.github/` match is the **untracked** `melodia_buildgraph.yml` (it
  invokes the graph; nothing consumes its output).
- `echo_gates.yml` records only `static_gates` rows via `Tools/record_gate.py`
  (line 117); `release_tag.yml` verifies only the four completion gates
  (`runtime`, `save_load`, `repeat_consume`, `package_launch`) against the
  ledger artifact (line 51).

No code path reads Gauntlet's exit code or logs into `gate_ledger.json` or
`Saved/Echo/state.txt`. The BuildGraph `Gauntlet` node is a dead-end lane: its
output has no consumer.

---

## Summary table

| Workflow | Last successful run | What it proves |
|---|---|---|
| `echo_gates.yml` | **never** (0/65) | No static gate has ever passed in CI; no CI-produced ledger row/artifact |
| `melodia_buildgraph.yml` | **never** (never on remote) | The Gauntlet lane has never executed on GitHub |
| `melodia_aws_publish.yml` | **never** (never on remote) | No AWS publish ever ran |
| `unreal_build.yml` | **never** (0/63) | No UE build/test ever completed in CI |
| `release_tag.yml` | **never** (0 runs) | No release ever gated or tagged by CI |

## The single fact that settles it

Of 128 workflow runs in the repo's entire history, **zero** have conclusion
`success` (78 failed, 2 cancelled, 48 queued behind the offline runner) — and
the only lane that could produce runtime evidence
(`melodia_buildgraph.yml` → `Gauntlet`) is an untracked file that was never
pushed, so it is not even registered on the remote. Any claim that "the build
is green" or that a completion gate was certified by CI is false on its face;
all gate evidence to date is local and owner-verified, none of it CI.

## Reproduce

```
gh api repos/:owner/:repo/actions/runners --jq '.runners[] | {name, labels: [.labels[].name], status}'
gh api repos/:owner/:repo/actions/runs?per_page=100 --jq '.workflow_runs[] | [.id, .workflow_id, .status, .conclusion, .created_at, .head_branch] | @tsv'
gh api repos/:owner/:repo/actions/workflows --jq '.workflows[] | {id, name, path}'
gh api repos/:owner/:repo/contents/.github/workflows --jq '.[].name'
```
