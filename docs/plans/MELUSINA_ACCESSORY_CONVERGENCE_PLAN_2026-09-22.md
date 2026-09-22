# Melusina Runtime Look Convergence — Existing World/Universe Geometry Pipeline (2026-09-22)

> **For Hermes:** Read the verified map (§1) before executing any wave. Every claim
> below was verified live on 2026-09-22 (Monolith run_python on the open editor +
> header reads + headless Blender dumps). This plan supersedes the v5 U6 approach of
> a standalone `DA_MelusinaFX_Accessories` system — see G1.
>
> Scope: converge Melusina's updated Blender/GN garment and accessory geometry through the **existing canonical DCC → Hython/Houdini → World/Universe Compiler → UE validation/runtime presentation pipeline**. TouchDesigner remains the existing semantic/show-control presentation consumer; it does not become a garment runtime owner. Bar: Infinity Nikki (soft painterly toon, layered cloth with visible physics, wardrobe-as-fantasy).
>
> **Hard redirect (owner, 2026-09-22): do not create a garment compiler, accessory runtime, look-preset runtime, fabric runtime, parallel catalog, or second equip system.** `UMelodiaWardrobeComponent` remains gameplay/save/equip authority. World/Universe compilation remains geometry/build authority. Existing Hython/Houdini garment/Vellum/VAT tooling remains fabric-generation authority. Existing material/cymatics/MPC and TD semantic lanes remain presentation consumers. This PR only supplies garment/accessory recipes, manifests, adapters, validation and evidence into those owners.

## 1. Verified correspondence map

### 1.1 UE runtime (the owner — converge INTO this)

| Piece | Location | Verified state |
|---|---|---|
| `UMelodiaWardrobeComponent` | `Plugins/MelodiaWardrobe/.../MelodiaWardrobeComponent.h` | LIVE re-host (Decision 044) of the quarantined outfit component: `EquipGarment(slot, mesh)` leader-poses same-skeleton garments; null = hide, cheap re-equip; `EquipCosmetic(id)` resolves via subsystem + mirrors to narrative record; `ApplyCosmeticPresentation(id)` = presentation-only seam (no save mutation); `ApplyWardrobeState()` = post-save-restore; `SetSlotMaterial`; `bEnableBattleWardrobe` explicit gate |
| Body-region clipping | `ApplyBodyRegionVisibility()` + `Tools/wardrobe_intersection_audit.py` | Contract exists (Nikki-translation §6 precompute tier): catalog-authored compatibility → runtime union → body region-hide morphs; **degrades safely to "no collapse" when morphs are missing** — and they ARE missing (G2) |
| Cosmetic catalog | `UMelodiaCosmeticCatalog` / `UMelodiaCosmeticDefinition` (DataAssets) | `FindById` / `FindFormById` / `FindCosmeticsWithDanglingForm` (the silent-no-op guard, surfaced); Form/Style records (`FMelodiaResonantForm` — the magical-transform lane) |
| Slot defaults | `DefaultGarmentMeshes` map | "The Melusina V2 pawn supplies Shirt/Skirt/Boots/Accessories here" — the V2 modular set IS the default wardrobe |
| Modular meshes | `/Game/Melodia/Characters/Melusina/Outfits/V2/` | `SK_Melusina_V2_{Body,Shirt,Skirt,Boots,Accessories}` — all SkeletalMeshes on shared `SK_Melusina_Skeleton`; Accessories bounds origin (−0.2, 14.0, 80.5) extent (97, 43, 62) |
| Live proof | Capture level | `BP_MelusinaSwordsman_Presentation_C_1`: `WardrobeSlot_Shirt` (SK_Melusina_V2_Shirt) leader-posed on `MelusinaPresentationMesh` (V2 Body) + `WaterHairMesh` (SK_MelusinaHair) |
| Quarantined ancestor | `UMelodiaOutfitComponent` (MelodiaCore, Decision 016) | Still on `bp_melusina` CDO; NotBlueprintable/NotPlaceable; slots Body/Hat/Gloves/Shawl/Trail/HairCharm. **Do NOT build on it.** New work targets MelodiaWardrobe only |
| FX attachment plan | `.hermes/plans/2026-09-22_005015-melusina-ue-closeout-v5.md` U1–U5 | Sockets `FX_WingRoot`/`FX_RingStack` on the SkeletalMesh asset + duplicated capture map + deterministic ring rotation — unexecuted; wings/rings are rigid pieces, NOT same-skeleton garments |
| `/Game/Accessories` | — | DOES NOT EXIST (verified). No accessory runtime beyond the wardrobe plugin |

### 1.2 Blender authoring surface (converge FROM this)

| Piece | Location | Verified state |
|---|---|---|
| Accessory Studio v2 (regalia) | `Saved/Accessories/Melodia_Accessory_Studio_v2_MFX_20260922.blend` (1.6 MB) | Collection "Melusina FX Regalia": `TMP_FX_AngelWings_Carrier` (640 v), `TMP_FX_ClockworkRing_{Inner,Mid,Outer}` (4452/5772/7284 v); 5 cameras, Key/Fill/Rim lights — the staging studio that exported `Exports/MelusinaFX_20260922/` (eval FBX + 4 GLBs, written at unit_scale 0.1) |
| Accessory Studio v1 (eyewear) | `Melodia_Accessory_Studio_v1.blend` + `catalog_builders.py`, `nikki_chain_setup.py`, `brooch_lab/` (BROOCH_V10_GRANDMASTER_PLAN etc.) | The eyewear-atelier lane: 8 GLB heroes, 4 finishes — a finished authoring grammar worth reusing for UE cosmetics |
| GN kit | `deploy/surreal_arch/melodia_gn/` (repo) vs AppData 5.2 (123 .py vs 111) | 12 AppData-only modules incl. `wardrobe_kit` (the accessory GN kit is NOT in the repo authority) and `garment_ribbon.py` (live on Melusina_Skirt 09-21) |
| FX_Hero live scene | harp WIP blend (00:59 save) | Wings carrier + 3 rings + globs + horns, verified by the committed evidence JSONs (`rings_verify`, `globs_build`, `horns_fix`) |

### 1.3 The five gaps (each one is a real polish cost today)

- **G1 — two equip systems would be born.** v5 U6 planned a fresh `DA_MelusinaFX_Accessories` runtime. The wardrobe plugin IS the accessory system (catalog + slots + save + clipping). A second one violates the one-writer rule. The regalia needs socket-attachment + own motion (leader-pose can't carry rigid counter-rotating rings) — so the catalog must gain a delivery mechanism, not gain a sibling system.
- **G2 — the Nikki clipping tier is a no-op.** `SK_Melusina_V2_Body` has 120 morphs: visemes + ARKit face set only. Zero body-region-hide morphs (`wardrobe_intersection_audit.py`'s vocabulary is unauthored on the mesh). Every layered look currently relies on clipping tolerance instead of the authored contract.
- **G3 — the kit isn't in the repo.** 12 AppData-only GN modules (`wardrobe_kit`, `garment_ribbon`, `cute_decor`, `escher_decor`, …) = addendum A4. The accessory authoring kit is invisible to every other lane/machine.
- **G4 — no intake contract.** `TMP_*` prefixes, unit_scale 0.1 FBX, SM_-vs-SK_ lane ambiguity (rigid static vs skinned garment) — each import re-litigates the conventions. The v1 eyewear lane already proved the grammar (named heroes, finish variants, contact sheets); it was never written down as a contract.
- **G5 — material handoff is ad hoc.** Toon masters (`M_Master_Toon_Character`) + the animated flipbook set (`MelusinaAnimated/20260922`: wings ×3, rings ×3, globs ×2, 352 frames verified) have no written wiring recipe per accessory class (v5 U2 says "extend the existing families" — the how is tribal).

## 2. Redirected convergence plan — use the pipeline we already own

### Authority graph — no new systems

```text
Blender / melodia_gn source + authored silhouette
        |
        v
tracked garment/accessory recipe + provenance manifest
        |
        +--> Hython / Houdini
        |      - deterministic geometry processing
        |      - Vellum/offline fabric where tier requires it
        |      - VAT/cache/export where already specified
        |      - cymatic/material maps through existing generators
        |
        v
World / Universe Compiler geometry contract
        |
        v
UE import / semantic enrichment / validation
        |
        +--> UMelodiaWardrobeComponent = equip/save/runtime identity authority
        +--> existing material + MPC/cymatics consumers = reactive presentation
        +--> existing TD OSC/show-control lane = external/live presentation consumer
        |
        v
runtime + render evidence
```

The wardrobe does **not** compile geometry. The World/Universe Compiler does **not** own saves/equipment. TD does **not** own gameplay. Hython/Houdini does **not** create a parallel runtime. Each existing owner keeps its boundary.

### R0 — Tonight: converge the current Melusina look, do not architect a replacement
- Freeze the known-good V2 body/skeleton/runtime. Work from copies/derived garment geometry only.
- Treat the updated Blender static/skinned meshes and current GN silhouette work as source candidates for the existing geometry pipeline.
- Produce the smallest recipe/manifest needed for the current shirt/skirt/accessory/regalia set, with source blend, GN/Hython operation, output class (skeletal garment / rigid attachment / VAT hero cloth), material family, bounds and expected wardrobe slot/socket.
- Compile/import through existing guarded paths, bind the resulting assets to the **existing** wardrobe/runtime presentation surfaces, and capture a cohesive hero render state tonight.
- The approved hero state is evidence/configuration for existing systems; **do not introduce a new `LookPreset` runtime class or DataAsset merely to store it.**

### R1 — Canonicalize the GN source lane
- Re-measure and sync the AppData-only `melodia_gn` modules (`wardrobe_kit`, `garment_ribbon`, etc.) into repo authority using the established deployment gate.
- GN is an authoring front-end to the same geometry recipe contract, not a wardrobe runtime.
- Generated variants must be reproducible from tracked parameters/manifests so Universe/World compilation can request them later.

### R2 — Route fabric by the existing universal garment tiers
- Reuse `Docs/Art/UNIVERSAL_GARMENT_FABRIC_DRAPERY_2026-09-02.md` and `Docs/Art/CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md`; do not design another cloth framework.
- Structured body pieces remain skeletal/bone-driven; cheap secondary motion remains existing WPO; hero cloth uses the already-defined offline Hython/Houdini Vellum → VAT/cache route when warranted.
- Runtime Unreal should consume the compiled result. Do **not** attempt runtime Houdini/Vellum generation.
- Cymatic/iridescence/emissive outputs continue through the existing material family and single MPC/audio-reactive writer.

### R3 — Make garments a World/Universe Compiler geometry domain
- Extend the **existing** compiler recipe/schema only as narrowly required to describe character-attached geometry: source recipe, generated outputs, skeleton/slot or socket binding, fabric tier/cache, material family and evidence.
- Reuse the same deterministic compile semantics used for world geometry: source → recipe → compiled artifact/manifest → UE apply/validate → readback.
- A future outfit/silhouette change should therefore be a different recipe/parameter set through the same compiler, not a new subsystem.
- This is the long-term Infinity-Nikki-style lane: GN/Hython can vary hem length, skirt volume, ribbon density, sleeve profile, ornament density and other authored parameters; the compiler materializes approved variants; Wardrobe equips them.

### R4 — Runtime binding stays thin
- `UMelodiaWardrobeComponent` remains the sole gameplay/save/equip authority for garments/cosmetics.
- Same-skeleton compiled garments bind through the existing garment slot path.
- Rigid compiled geometry binds through existing/approved socket attachment seams. If a tiny adapter is genuinely missing, add only the minimum adapter after proving the compiler output cannot bind through an existing seam; **do not create a second accessory catalog or bespoke runtime geometry manager.**
- Body-region hide/intersection data should be compiler/intake metadata consumed by the existing `ApplyBodyRegionVisibility()` contract.

### R5 — TD / reactive presentation is downstream, not another authority
- Preserve the canonical TD boundary: game ↔ TD semantic/show-control on UDP `:9000`; TD may visualize garment/form/material state and drive approved presentation channels but never owns equip/save/geometry truth.
- Reuse existing OSC/MPC/cymatics semantics for live reactive cloth/material presentation where useful.
- Any TD/Hython bridge used for generation must emit a deterministic artifact/recipe/evidence back into the canonical game pipeline rather than leaving runtime truth inside a `.toe`.

### R6 — Prove one complete garment compilation
The long-term gate is one end-to-end proof, preferably the current Melusina hero skirt/look:
1. tracked Blender/GN source;
2. deterministic Hython/Houdini processing where required;
3. World/Universe Compiler recipe + manifest;
4. UE import/apply through the existing guarded surface;
5. existing Wardrobe binding;
6. material/cymatic presentation;
7. runtime readback + hero render;
8. restart proof before calling the garment path production-ready.

That proof becomes the template for future outfit silhouettes rather than creating per-outfit infrastructure.

## 3. Owner gates

| Gate | Question |
|---|---|
| G-A | Does this change reuse an existing World/Universe Compiler, Hython/Houdini, Wardrobe, material/MPC or TD seam? If yes, extend that seam; reject parallel ownership. |
| G-B | For tonight, does the change visibly improve the current Melusina render without destabilizing the known-good V2 body/skeleton? If not, park it after showcase. |
| G-C | For long-term outfit work, can the silhouette be represented as tracked GN/Hython recipe parameters + compiled artifacts while Wardrobe remains equip authority? That is the required direction. |

## 4. Traps encoded

- Leader-pose with a foreign skeleton deforms silently — the C0 skeleton rule is load-bearing.
- The quarantined `UMelodiaOutfitComponent` on bp_melusina will look tempting in the CDO — Decision 016 stands.
- FBX import into an existing path creates redirectors — new package dirs only.
- Compile NEVER between CDO set and save (Recipe 15); one editor; Monolith :9316 the only surface; `MODAL_OPEN` is not a hang.
- AppData melodia_gn is ~20 modules ahead per older notes; re-measure (A4 says 12 names) before any sync — census proves presence, never absence.
