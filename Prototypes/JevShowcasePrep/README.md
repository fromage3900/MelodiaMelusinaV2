# Jev Showcase Prep Conductor (isolated prototype)

Jev picks the next showcase asset-prep step from 8 authored actions. Code reads
state, Jev judges, humans execute. Nothing here writes `.umap` or `.uasset`
files, the editor, or the gate ledger. Delete this folder to remove it.

Owner decision: **six** showcase levels, recorded as the `LEVELS` tuple in
`jev_showcase_prep.py`.

- `/Game/Melodia/Characters/Melusina/Portfolio/L_MelusinaPortfolioCapture`
- `/Game/Melodia/Levels/Opening/L_MelusinaMorning`
- `/Game/EnvSandbox/Environments/L_FallenMoon`
- `/Game/EnvSandbox/Environments/L_KaleidoNave`
- `/Game/ZenForestTest`
- `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`

## Isolation contract

- This folder does not write `.umap` or `.uasset` files.
- It does not mutate the Unreal editor, Blender, `Config/DefaultEngine.ini`, or `Saved/Audit`.
- `classical-fallback` is deterministic and is not Jev evidence.
- Every decision records `source=jev-live` or `source=classical-fallback`.
- Unknown state stays `None`. The conductor does not invent zeros.

## Run

From `BS_GodFile`:

```
python -m pytest Prototypes/JevShowcasePrep/test_jev_showcase_prep.py -q
python Prototypes/JevShowcasePrep/assemble_showcase_state.py 60
```

`assemble_showcase_state.py` is read-only. It reads
`Saved/Audit/showcase_prep_2026-09-21/*.json` when that folder exists, plus
git dirty count, free space on `C:`, and whether `127.0.0.1:9316` accepts a
connection. Then it prints the state and `hud(triage(...))`.

Without `TYPESAFE_API_KEY`, triage stays on `classical-fallback`. With the key
set, the same call goes live (`jev-live`). The key is read from the environment
only and is never printed or written.

## Files

- `jev_showcase_prep.py` — closed action set, six-level `LEVELS`, `ShowcaseState`,
  Choice+Noul+Score in one `system_one` call, classical fallback, cooldown, HUD.
- `assemble_showcase_state.py` — read-only receipt and machine readers.
- `test_jev_showcase_prep.py` — authored-only tests. No network. No key required.

## Fallback

When most of the state is unknown, the fallback audits the hair chain if hair
flags are unknown, otherwise material instances on the capture level. It holds
when `C:` has under 20 GB free. `COOK_TO_G` only when every level is L3.
`RENDER_PROOF` only when the focused level is L2. `APPLY_FIX` only when a
receipt names an open defect.

Score: L0 blocking defects, L1 audited with open fixes, L2 clean audits no
proof, L3 clean + render proof on disk.
