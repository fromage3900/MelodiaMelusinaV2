# Houdini Lookdev + Weight-Paint Plan — Starskiff & Shorewake Dress — UE Tonight

**Date:** 2026-08-28 (night)
**Supersedes:** the weight-lab sections of `Docs/Handoffs/OVERNIGHT_HOUDINI_LEARN_LOOP_2026-08-28.md`
(its Melusina Weight Lab was a stub "needs hython" — hython is now PROVEN; its export path was
FBX, which Apprentice BLOCKS — corrected below).
**Review basis (honest):** no Starskiff or Shorewake-dress plan/spec exists in the repo —
`sea_above_shorelistener_concept_board_v1.svg` and `sea_above_melusina_character_board_v0.svg`
are shape-only concept art, and no `Cos_*` cosmetic assets exist. This plan therefore treats
**Starskiff** (Sea Above travel skiff) and **Shorewake dress** (the wearable evolution of the
Shorelistener concept) as owner-named hero assets and grounds them in the authorities that DO
exist:
- `Docs/Plans/MELUSINA_ANIM_NEXT_LEVEL_AND_OUTFIT_CORE_2026-08-16.md` — Phase A2 (V2 material
  instances expose **zero texture parameters** — the lookdev gap), Phase C (wardrobe slots
  leader-pose to the body mesh; `c_kilt_*` cloth bones live in the 465-bone skeleton).
- `specs/anim_presets/melusina_v2_material_map.json` — the approved source→instance mapping.
- `SK_Melusina_V2_Body` 5-slot material table + `M_Master_Toon_Universal` (never edit masters).
- `Docs/Production/HOUDINI_CREATIVE_PIPELINE_REFERENCE_2026-08-28.md` — verified Apprentice facts.

---

## 0. Pipeline verdicts that shape tonight (from live evidence, not hope)

| Want | Verdict |
|---|---|
| Houdini → UE skinned mesh (FBX) | **BLOCKED** — Apprentice cannot export FBX or Alembic (verified error strings in the reference doc) |
| Weight computation in Houdini | **WORKS** — bone capture + QA runs headless; weights leave as **JSON** |
| Skinned-mesh delivery to UE | **via Blender**: JSON weights applied to the 465-bone armature → FBX export → UE (Blender lane is already the proven animation/skinning path — see the melusina-blender-handkeyed-import skill) |
| Lookdev textures (COP-style) | **WORKS** — hython/PIL proven → staged → bound at the MI layer by the editor holder |
| UE material wiring | editor holder via Monolith `material_query set_instance_parameters`, instance layer only |

**Division of labor (tonight):** Houdini = lookdev textures + weight COMPUTATION + weight QA
evidence. Blender = mesh authoring, weight application, FBX export, render QA. UE (holder) =
import, MI binding, wardrobe slot, cloth physics.

## 1. Asset A — Shorewake dress (wearable; weight-paint critical path)

**Identity:** `Cos_ShorewakeDress` (follows the `Cos_*` cosmetic convention; the P0 wardrobe
pillar stays on `item.outfit.melusina_v2` → Glide — this dress is the post-P0 second outfit,
authored tonight, gated behind P0 evidence like everything else).

**Lookdev (Houdini/PIL tonight, texture convention faithful):**
- `T_MelusinaC_DressShorewake_BaseColor` — seafoam-to-deep-teal wake gradient, foam crest
  streaks near the hem (reuse the R5 `Foam_Mask` math), subtle Worley silk mottle (the
  Choral Sheep wool-lab look, 12%).
- `T_MelusinaC_DressShorewake_Normal` — silk fold normal from height (wrap-Sobel).
- `T_MelusinaC_DressShorewake_Emission` — foam-line glow near hem ONLY (static; the dress
  binds NO MPC writer — pulse-reactivity stays a Sea Above director exclusivity).
- `T_MelusinaC_DressShorewake_Roughness` — wet-silk ramp (low roughness where foam).
- Output: `Saved/Audit/melusina_lookdev/houdini_variants/` + manifest → staged to
  `Content/Melodia/Characters/Melusina/Textures/Clothes/` (new files only — never overwrite
  existing `T_MelusinaC_*`).
- **UE wiring (holder):** bind onto the skirt-slot MI via
  `material_query set_instance_parameters`, following `melusina_v2_material_map.json`; masters
  untouched. This also advances Phase A2 (the zero-texture-parameter gap) using the same calls.

**Weight-paint pipeline (the corrected Weight Lab):**
1. **Houdini (headless):** import dress mesh + skeleton rest pose (FBX *import* for reading is
   expected to work on Apprentice — probe first with the isolated pattern; if blocked, Blender
   exports the rest pose as OBJ + a bone-list JSON instead).
2. Bone Capture (biharmonic) against `c_kilt_*` + spine/pelvis deform bones → clamp 4
   influences → normalize.
3. **QA gate (the lab's real value):** export `weight_qa.json` — zero-weight vertex list,
   >4-influence violations, per-bone min/mean/max, stretch heatmap PNG. Gate: **0 zero-weight
   verts, 0 >4-influence violations** before anything ships to Blender. (Same success criteria
   the overnight plan wrote; now actually enforceable.)
4. **Blender:** `apply_houdini_weights.py` (new, system Python inside Blender) reads
   `weights.json` (per-vertex `{bone_name: w}`), creates vertex groups on the dress mesh
   against the 465-bone armature, parents with weights, exports FBX (skinned) →
   `SM_/SK_DressShorewake.fbx` into the staging area.
5. **UE (holder):** import skinned mesh, equip via `MelodiaWardrobeSubsystem` leader-pose slot
   (Phase C wiring — components already exist), KawaiiPhysics on the `c_kilt_*` chain, then the
   equip → save → restart → load roundtrip when it's time to certify.

## 2. Asset B — Starskiff (travel; lookdev-only tonight)

**No weight paint** — a skiff is a rigid body (static mesh + Nanite). If a cloth sail/awning is
wanted later, it joins the dress's cloth-bone path.

- **Lookdev:** `T_Starskiff_Hull_BaseColor/Normal/Roughness` — weathered pale hull planks,
  barnacle-encrusted waterline (reuse R5 `BarnacleCrust_Mask` + `WetRock` math — convergence,
  not new parallel systems), brass/rope trim in albedo. Wake foam emissive strip reuses
  `T_SeaAbove_Foam_Mask`/`Sediment_Ramp`.
- **Mesh (Blender, tonight or next):** placeholder hull proxy (hard-surface, 2-3 lumps +
  keel) — visual target from the owner's concept intent; Houdini renders QA via the existing
  Blender render suite (clay + textured passes).
- **UE wiring:** static mesh + `MI_Starskiff_Hull` instance; no wardrobe interaction; travel
  behavior is game-code territory — explicitly OUT of this lane (no new traversal authority
  without owner design).

## 3. Tonight timeline (Houdini/Blender lane, editor holder in parallel)

| Block | Lane work | Output |
|---|---|---|
| H0 | probe FBX *import* on Apprentice (isolated, wedge-proof pattern); author `dress_lookdev.py` + `starskiff_lookdev.py` on the reef-generator pattern | scripts |
| H1–H2 | cook both texture sets + manifests; weight-lab script (`dress_weight_lab.py`) authored | textures + lab |
| H2–H3 | run weight lab (if FBX import worked) → `weight_qa.json` until gate green | QA evidence |
| H3–H4 | Blender: dress mesh (adapt V2 skirt) + `apply_houdini_weights.py` + FBX export; skiff proxy hull | meshes |
| H4+ | stage → sandbox/clothes folders; holder: MI binding + import + wardrobe slot; run the Blender render QA on both heroes | in-game assets |

## 4. Evidence standard (unchanged, applies to every step)

Textures exist when their manifest says so and ingest passes. Weights are good when
`weight_qa.json` shows the gate green — not when the viewport "looks fine". UE wiring is real
when the holder re-reads the bound instance parameters / equipped cosmetic id back through
Monolith. Nothing here closes a P0 gate: P0 still closes only through the PIE + ledger path
(Phase 2-4 of the closeout plan).

## 5. Open owner inputs (needed, do not guess)

1. **Starskiff silhouette intent** — one sentence or a sketch reference; a placeholder proxy
   ships tonight regardless.
2. **v22 texture set of record** for Melusina (Phase A2 step 1, owner-confirmed) — the dress
   textures will follow the same folder convention as whichever set is canonical.
3. Confirm `Cos_ShorewakeDress` as the cosmetic id + that the dress replaces the skirt slot
   (vs. full-body swap) — affects the leader-pose slot and the weight-lab bone set.

---

## 6. EXECUTION LOG — H0–H2 done (2026-08-28 late night)

| Step | Result |
|---|---|
| FBX **import** probe | **GREEN** — `hou.hipFile.importFBX` exists and imported the Choral Sheep FBX (no `suppress_warnings` kwarg — drop it). Export stays blocked; import is the lab's read path. Probe: `probe_fbx_import.py` |
| Dress lookdev | **COOKED** — `T_MelusinaC_DressShorewake_{BaseColor,Normal,Emission,Roughness}` (seafoam→teal, silk folds, hem foam, static emission) |
| Starskiff lookdev | **COOKED** — `T_Starskiff_Hull_{BaseColor,Normal,Roughness}` + `T_Starskiff_Wake_Emission` (planks + barnacle waterline + brass trim; reuses reef math) |
| Staging | **8/8 hash-OK** → `Content/Melodia/Characters/Melusina/Textures/Clothes/` (new files only; 0 refused) + `stage_manifest.json` with per-file import flags |
| Weight lab | **AUTHORED** (`dress_weight_lab.py`): import → biharmonic capture → clamp 4 → QA gate (`weight_qa.json`: 0 zero-weight, 0 >4-influence) → `weights.json` for the Blender applier. Runs at H2-H3 once the dress mesh exists |
| Render QA | 8 flat renders in `Saved/Audit/sea_above/renders/textures/flat/melusina_lookdev/`; suite extended with `--tex-dir/--tex-out` |

**Bugs caught by the run:** `importFBX(suppress_warnings=…)` kwarg invalid; 1D gradient
collapsed broadcast width (needs `broadcast_to().copy()`); plank period 14 not power-of-two.
All fixed in-place; determinism unchanged.

**Remaining for tonight/tomorrow (H3+):** Blender dress mesh (adapt V2 skirt) →
`apply_houdini_weights.py` → weight-lab run to GREEN → skinned FBX → holder imports + binds MI
+ wardrobe slot. Skiff proxy hull + import. Owner inputs §5 still stand.

---

## 7. OWNER SUPERSEDED THE AUTOMATED PATH (2026-08-29, live)

**The owner hand-delivered the dress end-to-end in one session:** posed on Melusina in Blender,
manual weight painting, rigged, texturing in Substance, imported into UE. Consequences:

- The **weight lab's role changes**: from pipeline step to **optional QA tool** (run it against
  the owner's imported asset to certify 0 zero-weight / ≤4 influences if ever wanted — not a
  blocker, the owner's hand weights ARE the weights).
- **My flat-layout `SK_ShorewakeDress.fbx` is SUPERSEDED** — do not import it; it carries the
  Nikki morphs (Bloom/Swirl/ShimmerWave) but no pose/weights. The owner's rigged import is the
  asset of record.
- **Morph carry-over is unverified**: whether the owner's FBX path preserved the three
  transformation morphs depends on their export route. If absent, re-authoring them on the
  owner's rigged mesh is one Blender pass (per-panel stagger math already in
  `dress_transform.py`).
- **What the owner needs now is the UE-side material + transformation layer** — already
  specified: `Reef/IMPORT_QUEUE.md` (iridescent bell recipe pattern) and
  `shorewake_transform_manifest.json` (sequence table) + the staged
  `T_MelusinaC_DressShorewake_*` set in `Clothes/`. Substance exports slot straight into the
  same MI binding contract.
