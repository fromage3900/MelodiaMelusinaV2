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

1. Review [README.md](README.md) to choose your onboarding path.
2. **Environment & Level Designers:** Follow [Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md) for lightweight sparse checkout.
3. **Engineers & Researchers:** Clone the repository and pull only the Git LFS assets needed for the
  chosen lane. `Exports/` is also seeded in the local Perforce pilot; use Git for the project checkout
  until the shared Perforce server and cutover are announced.
4. Execute `deploy/validate_setup.ps1` (or `python Tools/test_melodia_mcp.py`) to verify your local environment health.

---

## Branch Naming

```
feature/<feature-name>       — new functionality or systems
fix/<bug-description>        — bug and regression fixes
docs/<documentation-target>  — documentation updates and whitepapers
cleanup/<area>               — repository and pipeline hygiene
collab/<role>/<task>         — collaborative environment art, level design, or UI
```

Examples:
- `feature/zundamon-npc`
- `fix/modifier-stacking`
- `docs/melusina-agent-harness`
- `collab/level-design/kaleido-nave`

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
and project metadata. Perforce is the intended authority for large and lock-sensitive art paths.
The local pilot has seeded `//melodia/Exports/...`, but it is not a shared collaborator server yet.

- Do not modify an asset through both Git and Perforce.
- Do not add `Content/`, `Exports/`, or `RawArt/` to an automated Git commit batch.
- Before committing text-only work, run `python Tools/source_control_triage.py` to review its batch.
- To commit an approved isolated batch, add exact paths to `specs/source_control_batches.json`, mark the
  batch `ready`, then run `python Tools/source_control_triage.py --commit-ready <batch-name>`.

The scheduled task `Melodia Source Control Triage` produces this report every 12 hours without staging,
committing, pushing, or deleting files. Perforce setup and cutover conditions are recorded in
[Docs/PERFORCE_MIGRATION_PLAN_2026-08-13.md](Docs/PERFORCE_MIGRATION_PLAN_2026-08-13.md).

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
