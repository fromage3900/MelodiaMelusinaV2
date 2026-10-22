# Local Work Sync Report — 2026-10-01

## Summary

Scanned all uncommitted local work in BS_GodFile and synced to git in isolated
batches. Perforce pending CLs left on hold pending owner approval.

## Starting State

- **Branch:** `docs/honcho-discord-sync` (ahead 2, behind 0)
- **Modified tracked:** 66 files (uasset LFS pointers, CURRENT_STATE.md, BS_GodFile.uproject, import_cascadeur_anim.py)
- **Untracked:** 377 files
- **P4 opened:** 184 files (112 add, 66 edit, 1 in CL 265)
- **P4 pending CLs:** 6 (all marked HOLD/REVIEW/SHELVE ONLY)

## Git Batches Committed

| # | Commit | Files | Description |
|---|--------|-------|-------------|
| 1 | f70881a8e | 5 | docs: Humber prep drafts, AIRI handoff, choral sheep weekly handoff |
| 2 | 3fc044121 | 5 | tools: choral sheep bake variants, echo reflex specs, cascadeur skeleton |
| 3 | 36f911722 | 15 | prototypes: EchoReflex, Jev audit/conductor/showcase prep scripts |
| 4 | 80b9d3130 | 102 | skills: Higgsfield agent skill suite (8 skill dirs) |
| 5 | 4d32d5b61 | 3 | chore: CURRENT_STATE.md, uproject, cascadeur import script |
| 6 | 9aa12c018 | 1166 | plugin: AscentCombatFramework source (18 modules) |
| 7 | 49950a848 | 64 | chore: 64 tracked files (uasset LFS pointers) |
| 8 | ef82d04af | 1 | chore: ignore scratch/IDE files (.gitignore) |
| 9 | 16dbd0d64 | 100 | plugin: AscentCombatFramework Resources + MelusinasStudy blend |

**Total:** ~1461 files landed across 9 commits.

## Remaining Untracked (at time of report)

- 342 Content/ files — gitignored by design, already opened in p4
- Plugins/AscentCombatFramework/Content/ — 1.4GB, 1446 uasset files
- Plugins/AscentCombatFramework/Source/AscentDialogueSystem/ — 5 zero-byte AI files
- Reference/ — 106MB, 247 files (LoL reference meshes)
- Docs/AIRI/MelusinaCard/ — 8KB (has a .zip the hook rejects)
- Content/_PROJECT/MelusinasHouse/SM_BézierCurve_003_fbm/ — 1 file

## Perforce State

- 184 files opened (112 add, 66 edit, 1 in CL 265)
- 6 pending CLs, ALL marked HOLD/REVIEW/SHELVE ONLY — none submitted
- CL 267: MelodiaIntegrationMap shared edit — HOLD
- CL 265: uproject text-config — HOLD (ACFU enable)
- CL 264: stock template BPs — REVIEW BEFORE SUBMIT
- CL 235: single-copy protection — SHELVE ONLY
- CL 227: align p4 with origin/main — pending
- CL 224: choral sheep ABP resave — pending

## Pre-Commit Hook Rejections Encountered

- .zip files (Docs/AIRI/MelusinaCard/Generated/Melusina.airi-card.zip, AutoLayout.zip)
- .pyc files (Prototypes/__pycache__/)
- .blend1 backup files
- Zero-byte files (AscentDialogueSystem AI/)

All were excluded from their respective batches and the commits succeeded.

## Notes

- Another lane landed commit 121862ae8 mid-session (feat(anim): bow hold clip)
- The .gitignore was updated to ignore scratch/IDE files (.vscode, .gemini, *.uproject.bak, branch_triage_*.json, skills-lock.json, run_build_*.bat, run_launch_*.bat, hda/backup/)
- SKIP_PROTECTION=1 was used for the .gitignore change (owner-approved)
