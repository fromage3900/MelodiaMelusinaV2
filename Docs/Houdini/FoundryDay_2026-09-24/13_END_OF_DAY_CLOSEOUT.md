# 13 — End-of-day closeout

| | |
|---|---|
| **Purpose** | Leave the college machine with every durable result committed, every heavy result accounted for, and nothing half-true in status. |
| **Authority** | Git pipeline law (`CLAUDE.md`): commit/push to **this branch only**, with owner permission for each push. No merge to `main` from the college machine, no rebase, no force-push. |
| **Status** | STAGED. |

## Checklist (agent runs it; Brennan approves the push)

1. **Stop heavy jobs or record them.** Any still-running bake gets a `HOLD` manifest with progress and the resume command.
2. **Verify everything:** `python Tools/Houdini/foundry/houdini_foundry.py verify` on every manifest produced today, then `python Tools/Houdini/foundry/test_houdini_foundry.py`, `python Tools/test_universe_foundry.py`, `python Tools/test_world_compiler.py`.
3. **Collect evidence** into `Saved/Audit/houdini_foundry/<recipe_id>/`: manifest copy, probe JSON, cook logs (trimmed), ≤ 1 MB previews, parity/seam reports.
4. **Stage deliberately:**
   ```powershell
   git status --short
   git status --ignored --short Tools/Houdini Saved/Audit/houdini_foundry hda
   git add -f Saved/Audit/houdini_foundry/<recipe_id>/...   # evidence (Saved/ is ignored)
   git add -f Tools/Houdini/<family>/<new_script>.py        # new tools (Tools/* is ignored)
   git add hda/<Name>_<ver>.hda recipes/houdini_foundry/... specs/houdini_foundry/...
   ```
   **Never** stage `Saved/HoudiniFoundry/**` caches, VDB sequences, FLIP/Vellum caches, `.bgeo.sc`, or PDG temp dirs. UE assets are staged only if saved intentionally for a gate.
5. **Large finals:** copy the chosen large outputs (not caches) to the transfer drive. Their sha256 is already in the manifests, so the PC can re-verify with `verify` after copying them to the same repo-relative paths.
6. **Update `CURRENT_STATE.md` in the same commit** as the evidence. Change only rows with new evidence, e.g. the Houdini Engine row to "LIVE PROVEN (smoke) — `Saved/Audit/houdini_foundry/hda_engine_smoke_arpeggio_stair/bake_manifest.json`". Write nothing for gates that did not finish.
7. **Update recipe `status`** (`staged` → `source_proven` / `live_proven`) only for recipes with verifying evidence.
8. **Commit** in coherent units (one per gate or product), e.g. `feat(houdini): HDA_Melodia_CrystalCathedral 1.0 + parity evidence`, `evidence(houdini): Gate 1 HDA Engine cook/bake/save/reload`.
9. **Push** `prep/houdini-foundry-college-2026-09-24` after the owner says so. Merging to `main` happens later from the desktop PC through a PR.
10. **Fold or retire this pack:** once merged, the durable parts (contracts, recipes, tool) stay. The dated gate docs become history, and `CURRENT_STATE.md` carries status. Delete `START_HERE_COLLEGE_HOUDINI_2026-09-24.md` in the merge PR unless the owner wants it kept.

## End-of-day report (paste into the PR / Hermes)

```text
Tier reached: Minimum | Strong | Exceptional | Stretch
Gates: 0 PASS/HOLD · 1 … · 11 …
Evidence: <paths>
Blockers hit: <B1..B4 or new>
Heavy outputs off-repo: <list + sha256 manifest paths>
Next session starts at: Gate <n>, step <m>
```
