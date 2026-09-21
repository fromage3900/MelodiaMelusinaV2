# Lookdev — Handoff, 2026-09-21

Four lookdev lanes moved today. Each section lists what is proven, what is not, and the single next
action. Renders are in the companion doc `PORTFOLIO_RENDERS_HANDOFF_2026-09-21.md`.

---

## 1. Melusina in UE — hair, wardrobe, bow (landed, `13dbc182e`)

- **Hair:** `ABP_Melusina_WaterHair` `bBoneSubdivisionCollisionOnly` True → **False**. The 220 inter-bone
  dummy bones KawaiiPhysics already generated are now simulated joints. No re-rig, and the tune is
  unchanged (Damping .18, WorldDamping .50/.50, Stiffness .08, LimitAngle 60, Wind .20). Stable in PIE.
  Pre-change copy: `Saved/Audit/MelusinaPolish_20260920/ABP_Melusina_WaterHair.pre_vendor_tune_20260920.uasset`.
- **Wardrobe on presenter actors:** `GetBodyMesh()` fallback (C++). The presenter now shows Shirt / Boots /
  Accessories. The R2 skirt stays a standalone actor (its own skeleton). W6 in
  `Docs/Production/MELODIA_CPP_GAMEPLAY_ROADMAP.md` tracks the name-based fallback as debt.
- **WaveHarp bow:** attach solved: `hand_l`, scale 0.9, world `(0,90,0)`. Transform sequence verified
  (`74d9f936f`).
- **Next:** capture from the canonical camera. See the renders handoff.

## 2. Shorewake outfit — whole-outfit swap (C++ built 15:06, catalog pass pending)

- New `FMelodiaCosmeticRecord::ReplacedSlots`. The Shorewake dress (`SK_ShorewakeDress_Melusina465`,
  48 `SW_Dress_P*` material slots, `SK_Melusina_Skeleton`) replaces Shirt + Accessories and keeps Boots.
  The hat is not a wardrobe slot.
- **Next:** the catalog pass in `CURRENT_STATE.md` §3 *C++ rebuild pass 1*, then a PIE look at the
  dress on her. Its 48 material slots are unreviewed for lookdev. Check for clipping at the collar and
  hem, since the Accessories shawl, which used to cover the collar, will be gone.

## 3. Faraway Mother — Stage 1 + 2 (`cc9cb6e6a`)

Full detail: `Saved/Audit/faraway_mother/HANDOFF_STAGE1_2_2026-09-21.md`.
Level `/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype`.

- Stage 1: 7/7 placed, reload OK, no Landscape (per contract). Z comes from the manifest fallback
  because the Visibility raycast failed (DrawDebugTrace vs TraceChannel).
- Stage 2: four MIs (`MI_Mother_Mantle/Gown/Veil/Corset`) on Nikki/Universal masters. Scalars applied.
  **Texture maps did not bind** (`bound=false`: master parameter names did not match).
- **Next:** run `Content/Python/faraway_mother_stage2b_texbind_2026-09-21.py`, then take a viewport read
  before any beauty frame. The imported textures under
  `/Game/EnvSandbox/Textures/Copernicus/Faraway/` are **untracked** in git (`Content/EnvSandbox/*` is
  gitignored). Back them up before any cleanup.

## 4. Blender composition — Melusina + Choral Sheep + Sir Melodious (audit done, plan not executed)

- Audit: `Saved/Audit/staging_composition_audit_2026-09-21.json` (13:50).
  Plan: `.hermes/plans/2026-09-21_composition-melusina-sheep-cameras-goo-decor.md` (14:08).
- Findings the plan acts on: `Cam_Beauty` (50 mm f/4) puts the sheep ~28° off-axis. Render resolution is
  parked at 20 % (384×216). There is a port 9876 double-bind (second Blender). `Melusina.001` (18.8k
  body) is linked to no collection.
- The live `.blend` (`Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend`) is the owner's
  and is **dirty**. The plan mutates it only in memory, on an explicit GO per task, and never saves it.
- **Next:** plan Phase 1 (render-body decision, resolution, light isolation). Every task needs owner GO.

## 5. Blender / Cascadeur upstream (runbook written, nothing exported)

`Docs/Production/MELUSINA_REEXPORT_RUNBOOK.md`. The blocker is **root motion**: `root`/`c_traj` have
zero translation on Idle/Walk/Run/Sprint, so no BlendSpace speed can be placed correctly and the feet
slide. One Blender pass should also re-export the skirt onto `SK_Melusina_Skeleton` so the wardrobe can
equip it (roadmap W7).

---

## Untracked lookdev content to decide on

The working tree holds lookdev assets that are **not in git**: new `NS_Melusina_*` Niagara systems
(`Content/Melodia/VFX/`), `Melodia/Cymatics/MelodiaRoseVelvet` and `MelodiaSapphireGlass`, the
`Polish_20260920` R1 skirt, `Content/Melodia/_PROJECT/04_Materials/*`, and the
`EnvSandbox/VFX/Materials` reorganisation (26 flat MIs deleted, new `Instances/`, `Systems/`,
`Templates/`). They go into git only on the owner's commit decision (see the closeout commit plan).
