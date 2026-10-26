# Carillon & LittleGuys — recovered HoudiniForge creature families

**Status:** EXISTING REPOSITORY ARTIFACTS + PARTIAL EDITOR STAGING; regional placement PROPOSED  
**Recovery read:** 2026-10-26  
**Stable editorial grouping:** `creature_collection.houdini_forge.carillon_and_littleguys` — editorial only, not a gameplay ID or a new parent species.

> **Correction to earlier brainstorming:** The owner calls this collection **Carillon Bell creatures**. The original HoudiniForge sources actually distinguish a **Carillon architectural bell line**, **Gaudy/LittleGuys creatures**, and **MusicBoxMimic**, with Dingle nearby. Do not merge all of them into one biological species or rename original assets without approval.

## 1. What the supplied reference renders show

**Sheet 1 — pastel/lavender, two rows:** top and bottom represent resting/arch vs revealed/awake design comparisons, not eight independent species. Best supported identification left to right:

| Position | Repository working name | Readable art identity | Match confidence |
|---|---|---|---|
| Col 1 | `ChimeSnail` | spiral lavender carapace, small snail body, bell-tipped feelers | High |
| Col 2 | `PearlJellybell` | tiny white jelly/teardrop bell with glossy eyes and thin dangling limbs | High |
| Col 3 | `JellybellQueen` / `PearlJellybell_Queen` | crowned larger white jellybell | High |
| Col 4 | `MusicBoxMimic` | ivory music chest, closed vs open-lid expressive face | High |

**Sheet 2 — dark contact sheet:** five vertical architectural carillon explorations, two view/state rows. The 2026-10-15 source handoff identifies five original variants as **BellSpirit**, **ChandelierWraith**, **BellGolem**, **Hydra**, **InvertedTower**. The exact column-to-variant correspondence is not verified by embedded labels; **do not silently label individual columns as a named variant**.

### Not shown / uncertain
- `Dingle`: separate NPC/creature staging family, not confidently mapped to either image; do not assume hostility because an animation pack exists.
- `Hydra`: present in five-variant blockout documentation, but **not present** among the four Arch/Awake creature pairs in the currently checked `Carillon/Creatures` Git tree. Search PC source/staging before classifying lost or cancelled.
- “Carillon Bell creatures” is the owner's collection label. Exact in-world taxonomy and cultural naming are not yet approved.

## 2. Source-verified inventory in Git main

| Asset family | Tracked files and state | Production note |
|---|---|---|
| Carillon BellSpirit | `SM_GPX_Carillon_v1_BellSpirit_{Arch,Awake}.uasset` | paired static meshes |
| Carillon ChandelierWraith | `SM_GPX_Carillon_v2_ChandelierWraith_{Arch,Awake}.uasset` | paired static meshes |
| Carillon BellGolem | `SM_GPX_Carillon_v3_BellGolem_{Arch,Awake}.uasset` | paired static meshes |
| Carillon InvertedTower | `SM_GPX_Carillon_v5_InvertedTower_{Arch,Awake}.uasset` | paired static meshes |
| Carillon Hydra | no matching pair listed in checked `Carillon/Creatures` directory | previous v1 concept only; source recovery needed |
| ChimeSnail | `SM_LG_ChimeSnail_{Arch,Awake}_gaudy_{v2,v4}.uasset` | v4 is later lookdev; source files need recovery |
| PearlJellybell | `SM_LG_PearlJellybell_{Arch,Awake}_gaudy_{v2,v4}.uasset` | small jellybell, source files need recovery |
| JellybellQueen | `SM_LG_PearlJellybell_Queen_{Arch,Awake}_gaudy_{v2,v4}.uasset` | visual crown variant, not automatic boss |
| MusicBoxMimic | `SM_LG_MusicBoxMimic_{Arch,Awake}_v3.uasset` | paired states |
| Dingle | `SM_GPX_NPC_Dingle_LOD_gaudy_{v2,v4}.uasset` and separate `NPC/Dingle` staged mesh | kept separate; NPC/enemy role unresolved |

**Confirmed by Git contents listing:**
- `Content/Staging/HoudiniForge/Carillon/Creatures/` — 8 static mesh .uassets, 4 paired families.
- `Content/Staging/HoudiniForge/Carillon/Parts/` — 64 shared bell, halo, filigree, crown, yoke etc. parts per original handoff.
- `Content/Staging/HoudiniForge/Carillon/Skeletal/` — 2 cord packages.
- `Content/Staging/HoudiniForge/Gaudy/` — 12 Arch/Awake gaudy meshes for ChimeSnail, PearlJellybell, Queen (v2 and v4), plus 2 Dingle gaudy meshes and 5 related MIs.
- `Content/Staging/HoudiniForge/LittleGuys/MusicBoxMimic/` — 2 meshes.
- `Content/Staging/HoudiniForge/Anim/<Creature>/` — **9 families** × 10 tracked packages each (skeletal mesh, skeleton, 7 sequences, Strike Ring montage) = **90 asset entries**.
- `Content/Staging/HoudiniForge/Enemies/` — 7 staged Blueprints: four Carillon ACF variants, three Explore variants; **not evidence that all nine families have playable AI**.
- Git directory entries for these binary `.uasset` files are **LFS pointer-sized**. File presence does not prove hydrated LFS bytes, editor load, original editable .blend/.hip files, or functioning encounters.

### Nine animation families

`BellSpirit`, `ChandelierWraith`, `BellGolem`, `InvertedTower`, `ChimeSnail`, `PearlJellybell`, `JellybellQueen`, `MusicBoxMimic`, `Dingle`.

Each directory lists `Alert_WakeUp`, `Death`, `HitReact`, `Idle`, `Move`, `Strike_Ring`, `Turn_Look` plus montage/mesh/skeleton. Times in the 2026-10-15 editor report: 1.25 s / 1.88 s / 0.50 s / 2.50 s / 1.25 s / 0.62 s / 1.67 s respectively. “Death” is a file name, not a decision that the Faraway Mother's nonviolent encounters must kill anything.

## 3. Original musical and gameplay contracts — preserve, do not reinvent

From [HoudiniForge Sol handoff](../../HoudiniForge/SOL_HANDOFF.md):

- Architectural Carillon bell profile/notes are driven by `note`, `pitch_hz`, `decay_s`, `strike_vel`, `piece_id`, `mount`, `roams` and related anchor attributes. **Pitch is semantic data, not inferred from shape**.
- Shared coordinate convention `shared_zup_cm`; flip Y **once** on UE intake; crown pivot for bell rigs.
- Original staging was **Ocean Cathedral** with Aeolian reuse notes. Cathedral C3 bourdon was intended as a stationary floor boss, lower choir C3/G3/C4 stationary, higher C5–C6 bell forms roaming on walkable/navmesh corridors. Those are old *scene-specific plans*, **not** permission to spawn any of them in Poitou or Faraway Mother.
- State names `arch`, `awake`, `awake_roam`, `awake_combat` appear in the old handoff. Arch vs Awake static pairs are not proof of a runtime state swap.
- Reuse `BP_EnemyExplorePawnBase` or already-owned ACF enemy parents, current audio/beat signals, existing material instances and `BP_MelodiaNiagaraDriver`; no new global combat, spawning, audio or material frameworks.
- Original scale/headroom estimates and door clearances must be checked against the destination level. Older notes flag anchor coordinate uncertainty and Dingle collar clearance.

### Historical staging bounds (cm; **not** freshly measured)

| Family | X × Y × Z cm | Role/scale implication |
|---|---|---|
| BellSpirit | 1288 × 182 × 598 | colossal/sweeping architectural silhouette |
| ChandelierWraith | 458 × 402 × 525 | suspended architectural enemy |
| BellGolem | 863 × 320 × 990 | colossal bell body |
| InvertedTower | 747 × 747 × 994 | tower-scale silhouette |
| ChimeSnail | 68 × 47 × 39 | handscale wildlife |
| PearlJellybell | 18 × 18 × 23 | tiny ambient scale |
| JellybellQueen | 37 × 35 × 54 | small rare variant |
| MusicBoxMimic | 57 × 55 × 77 | prop-/chest-scale |
| Dingle | 280 × 319 × 279 | larger support/NPC creature |

Source: [Enemy wiring live report](../../HoudiniForge/ENEMY_WIRING_LIVE_2026-10-15.md) section TODO item 5. Treat historical measurements as staging claims pending UE verification.

## 4. What is NOT finished / verified

The 2026-10-15 report differentiates **saved before 14:25** from **unsaved after 14:26**. Some later assets exist in Git (including animation folders and gaudy-v4 entries), but that **does not prove editor/persistence state or encounter correctness**.

Old open tasks:
1. Physics Assets not generated on skeletal import (check current editor before adding).
2. Skeleton sockets `SKT_Emit_*`, `SKT_Weak_*` absent in that pass.
3. Strike Ring `ACFNotifyFX` placed at 0.267 s (frame 8 at 30 fps), but FX payload **empty**.
4. ACF wake/target/turn/combat phase event wiring pending.
5. Enemy Blueprints still using static `CreatureMesh` rather than animated `CharacterMesh0` / verified AnimBP; update only after scale/rig check.
6. Dingle float BP not made; no automatic hostile role for Dingle.
7. BellSpirit bounds, material fidelity, UV and vertex colour needed checks.
8. Old handoff notes missing `/Game/ACFEffectsManagerComponentBP` reference on `BP_HF_BellGolem_ACF`; verify current state rather than trusting prior warning.
9. Source Blender/Houdini rigs/FBX exports and intermediate stages were under **gitignored local `Saved/Staging/GrokPrep/houdini_forge/`**; recovering these is likely what owner means by “forgot to commit.”

No PIE smoke, packaged proof or character-specific saved/restart proof was re-run as part of this documentation.

## 5. Regional assignments: existing evidence vs new proposal

| Family | Original work context | New regional proposal | Decision |
|---|---|---|---|
| BellSpirit / ChandelierWraith / BellGolem / InvertedTower | Ocean Cathedral / Aeolian architectural chimes | Keep home there unless specific Poitou encounter warrants a deliberate downscale/retune | **Keep original; defer migration** |
| Hydra | Original five-variant blockout | None until source located | **Recover/decide later** |
| ChimeSnail | Gaudy/LittleGuys; Aeolian ambient referenced | **Faraway Mother** soft/lullaby styling; could read as a spiralling comfort creature | **VISUAL / REGION CANDIDATE** |
| PearlJellybell | Gaudy/LittleGuys; Aeolian ambient referenced | **Faraway Mother** passive floating hush ecology, if no overlap with proposed Hush Jellies | **VISUAL / REGION CANDIDATE** |
| JellybellQueen | Gaudy/LittleGuys | Faraway rare variation of same design language; not an automatic miniboss | **VISUAL / REGION CANDIDATE** |
| MusicBoxMimic | LittleGuys; music-box states | **Poitou** optional indoor/architectural encounter; not the P0 golden walk's mandatory fight | **REGION CANDIDATE** |
| Dingle | Explicit `NPC/Dingle` and staged animated family | Region and hostility remain unassigned | **HOLD** |

**Visual recommendation only:** The owner identified the **pink creatures** for potential Faraway Mother reuse. This likely corresponds to the first sheet's ChimeSnail / pearl-jelly forms; no existing `_Faraway` fork has been verified. Their material retune should prioritize muted ivory, blush/lavender, velvet-lullaby sound, and fewer hard brass edges, but **do not replace current source asset looks**.

Do not mistake these creatures for Les Emmaillotés. [Les Emmaillotés](LES_EMMAILLOTES.md) stays the approved intimate swaddled/comfort encounter. The Carillon small-creature candidates would be secondary ecology only if they serve the existing route without expanding mechanics.

## 6. Minimum gameplay-role hypotheses (not historical implementations)

- **ChimeSnail:** roaming musical patrol / ambient moving chime, can yield on timing; no new locomotion system.
- **PearlJellybell:** lightweight note cue / ambient motes, often better as pure scenery than a fight.
- **JellybellQueen:** optional clustered resonance leader that changes timbre, not necessarily hit points.
- **MusicBoxMimic:** localized wake/sleep chest-shaped encounter using existing Arch/Awake pairs.
- **Large Carillon line:** stationary or roaming spectral bell enemies within existing cathedral ACF + Explore framework; retain original note/anchor semantics.

No new gameplay verbs, creature-family spawn services, or obligatory encounters proposed.

## 7. Decision gates

**Already owner-confirmed:** The depicted designs are owner-made enemies; they belong to the umbrella *Carillon Bell creatures* collection in personal working nomenclature; the pink subset is being considered for Faraway Mother; owner plans to locate/commit untracked editable source on their machine.

**Not yet owner-locked:** Exact P1 members, art recolours, relation of Queen to other jellybells, enemy placement, AI behavior, permanent formal species taxonomy, and any Poitou level assignment.

**Tomorrow's recovery checklist:** [Carillon source recovery handoff](../CARILLON_SOURCE_RECOVERY_2026-10-26.md).

## Evidence pointers

- [HoudiniForge Sol handoff](../../HoudiniForge/SOL_HANDOFF.md) — authored conventions, staged asset lists, paths, previous import claims.
- [HoudiniForge Aeolian inventory](../../HoudiniForge/AEOLIAN_INVENTORY_v1.md) — regional historical placement, static/ambient suggestions.
- [2026-10-15 enemy wiring report](../../HoudiniForge/ENEMY_WIRING_LIVE_2026-10-15.md) — saved vs unsaved staging, bounds, animation, open integration.
- Git content directories `Content/Staging/HoudiniForge/{Carillon/Creatures,Gaudy,LittleGuys/MusicBoxMimic,Anim,Enemies}` — tracked .uasset presence only.
