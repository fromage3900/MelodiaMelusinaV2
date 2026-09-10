# CLOSEOUT PLAN — Orphan maps + Sheep NS flipbooks + org sweep — 2026-09-09

**Goal:** Finish material wiring that still blocks a clean session close. No Monolith `save_packages` / `recompile_material`. Owner Ctrl+S.

## Phase A — Sheep NS flipbooks (P0, visual blocker)

**Systems:** `NS_ChoralSheep_WoolMotes`, `NS_ChoralSheep_BeatBurst`  
**MIs:** `MI_NS_ChoralSheep_WoolMote`, `MI_NS_ChoralSheep_BeatStar`

### Diagnosed
| Issue | Detail |
|-------|--------|
| BeatStar grid | Overrode `GridCols/GridRows` to **1x1** while parent master defaults **4x4**. Texture `T_Spark_Twinkle8` (512^2) is an **8-frame** atlas — whole sheet as one sprite = broken. |
| WoolMote | Parent Static Glint; FlipbookTexture on Melodia `_PROJECT` diamond alpha; grid 1x1 may be OK for single-frame — verify after BeatStar. |
| Hookup | Scaffold: attach WoolMotes; fire BeatBurst on pitch hits — BP wiring still thin. |

### Fix steps
1. BeatStar: `GridCols=4`, `GridRows=2`, `FlipFPS=12` (live). Ctrl+S. If cells wrong in PIE try 8x1 or 2x4.
2. PIE both NS — confirm animation + soft particle.
3. WoolMote follow-up if still wrong.
4. Keepers: `NS_WOOLMOTES.png`, `NS_BEATBURST.png`.

## Phase B — Wire maps on MI_Orphan_* (P0)

**Where:** `.../PBR_Auto/MI_Orphan_*` (~96) parent Universal, tex_overrides=0. Pre-existing names (not our renames).

### Batch rule
1. CSV: MI, stem after `MI_Orphan_`, matched T_* / _BaseColor.
2. Auto-wire **only** 1:1 stem matches.
3. Bind albedo/normal/ORM when present; `TextureWeight=1`.
4. No match → SCRATCH list, do not invent maps.
5. Batches of <=25; owner Ctrl+S; PR `content/materials-orphan-map-wire-2026-09-09`.
6. Rename Orphan→pretty names = **separate** later PR.

## Phase C — Org sweep (P1 docs)
LABEL_MAP Orphan bucket; stamp flipbook fix; park HeightBlend/V2Test/Lane D/`_PROJECT` archive/Shorewake/Rokoko explicitly.

## Phase D — Snapshot gate
CF_CLOSE_* + NS keepers + receipts → session closed.

## Ownership
New Bot: live params + orphan CSV (no save). Melodia bot: plan/docs/PRs. Owner: Ctrl+S + PIE.