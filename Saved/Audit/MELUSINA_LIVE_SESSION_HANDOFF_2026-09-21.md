# Melusina live-session handoff — 2026-09-21 (Blender MCP lane)

Session: live Blender 5.2.1 via MCP :9876, WIP file
`C:\EnvironmentPortfolio\harp_bow_pipeline\Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend`
(1139 objects, scene frames 1–240 @ 24 fps). **Nothing was saved.** All changes below are
in-memory; the file is dirty and saving is the owner's call.

Evidence directory: `Saved/Audit/melusina_live_20260921/` (probe_*.py/json, fix_*.py/json).

## 1. Verified — Jev is live (was: "jev isn't being used")

`TYPESAFE_API_KEY` is now set (Hermes `.env` + Windows user env var). The key **must keep
its `apikey_` prefix** and is sent as `Authorization: Bearer apikey_…`; a trimmed key returns
401, a full one 200. `typesafe-sdk 0.7.0` is installed.

- `Tools/listening_field/jev_director.py verify` → `boundaries: 14 agreement: 1/14`
- Jev-sourced directives: **14/14, zero fallback**; confidences 0.0–0.76
- Evidence: `Saved/Audit/listening_field/directives_jev_v1.jsonl`

Jev disagrees with the authored table on 13 of 14 boundaries (mostly `world` RELEASE vs
RESTRAIN and differing restraint levels). That divergence is a design question for the owner,
not a defect — the table is the answer key, Jev is the live judgment.

## 2. Verified — bow / arrow / bowstring

- **The bowstring DOES transform.** `Draw` shape key: 184/200 verts move, max delta 0.30 at
  mid-string, pulling −Y. Driver `d*(1-r)` reads `Draw`/`Release` custom props on
  `ME_WaveHarp_CTRL_Functions`. Frame sweep: rest y≈+0.108 (f96) → drawn y≈−0.179 (f136) →
  rest again by f168. The action `ME_WaveHarp_CTRL_FunctionsAction.001` keys Transform / Draw /
  Release / Pluck / Resonance over frames 1–180.
  **Open (per Claireon 2026-09-20 §102): this continuous transformation does not exist in UE —
  the UE assets are static snapshots. That is the likely source of the complaint.**
- **The arrow flies the wrong way, measured.** Melusina faces **−Y** (nose y=−0.336, head
  y=−0.159). The arrow flies **+Y** (f150 → y=+1.39, f156 → +2.52). 180° off — over her shoulder.
  The staged root `ME_WaveHarp_R08_STAGE_Root` has zero rotation, and the staged asset sits
  1.13 m from her rig.
- `SOCKET_Bow_Aim` is **coincident with `SOCKET_Bow_Grip`** (both local (0,0,0)) in the R08 set;
  the legacy set had the aim 0.15 above the grip. Any consumer using Aim−Grip as a direction
  gets a zero vector. Also `ME_WaveHarp_Legacy_*_SOCKET_Arrow_Nock` sits at local (0,−10,0).
- Accepted UE convention (Claireon §99): attach R07 bow to `hand_l`, scale 0.9, align at the
  draw beat to world rotation (pitch 0, yaw 90, roll 0).

## 3. Fixed in memory — eyes

- **Cornea re-weight applied.** The 100 verts weighted to `eyes` — a non-deform aim bone under
  `MCH-eyes_parent` — moved to `DEF_eye.L` (50, x<0) and `DEF_eye.R` (50, x≥0), weights
  preserved 0.985–1.0, `eyes` group cleared. A non-deform bone's group is ignored by the
  armature modifier, so those verts never followed the head in Blender either, and in UE they
  would collapse to the root.
- Lashes/irises/brows are structurally sound (skinned to real deform bones: DEF_forhead_04.L/R,
  DEF-lid.T/B.*, DEF_eye.L/R). Each carries one stray non-bone group that does nothing
  (`faceit_eyelashes`, `faceit_left_eyes_other`, `faceit_facial_hair`).
- Blink driver reads the **absolute world Y** of `eye_ctrl` (`Key 2 = var + 1.0`, var is a
  TRANSFORMS LOC_Y WORLD_SPACE read) → constant 0.68789. `Key 2`/`Key 120` are geometrically
  empty shape keys. Body blink keys `eyeBlinkLeft/Right` exist with muted drivers (authored
  expression state — untouched).

## 4. Fixed in memory — Sir Melodious

- **23 rig-control shapes hidden from render** (`sirmelodious_cs_*`, all previously
  render-visible and unparented) — plan Phase 3.1.
- **Two textures repointed** to recovered files (4096², users 4 and 2):
  `sirmelo_BaseColor.png`, `tie_BaseColor.png` → `Saved/Audit/melusina_lookdev/Textures_Recovered/`.
- **Still missing (3):** `Material.021_BaseColor.png`, `Material.021_Normal.png`,
  `coat_BaseColor.png` — not found anywhere on C:/G: under those names. `SirMelodiousBody`
  also has an **empty material slot 0**.

## 5. Sheep — three of four pieces placed, horns diagnosed

Plan Phase 2.1 executed for `SheepMusicBeads`, `SheepPearlDanglers`, `SheepLissajous_Halo`
(hosts moved off the x=7.62 staging row, bone-parented to `rig`):
neck beads 0.132 m from the neck anchor, pearls 0.068 m, halo 0.42 m above the head.
(Plan tolerance 0.25/0.35/0.45 respectively — the halo passes at 0.42/0.45.)

`SheepHorns` — measured, not yet right:
- It **does** generate: 6,144 verts, 85-node group `MEL_S5_horns` (users=1).
- It is a **world-space carrier**: moving the host 0.7 m up changed nothing (centroid stayed
  z=0.338). Its `MrSheepFinal` Object Info node + two `Align Curve to Surface` groups place it
  from the body's geometry.
- Current world placement: bbox x 2.34–2.73, y −1.18..−0.86, z 0.18–0.50 — centred on the
  midline but **0.69 m below the skull** (skull z=1.0285), i.e. on the chest. Size 0.39 × 0.32 ×
  0.32 m at host scale 0.15.
- **Dial facts:** writes go to `mod.properties.inputs["Socket_N"]["value"]` and need an explicit
  `ob.update_tag()` afterwards or the depsgraph serves a cached mesh (this invalidated a first
  sweep). With the tag, `Horn Length` drives size (0.4 → 2.56 m, 2.0 → 3.46 m in object space).
  **`Curl Turns` (Socket_3), `Spread` (Socket_7) and `Align To Body` (Socket_10) are not wired
  inside the group — those three dials are dead.**
- Remaining fix is inside the group's `head y` / `rise` anchor math (lift ~0.7 m to the skull),
  not the host transform.

## 6. Open, unchanged

- **Hair:** all 8 SHP curve systems still generate zero geometry; the three water-hair meshes
  (`Hair Strand.004/.007/.010`, the only users of `Water (Advance).002`) are hidden in both
  viewport and render. UV layers exist (`shp_uv_map`, `shp_uv_hair` active render, `shp_uv_flys`,
  `shp_uv_orn`) with flys/orn all-zero and 30 degenerate polys on `.007`.
- **Geometry:** `Melusina.001` (18,791-vert duplicate body, no collection) is render-visible
  8.34 cm below `Melusina_Base` → double body in renders; `Retopo_Melusina_002` is a 0-vert
  shell; six strand systems carry the −8.34 cm offset.
- **Dress detail / dangle work** (plan Phase 6): not started. Registry ready —
  `MEL_nikki_star_pendant` (Hang .075/Droop .08/Cord .0026) on the shawl back-edge,
  `MEL_nikki_bead_string` (Droop .1) skirt-side; brooch hero per `Saved/Accessories/brooch_lab/genome/`.
- **FLIP water hair:** not baked. Domain `FF_MelusinaHair_Domain` frames 1–240 res 72, cache
  dir `G:\…\KitbashExport\flip_cache_melusina_waterhair` does not exist; no `.bobj` anywhere.
- **Lights (plan Phase 1.3):** the three harp-stage lights are still not isolated.

## 7. Method notes for the next operator

- Run scripts through the live socket (`bl_sock.py`), never headless.
- `ob.bound_box` is cached — it does not refresh without a depsgraph update. Measure through
  `evaluated_get(dg).to_mesh()`.
- Blender 5.x actions may be **slotted**: `action.fcurves` can be empty; walk
  `action.layers[].strips[].channelbags[].fcurves`.
- `Driver` has no `.mute` in 5.2 (use the fcurve's), and `FCurve.evaluate()` needs a frame.
- GN modifier inputs: `mod.properties.inputs[identifier]["value"]`, then `ob.update_tag()`.
- `Collection` has no `users_collection`; build a parent map from `bpy.data.collections`.
