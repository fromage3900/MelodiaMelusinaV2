# GOAL — Melusina final runtime rig, today (2026-09-24) — Infinity Nikki bar

**Bounded:** today only; the runtime Melusina only; each step ends in a PIE gate on `L_MelusinaMorning`. Nothing outside the list below.
**Ruling:** Jev `jev-1.13.0` / `jev-live` — FINISH_RUNTIME_RIG_TODAY (0.94); no owner direction call needed (0.11). Runtime readiness 1.69/4, doll 1.11/4.
**Owner split:** the owner prototypes the doll look today by sculpting doll details into her normal maps. The agent does not touch the DollKit or those normal maps.

**Runtime owner:** `BP_MelusinaJRPGCharacter` → `SK_Melusina_V2_Body` (ARP, 465-bone `SK_Melusina_Skeleton`) + `ABP_Melusina_Current`; hair `SK_MelusinaHair` + `ABP_Melusina_WaterHair`; `EyeIrises`/`EyeLashes` on `head_x`.
**Probe helpers:** `Saved/Audit/melusina_hair_lookdev_20260924/hair_view.py` (views, variants, eye probes, blink log, actor framing).

## Infinity Nikki bar (every gate is judged against this)

1. **Silhouette first:** hat, hair and outfit read as one clean, layered silhouette at gameplay distance.
2. **Face is the hero:** both eyes clearly visible at rest; hair frames the face, never covers the eyes; brows present; clean blinks on **both** eyes.
3. **Rigid things stay rigid:** the hat, hair ties and ornaments ride the head with no slip or float; soft things (strands, ribbons) follow through and settle.
4. **No clipping:** hair never through face or shoulders; hat never through hair.
5. **Motion beauty:** idle, run, stop and jump all read graceful; the water layer (FluidNinja droplets + FLIP drip) supports the silhouette, never hides her face.
6. **Materials are Nikki-lane instances** of existing masters — no new masters.

## Steps

### R0 — Restore her hat
- The hat is material sections on `SK_Melusina_OLD` (`Material_019` hat ruffle; identify the rest by isolation in PIE) and was never split into the V2 parts.
- Extract only those sections into a new `SK_Melusina_V2_Hat` on the same `SK_Melusina_Skeleton` (Geometry Script: copy from skeletal mesh → keep hat material IDs → write to the new asset). Materials → Nikki-lane MIs.
- Add it to `BP_MelusinaJRPGCharacter` leader-posed to `CharacterMesh0`, like the V2 wardrobe parts. It is not a wardrobe slot (never swapped).
- **Gate:** PIE four views: hat seated on the head, no gap, no hair poking through the crown, and it rides the head through run/jump.

- **R0 DONE 2026-09-24 (pending front/profile re-frame):** hat = sections 26–31 of `SK_Melusina_OLD` (`Material_019` ruffle, `Material_018` hat body, `Iridescence_002` gem + their three outline shells; the only sections above the head, z 181–204). New `SK_Melusina_V2_Hat` (duplicate of OLD rewritten with only those triangles via Geometry Script; 52,659 verts / 104,885 tris; stale morphs removed; saved). `BP_MelusinaJRPGCharacter`: `HatMesh` (stencil 4) attached SnapToTarget to `Mesh` + `SetLeaderPoseComponent(Mesh)` at the end of BeginPlay; compile 0/0, saved. PIE: `HatMesh` found, parent `CharacterMesh0`; back view shows the mini top hat seated on the crown. Hat materials are still the old `M_Material_018/019` + `M_Iridescence_002` (Nikki-lane MIs = later).
- **Editor crash 13:23:** GPU `E_OUTOFMEMORY` at the start of the 24th PIE session of the day (not an asset fault). All work was saved before it.

### R1 — Left-eye blink
- `eyeBlinkLeft`/`eyesCloseL` on the source body don't close the left lid (verified by forced-morph A/B). **Source found:** live Blender `Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend`, object `Melusina_Base` (18,891 verts = UE V2 body). `eyesCloseR` moves 125 verts (max 4.4 cm); `eyesCloseL` only 78 verts (max 2.3 cm) — half-built. `eyeBlinkLeft/Right` keys are empty (0 verts) in this file. V2 FBX: `Exports/MelusinaClothes/V2/SK_Melusina_V2_Body.fbx`. Fix at the source `.blend` (mirror the working right keys), re-export and reimport **with owner OK** (hero body).
- **Gate:** straight-on natural blink: both lids cover both irises.
- **R1 DONE 2026-09-24:** Blender (live, in memory, NOT saved — owner saves): `Melusina_Base` `eyesCloseL` rebuilt as a positional mirror of `eyesCloseR` (125/125 verts paired, worst 6.5 mm); `eyeBlinkLeft/Right` filled from `eyesCloseL/R` (the `populate_melusina_arkit_shapekeys.py` mapping). A topology mirror was tried first and rejected (moved 8,482 verts). UE: Blender and `SK_Melusina_V2_Body` share vertex order (18,891 verts, constant offset only), so the corrected left lid was written by index as morph targets `eyesCloseL` + `eyeBlinkLeft` via Geometry Script (max 4.44 cm = right side; morph count still 120; saved) — no full body re-export. PIE straight-on natural blink: **both eyes close**. Proof `Saved/Audit/melusina_hair_lookdev_20260924/blink_both/blink_both_sheet.jpg`.

### R1b — Magical-girl SDF eyes + sparkles + cymatics (owner request)
- `MI_Melusina_Nikki_Iris` (child of `M_Master_Nikki`: twinkle iris, glitter halo, cymatics from `MPC_Cymatics_Driver.Cymatic_BeatPulse`, low pastel) built and compiled (476 PS instr) — but the iris rendered as a blank pale disc, so `SM_R_Iris_002` was **reverted to `MI_Melusina_IrisDisc`**.
- Root cause: there is **no iris artwork** in UE. `T_Melusina_V2_Iris_Material020_*` are flat white; the `T_Melusina_IrisFront/Back_*` and `T_Melusina_M_Iris_front_*` sets are 32×32 placeholders. The Blender source (`Iris.002` → `Imports/MelusinaTextures/Material.020_*.png`, 4096²) is a projected bake (purple/red blobs, 4 lilac highlight blobs), not an iris design.
- **Owner decision:** a procedural SDF iris needs new material logic (pupil + iris gradient + star catchlights + twinkling sparkle ring + beat pulse). Options: (a) new `MF_Melusina_SDFIris` wired into `M_Master_Nikki` behind a switch (master edit — red tier, needs OK); (b) `M_SDF_StarBloom` MI in UV mode on the disc (stars, no pupil/cymatics); (c) owner paints an iris texture and the Nikki MI animates it.

### R2 — Hair off her right eye at rest
- Part the side strands crossing her right eye with the existing bangs-lift pattern.
- **Gate:** front + front ¾ at rest show both eyes; a run/jump clip keeps strands off the face.

### R3 — Brows
- Fit `Melusina_Brows_Export_20260922_L/R` + `MI_Melusina_Brows_Dark` to the V2 face.
- **Gate:** brows on the brow line in front and profile close-ups.

### R4 — Kawaii performance
- 219 inter-bone dummy bones (threshold 100): tune subdivision without changing the look.
- **Gate:** warning resolved; motion clip unchanged.

### R5 — Face readability (if time)
- Face reads dark in lit shots. Test a face fill/rim in Morning in PIE; the face SDF bake stays later.

### R6 — Close
- Final Nikki-bar sheet (four views, eyes, blink, motion) from PIE on Morning.
- `CURRENT_STATE.md`: fix stale lines (slot-1 water MI, one-eye blink, hat), record today.
- Commit on owner OK only.

## Not in this goal
DollKit E1–E8; multi-segment hair re-rig; idle-VFX activation; the owner's normal-map doll sculpt.
