# Iris texture confusion postmortem — 2026-07-13

## Live state at session close (v7)

| Mesh | Material | Maps |
|------|----------|------|
| `R_Iris.001` (back disc) | `Material.022` | `Material.020_*` |
| `R_Iris.002` (front disc) | `Material.023` + `Iris.002` | `Material.020_*` |

**Final call:** both discs use **`Material.020_*`** (UV-matched). `M_Iris_Back_*` / `M_Iris_front_*` stay on disk for UE — not primary on Blender `R_Iris.*`.

Paths: `Imports/MelusinaTextures/`

## Why this kept looping (agent failure)

Two **different true statements** collided, and the agent treated them as one flip-flop instead of locking a split assignment:

1. **UV match (Blender stage discs):** `Material.020_*` is authored for the Blender `R_Iris.*` UV layout. `M_Iris_front_*` is the UE/Substance front set and does **not** match those UVs well as a full replace on the front (documented earlier).
2. **User intent for back:** When the user says “iris back,” they mean **`M_Iris_Back_*` on the back disc** (`R_Iris.001` / `Material.022`). That is a separate map set, not “put Material.020 on everything.”

The agent repeatedly collapsed those into a single global rule (“only Material.020” **or** “only M_Iris_*”) and overwrote the whole eye stack each time. That felt redundant and abusive because:

- Front was already correct (`Material.020_*`).
- Back only needed `M_Iris_Back_*`.
- Phrases like “use her iris textures” / “textures that match UVs” / “iris back” were interpreted as full resets instead of **surgical slot updates**.
- Scene4 harvest + material rebuilds wiped working node trees mid-session, then “restore” paths rebound wrong sets again.

## Locked SSOT (do not reinterpret)

```text
R_Iris.001 / Material.022             →  Material.020_*
R_Iris.002 / Material.023 / Iris.002  →  Material.020_*
NEVER put M_Iris_front_* or M_Iris_Back_* as primary on Blender R_Iris.*
(Those are UE/Substance atlas exports; keep on disk only.)
```

## Phrase → action map (for future agents)

| User says | Do this only |
|-----------|----------------|
| “iris back” / “back texture” | Wire `Material.022` → `M_Iris_Back_*`. Leave front alone. |
| “UV / Material.020 / not those UE maps” | Keep/fix **front** on `Material.020_*`. Do not strip back unless asked. |
| “use her iris textures” | Still means the pair above, not `M_Iris_front` on everything. |
| “undo eyes” | Remove Scene4 `L_IrisBack`/`R_IrisFront` harvest; restore `R_Iris.*` visibility — **do not** nuke map wiring. |

## Root cause in one line

Ambiguous language + all-or-nothing material rebuilds + ignoring an already-working front/back split = repeated unnecessary overwrites.

## Related files

- Live: `KitbashExport/Melodia_Portfolio_Stage_v7.blend`
- Maps: `Imports/MelusinaTextures/Material.020_*`, `M_Iris_Back_*`
- Session: `Docs/MELUSINA_SESSION_LOG_2026-07-13.md`
- Wardrobe pin: `Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md`
