# Melusina Accessory Convergence Plan — Blender ↔ UE, Nikki bar (2026-09-22)

> **For Hermes:** Read the verified map (§1) before executing any wave. Every claim
> below was verified live on 2026-09-22 (Monolith run_python on the open editor +
> header reads + headless Blender dumps). This plan supersedes the v5 U6 approach of
> a standalone `DA_MelusinaFX_Accessories` system — see G1.
>
> Scope: UE + Blender ONLY. Bar: Infinity Nikki (soft painterly toon, layered cloth
> with visible physics, wardrobe-as-fantasy). Non-goal: any new parallel equip system.

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

## 2. Convergence plan (waves)

### C0 — Write the accessory intake contract (repo doc, ~1 page, S)
- Slot vocabulary = `EMelodiaWardrobeSlot` (+ the FX attachment spec below); skeleton rule: wardrobe-lane garments MUST share `SK_Melusina_Skeleton` (leader-pose copies by index — foreign skeleton silently deforms); naming `SK_/SM_ + family + variant`, `TMP_` never leaves Blender; FBX recipe: unit_scale 0.1 + bounds gate (wings ≈ 230 UE units); materials: one parent from the toon-master family, MI params gated via MEL reflection helpers; every piece ships with an audit JSON (source blend, bounds, morph list, slot/attachment spec).
- This is the artifact that kills G4 permanently.

### C1 — GN kit sync (A4, Blender-closed window, M)
- Repo is authority: land the 12 AppData-only modules via the `higgsas_gate.py` pattern → deploy copy. Unblocks `wardrobe_kit` + `garment_ribbon` for every lane.

### C2 — Author the body-region morph tier (Blender → UE, M/L — the biggest Nikki win)
- On the V2 body (a COPY first): shape keys per the `REGION_BANDS` vocabulary of `Tools/wardrobe_intersection_audit.py` (torso band, arm bands, leg bands at the tool's arm-radius fraction) → export through the guarded FBX lane → morph targets appear on `SK_Melusina_V2_Body`.
- Evidence: `ApplyBodyRegionVisibility()` collapse/expand JSON + before/after PIE stills (shirt equipped, regions collapsed exactly under it).
- This turns the clipping contract from no-op to live and is prerequisite for any true layered-Nikki look.

### C3 — One catalog, two delivery mechanisms (UE C++, closed-editor build, M)
- Extend `UMelodiaCosmeticDefinition` with an optional attachment record: `SocketName`, `StaticMesh`, `MotionSpec` (rate/axis per piece — rings: outer +0.6, mid −0.42, inner +0.78 rad/s, Blueprint/tick, classical only). `EquipCosmetic`/`ApplyCosmeticPresentation` dispatch: same-skeleton garment → leader-pose slot (existing path, untouched); attachment record → spawn socketed static on `FX_WingRoot`/`FX_RingStack` (v5 U1–U5 geometry, unchanged).
- The regalia, eyewear heroes, and brooch become catalog rows — one system, one save authority, no `DA_MelusinaFX_Accessories`.
- Rule 15/21: header change = full closed-editor build before any editor work that day.
- Recon first: locate the live `UMelodiaCosmeticCatalog` DataAsset (or author the first one) and verify `FindCosmeticsWithDanglingForm` returns empty.

### C4 — Regalia landing (UE, depends on C3 or owner-simplified variant)
- v5 U1–U5 verbatim (import `MelusinaFX_regalia_wings_rings_eval.fbx` → `/Game/Melusina/FX/Regalia20260922/`, Nanite wings ON rings OFF, collision NONE; sockets; duplicated capture map) — then the pieces attach through the catalog, not bespoke blueprints.
- Materials per C0 recipe: iridescent/brass placeholders from house masters; the 20260922 flipbooks wire as image-sequence samplers in the next lookdev pass (v5 U2 note).

### C5 — Intersection audit integration (repo + UE, S after C2)
- Run `wardrobe_intersection_audit.py` per new garment at intake (contract requirement from C0); commit the compatibility JSON beside the catalog; `ApplyBodyRegionVisibility` consumes it at runtime.
- Proof: equip shirt+skirt+regalia set → one PIE capture, zero visible clipping at the covered regions, `GetAppliedBodyRegionHides()` mirrors the expected set.

## 3. Owner gates

| Gate | Question |
|---|---|
| G-A | C3 direction approved: catalog gains an optional attachment record (C++ change + closed-editor build) instead of v5's standalone `DA_MelusinaFX_Accessories`? |
| G-B | First catalog families: FX regalia (wings/rings), eyewear heroes, brooch — which order? |
| G-C | C2 body-morph pass runs on a copy and lands via the guarded FBX lane — confirm the V2 body intake path before any touch |

## 4. Traps encoded

- Leader-pose with a foreign skeleton deforms silently — the C0 skeleton rule is load-bearing.
- The quarantined `UMelodiaOutfitComponent` on bp_melusina will look tempting in the CDO — Decision 016 stands.
- FBX import into an existing path creates redirectors — new package dirs only.
- Compile NEVER between CDO set and save (Recipe 15); one editor; Monolith :9316 the only surface; `MODAL_OPEN` is not a hang.
- AppData melodia_gn is ~20 modules ahead per older notes; re-measure (A4 says 12 names) before any sync — census proves presence, never absence.
