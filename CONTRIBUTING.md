# Contributing to Melodia

```
✧ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧
```

Welcome! This guide outlines how to contribute to Melodia — whether you are an environment artist, technical designer, gameplay engineer, or AI researcher.

---

## Code of Conduct

All contributors are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it to understand our community standards and enforcement guidelines.

---

## Quick Start

1. Read [CURRENT_STATE.md](CURRENT_STATE.md), [DOC_INDEX.md](DOC_INDEX.md), and [Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md](Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md) before expanding scope.
2. Run `python Tools/git_ok.py`, verify the latest `main` Echo run is green, and cut one scoped branch from current `main`. Do not start production from a stale PR/recovery branch.
3. Review [README.md](README.md) to choose your onboarding path.
4. **Environment & Level Designers:** Follow [Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md) for lightweight sparse checkout.
5. **Engineers & Researchers:** Clone the repository for engineering/configuration work. Perforce is now
  in **active pilot**: UE 5.8 is connected and source-control operations are working. `Exports/` is
  seeded in the depot. Do not assume full creative-root cutover yet; check
  `specs/source_control_ownership.v1.json` before deciding whether Git/LFS or Perforce owns an asset.
6. Execute `deploy/validate_setup.ps1` (or `python Tools/test_melodia_mcp.py`) to verify your local environment health.

---

## Production Governance

`main` is canonical durable game/runtime/capstone truth. Feature branches are scoped work, not competing project state.

Read [Docs/Production/BRANCH_WORKSTATION_POLICY.md](Docs/Production/BRANCH_WORKSTATION_POLICY.md) before merge, salvage, deletion, or machine-specific branch work.

### Default contribution mode: content production

Melodia's stable systems are now infrastructure for authored work. Prefer the existing seam that already owns the problem:

| Goal | Default authoring seam | Do not add |
|---|---|---|
| New environment / world slice | recipe + World Compiler + existing UE PCG | second compiler / parallel world authority |
| Reactive world look | existing audio-reactive → cymatics writer chain + material/Niagara consumers | direct MPC writers |
| Blender/GN set dressing | Melodia Studio/GN source → fresh-main promotion PR | wholesale workstation-branch merge |
| Encounter / boss / side quest | Quill + Phoenix + rhythm + existing consequence/save owners | new battle/quest/save framework |
| Lookdev / VFX polish | existing master materials, instances, Niagara, frozen PPV rules | one-off master/framework per effect |
| Houdini / Hython source generation | deterministic tools under `Tools/Houdini/` + manifested outputs -> existing UE/world lane | Houdini as runtime authority / untracked one-off DCC pipeline |
| Melusina Rokoko mocap | Blender retarget/root-motion export -> guarded `Content/Python/import_rokoko_mocap_batch.py` -> existing ABP/state owner | manual production FBX drag/drop / second skeleton/import lane |
| UE C++ engineering | JetBrains Rider owner/usages discovery -> focused native edit -> correct UBT/test/runtime evidence | C++ rewrite of an existing content/Python/Blueprint-owned lane |

A contribution that changes architecture must name the current owner seam, show the blocking requirement, and explain why authored content cannot express it.

### Editor-heavy session rule

For UE/Blender lookdev and worldbuilding, cut a short-lived `feature/<intent>-<date>` branch from green `main`. Do not merge/rebase/switch branches while live editor state is open. Commit intentional slices, close the editor, run the relevant proof + Echo/LFS gates, merge, and start the next session from refreshed `main`.

### No unrequested cleanup

Repository cleanup is not a default contribution category. Cleanup must resolve a concrete blocker, integrity risk, discoverability failure, or verified duplicate authority. Do not open broad formatting/refactor/branch-count work simply because it is available.

### Branch roles

Classify non-main branches before acting on them:

- **ACTIVE** — current scoped implementation;
- **CANONIZED** — meaningful work already contained in `main`;
- **WORKSTATION** — intentional parallel production lane;
- **RECOVERY** — selective salvage source;
- **OPERATIONAL** — infrastructure intentionally outside `main`;
- **UNKNOWN** — investigate before merge or deletion.

`collab/laptop/longterm` is the preserved ASUS laptop Blender / Geometry Nodes WORKSTATION lane. Do not auto-delete it and do not wholesale-merge it over current `main`.

### Evidence ladder

Use the weakest accurate claim:

`SOURCE PRESENT → SOURCE BUILT → LIVE PROVEN → RESTART PROVEN → PACKAGED PROVEN → PORTFOLIO APPROVED`

Reference art is not runtime proof. A committed asset is not automatically live-proven. A TD visual does not create gameplay truth.

### Capstone bias

Contributions should preferentially improve visible/playable/presentable capstone proof. Infrastructure work should be bounded to the blocker it removes.

---

## Branch Naming

```
feature/<feature-name>       — new functionality or systems
fix/<bug-description>        — bug and regression fixes
docs/<documentation-target>  — documentation updates and whitepapers
cleanup/<area>               — repository and pipeline hygiene
collab/<role>/<task>         — collaborative environment art, level design, or UI
integration/<topic>           — reviewed recovery/integration lanes shared across workstations
recovery/<machine>/<topic>    — preserve divergent machine work before reconciliation
```

Examples:
- `feature/zundamon-npc`
- `fix/modifier-stacking`
- `docs/melusina-agent-harness`
- `collab/level-design/kaleido-nave`
- `integration/laptop-house-recovery-20260904`
- `recovery/laptop-main-20260904`

---

## Commit Conventions

We follow standard Conventional Commits:

```
<type>: <short imperative description>

Examples:
  feat: add Zundamon NPC Blueprint with quest giver interface
  fix: correct multiplicative modifier stacking in battle controller
  docs: add Melusina Agent Test Harness evaluation whitepaper
  chore: update .gitignore for loose scratch binaries
```

Allowed types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `style`.

---

## Pull Request Process

1. **Branch:** Create a branch from `main` using the naming convention above.
2. **Focus:** Keep commits focused, clean, and atomic.
3. **Validate:** Run test suites locally (`python Tools/test_melodia_mcp.py` and workspace validators).
4. **Open PR:** Submit a Pull Request against `main` detailing what was changed and why.
5. **Review:** Wait for automated CI status checks and maintainer review before merge.

## Source Control Workflow

Git is the authority for `Source/`, `Plugins/`, `Config/`, `Tools/`, `Docs/`, `deploy/`, `specs/`,
project metadata, and **`Content/Python/` editor/PCG automation source**. Perforce is the intended
authority for large and lock-sensitive creative content. The nested Git exception is explicit in
`specs/source_control_ownership.v1.json`; do not migrate `Content/Python/` into Perforce.

Current state: **`active_pilot`**. UE 5.8 is connected to Perforce and source-control operations are
working in-editor; `//melodia/Exports/...` is seeded. This is production-capable pilot evidence, but it is
not yet a claim that all `Content/`, `Exports/`, and `RawArt/` paths have completed cutover.

Cutover states are intentionally explicit:

`planned → active_pilot → production → cutover_complete`

- `active_pilot`: UE↔Perforce works; Git/LFS overlap or missing cross-workspace proof may remain.
- `production`: declared creative roots use Perforce normally, with World Partition and second-workspace round trips verified.
- `cutover_complete`: `python Tools/validate_source_control_ownership.py --check-cutover` passes and no target Perforce path remains Git-owned.

- Do not modify an asset through both Git and Perforce.
- Do not add Perforce-owned `Content/`, `Exports/`, or `RawArt/` paths to an automated Git commit batch.
  `Content/Python/` is the explicit Git-owned exception.
- Before committing mixed working-tree work, run `python Tools/triage_working_tree.py --print-paths`.
  It is report-only: it never stages, commits, pushes, deletes, resets, or stashes.
- `specs/source_control_batches.json` is retained as an owner-reviewed batch manifest only; it does not
  authorize a commit by itself.

The canonical cutover state and evidence gates live in
[`specs/source_control_ownership.v1.json`](specs/source_control_ownership.v1.json) and are enforced by
[`Tools/validate_source_control_ownership.py`](Tools/validate_source_control_ownership.py).

---

## File Ownership & Architecture Boundaries

| Subsystem / Area | Component Scope | Review Required? |
|------------------|----------------|:----------------:|
| `Plugins/MelodiaCore/` | Native C++ Subsystems & Substrate Shaders | Yes |
| `deploy/melodia_mcp_server.py` | Model Context Protocol & Tool Registry | Yes |
| `Content/Python/gmm/` | GMM Gameplay Automation & Fixtures | Yes |
| `deploy/surreal_arch/` | Procedural Geometry & Blender Bridge | Yes |
| `Docs/` | Technical Whitepapers & Specifications | No |
| `Tools/` | Test Scripts, Diagnostic Probes, Linting | No |

---

## Asset Naming Conventions

Follow the canonical asset hierarchy:

| Prefix | Asset Type | Example |
|:------:|:-----------|:--------|
| `MF_` | Material Function | `MF_Triplanar` |
| `M_` | Master Material | `M_Master_Toon_Universal` |
| `MI_` | Material Instance | `MI_Show_CelestialNebula` |
| `BP_` | Blueprint Actor / Component | `BP_Zundamon_NPC` |
| `L_` | Canonical Level Map | `L_MelusinaMorning` |
| `WP_` | World Partition Level | `L_WP_SakuraDream` |
| `SK_` | Skeletal Mesh | `SK_Melusina_Rig` |

---

## Prohibited Artifacts (What NOT to Commit)

Do NOT commit:
- `.blend1`, `.blend2` backup files (auto-ignored).
- `Intermediate/`, `Saved/`, `Binaries/` Unreal build artifacts (auto-ignored).
- Ephemeral root probes or scratch diagnostic scripts (`check_bp*.py`, `pie_smoke*.json`).
- Archive bundles (`.zip`, `.7z`, `.bundle`).
- Secret keys, local tokens, or `.env` files.

---

## Security Disclosures

If you discover a security vulnerability, please refer to our [Security Policy](SECURITY.md) and report it to [melodia-security@brennanshepherd.com](mailto:melodia-security@brennanshepherd.com).

---

## Documentation & Help

- Complete Documentation Index: [DOC_INDEX.md](DOC_INDEX.md)
- Agent Test Harness Whitepaper: [Docs/MELUSINA_AGENT_TEST_HARNESS.md](Docs/MELUSINA_AGENT_TEST_HARNESS.md)
- LLM Daemon Ecosystem Report: [Docs/OLLAMA_UE5_INTEGRATION_REPORT.md](Docs/OLLAMA_UE5_INTEGRATION_REPORT.md)
- Live Collaboration Setup: [Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md)
