# GOAL — Melusina signature S3–S5 + Blender hot pass to reimport (2026-09-25, owner: "set a goal and work through it")

**Bounded:** tonight's session. One editor, Monolith as the mutating surface, code freeze lifted for tonight (owner). Every step ends in a build/PIE/validator gate; owner eye-checks are listed, not faked.
**Parents:** `.hermes/plans/2026-09-25_0600-melusina-blender-hot-pass.md` (H0–H9, S1–S5, Jev 2.79/4) · `.hermes/plans/2026-09-25_0010-p0-backlog-oneshot-goal.md`.
**Already done tonight:** S1 hair listens (built, weak live proof) · S2 pitch-class Chladni (built, values proven, eye-check pending) · skirt skeleton + bone-constraint rings · H0 contract/validator · H2 stray-weight clean · voice lines · arrival spawn tag (built).

## Order

### G1 — S3 Transformations on a cadence — **DONE 2026-09-25** (flourish start=beat; component on the pawn, costume mode; whole-outfit swap restored so Shorewake replaces Shirt+Accessories)
- `UMelodiaMagicalTransformComponent` (owner of `MagicalTransform*` material params) begins/resolves an outfit swap on the next phrase/bar boundary instead of immediately: the swap request is queued, and the visual peak + wardrobe equip land on the downbeat (music clock bar event; PhraseBus boundary when live).
- **Gate:** build + headless 101/103; PIE: request a swap mid-bar → log shows equip on the next bar boundary (±1 frame); wardrobe state/save unaffected.

### G2 — S4 Melusina × Sir Melodious duet — **DONE 2026-09-25** (two call→response pairs on the beat)
- Iris sparkle on the beat (`MF_Melusina_SDFIris` already reads `Cymatic_BeatPulse`; confirm it is driven) + Sir answers her note with a call/response chirp through the existing voicing.
- **Gate:** PIE log of one call→response pair on consecutive beats.

### G3 — S5 Silhouette gate — **DONE 2026-09-25** (`Saved/Portfolio/Silhouette_20260925/`: Default + Shorewake custom-depth masks, 750 cm. Both pass; Shorewake reads weaker — puff sleeves + narrower A-line vs Default's wing sleeves + bell skirt. Caveat: other stencil actors (arch, Sir) share the mask.)
- Headless/PIE black-silhouette capture of Melusina at gameplay distance per outfit (current + Shorewake); sheet saved to `Saved/Portfolio/Silhouette_<date>/`.
- **Gate:** sheet exists; failing outfits listed.

### G4 — H3 Body collision from the mesh (Blender, working copy) — **DONE 2026-09-25** (owner: "just do a subdivide")
- Limbs subdivided into ARP stretch/twist/twist_2 segments, one capsule each: 28 capsules, L/R symmetric (`Tools/melusina_fit_body_capsules.py`, text block `MELUSINA_BODY_CAPSULES` in R09, `Saved/Audit/p0_closeout_2026-09-24/h3_body_capsules.json`). Empty segments skipped: neck.x, arm_twist.l/r.
- Headless Blender hang on exit (ARP threads) fixed with `os._exit(0)` at script end.

## Updated goal (owner 2026-09-25 "set an updated goal to execute")
- **G5** — H9 export dry run (below), then validator on the staged FBX. — **STAGED, SCALE GATE FAILS 2026-09-25.** `Tools/melusina_export_dryrun.py` exports body+skirt headless to `Saved/Staging/MelusinaExport_20260925/`; `Tools/validate_melusina_staged_fbx.py` checks them. Blink morphs present (121 on body). Found: working-copy scene unit scale 0.1 makes ARP silently skip Units x100 (`_set_units_x100` requires scale 1.0) — dry run now sets 1.0 in memory. Still 1.988 vs reference `SK_Melusina_V2_Body.arp.fbx` 198.8 (100× short) and 432 vs 387 bones. Do not reimport until those match.
- **G6** — Feed the G4 capsules into UE: body capsules as Kawaii `LimitsDataAsset` capsule entries on the skirt/hair nodes (replaces the hand-placed hip/leg capsules); gate = PIE run/jump, no skirt-through-thigh.
- **G7** — Owner OK on the staged set → reimport body + skirt; gate = both blinks close, skirt ring constraints still bound.
- Capsules fitted to `Melusina_Base` per deform bone (pelvis, thighs, shins, spine, chest, neck, head, upper arms) → exported as the body physics asset in H9.
- **Gate:** capsule list with per-bone radii/lengths in the working copy; validator still passes for the parts it covers.

### G5 — H9 prep: export dry run
- ARP game-engine export of skirt (+ `NurbsCurve_profile.001` hip trim) and body from the working copy into a staging folder, validated against the contract (bone count, cm scale, morphs incl. both blinks) — **no UE reimport** until the owner OKs the batch.
- **Gate:** staged FBX set + validator report.

G5 scale: owner confirmed the staged body imports at her normal height (scratch `/Game/_Staging/MelusinaExportCheck`, unsaved). Open: 432 vs 387 bones.

> **Superseded 2026-09-25 13:30** by `2026-09-25_1330-melusina-dcc-longterm-goal.md` — the audit there corrects several claims below (eyes, fingers, bone count, ARKit, face SDF).

## Long-term DCC pass (owner 2026-09-25: "work outside UE imperative for her long-term")

**Verified state (read 2026-09-25):**
- Rig Postmortem (artifact TD5YxaZcSbmcVujHeoEbXr): eyes fix **done in blend** (`eyes` 0 verts; DEF_eye.L/R 50/50) but UE body is the 09-02 export, so it only lands with G7. Fingers **not fixed**: 28 `c_*` finger-controller groups still carry weights (orphaned on FBX export).
- Locomotion **not fixed**: `BS_Melusina_Locomotion_Hybrid` still 7 samples / 4 clips (Walk 150+180, Run 300+420, Sprint 540+630), all root-locked, axis max 650 < sprint 714.
- Face: 121 shape keys, 75 ARKit-named → UE face rig is morph-driven (no new bones needed).

**Tools on hand:** Blender 5.2 — auto_rig_pro, faceit, quick_baker, SimpleBake, Sanctus-Bake, BakeLab2, deep_paint, ZenUV, uvpackmaster3, rokoko-studio-live, ue2rigify, send2ue, live_link_unreal, collider_tools, Jiggle_Maker, SwingyBone, stylized_hair_pro, simply_cloth_studio, tripo_3d_for_blender, rust_gpu_sdf_addon. Houdini 22 + Engine. Marvelous Designer.

**Order (each depends on the one above):**
- **D1 Fingers** — decide re-weight to the deform chain vs export config (postmortem's open decision); fix in R09; staged export re-validated with `test_melusina_skin_topology_contract` at 0 new violations. Also explains the 432/387 bone gap.
- **D2 Vertex-colour zones** — paint `Col` layer on body+garments: R = MPC reactivity mask (Chladni/beat), G = face-shadow/SDF region, B = wetness/tide, A = cloth stiffness for Kawaii/cloth. Master already reads vertex colour? verify before painting; ship only channels a master consumes (no new master — MI rule).
- **D3 SDF face shadow map** — bake a threshold-SDF from 32 light angles in Houdini (or Blender GPU SDF addon) → `T_Melusina_FaceSDF`; wire into the existing face MI through an existing master input only; ask if the master lacks one.
- **D4 Face rig in UE** — reimport body with morphs (G7), ARKit curve mapping + Live Link Face pose asset; gate: blink both eyes + visemes in PIE.
- **D5 Locomotion** — retarget Rokoko takes with root motion kept, measure with `get_root_motion_speed`, rebuild BlendSpace from measured speeds (dedupe, axis ≥ sprint). Only after D1+G7.
- **Not doing:** Tripo/UV re-unwrap on skinned garments (breaks weights, Kawaii chains, MIs). Tripo OK for unskinned render props.

## Owner eye-checks owed
S1 hair sway (foreground PIE) · S2 skirt figure legibility · skirt/hair motion clipping (run/jump) · KaleidoNave arrival point.
