# Melodia Melusina — Current State

**This is the only status document.** If any other file states what works, what is open, or what
to do next, that file is wrong: fix this one instead. Update it in the same commit as the change it
describes. Handoffs, plans, receipts and session notes go in the commit or PR message, never in a
new file.

**Updated:** 2026-09-22 · **Engine:** UE 5.8 · Blender 5.2 LTS · C++20 · Python 3.11
World Compiler live close-out **2026-09-19**: `--skip-scaffold --fx --lookdev` **PASS**. Meadow on **BrushifyIsland_*** SpeedTree + walk dressing — not Sphere3D. Proof `Saved/Audit/world_compiler_morning_rainbow_bloom_proof_2026-09-19.json`. Board: `Saved/Audit/Screens/wc_morning_rainbow_bloom_{waterline_dolly,website_oblique,website_top,website_south,south_fix}_2026-09-19.png`.
Morning Niagara rewire **2026-09-19 14:49 disk** + **User-param bind PASS 2026-09-20**: Uni parents off `L_MelusinaMorning` actors; Melodia children `NS_Morning_{PetalDrift,PollenSparkle,PondMist,WindFront,DustShafts}` + parked Glint/Impact. `rewire_morning_fx.py --effect bind-user` bound SpawnRate→`User.PetalSpawnMultiplier` / `MoteSpawnMultiplier` / `MistDensity` and WindFront `Gust_Leader` SpawnBurst `Spawn Count`→`User.WindFrontVisible`. Proof `Saved/Audit/niagara_rewire_bind-user_summary_2026-09-20.json`. No MPC writes. Hue-reveal remains PIE wind only.
**Git 2026-09-22 (09-21 audit + convergence — read `Saved/Audit/git_health_2026-09-21.md` and `Docs/Audits/BRANCH_PRUNE_RECEIPT_2026-09-21.md` BEFORE re-reviewing any branch):** PR #281 merged owner-directed (main tip `dea0522ac`), but its own body's proof ladder — closed-editor build, focused NarrativeRecord automation, editor-process restart/repeat-load, packaged restart, fresh golden run — is **not** discharged, so **Issue #51 stays OPEN**. Zero unpushed commits on any lane: frequency-ecology tip `0e1963b1d` carries the 09-21 doc commits (CURRENT_STATE session records, handoffs parked to `Saved/Audit/`, audit + receipt); `codex/game-state-2026-09-04-checkpoint` (4 commits) and `codex/snapshot-prep-20260914` were re-pushed after their remote ref had been deleted — stale tracking refs are how that was caught. Pruned per receipt (SHAs recoverable there, no gc run): 6 remote refs (`fix/runtime-gameplay-closure-20260921` + its recut head via gh, `docs/production-spine-paradigm-20260921`, `fix/retire-front-door-suite-20260921`, `docs/canonize-converged-project-state-20260920`, `feature/house-gn-paris-20260920`) and 7 local parity twins. **KEEP decisions, not backlog:** `backup/*`, `recovery/*`, `collab/laptop/*`, `feature/harp-recovery-2026-09-20` (live worktree), and the Tier-3 pre-collapse families (`cursor/*`, old `codex/*`, `backup/pr166`-class) — each needs its own content check + receipt before any prune; do not bulk-delete. Open convergence: the frequency-ecology lane is 145 behind main and its diff drags pre-collapse docs — land it via PR with rebase-class conflict handling when showcase prep settles, not before. Isolated landing only; do **not** dump the dirty tree (Frozen PPV, MPCs, `DefaultEngine.ini`, EnvSandbox dumps, Oceanology, Humber stay parked; currently 147 M / 41 D / 146 ??). Never robocopy/junction/overwrite `harp_bow_pipeline`.
**Listening Field 2026-09-20:** Jev director + phrase bridge + spec on disk. Closed-editor `BS_GodFileEditor Win64 Development` **PASS 2026-09-20 17:48** (`UnrealEditor-BS_GodFile.dll` 3,232,768 bytes, `RecvFrom` ingest). Prior PIE bind was UDP `:9000`; python `phrase_bridge` sent `,isifsfi` / `,ii` but GetCurrentState stayed 0 on the 15:18 `Recv()` DLL. Re-open the editor and re-send to prove ingest. Choral Sheep consumer is existing `TryBeginHarmonize`. Jev never mutates the editor. Do not UBT while the editor is open.
**Owner-queue proofs 2026-09-20:** Fleece REST vs HIT on the approved Nikki path (`MI_ChoralSheep_Body`→`M_Master_Toon_Character`, child `MI_ChoralSheep_Body_Chladni_C` + `T_Chladni_C_ROOT`) — HIT shows C-root Chladni contours. Stills `Saved/Audit/Screens/ship_queue_fleece_{REST,HIT}_v2_clean.png`. 8s Creature→Motif→Harmony→World mp4 `Saved/Audit/AE/ship_queue_beat_8s/Melodia_ShipQueue_Beat_8s.mp4` from those stills + waterline plate. AE JSX is `C:/MelodiaTouchDesigner/ae/ship_queue_creature_motif_harmony_world.jsx`; headless AfterFX 2026 `-noui` dies on GPU3 while this editor holds the adapter. Do not rebuild the TD scene.
**harp_bow_pipeline junction incident 2026-09-20 (RESOLVED):** `C:\EnvironmentPortfolio\harp_bow_pipeline` was a junction to `G:\EnvironmentPortfolio_Snapshot_20260918\harp_bow_pipeline` whose 11 `.blend` files (all `Melusina_Harp_HERO01_*` incl. the `pre_rokoko_live` checkpoint) are robocopy-truncated zero-filled husks — Sep 8–12 Rev02/ArcherPose/BowPose staged work initially reported unrecoverable; **recovered late 2026-09-20** — an intact full-data copy was found at `D:\_relocated\harp_bow_pipeline` and all 21 `.blend` files were restored to the C: folder with no overwrites (`verify_blend.py` 21/21 OK; Rev02 opens + renders — 971 objects, EEVEE `Cam_Beauty` proof `harp_bow_pipeline/HERO01_Rev02_recovery_render_proof.png`; receipt `Saved/Audit/mocap/harp_recovery_2026-09-20.json`). D: stays master; G: left untouched as evidence. Junction replaced with a real C: folder holding one DNA-verified base (`Melusina_HERO01_Base_Sep5_Recovery.blend`, copy of the Sep 5 backup, verified AFTER copy) + 15 evidence PNGs + `HERO01_UE_RENDER_PROGRESS.md`. Intake gate: `python Tools/mocap/verify_blend.py <file-or-dir>` — rejects zero-filled husks, handles zstd-compressed blends. **v23 grandmaster is zstd, NOT a husk** (opened live 3× 09-20; skeleton FBX + rig-gate receipts from it valid). **Correction to the A2 note above: RecvFrom closed-editor UBT ran 17:48 — `UnrealEditor-BS_GodFile.dll` stamped; PIE ingest still owed on reopen.** Cascadeur inbox: 43 manifests all legacy Quaternius/UAL1 Lane-B (validator BOM-fixed to `utf-8-sig`); `SC_Melusina_Golden.casc` unauthored; binding source `Tools/Cascadeur/Melusina/SK_Melusina_Skeleton_Cascadeur.fbx` exported (760 nodes verified). Rokoko `character_rig_RokokoLive` confirmed absent from v23 (receipt `Saved/Audit/mocap/rig_gate_2026-09-20.json`) — rebuild before next suit session only against the v23 snapshot. Owner confirms current locomotion/Rokoko is proven and working (2026-09-22); do not rebuild or rerun from the old snapshot; `Tools/mocap/` = rig_gate, export_take, export_skeleton_fbx, verify_blend.
**Pre-collapse docs:** every deleted handoff/plan/report is recoverable with
`git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).

**Showcase prep 2026-09-21 (not committed):** Phase E measured `WaterHairMesh` on `L_MelusinaPortfolioCapture`: chain bones stayed **0.0 cm** off the reference pose while Update Animation in Editor was on and the editor world advanced 2.04 s. That checkbox is transient, so the later reload cleared it. `UMelodiaHairComponent` constructs with `bCanEverTick` false; the instance flag was set true and the capture level was saved with `LevelEditorSubsystem.save_current_level`. The shirt slot was already present (`SK_Melusina_V2_Shirt`, visible, scale 1, leader-posed to `MelusinaPresentationMesh`, spine match 0 cm). Hair was not leader-posed and Kawaii was not retuned. The editor world then went null with four dirty Morning external actors, so the transient flag was not turned back on. Still, other levels, and cook were skipped. One editor was already open on `L_MelusinaPortfolioCapture` (Monolith `127.0.0.1:9316`). `WaterHairMesh` was already Update Animation in Editor off and Always Tick Pose. `Staging_R_Iris_003_L` and `Staging_R_Iris_004_R` were already detached; their scale was set to 1,1,1. The capture map is dirty. The agent did not save it — owner Ctrl+S. The eight Sir Melodious staging meshes are not in the open level, and their offsets were not recovered. Audits are not L2. Capture: 76 material slots, 10 bad parents (4 MatineeCam engine materials, 4 material-instance parents, 2 empty), 10 missing texture overrides on the harp and bow. None of the eight `NS_Melusina_*` systems use the `Content/Melodia/_PROJECT` flipbook authority; both flipbook copies measure Grid 4x4 and FlipFPS 15. Globules uses `ENV_StorybookAmbientVFX`. Globules, Splash, and Ripple each have 2 missing-bytecode diagnostics. Kawaii numbers match the accepted tune and the hair tick flags match; the Kawaii root is `HairExp_Rig`. The other five levels were not loaded. No render proof and no cook. Receipts: `Saved/Audit/showcase_prep_2026-09-21/`.

**Eyelash MI 2026-09-22 (owner-ordered, saved):** `MI_Melusina_Eyelash` created from `M_Master_Toon_Character` with one override (`BaseTint` near-black); both `SM_R_Eyelash` slots (794 + 830 tris) repointed from the FBX-import placeholder materials to it. Saved packages verified, dirty 0. Still owed: socket to `head_x`, portfolio + runtime staging, blink-drive proof.

**Iris sparkle+ORM + lash staging 2026-09-22 ~01:10 (editor closed clean before saves):** toon masters graph-read zero Flipbook/SubUV nodes, so atlas bind cut; fallback shipped on `MI_Melusina_IRISFRONT_001` (V2 body slot 4) + `MI_Staging_Iris`: twinkle on (Intensity 0.3, TwinkleSpeed 1.5, Threshold 0.65, Contrast 1.0, DriftSpeed 0.08 — first pass 0.6/0.35 was full-noise in preview, retuned), IRISFRONT Rough/Metal/Emissive off neutrals onto real `Material020` iris maps; remaining ORM slots neutral (no packed iris ORM exists — stated). Both MI packages saved, dirty 0, preview stills `Saved/Screenshots/Monolith/20260922_0036{31,51}_MI_*.png`. `Staging_Lash_Pair` spawned in capture level scale 6, bounds dead-on eye midpoint (-0.43, 31.4, 155.2), but level NOT saved before editor exit — re-verify on reopen, respawn with same numbers if lost. No brow FBX on disk (`Melusinaeyeparts.fbx` = lash + `R_Iris.002` only). Iris discs scale 0.01 persisted, still `bHidden=True`.

**CORRECTION 2026-09-22 ~04:10 — staging tree was deleted from disk, reset cause found:** `Content/Melodia/Characters/Melusina/Portfolio/Staging/` (R_Iris_003/004, `MI_Staging_Iris`, `T_Iris_*`) is gone — it was never git-tracked, so no `D` entries and no recovery via git. Sessions of "resetting" = (a) map/asset edits never explicitly saved + editor restart, compounded by (b) the untracked Staging folder being deleted between sessions by an unknown hand. On-disk truth now: capture map = 11-actor HEAD state, no iris/lash actors, no beauty camera. Survived: `MI_Melusina_Eyelash`, `SM_R_Eyelash` (root, tracked? verify), `MI_Melusina_IRISFRONT_001` with RoughnessMap→Material020 persisted but twinkle scalars at 0.0 (re-applied live, then editor crashed before save — re-apply again). Iris re-import (`Iris_and_SirMelodious.fbx`, survives with Material.020 PNGs) **crashed the editor** (callstack, StaticShutdownAfterError) — do NOT bulk-import that file; next attempt must be an iris-only export, small file, owner-supervised. Rule going forward: every staging mutation ends with explicit map-package save + mtime check, and staging sources must live under tracked paths (owner `.gitignore` call).

**Iris restore 2026-09-22 ~11:16 (owner imported meshes, SAVED + reload-proven):** `/Game/SM_R_Iris_002` (owner import, single disc ~1.7 cm, offset family matches lashes) is the live disc — old R_Iris_003/004 pair-assets are unrecoverable (deleted tree). Disc mesh slots → `MI_Melusina_IRISFRONT_001` (single iris authority; staging-disc fork is dead). IRISFRONT twinkle re-applied + verified live (0.3/1.5/0.65/1.0/0.08) **plus real `T_Melusina_IrisFront_ORM`** (exists since Sep 10 — corrects the earlier "no packed ORM" claim). Staged in capture map: `Staging_Iris_L/R` at eye marks scale 2, `Staging_Lash_Pair` at verified numbers, all visible; face close-up `Saved/Screenshots/slate_20260922_111530.png` shows the iris seated in the socket. Map + MI saved explicitly (umap 51.2→56.3 KB, mtime 11:15:57) and **reload-proofed 3/3 from disk** — the resetting loop is closed for this work. Still owed: brows (no brow mesh in UE; owner re-export), lash/blink motion proof, beauty still.

**Closeout 2026-09-22 ~13:46 — eyes seated, saved, reload-proven:** anchored on authored `VFX_EyeSparkle_L/R` world positions (L(-6.03,30.4,154.7) R(5.17,30.4,154.8)) after blind Z-stepping failed. New `MI_Melusina_IrisDisc` (Universal parent, Material020 Albedo/Normal/Emission/Alpha, twinkle set, BaseTint white) on `SM_R_Iris_002` slot 0 — fixes the white-disc/purple-speck UV mismatch (body maps on disc UVs). Final: `Staging_Iris_L/R` scale 3.5 at sparkle marks, `Staging_Lash_Pair` scale 6 centered between; face proof `Saved/Screenshots/slate_20260922_134523.png` shows iris + lash line seated in the socket. Map + both MIs + both meshes saved (umap mtime 13:45:53) and **reload-proofed 3/3**. Reset loop stays closed only while every session ends in explicit save — no exceptions.

**Convergence pass 2026-09-23 ~02:30 (build mode, editor DOWN at close):** `angel_convergence.py` throne-rim + param-link fixes landed (curve-circle resample rims, direct param sockets); live Blender verify **PASS 3/3** (`Saved/Audit/angel_convergence_headless_2026-09-22.json`: 19/12/16 nodes, preset keys + audio_attrs green). Contact sheets A–D already on disk in `Saved/Audit/contact_sheets_2026-09-22/` and current (Sheet D shows the new verify). Blender in-memory work (horns seated, 4 piano hooves w/ `HoofPianoKeys`, 12 doll balls, brow modifier cleanup) believed saved 20:22 — re-verify on reopen. **Brow FBX import CRASHED the editor a second time** (even the 165 KB brow-only file; StaticShutdownAfterError, no partial assets — `Eyebrows/` path absent, all prior eye work intact on disk). Rule now absolute: **no FBX imports via automation, any size — manual owner-side import only.** Brows stay Blender-side until then. 141 Morning deletions confirmed intentional (owner). `BP_Melusina.uasset` cleared for eye/lash/brow components + sockets — NOT yet executed (editor died first). Still owed: brow import, BP component promotion, blink port, lash/blink motion proof, beauty still, 98bpm wav (UE-only uasset).

## CANONICAL MELUSINA HAIR EVALUATION

Proved 2026-09-22 on the **runtime** unit `BP_MelusinaJRPGCharacter` in `/Game/Melodia/Levels/Opening/L_MelusinaMorning` (not the portfolio stage). Closed-editor `BS_GodFileEditor Win64 Development` **PASS** after renaming a local that shadowed `USkeletalMeshComponent::AnimClass`. One editor. No retune.

**Contract (saved template + live PIE):** `WaterHairMesh` mesh `SK_MelusinaHair`, skeleton `SK_Melusina_Hair_Skeleton`, anim `ABP_Melusina_WaterHair`, no hair leader pose, Always Tick Pose. Parent `CharacterMesh0` (`SK_Melusina_V2_Body`) socket `head_x`. Saved relative `(0.0001, 144.1994, -15.9001)`, roll `-90`. PIE relative after bind inverse `(0.0, 144.2298, -15.8971)`, roll `-90`. Shirt wardrobe slot on `SK_Melusina_Skeleton` leader-poses to `CharacterMesh0`. Log: `MELUSINA_HAIR_BOUND owner=BP_MelusinaJRPGCharacter_C_1 … attach_bone=head_x`.

**Live Kawaii node:** root `hair_root` (was `HairExp_Rig` from `ed1a3c6e5` 2026-09-16 until the 2026-09-23 fix below); damping `0.18`, stiffness `0.08`, world damping `0.50/0.50`, limit `60`, radius `2`, gravity `(0,0,-120)`, wind `0.20`, dummy length `3`, subdivision count `1`, warm-up `20`. Disk ABP still reports `bBoneSubdivisionCollisionOnly=true` on this reopen; the partial relief `bBoneSubdivisionCollisionOnly=false` remains the 2026-09-21 change in `13dbc182e`. `DA_Melusina_HairCollisionLimits` is assigned and enabled.

**PIE samples of `A_DEF_hair_bbone_000` (offset from reference pose):**
- world `26.2575` s: delta `0.1618` cm, yaw `-19.8178`, socket world `(-552.5666, 949.8093, -1887.7355)`, scalp-to-`head_x` `13.4852` cm
- world `30.3031` s: delta `0.1638` cm, yaw `-2.6483`, socket world `(-545.0369, 929.6370, -1930.8461)`, scalp-to-`head_x` `17.589` cm

**Hair-follows-head fix — 2026-09-23 (owner-reported "hair isn't following her head"):** with the Kawaii root on `HairExp_Rig`, `hair_root` (the single parent of all 73 strands) was itself simulated, so the whole hair mass swung on physics instead of riding the head — the drifting scalp-to-`head_x` distance above (13.5 → 17.6 cm in 4 s) is that symptom. Root set back to `hair_root` (its pre-09-16 value) in `ABP_Melusina_WaterHair`; all tuned values unchanged; compile 0/0; saved. PIE `L_MelusinaMorning`: `hair_root` in `head_x` space identical across samples 2 s apart (loc `(0, 0.03, 0)`, rot `(67.67, -91.29, -68.87)`) while the head moved — the hair now rides the head and only the strands simulate. Visual confirmation still owed (the editor was crashed by RiderLink before the screenshot).

**Eye binding — 2026-09-23 (Jev `jev-1.13.0`: HEAD_X_BONE / KEEP_UNTIL_PROVEN / STATIC_SEAT_ONLY; CORRECTED same day):** the first pass (`EyeIris_L/R` at scale 3.5 + `EyeLashes` at 6, copied from the capture-map staging offsets) was numerically "on the anchors" but **visually wrong**. The anchors are the eyeball centres (`DEF_eye_L/R`), so the irises were buried inside the head, lying flat and edge-on, and a lash arc sat off the face. Root cause: `SM_R_Iris_002` holds **both** irises (model-space centres x ±0.61, y 3.2, z 15.56, facing −Y) and `SM_R_Eyelash` holds both lash arcs in the same model space (centres ±0.70), so each staging copy drew a pair. Fix in `BP_MelusinaJRPGCharacter`: `EyeIris_R` and its attach nodes are deleted, and the remaining component is renamed `EyeIrises`. `EyeIrises` and `EyeLashes` share one model→face transform: scale 9.2556 (eye-bone gap 11.2 cm / model iris gap 1.21), relative to `head_x` loc (−0.0927, 133.6406, 45.0741), rot (roll 89.80, pitch 0, yaw −180), still attached on BeginPlay to `CharacterMesh0` `head_x` (KeepRelative). PIE proof from the saved BP: the iris pair is centred on the eye line (lateral/vertical error ≤0.01 cm), 1.46 cm in front of the eyeball centres and upright, and an unlit close-up shows both lash arcs seated over the painted sockets. Compile 0/0, saved. **Open:** in lit PIE her face is in deep shadow (sun behind the pawn, a lighting/look-pass issue, not the mesh), and the capture-map `Staging_Iris_*`/`Staging_Lash_Pair` copies are now superseded and can be removed. Blink stays a later pass: the `eyeBlinkLeft/Right` curves do animate (0→1 observed).

**Golden spiral re-landed on `L_MelusinaMorning` — 2026-09-23:** `BP_Morning_GoldenSpiral` + `/Game/Melodia/PCG/Morning/PCG_Morning_GoldenSpiralTreads` (spline → sampler 74 cm → spawner, `SM_ATL_Palace_FloorA` treads 73×161×16 cm). The spline is now a 37-point, 37 m log-tapered spiral (r 1350→900) wrapping `BrushifyIsland_10` from the east courtyard floor (z −610) at 60° clockwise through east/south to the island's south rim (z 575): 17.7° ramp, ~24 cm rise per tread. The west half is walled by islands 01/02/03/06/09 at every height (capsule-clearance map), so it wraps the open 180°, not 360°. Spawner collision set to BlockAll and a box simple collision added to `SM_ATL_Palace_FloorA` (it had none); 39/39 path traces hit treads, capsule clearance is clean end to end. Landings: `Morning_SpiralLanding_Base/Top`; the three stray clearing slabs were deleted. External actors saved and verified on disk.

**Hero-render plan for `L_MelusinaMorning` — 2026-09-23 (Jev `jev-1.13.0`).** Dell and Brook were deleted by the owner today (bad assets, off scale, not walkable). `Content/Python/morning_house_dell_build.py` (the source of the `MH_*` rosette/bank actors) is deleted; only two old `.hermes/plans` docs mention it.
- **Zones:** `SUBSTITUTE_SPIRAL_FOR_DELL_BROOK` (0.90). The four renders are (1) Rainbow Bloom Meadow, (2) Golden Spiral ascent round `BrushifyIsland_10`, (3) the island-rim overlook from the top landing, (4) Morning Dressing / owner-decorated MAD. The Dell/Brook rebuild with proper assets is deferred. `REBUILD_DELL_BROOK_TODAY` scored 0.03.
- **Method:** `MRQ_CINE_CAMERAS` (0.99): one CineCameraActor per zone and Movie Render Queue stills with AA and warm-up so the wind is moving.
- **Order:** `FIX_WINDFRONT_SPAWN_FIRST` (0.86). Fix the `NS_Morning_WindFront` spawn count (a float read as int, 1,065,353,216) before any render. Then cameras, then the look pass.
- **Dressing zone:** `OWNER_HAND_DRESSED` (0.82). Take the owner's MAD decoration as the zone; the empty `PCG_Morning_MemoryDressing` volume gets disabled, not repaired.
- **Melusina:** `MELUSINA_IN_HERO_SHOTS` 0.59 vs `ENVIRONMENT_ONLY` 0.41, confidence only 0.18. **Owner call.** The default is environment renders first, with a Melusina shot added if the hair visual check passes.
- **Guard:** no agent edits the level while the owner is decorating. The WindFront fix is asset-only, so it can go first.
- **WindFront FIXED (2026-09-23):** `NS_Morning_WindFront` had two user parameters both named `WindFrontVisible`, a float (1.0) and an int. `Gust_Leader`'s `SpawnBurst_Instantaneous` Spawn Count was linked through the int slot, so it read the float's bits: 1.0 → 1,065,353,216. The float is the contract (`world_compiler_ue.py` and `rewire_morning_fx.py` set it with `set_variable_float`), so the int is deleted. Spawn Count is now a constant 1, and Use Spawn Probability is on with Spawn Probability bound to `User.WindFrontVisible` (0 hides the gust, 1 shows it). Compiled, `validate_system` valid, saved.
- **Rainbow meadow texture fix (2026-09-23, after a broken Kimi pass):** Kimi's `MI_RainbowSpeedTree_B*_F1/_Tall` carried 6 of the band MIs' overrides, so they inherited the owner's intentional `SharedBend` 5.96 on `MI_Plant_Flower_GenericFlower1` and the cards blew up. All 14 are deleted. The 7 new `MI_RainbowSpeedTree_B*_Tall` are exact duplicates of each band MI with only `ColorOpacity` → `GenericFlowerTall_Color` (tall cards had been using the short flower's atlas), selected by the compiler's `mesh_mi_suffixes` (landed in `addebc328`). The meadow species `scale_range` is now [0.45, 0.8]: with the correct atlas the whole tall card shows, and 0.85–1.45 read as giant. Table reimported; field regenerated in place (pose untouched): 931 flowers at 0.38–0.79.
- **Canonical reusable meadow:** `/Game/Melodia/PCG/Meadow/PCG_Meadow_RainbowBloom`. Graph: 55 cm local grid culled to the volume → projected down onto any hit surface → ±22 cm jitter, random yaw, scale 0.45–0.8 → 14 weighted Flower1/Tall × band-MI entries, no collision. Placed as `Meadow_PCG_Canonical` (a `PCGVolume` on `BrushifyIsland_07`, 8×8 m → 225 flowers). Alt-drag and scale it to lay more meadow. `PCGVolume` can't be a Blueprint parent, so the placed volume + graph is the tool.
- **Two-writer warning:** the glitter-drift lane (`addebc328`) re-ran the full UE world compiler on this level at ~17:00 (re-placed FX actors; its note says they render white quads) while this lane was editing. The level commit that follows captures that disk state.
- **Morning FX white quads fixed at source (2026-09-23):** both materials have been broken since `ff5b02158` (09-19). `M_Niagara_Morning_PetalCard` (Masked, Substrate): the `PetalSDF` mask × particle alpha (`Multiply_2`) was never wired to Opacity Mask, so every petal sprite drew as a full card; it is now wired. `M_Niagara_Morning_PollenMote` (Translucent): emissive took only RG, opacity took R, the texture fell back to the engine's `DefaultTexture` (a grey checker, i.e. squares), and all parameters were named `Param*` with black/zero defaults. Now emissive = RGB, opacity = A, `SpriteTex` = `/Game/Alphas_Sparkles/T_Spark_Sparkle4`, `TipColor`/`BaseColor` warm white, `BoilAmount` 0.02, `BoilFPS` 8, `Glow` 1.5. Both recompiled and saved; the owner still needs to confirm visually. Note: the `MI_Morning_Pollen_B*` `BandHue`/`HueSeed` overrides hit no parameter in the pollen material (the fx pack promised `params_add` that never landed). `FX_BowStage_PondMist` has no Niagara system assigned.
- **Glitter drift LANDED (2026-09-23, build lane):** `melody_glitter` species live in `L_MelusinaMorning` — 57 `/Game/EnvSandbox/SM_MelodyToken` piles (10–25 cm) on `WC_EscherWalk_*` + island skirts, all 7 bands, wearing new `MI_RainbowGlitter_B0..B6` (toon parent `M_Master_Toon_Universal`, BaseTint band tints, Sparkle 0.5/160 — the `MI_MelodyToken_Water` precedent; first-pass `M_Glitter_WorldAligned` parent rendered flat white, reparented after two still reads). Lane additions, all additive: `Tools/world_compiler.py` species-`band_mi_prefix` precedence + per-species `scale_range` + `glitter_lane` dressing emission; recipe `palette.glitter` (+ schema); `world_compiler_ue.py` `glitter_materials` step; `test_world_compiler.py` per-species scale bound — ALL PASS. Neutrality proven: pre-species compile is byte-identical to the saved 09-19-era bundle (`points.csv b6a0f333…`, `fx_anchors 9e5c33be…`). Live: DT 1089/1089 no drift, regen 1085/1089 (99.6%, inside the 95% ground_probe tolerance), glitter 57/57 exact per band, MIs re-read live, map + folder saved, dirty 0, cycle begin/end packets under `Saved/Audit/SceneContext/L_MelusinaMorning/`. Stills `Saved/Audit/Screens/wc_morning_rainbow_bloom_*_2026-09-23.png` (FX-hidden diagnostic twin set at `Saved/Audit/Screens/wc_glitter_diag_2026-09-23/`). Driver proof `Saved/Audit/world_compiler_morning_rainbow_bloom_proof_2026-09-23.json` reads FAIL on strict per-band equality — true rung is PASS_WITH_NOTES (see defects). **Lane lesson:** a never-before-generated mesh (`SM_MelodyToken`, log `Waiting for static meshes to be ready`) makes the first generate silently fall back per-point — **generate twice after introducing a new mesh** (first pass: 0 tokens, +53 mis-fallbacks; regen: 57/57). **Open defects from this pass:** (1) all 17 re-placed `WC_NS_Morning_*` FX actors render as WHITE QUADS in SceneCapture (hide-test proven; meadow+tokens clean without them) — Niagara FX material lane, not WC; (2) `waterline_dolly` still is black (camera likely inside shifted geometry; 09-19 board was fine); (3) scene reads darker than the 09-19 board (sky/time drift, owner look call). Do not retune PPV/MPC for any of this.

Pass means the node is writing. The silhouette is still **73 two-bone strands**. Portfolio-grade flow waits on the multi-segment re-rig. Still: `Saved/Screenshots/WindowsEditor/HighresScreenshot00107.png`.

**Same build — jump/glide input:** grounded Jump on press, `StopJumping` on release so `JumpMaxHoldTime` can hold, no next-tick stop, no `MaxWalkSpeed` zero on that path; while falling, held jump requests Glide once (`bAwaitingGlideTap` removed). Feel pass stays the owner's.

**Closeout commit (local, not pushed):** `19fa3bab7`. Handoff: [`Docs/Handoffs/MELUSINA_HAIR_JUMP_CLOSEOUT_2026-09-22.md`](Docs/Handoffs/MELUSINA_HAIR_JUMP_CLOSEOUT_2026-09-22.md).

## MELUSINA RENDER-POLISH PLAN — 2026-09-23 (reconciled with the existing plans)

**Authorities, not replaced:**
- `Docs/Plans/MELUSINA_AAA_LOOKDEV_GRANDMASTER_PLAN_2026-09-22.md` (v7 gating list, waves W0–W8)
- `docs/plans/MELUSINA_ACCESSORY_CONVERGENCE_PLAN_2026-09-22.md` (`8f19f6485`: C0–C5, one wardrobe catalog)
- `.hermes/plans/2026-09-22_005015-melusina-ue-closeout-v5.md` (`dc9251365`: regalia U1–U8)
- `.hermes/plans/…v4-nikki-lissajous-closeout.md` (Nikki fabric bar N1–N4)
- `Docs/Plans/INFINITY_NIKKI_LOOKDEV_PLAN_2026-09-22.md` (L1–L5)

This section only records live state and the owner's order for tonight.

**Live state (PIE, runtime `BP_MelusinaJRPGCharacter`, 2026-09-23):**
- **Materials:** every body/wardrobe/iris MI is a child of `M_Master_Toon_Universal`; `MI_Melusina_Eyelash` is on `M_Master_Toon_Character`; the hair is `MI_Melusina_WaterHair_v10` on `M_Water_Master_Grand_v10_Substrate` (HANDS OFF per v7). **No Melusina MI is on the revived `M_Master_Nikki` fabric master yet.**
- **Blink:** the body has `eyeBlinkLeft/Right` morphs and the ABP curves animate (0→1 observed), but no blink has been seen. The static `EyeIrises`/`EyeLashes` don't deform with the lids.
- **Regalia (v5 U1):** `Exports/MelusinaFX_20260922/MelusinaFX_regalia_wings_rings_eval.fbx` is not imported; `/Game/Melusina/FX/Regalia20260922` doesn't exist. The animated flipbooks are imported (`/Game/EnvSandbox/Textures/MelusinaAnimated/20260922`) but not wired (v4 H3).
- **Baked hair/eye maps:** 24 maps are staged, and the guarded importer has not run.
- **FLIP drip:** another lane staged drip-bind stills 09-23 (`Saved/Audit/melusina_bake_staging_20260922/canonical_morning_pie_stage_*drip*`); `WaterHairFlipCache` is present but empty on the pawn.
- **VFX:** 19 Niagara components, all active at idle (11 are action/skill systems).

**Owner order (2026-09-23 evening):**
1. **Blink — WORKING, PIE-proven 2026-09-23.**
   - **Chain:** the ABP `BlueprintThreadSafeUpdateAnimation` timer (a blink every 3.5 s, `BlinkPhase` over 0.18 s, `BlinkAlpha = p(1−p)·4`) → `AnimGraphNode_ModifyCurve_1` (Blend, Alpha = `BlinkAlpha`) → `eyeBlinkLeft/Right`. All 120 skeleton curves are morph-flagged → the `eyeBlink*` morphs on `SK_Melusina_V2_Body`.
   - **Proof:** unlit close-up frames show a full open→half→closed→half→open cycle, and the lids fully cover the seated `EyeIrises`; a forced-morph A/B matches (`Saved/Audit/melusina_blink_20260923/`).
   - **Trap:** the idle clip carries no `eyeBlink` keys. Blink length is `min(dt,0.045)/0.18` per tick, so at the ~3 fps of a PIE capture it stretches to about 1 s — that's not a bug. `BlinkAlpha` is a variable, and `get_curve_value('BlinkAlpha')` always reads 0.
   - **Still open:** v7 W3 cornea-onto-`DEF_eye` stays long-term (for eye-look).
1b. **Fringe off the face — DONE 2026-09-23 (owner option A).**
   - **Finding:** no strand joint sits in front of her face (every root is ≥3.5 cm behind the eye plane). The card geometry of the four front bangs, `A_DEF_hair_bbone_000/006/010/012`, crossed her eyes. So a Kawaii face sphere would have done nothing on 2-bone strands (the v7 re-rig limitation).
   - **Fix:** four `AnimGraphNode_ModifyBone_0..3` in `ABP_Melusina_WaterHair` between LocalToComponent and Kawaii: additive rotation in `hair_root` space, (Pitch 8.7, Yaw 23.2, Roll −2.5) ≈ 25° about her lateral axis, which moves the bang tips ~4.5 cm back per 20°. Kawaii still simulates from the lifted pose. Compiled and saved.
   - **Proof:** unlit before/after, forehead and both eyes clear (`Saved/Audit/melusina_blink_20260923/bangs_before_after.png`).
   - **Hair material:** Jev `MI_OF_M_MASTER_NIKKI` 0.99 (no new master; a dedicated hair master deferred to post-render as a Nikki function layer, 0.93); slot split `WATER_SLOT_STAYS_WATER` 0.64.
1c. **Hair on `M_Master_Nikki` — DONE 2026-09-23.** A PIE slot-debug found that slot 0 `Water(Advance)` is the visible bulk of the hair; `Cosmos` and outline slot 2 barely render. Jev re-ruled with that fact: `MAIN_SLOT0_TO_NIKKI_KEEP_WATER_ON_COSMOS` 0.91, `PEARL_IRIDESCENT_AQUA` 0.95. New `MI_Melusina_Nikki_Hair`:
   - `Albedo` = `WhiteSquareTexture` (without it the master's `DefaultTexture` checker showed)
   - `BaseTint` (0.62, 0.88, 1.0)
   - PearlSheen (values from `MI_Nikki_Show_PearlSheen`)
   - Iridescence 0.35
   - ShadowDream

   `SK_MelusinaHair` slots: 0 → Nikki hair, 1 → `MI_Melusina_WaterHair_v10` (untouched), 2 and 3 → `MI_Melusina_Outline_005` (the dark strand edges now draw). Lit PIE proof in `Saved/Audit/melusina_blink_20260923/nikki_hair_lit.png`. Still open: the face reads dark in lit shots.
2. **Nikki masters on Melusina's materials.** Move the fabric slots to MIs of `M_Master_Nikki`: shirt `MI_Melusina_Material_008`, sleeve, shawl, bow, front panel, gloves. Keep skin, face, outline and eye on the toon family; the hair MI stays hands off. Duplicate before change and preserve params. Owner confirms the slot list.
3. **Imports:** regalia (v5 U1–U3 verbatim), flipbook wiring (v4 H3 / convergence C4 materials), baked maps (guarded importer). Each has its own evidence JSON.
4. **VFX idle set:** confirm activation paths, then `auto_activate` off for action systems.

Hero cameras are owner-framed; the `CAM_Hero_*` actors are placeholders.

## STAGING GOAL — owner-approved 2026-09-23 night ("stage all of it; doll-rig beginnings in use; stage wings + clockwork rings")
Everything goes on the canonical runtime `BP_MelusinaJRPGCharacter` (no second pawn, no new framework). Each step is saved + committed separately and PIE-verified; materials are MIs of `M_Master_Nikki`.
- **G1 Doll-rig beginnings:** the 12 `Portfolio/Staging_20260923/DollBall_*` (the doll-kit's porcelain ball joints; they share the eye meshes' character model space) become components on her joint bones (shoulder/elbow/wrist/hip/knee/ankle L/R), with model→bone relative transforms derived like the eyes (scale 9.2556), and a new porcelain MI. The full 15-segment `MEL_DollRig` body stays in Blender (different skeleton).
- **G2 Brows:** `Melusina_Brows_Export_20260922_L/R` + `MI_Melusina_Brows_Dark` on `head_x`, same model→face transform as `EyeIrises`.
- **G3 Regalia (v5 U1–U5):** import `Exports/MelusinaFX_20260922/MelusinaFX_regalia_wings_rings_eval.fbx` → `/Game/Melusina/FX/Regalia20260922/`; attach the wings and 3 clockwork rings behind her upper back; rings spin via RotatingMovement (outer +0.6, mid −0.42, inner +0.78 rad/s); Nikki MIs as placeholders.
- **G4 Idle VFX:** `auto_activate` off only for the action systems with a verified activation path.
- **G5 Body slot-3 sleeve override** → `MI_Melusina_Nikki_sleeve_003`.
- **G6 Evidence:** PIE stills + refreshed S1 draft.
- **RESULTS (2026-09-23 night):**
  - **G1 DONE** (`105493272`, `c17c105b2`). The doll-kit GLB is imported to `/Game/Melodia/Characters/Melusina/DollKit` (15 segments on `MEL_DollRig`, 16 balls, 4 gears); `IK_MEL_DollRig` + `RTG_Melusina_to_DollRig`; her CuteIdle is retargeted; `BP_MelusinaDollKit_Preview` (segments play the retargeted idle, balls and gears socketed at inverse-rest offsets, Nikki porcelain/brass MIs). `DollKit_Preview_Melusina` stands on the island-09 meadow of `L_MelusinaMorning`, animated in PIE. Jev: import+retarget+preview 0.88. Trap: Interchange import leaves assets unsaved — save the dirty `/DollKit` packages explicitly.
  - **G2 REMOVED:** the staged brows (R-head model space) don't land on the V2 face without a fit pass. The components were added and then deleted; the fit is a follow-up.
  - **G3 DONE** (`16616c245`, `ad004db23`). Regalia imported to `/Game/Melusina/FX/Regalia20260922` (force-added; `Content/*` is ignored), ×10 FBX units, under `RegaliaRoot` (= the body-mesh frame 0,0,−73 yaw −90), brass rings, pearl wings, NoCollision. The ring halo reads behind her upper back in every gameplay frame. The spin (3 RotatingMovement, pivot at ring centre, BeginPlay `SetUpdatedComponent`) starts correctly but **stalls after ~0.8 s** in PIE — follow-up. The wings carrier doesn't read yet (thin, same pearl as the hair).
  - **G4 NOT APPLIED — no activation path exists:** the 11 action/skill Niagara components are only attached at BeginPlay; there are zero Activate nodes in the BP and zero C++ refs. Turning auto-activate off would make them dark forever. The owner decides: keep them, or wire activation to skills.
  - **G5 DONE** (`5778f9d98`): body slot 3 → `MI_Melusina_Nikki_sleeve_003`.
  - **G6:** `Saved/Portfolio/ContactSheets_20260923/S1_Melusina_Gameplay_DRAFT_v2.jpg` (halo + doll companion).

## GOAL WHILE OWNER OFFLINE — 2026-09-23 ~19:20 (Jev `jev-1.13.0`)
The owner chose **face option 3**: leave the face tonight, since shots are mostly third-person; face-SDF shading comes after the renders.
- **Autonomous now:**
  - S1 third-person gameplay tiles, PIE-only with no saves: follow camera at meadow/spiral/rim/house, her facing down-sun, assembled as a 3×2 2400w JPG draft.
  - Read-only face-SDF (`bFaceSDF_UV1`) check.
- **Deferred to the owner (Jev):**
  - idle-VFX auto-activate trim (0.75)
  - BP body slot-3 sleeve override → Nikki (0.69)
  - regalia FBX import (0.66)
  - S3 Faraway level switch (0.96)
- **Owner-framed:** the S2 Morning views.
- **RESULT (autonomous hour):**
  - **S1 draft:** `Saved/Portfolio/ContactSheets_20260923/S1_Melusina_Gameplay_DRAFT.jpg` (2400×972, 3×2, captioned). Third-person follow-cam in PIE with her facing down-sun. Tiles: meadow crest, golden-spiral ascent (placed on tread instance 22), toward home, gazebo approach, wind through the bloom, rim overlook (weakest; swap candidate). Raw frames are in `S1_gameplay_raw*/`. The Choral Sheep companion is visible beside her.
  - **Seen:** a dark teardrop shows through the back of her hair in several tiles, likely the inner `Cosmos` water slot between strands.
  - **Traps:** in PIE the `BP_Morning_GoldenSpiral` spline reads as its 2-point default, but the generated treads are intact, so place things via the ISM instances. The island-09 top (z ≈ 1203) is the most photogenic walkable meadow.
  - **Face-SDF (read-only):** `M_Master_Toon_Universal` exposes `FaceSDF_Texture` (+ `bFaceSDF_UV1`), but **no face-SDF texture exists in the project**. Option 2 needs a face-shadow SDF bake + UV1 first, so it's post-render.

## WEBSITE CONTACT SHEETS — bounded plan, 2026-09-23 night (Jev `jev-1.13.0`)

Goal: three upload-ready sheets tonight; no new systems.
- **Sheets `THREE_SHEETS` (0.69):**
  - **S1, Melusina character:** front, ¾, side and back full body; a face close-up; a fabric detail. Blink proof is already done.
  - **S2, `L_MelusinaMorning`:** the meadow, spiral, rim overlook, house and FX.
  - **S3, Faraway Mother crystals:** the 3 existing `FM_Cam_UF_*` plus 3 more.
- **Capture `PIE_CAPTURE_WITH_FILL_LIGHT` (0.54 vs lit-only 0.45):** the proven PIE frame capture. S1 gets one temporary fill light spawned only in the PIE world, never saved. MRQ is out (0.01; untested tonight).
- **Framing `SCRIPTED_ORBIT_CHARACTER_OWNER_ENV` (0.88):** a deterministic orbit around the pawn for S1. S2/S3 views are owner-framed; each one is saved as a CineCamera from the viewport. The `CAM_Hero_*` placeholders get replaced.
- **Format `GRID_3x2_2400W_JPG` (0.66):** 6 tiles, 2400 px wide, JPG, titled captions. Output to `Saved/Portfolio/ContactSheets_20260923/` (Saved stays local by design).
- **Gates:**
  - Wait for the `M_Master_Nikki` shader compile before any capture (reparent→capture crash rule).
  - One PIE session per sheet.
  - The owner eyeballs each sheet before upload.
- **Known gap:** the body mesh's slot 3 gets `MI_Melusina_sleeve_003` through a BP component override, so it stays toon until that override is repointed.

## CANONICAL MELUSINA BLUEPRINT FAMILY — 2026-09-22

**Ultimate means the existing runtime class:** `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter`. Keep its asset name and current game-mode selection. Do not create a second `BP_Ultimate_Melusina` or move working locomotion/Rokoko, Universe Foundry, wardrobe, or Niagara behavior into a parallel owner. The owner confirms locomotion, Rokoko, and the required Foundry integrations are proven and working; this review accepted that status and did not rerun their gates.

Jev System One selected the existing runtime BP as Ultimate (confidence 1.0), reversible documentation-first deprecation for unused roots (0.83), and a single-authority visual-first delivery slice (1.0). Jev also selected keeping the distinct battle-presentation role (1.0) and current Rokoko animation authority (1.0). These are bounded choices, not new runtime systems.

| Blueprint path | Classification | Current disposition |
|---|---|---|
| `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` | Runtime character; selected by `BP_MelodiaJRPGGameMode` on configured route maps | Canonical/Ultimate, retain name and authority |
| `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation` | Separate battle/presentation actor | Retain; it is not a second exploration pawn |
| `/Game/Characters/Melusina/BP_Melusina` | Old standalone character BP; zero asset referencers in the audit | Deprecation candidate; quarantine only after a fresh referencer check |
| `/Game/Melodia/Characters/Melusina/bp_melusina` | Legacy `MelodiaSmokeCharacter`; prior live Asset Registry inspection found only orphan `/Game/Melodia/_PROJECT/BP_MelodiaGameMode` as referrer | Reversible pair candidate; recheck references before any move |
| `/Game/Experiments/MelodiaJRPG/Skills/BP_Melusina{TrueStrike,Tidecall,PetalCadence,LullabyMend,FocusAttack,DoubleHit}` | Six combat-skill Blueprints | Keep as skills; not character variants |
| `/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell` | Room-shell actor | Keep; not a character |

The current disk scan lists 11 matching `BP_Melusina*` `.uasset` paths. The smoke package appears once on disk as `bp_melusina.uasset`; the live asset search and Git report it with different casing. Treat it as one Unreal package and never remove it by spelling directly from disk. The prior live Asset Registry inspection found three referencers for the canonical runtime BP, zero for `/Game/Characters/Melusina/BP_Melusina`, and zero for the orphan smoke GameMode; those referencer results have no saved receipt, so repeat them before package moves. The six skills are `BP_MelusinaDoubleHit`, `BP_MelusinaFocusAttack`, `BP_MelusinaLullabyMend`, `BP_MelusinaPetalCadence`, `BP_MelusinaTidecall`, and `BP_MelusinaTrueStrike`. LullabyMend and Tidecall had no Asset Registry references in the prior inspection; keep them because that does not rule out data/soft references. `BP_MelusinaRoomShell` is a referenced house/PCG actor. Animation Blueprints are supporting assets, not extra pawn authorities.

**Convergence contract.** `Tools/universe_foundry.py` remains the authoring pipeline; runtime consumes its outputs through existing gameplay contracts. Keep the verified locomotion/Rokoko chain in its existing animation authority. The runtime BP composes those owners and its 13 directly attached unique Niagara systems; do not add another locomotion graph, animation controller, Foundry manager, or VFX framework. The battle actor stays a separate presentation role.

**Visual and bake work still open.** Build one contact sheet for the 13 attached systems,
showing full systems and enabled/disabled emitters (including the three Globules sockets and
paired EyeSparkles). Blender staging has 24 hair/eye maps and 240 numbered FLIP frames; the bake
evidence's 480 nonempty BOBJ count includes 240 preview files, so neither number is UE import
proof. `final_bake_verify.json` is `pass=false` / `pass_with_limitations=true`: HairB BaseColor
remains a measured self-occlusion limitation.

**FLIP archive gate 2026-09-22 — Blender PASS, UE import still owed.** The earlier
`flip_surface_sequence.abc` includes 240 per-frame names plus `Camera` and `Cube`; the first
isolated-scene `flip_surface_sequence_single_track.abc` is static at frames 1/120/240; and the
Geometry Nodes `flip_surface_sequence_gn_single_track.abc` imported as 240 mesh tracks. All three
remain excluded from UE. The approved `flip_surface_sequence_animated_single_track.abc` was
exported from one persistent Blender mesh with a zero-strength Smooth modifier and `global_scale=100`.
Its Blender import round-trip found one mesh track with a Mesh Sequence Cache modifier, exact
vertex/triangle matches on all 240 source frames at 24 fps, and centimeter-scaled bounds matches
at frames 1/120/240. Archive: 290,327,257 bytes, SHA256
`8e47c10ec16e52171610b4a04e39e398afc98733a99a136addec25d1d266f589`; receipt
`Saved/Audit/melusina_bake_staging_20260922/flip_alembic_export_animated_single_track_evidence.json`.
The exporter `Tools/Blender/melusina_bake_staging_20260922/flip_alembic_export_animated.py` and
the local import runbook under `Exports/MelusinaBakeStaging_20260922/UE_import/` are ignored by
Git; promote the exporter deliberately before claiming a reproducible checked-in tool. Isolated
three-quarter renders at frames 1/60/120/180/240 show a vertical fluid column spreading into a
broad pool, consistent with the staged FLIP Drip/Sheet inflows. The owner clarified this is the
**drip layer of her water hair**, not replacement strand geometry. Corrected live Jev choice
(`jev_flip_role_choice_corrected.json`, confidence 1.0) supersedes an earlier choice framed as
strand hair: stage one Geometry Cache after the editor writer slot clears, preview alignment,
timing, scale, silhouette, and restart playback with the existing WaterHairMesh, then attach it
to the canonical pawn only if those gates pass. The old v22 importer treats Geometry Cache as
the hair body and allows replacement; it is not the importer for this supporting drip layer. Review
images are under
`Saved/Audit/melusina_bake_staging_20260922/contact_sheets/flip_archive_samples/`.

The current Blender sequence has all 240 numbered frames, a fresh review sheet at `Saved/Audit/melusina_bake_staging_20260922/contact_sheets/render_sequence_sheet_final_20260922.png`, and a `render_sequence_evidence.json` receipt reporting PASS for frame presence and measured motion. It is not a portfolio render: the heroine reads as a dark silhouette, her face is obscured by the hair, and the harp sits detached at frame right. Live Jev selected a runtime face-first capture slice (confidence 0.970; redacted receipt `Saved/Audit/melusina_bake_staging_20260922/jev_visual_choice.json`) before committing source hair, material, or prop repairs. Use the existing portfolio capture setup and assess those repairs from the truthful Unreal image. Read-only inspection of `harp_wip_stage_src.blend` at frame 60 found `Hair Strand.004/.007/.010` parented to `character_rig` with object origins `(0,0,0)`, matching the body mesh's rig-root origin while their geometry bounds sit around the head. This is standard skinned-mesh space, not evidence of a bad pivot. Preserve the runtime inverse-bind attachment offset; correct the face readability/material and harp placement through their owning source/shot, not by zeroing the hair origin or adding a runtime compensation.

The U2 Blender archive gate passed; UE import remains unverified. The last editor query found no
texture parameters on the named water master or water-hair MI, so import of the 24 staged textures
can proceed separately from material wiring. A guarded offline draft importer is staged at
`Saved/Audit/melusina_bake_staging_20260922/ue_import_approved_bakes_20260922.py`: explicit
preflight/textures/cache phases pin the approved source hashes, require empty new package paths,
and preserve the existing BP, meshes, MIs, and level. It has not run. Do not invent a new master
or runtime material owner.
An Unreal Editor and Monolith are live, but another Claireon/MCP lane owns that editor; the
latest read-only handoff reported five dirty packages, including `ABP_Melusina_Current`. Asset
import, Niagara previews, and the runtime portrait await a confirmed single-editor writer slot.
No locomotion, Rokoko, or Universe Foundry retest is
required by the owner-confirmed status.

For the Niagara sheet, no saved full-system image of the 13 attached systems was found in the current targeted preview/screenshot folders; the 2026-09-21 `audit_niagara.json` is structural only (`isolated_preview_non_black: null`). The offline 13-system/22-emitter card manifest is `Saved/Audit/melusina_bake_staging_20260922/niagara_capture_manifest_20260923.json`; it keeps enabled/disabled counts null and separates runtime component names from presentation-only sockets. Capture one consistently framed Monolith `preview_system` image per unique system, then build 13 labeled cards with the BP component role, verified socket, and live enabled/disabled emitter counts. Label these as isolated previews, not runtime proof. Paired EyeSparkles and the three Globules mounts are repeated uses of shared systems and remain intentional. The unattached `NS_Melusina_ImpactBurst` and `Melusina_WaterFX` are separate retirement candidates only after fresh reference and gameplay-cue checks. Under the Infinity Nikki lens, prioritize FX that read as responsive character cues and reveal the magical field; do not merge effects based on structural similarity alone.

The same 2026-09-21 audit reported `flipbook_authority_ok=false` and one duplicate flipbook-material hit on `NS_Melusina_EyeSparkle`; its detailed `systems` list covers eight systems, not the full 13. Re-read current material references before changing any Niagara asset. This is an existing authority drift candidate, not a reason to create another VFX framework.

**Hair offset is not a free transform to zero.** The saved `WaterHairMesh` relative Y offset `144.1994` and roll `-90` are part of the current inverse-bind attachment to `head_x`; changing them blindly can displace the hair. The observed render problem is face readability and composition, not yet a demonstrated source-origin mismatch. Compare the staged Blender origin/bind against the live attachment, fix the source pivot only if that comparison proves the mismatch, then capture the runtime unit in an isolated portfolio view. Do not add a compensating runtime offset.

**Tonight / next (not this commit):** eye the Morning still for seat; re-read `bBoneSubdivisionCollisionOnly` live (disk ABP still reported `true` on reopen); multi-segment hair re-rig for real flow; owner jump feel; root-motion locomotion re-export; cornea / fingers / environment. Do not retune Kawaii to fake curvature.

---

## 1. What the game is

A solo rhythm-JRPG. QuillScript owns narrative; the TurnBased JRPG template owns party, turns,
damage, inventory and saves. Rhythm timing rides on top of JRPG commands, outfits grant traversal,
and played phrases unlock the world. Shape: OMORI. Music-as-key: Zelda. Wardrobe bar: Infinity
Nikki. Architecture detail: [`SYSTEM_MAP.md`](SYSTEM_MAP.md), [`DATA_FLOW.md`](DATA_FLOW.md).
Settled decisions: [`_DECISION_LOG.md`](_DECISION_LOG.md).

---

## 2. What works — and how strongly it is proven

Evidence ladder (never collapse levels): SOURCE BUILT → LIVE PROVEN → RESTART PROVEN →
PACKAGED PROVEN.

### PROVEN CREATIVE CAPABILITY SURFACE - BUILD WITH THIS NOW

This is the affordance map for a fresh agent. It is not a claim that every possible Chapter or
asset is already finished. `LIVE PROVEN` means a current receipt, ledger row, or PIE proof exercised
the named seam. `RESTART PROVEN` and `PACKAGED PROVEN` are stronger, separate levels. `PRESENT /
SOURCE-TOOL PROVEN` means the source, plugin, generator, or asset family exists and has been checked;
it does not mean a live UE cook or finished content. `SCAFFOLDED` means the contract is useful but
still has a named proof or integration blocker.

**Default:** author content through these seams. Boss battles, new rhythm skills/attacks, side
quests, encounters, creature episodes, outfit abilities, and musical world puzzles are now content
problems. They do not require another gameplay framework or another authority.

#### Gameplay and content authoring

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| QuillScript narrative and encounter authoring | **LIVE PROVEN (scoped)** - authored `MelodiaQuillSmoke` drives the integration proof; the allowlist contract is checked by [`test_qsc_allowlist_contract.py`](Content/Python/Tests/test_qsc_allowlist_contract.py) | `Plugins/QuillScript/`, `Content/MelodiaIntegration/Narrative/*.qsc`, `UMelodiaNarrativeSubsystem`, `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig` | Dialogue, choices, encounter intent, consequence and reward content | A new dialogue runtime, quest authority, or parallel notification bus |
| Chapter scaffold and stable IDs | **SOURCE + CONTRACT PROVEN; existing package has a known validation failure** - [`scaffold_chapter.py`](Tools/scaffold_chapter.py), [`test_scaffold_chapter.py`](Tools/test_scaffold_chapter.py), [`test_melodia_chapter_content_package_contract.py`](Tools/test_melodia_chapter_content_package_contract.py), `Chapters/_template/`; scaffold regression passes, while existing Shorewake IDs still fail the broader QSC contract | `Chapters/_template/{quill,maps,encounters,rewards}`, `Tools/scaffold_chapter.py`, `specs/progression/` | New Chapters, side quests, creature Episodes and reusable encounter/reward packages with gated IDs | A new chapter loader or hand-authored ID convention; validate the IDs and use the scaffold |
| Quill encounter -> JRPG battle -> rhythm -> typed result -> Quill resumes once | **LIVE PROVEN (scoped owner seams)** - [`ue_level_building_coinsheet_2026-09-01.json`](Saved/Audit/ue_level_building_coinsheet_2026-09-01.json) records `battle_integration_map` pass for unavailable/victory/defeat/fled, typed results and exactly-once Quill resume; the separate `rhython_grade_to_result` row proves grade-to-damage. This is not a fresh packaged golden run | `MelodiaExternalJRPGBridgeSubsystem`, `MelodiaNarrativeSubsystem::CompleteBattle` / `ResumeQuillOnce`, `MelodiaIntegrationMap`, `MelodiaQuillSmoke` | Boss battles, normal encounters, authored phase consequences, rewards and checkpoints | A new battle manager, transition graph, combat result type, or second Quill resume path |
| Rhythm grade affects authoritative JRPG combat | **LIVE PROVEN** - `FMelodiaRhythmGradeBoundaryTest`, the `rhython_grade_to_result` ledger row, and `MelodiaRhythmCombatSubsystem` verify Q/W/O/P grade data reaches the stock skill damage path. 2026-09-17: `DA_CrescendoWave`, `DA_DissonantSilence`, `DA_DownbeatBreak`, `DA_HarmonyShield`, `DA_TempoShift` existed fully authored but were never wired into `RegisterSkill` in `BP_MelodiaJRPGGameInstance` (only `DA_CadenceStrike`/`DA_ResonantArc`/`DA_LullabyMend` were) — added the missing `RegisterSkill` calls; live PIE confirms all 8 skill IDs now resolve via `MelodiaRhythmCombatSubsystem::find_skill` on fresh boot. Full in-battle rhythm-prompt UI feel-test still blocked by an unrelated pre-existing `BP_BattleController`/`BP_BattleBase` bug (`battleUI`/`playerUnits` never populate outside the normal encounter-trigger flow, causing a runaway loop in `GetReadyUnitsBasedOnSpeed`) | `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.cpp`, authored `UMelodiaRhythmSkillDefinition` / skill data, `Content/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance` | New rhythm skills, attacks, patterns, grade-driven damage, healing or resource effects | A second damage formula, rhythm combat authority, or bespoke boss combat framework |
| Wardrobe, traversal and gameplay capability hooks | **LIVE PROVEN + RESTART PROVEN baseline** - `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, [`P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`](Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md), and the restart slot proof pass | `Plugins/MelodiaWardrobe/`, `UMelodiaWardrobeSubsystem`, `MelodiaTraversalComponent`, wardrobe catalog manifests | Outfit abilities, traversal gates, creature/world relationships and battle/rhythm affordances | A new outfit inventory, equipment owner, traversal capability registry, or cosmetic-only workaround |
| Music-as-key world unlock | **LIVE PROVEN (scoped)** - the coinsheet receipt records one idempotent Piano phrase -> typed world result -> visible route; [`music_world_key_real_input_2026-08-31.json`](Docs/Evidence/music_world_key_real_input_2026-08-31.json) and [`P0_REAL_INPUT_PROBE_2026-09-09.json`](Docs/Evidence/P0_REAL_INPUT_PROBE_2026-09-09.json) provide route/input evidence | `Content/Melodia/_PROJECT/Blueprints/Gameplay/BP_MusicManager.uasset`, `MelodiaMusicClockSubsystem`, Quill world-result path, `Content/Python/build_pcg_piano.py` | Musical world puzzles, phrase-locked routes, keys, shrines and side-quest progression | A new puzzle framework, second music clock, or one-off door/route authority |
| Choral Sheep companion and Harmonize | **LIVE PROVEN (PIE behavior + REST/HIT fleece stills 2026-09-20)** - 2026-09-13 morning probe plus 2026-09-20 `ApplyChoralSheepDefinition` true / `TryBeginHarmonize` true / weight 1.0→0.0. Visual lock: `MI_ChoralSheep_Body` → `M_Master_Toon_Character`; child `MI_ChoralSheep_Body_Chladni_C` + `T_Chladni_C_ROOT`. REST still is dark wool; HIT still shows blue Chladni contours (`Saved/Audit/Screens/ship_queue_fleece_{REST,HIT}_v2_clean.png`) | `Content/Melodia/Companions/ChoralSheep/`, `BP_ChoralSheep`, `DA_ChoralSheepDefinition`, `MelodiaCompanionComponent`, `TryBeginHarmonize` | Creature Episodes, companion abilities, creature reactions and harmony moments | A new companion framework, ad-hoc creature state, or rig reopening without a current defect |
| Save, checkpoint and reward ownership | **LIVE/RESTART PROVEN for the baseline; long-chain repeat proof remains open** - `UMelodiaNarrativeSubsystem` owns authored checkpoints/consequences and exactly-once transactions; stock JRPG owns its save state; [`ue_level_building_coinsheet_2026-09-01.json`](Saved/Audit/ue_level_building_coinsheet_2026-09-01.json) records wardrobe restore. Issue #51 remains the explicit long-chain gate | `MelodiaNarrativeSubsystem`, `MelodiaSaveRecoverySubsystem`, `MelodiaSaveSlotLibrary`, `BP_JRPGSaveGame`, canonical reward/flag paths | Checkpoints, reward claims, side-quest completion, route restoration and durable episode history | Direct SaveGame writes, duplicate reward registries, or a new save authority |

#### Procedural worldbuilding and musical fields

The productive affordance is real: the proven Sea Above path enriches PCG points with a Resonance
float and packs it into per-instance custom data for material response. Musical/cymatic data can
drive geometry, scatter and material/Niagara response. Use that lane; do not manually place every
instance or invent a new world signal system.

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| UE 5.8 PCG and PCG Extended Toolkit | **PRESENT / SOURCE-TOOL PROVEN; LIVE PROVEN in scoped graphs** - `BS_GodFile.uproject` enables `PCG`, `PCGPythonInterop` and `PCGExtendedToolkit`; `Plugins/PCGExtendedToolkit/PCGExtendedToolkit.uplugin` targets UE 5.8; Sea Above receipts and offline contracts cover the current graph path | UE PCG graphs, `Plugins/PCGExtendedToolkit/`, `Content/Python/pcg/`, existing `/Game/EnvSandbox/PCG/` authorities | Procedural biomes, musical architecture, scatter, falloffs and setpieces | Hand-authored actor forests, a new scatter framework, or a parallel PCG graph authority |
| Resonance Ecology processor and instance material bridge | **LIVE PROVEN on 1 Sea Above graph; reusable editor tooling for the remaining graphs** - current state records `PCG_East_PhyllotaxisCourtyard` at 140 instances with Resonance 0.030-0.925 and one custom float; [`SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json`](Docs/Evidence/SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json) records placement/runtime pass and no parallel graph | `Content/Python/pcg/resonance_ecology_processor.py`, `Content/Python/pcg/apply_resonance_to_sea_above.py`, `Content/Python/pcg/test_resonance_ecology.py`, existing Resonance Cathedral/Sea Above graphs | Cymatic ecology bands, musical density, material variants and resonance-driven geometry/scatter | Hardcoded biome bands, per-asset custom scripts, or another PCG enrichment authority |
| World Field Bus Resonance/Tension contract | **SCAFFOLDED / SOURCE CONTRACT - not LIVE PROVEN** - `MelodiaWorldFieldBus.*` defines `ResonanceN/M`, `Tension`, `BeatPulse` and position sampling; [`world_field_bus_probe_2026-09-02.json`](Saved/Audit/world_field_bus_probe_2026-09-02.json) says SCAFFOLD and the PIE note records parameter-name alignment still open | `UWorldFieldBus`, `MelodiaCymaticsSubsystem`, `MelodiaOceanologyWaterBridgeSubsystem` | A shared future field for cymatic water, PCG and material consumers once the contract is closed | Another global bus, guessed MPC parameters, or claiming the current scaffold is a live contract |
| Sea Above musical PCG proof | **LIVE PROVEN (scoped) / not full route certification** - [`SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json`](Docs/Evidence/SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json) is `PLACEMENT_RUNTIME_PASS`; current state records 1 of 9 Resonance Ecology graphs. [`P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json`](Docs/Evidence/P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json) is `PASS_SCOPED`, with visible-frame/focused-player/package work still open | `LV_SeaAbove_Prototype`, existing PCG graph authorities, `Content/Python/pcg/apply_resonance_to_sea_above.py`, `Docs/Evidence/P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json` | Author a musical biome or setpiece now, while keeping the uninterrupted player route and visual-capture boundary honest | A new Sea Above world framework or a claim that every graph/consumer is already live |
| Resonant World generator + World Compiler | **SOURCE/TOOL PROVEN + LIVE PROVEN scoped on `L_MelusinaMorning`** — flowers on **BrushifyIsland_*** only; dressing (`brushify_overgrowth` / `brushify_roots` / `brushify_bush`) on `WC_EscherWalk_*` plus island skirts. Bedroom / classic_arch / Sphere3D / `WC_DellFloor` never plantable. 2026-09-18 compile **1090** points (971 flowers + 119 dressing) / **1079** PCG ISMs; `WC_morning_rainbow_bloom_Field` pinned to island AABB. `WC_Lookdev_waterline_dolly` at `[-3100,200,180]` roll 0. No Landscape, no PCG graph rewrite, no MPC/PPV writes. Compile stays CLI. Proof [`world_compiler_morning_rainbow_bloom_proof_2026-09-18.json`](Saved/Audit/world_compiler_morning_rainbow_bloom_proof_2026-09-18.json), close-out [`camera_dressing_closeout_2026-09-18.json`](Saved/Audit/camera_dressing_closeout_2026-09-18.json). Substrate Toon A/B remains PARK. | [`WORLD_COMPILER_CONTRACT.md`](Docs/WorldGen/WORLD_COMPILER_CONTRACT.md) §6.1, `Tools/world_compiler.py`, `Content/Python/world_compiler_ue.py`, `Content/Python/world_compiler_panel.py`, `recipes/morning_rainbow_bloom.v1.json`, `Content/Python/resonant_world_generator.py`, `Tools/terrain_handoff.py`, `Tools/scaffold_chapter.py` | Compile a recipe into PCG-driven dressing (point field + band MIs + signal bindings) without a new authority | A new scatter framework, Python-wired PCG graphs per species, `new_object` ISMs, a second MPC writer, a second compiler inside EUW, Houdini Engine as a live overlay |

#### Houdini, Hython and Copernicus production lane

This is an available production lane, not a research-only idea. The evidence boundary is important:
Houdini 22 Hython is healthy and the Copernicus/HDA generators, manifests and asset families are
present; current `origin/main` does **not** contain a receipt proving a custom HDA cooked and baked
inside UE. License/editor-cook proof remains intentionally unpromoted.

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| Houdini Engine plugin in UE 5.8 | **PRESENT / SOURCE + PREFLIGHT PROVEN; LIVE UE HDA COOK NOT PROVEN** - [`HoudiniEngine.uplugin`](Plugins/HoudiniEngine/HoudiniEngine.uplugin) is H22.0.368/UE 5.8 and `BS_GodFile.uproject` enables it; [`smoke_houdini_engine_pcg.py`](Content/Python/smoke_houdini_engine_pcg.py) checks the plugin/hython/project; the smoke/spec still record license and editor-cook steps as pending | `Plugins/HoudiniEngine/`, `BS_GodFile.uproject`, `Content/Python/smoke_houdini_engine_pcg.py`, `hda/README.md`, `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` | HDA geometry, procedural stairs/chords, Houdini-authored production geometry and design-time bake to UE meshes/HISM/Nanite | A new UE procedural bridge; use the HDA lane when the license/cook gate is actually available, with PCG/Python as fallback |
| Hython procedural generation and deterministic handoff | **SOURCE/TOOL PROVEN; output families are receipt-backed, not a live UE cook claim** - [`hython_monolith_bridge_report.json`](Saved/Audit/hython_monolith_bridge_report.json) records Houdini 22.0.368, `hou_available`, and a healthy Hython lane; manifests record seeds, outputs and hashes | `Tools/Houdini/`, `Tools/Houdini/copernicus/`, `Content/Python/create_hda_arpeggio_stair.py`, `Saved/Audit/copernicus_cymatic_manifest.json` | Deterministic geometry/HDA generation, seeded variants, reproducible handoff into UE | One-off exported meshes without seed/manifests, or a bespoke procedural backend |
| Copernicus texture/material generation | **PRESENT / SOURCE + OFFLINE ASSET PROVEN; live UE/HDA handoff not proven** - [`copernicus_dress_bake.py`](Tools/Houdini/copernicus/copernicus_dress_bake.py) builds the SOP -> COP network; [`README.md`](Tools/Houdini/copernicus/README.md) documents the COP/ROP path and contracts; Hython and output manifests are audited | `Tools/Houdini/copernicus/copernicus_dress_bake.py`, `copernicus_fabric_sheen.py`, `copernicus_terrain_height_to_nanite.py`, `copernicus_petal_variants.py`, `Content/Python/verify_tex_contract.py` | Dress/fabric sheen, masks, curvature/thickness/AO, terrain-height -> Nanite, petal and material variants | Ad-hoc PIL-only material baking, a new texture pipeline, or making live HDA cooking a hidden dependency |
| Cymatic PBR map families | **PRESENT / SOURCE + ASSET PROVEN; live material import/build remains separate** - [`cymatic_audit_2026-09-01.json`](Saved/Audit/cymatics_audit_2026-09-01.json) and [`cymatics_present_status.json`](Saved/Audit/cymatics_present_status.json) record valid on-disk families and offline wiring while noting live import/build work; `copernicus_cymatic_parallax.py` defines seeded Chladni/cymatic families and nine-map output | `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py`, `Saved/Audit/copernicus_cymatic_manifest.json`, `Saved/Audit/copernicus_cymatic/`, `Saved/Audit/cymatics_present_status.json` | Cymatic stone, fabric, sheen, masks, animated/flipbook variants and material dressing | A new master shader or untracked texture family; extend the existing map/MPC contracts |

#### Materials, cymatics, shaders and presentation

The material convention is scalar MPC data, not a new master per effect: `MPC_Melodia_Palette`
is the audio source, `MPC_Cymatics_Driver` is the cymatic driver, and the existing driver fields
include `Cymatic_BassIntensity`, `Cymatic_MidIntensity`, `Cymatic_BeatPulse`,
`Cymatic_EmissiveScale`, `Cymatic_IridescenceShift`, `Cymatic_UVDistortion` and
`Cymatic_ModeN/M`. `WorldField.ResonanceN/M` and `WorldField.Tension` are bus-struct fields, not
MPC parameters; the water bridge maps them to its consumer contract. Extend those existing
contracts and the canonical masters when a new reactive variant is needed.

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| Nikki-derived toon/material path | **PRESENT / ASSET + SOURCE PROVEN; scoped live use** - `M_Master_Toon_Character.uasset` and `M_Master_Toon_Universal.uasset` are tracked; Sheep proof binds `MI_ChoralSheep_Body` to the approved character master with Chladni as a child | `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Character.uasset`, `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.uasset`, `Content/Melodia/Companions/ChoralSheep/`, [`CHORAL_SHEEP_RETARGET_DEFORMATION_PROOF_2026-09-13.json`](Docs/Evidence/CHORAL_SHEEP_RETARGET_DEFORMATION_PROOF_2026-09-13.json) | Author new hero, creature, outfit and biome material variants while keeping the current toon identity | A new master-material architecture or replacing the Nikki-derived base with a parallel shader |
| Audio-reactive presentation and cymatics driver | **SOURCE + SCOPED LIVE PROVEN** - the audio palette writer and read-only Cymatics runtime are scoped-live proven; the dedicated driver writer is source/asset proven and remains a separate material contract. Sea Above pulse/mode/amplitude automation is `PASS` with one audio writer | `MelodiaAudioReactivePresentationSubsystem.*`, `MelodiaCymaticsSubsystem.*`, `MelodiaCymaticsWriterSubsystem.*`, `Content/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.uasset`, `Content/Melodia/Cymatics/MPC_Cymatics_Driver.uasset`, `Docs/Evidence/P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json` | Audio-reactive materials, Chladni response, beat/mode/tension-driven water, Niagara and surface presentation | A second audio writer, a second MPC contract, or a new master shader for each variant |
| Chladni/cymatic shader automation | **PRESENT / SOURCE PROVEN; consumer-specific visual proof varies** - `Source/MelodiaShader/Shaders/` contains the shader module; Chladni sampling and material automation scripts are present; use the current PPV/material receipts for visual proof | `Source/MelodiaShader/Shaders/`, `Content/Python/assign_toon_profiles.py`, existing MPC contracts | Reactive shader/material variants and automated parameter application within the frozen identity | Hand-guessed parameters, per-widget/per-material constants, or a new universal master |
| Frozen PPV, Niagara and flipbook presentation stack | **OWNER-APPROVED / LIVE PROVEN scoped** - [`PPV_STENCIL_PIE_2026-09-13.json`](Docs/Evidence/PPV_STENCIL_PIE_2026-09-13.json) and the current identity record in this file prove the frozen visual boundary; canonical Niagara effect types and companion VFX assets are tracked, while visual work remains asset-specific | Frozen `PPV_NikkiDream` stack, `Content/Melodia/VFX/EffectTypes/ET_Melodia_CharacterFX.uasset`, `Content/Melodia/Companions/ChoralSheep/VFX/`, `Tools/Houdini/sea_above_reef/shorewake_animated_flipbook.py`, `Content/Python/import_flipbooks.py`, `UMelodiaAudioReactivePresentationSubsystem` | Storybook identity, audio-reactive VFX, canonical Niagara effects, flipbook shimmer and polished captures | A new post-process identity, duplicate Niagara framework, or a “fancy VFX” system outside the canonical stack |

#### UI authoring

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| Melodia UI artist skill and existing Quill UI chain | **PRESENT / SOURCE-TOOL PROVEN; audit workflow established** - both agent skill copies define the token SSOT, Quill widgets, audit and editor apply workflow; current state records the read-only inventory of 144 widget Blueprints / 955 styled widgets | [`.claude/skills/melodia-ui-artist/SKILL.md`](.claude/skills/melodia-ui-artist/SKILL.md), [`.agents/skills/melodia-ui-artist/SKILL.md`](.agents/skills/melodia-ui-artist/SKILL.md), `melodia-design-system/tokens.json`, [`ui_style_audit.py`](Tools/ui_style_audit.py), `Content/Melodia/UI/Quill/`, `Content/Python/assign_melodia_quill_presentation.py` | UI polish, new dialogue/selection screens and authored screens that match the current identity | A new widget framework, manual style guesses, or hand-editing `.uasset`; load the skill first |

**Concrete authoring example:**

```text
Quill boss intent (allowlisted encounter ID)
  -> Phoenix skill/action (authored JRPG skill data)
  -> existing rhythm phrase/session
  -> Q/W/O/P grade
  -> Phoenix authoritative damage/result
  -> Quill consequence, reward and checkpoint
```

The current proof covers the owner seams needed for this shape. Author the boss's IDs, skill data,
phrase, dialogue, consequence and reward through those entry points; do not design another battle or
rhythm framework. Keep the packaged golden-run and long-chain persistence gates separate until they
have their own evidence.

**Tutorial instance — Melody Slime first tide (authored 2026-09-18, PIE proof still owed):**
`SlimeTideCurrent` + `Chart_Tide_Wave` transcribed to `DA_MelodySlimeTutorialSongs` ("Tide Wave",
12 eighth-notes, 128 BPM) + `DA_TideWave` (`tide_wave`, auto-discovered by the subsystem scan) +
`BP_MelusinaTidecall` (stock skill, PetalCadence behavior) mapped in `StockSkillRhythmIds` (6/6
entries preserved) + `MelodiaQuillSlimeTutorial` (30 compiled statements, battle/quest/reward/flag
notifies verified) with allowlisted `melodia_slime_tutorial` / `quest.slime_tutorial.first_tide` /
`reward.slime_tutorial.tidecall` / `flag.slime_tutorial.completed`. MorningIntro carries
`mel_perch_01` + `mel_battle_entry` voice cues (compiled). `BP_MelodySlimeTutorialBattle` roster is
`{slime: chance 1.0, lvl 1}` with `fleeChance 100`. Wired 2026-09-18 (commit 593ef613e):
battle actor tagged `melodia_slime_tutorial` (actor package force-added, one-time),
`Morning_QuillTrigger_SlimeTutorial` placed at the battle actor in the persistent level with
`QuillScriptToPlay` resolved to the tutorial QSC, map + 3 external packages saved, dirty 0,
pushed 0 0. Still owed: Tidecall display-text check + the real-input PIE
proof (victory/defeat/flee + exactly-once resume). `MI_MelodySlime_Body` (toon master, Tide tint,
canonical Chladni, `BeatAccent 1.5`) is presentation-ready; the unit still wears the mannequin
until the visual swap is judged. Breath wired 2026-09-18: tick-driven squash-and-stretch on
`SlimeMesh` (`Sin(time)` through mirrored `MapRangeClamped` ±5%, XY swell against Z settle,
parent Tick preserved, 0 errored BPs); beat-pulse rides the existing driver→master path.
Skin bound 2026-09-18: `SlimeMesh.OverrideMaterials[0]` now wears `MI_MelodySlime_Body`
(the mesh slot alone wore plain `Material_002`); master carries the full reactive
vocabulary (`BeatAccent`, `Chladni*`, `HarmonizeActive`, 31 params).

**Zundamon battle unit + Morning exploration platform crossing (authored 2026-09-18):**
`ABP_Zundamon_Battle` (`target_skeleton = SK_Zundamon_Skeleton`, duplicated from the stock
`A_BattleAnimationBlueprint`) plus `AM_Zundamon_Attack`/`AM_Zundamon_GetHit` montages are compiled
and saved. `BP_WeakEnemy`'s `BeginPlay` now sets `SkeletalMeshAsset`/`AnimInstanceClass` to the real
Zundamon mesh/ABP (a per-child graph override, not a CDO write, so the shared `BP_UnitBase` parent
and its other children stay untouched); live PIE confirms `BP_WeakEnemy_C_*` spawns with the real
mesh. **Known gap:** `Content/TurnBasedJRPGTemplate/Blueprints/Units/EnemyUnits/*` is excluded by
`.gitignore` (line 178), so `BP_WeakEnemy`'s wiring cannot be committed — it exists only on this
machine's disk and must be redone if that file is ever lost. `L_MelusinaMorning`'s ~46-piece
`WC_EscherWalk_*` blockout was redesigned into one continuous golden-ratio spiral (φ-scaled radius
per turn, five Fibonacci-fraction clearings) connecting the real `BrushifyIsland` terrain, with
`BP_Starskiff_MK2` relocated to water level at the spiral's base. The four pre-existing, never-wired
`MelodiaMovingPlatform` actors near the spiral's summit spur (previously default blockout values,
`bAutoStart=false`) are now a real crossing: repositioned into a bridge line to a new landing piece,
`bAutoStart=true`, staggered `TravelDuration` (1.6-2.6s) so their vertical ping-pong drifts out of
phase over time — confirmed moving via two live PIE position reads (DedicatedServer net mode, no
relay/Blueprint-graph wiring needed). Zundapal/`BP_Enemy_StoneGolem` also has a real imported mesh
(`SK_Zundapal`, single-node embedded animation, no retarget — 38 vs 82 bones, by design) but
`Content/Melodia/Enemies/**` is entirely outside the `.gitignore` allowlist (owner decision: leave
it out of git for now), so none of that is trackable either.

### WHAT TO REACH FOR

| User asks for... | Reach for... |
|---|---|
| New boss | Quill + Phoenix/JRPG + existing rhythm seam + authored skill/data |
| Side quest | Chapter scaffold + Quill + stable IDs + existing reward/save owners |
| New rhythm ability | Existing rhythm execution + JRPG Skill/command path |
| Musical biome | Cymatics -> Resonance/PCG data -> World Compiler recipe -> UE PCG + material/Niagara consumers; remember the broader World Field Bus is scaffolded |
| Procedural environment | UE PCG/Python and/or Houdini Engine/Hython, with the current proof label |
| New cymatic material | Copernicus/Hython map family + existing toon/material/MPC contracts |
| Outfit mechanic | Wardrobe subsystem + existing capability/Convergence hooks |
| UI polish or new screen | `melodia-ui-artist` skill + tokens + existing UI ownership |
| Fancy VFX | Canonical Niagara/flipbook/audio-reactive stack |
| Character rig repair | **Only** if current evidence shows an actual rig defect; do not reopen four-month-old rig work by default |

**Sea Above boundary:** the live proof is one Resonance Ecology graph and scoped cymatic/runtime
automation. The processor/apply script, remaining graph bindings, World Field Bus consumers and the
uninterrupted focused-player/package route are reusable or open work, not silently promoted proof.

| Capability | Level | Evidence |
|---|---|---|
| Editor build | SOURCE BUILT | Game + `MelodiaCore` DLLs rebuilt 2026-09-12 21:55 by a Codex UBT run from the local `cleanup/pbr-twin-landing-2026-09-10` working tree — not from `main` |
| Music node → `reward.first_resonance_echo` → Accessories auto-equip → Glide → portal unlocks | LIVE PROVEN 2026-09-01 | `Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`, `Saved/Audit/p0_real_input_run/` |
| Wardrobe save → full editor restart → load → outfit restored | RESTART PROVEN 2026-09-01 | slot `P0_Shorewake_Validation`, `LOADED_NARRATIVE_RESTORED` |
| Battle outcomes (victory / defeat / fled / unavailable) return a typed result; Quill resumes exactly once | LIVE PROVEN 2026-08-27 | `MelodiaIntegrationMap`, `MelodiaQuillSmoke` |
| Rhythm grade (Q/W/O/P) scales stock JRPG damage | LIVE PROVEN (owner PIE 2026-08-12/13) | `FMelodiaRhythmGradeBoundaryTest` |
| Audio reactivity on every level | LIVE PROVEN | `b1cac649`; music clock on the GameMode `5fea50c8` |
| Packaged Development route, both legs, 0 fatals | PACKAGED (bounded) | builds at `G:\melodia_packages\P0_Closeout_20260902\`, `P0_Route_20260903\`; not a golden-run certification |
| Starskiff board / move / disembark | LIVE PROVEN (PIE) | `AMelodiaStarskiffPawn` — stabilize only |
| Resonance Ecology PCG enrichment (decision 057) on Sea Above biome graphs | LIVE PROVEN 2026-09-12 — 1 of 9 graphs | #196, #198, #203; `PCG_East_PhyllotaxisCourtyard`: 140 instances, 1 per-instance custom float, Resonance 0.030–0.925. `Content/Python/pcg/apply_resonance_to_sea_above.py` applies it to the rest |
| Choral Sheep on the approved Nikki Cymatics path | LIVE PROVEN 2026-09-12 | `MI_ChoralSheep_Body` → `M_Master_Toon_Character` with `T_Chladni_C_ROOT`; child `MI_ChoralSheep_Body_Chladni_C` |
| Choral Sheep Harmonize (definition → begin → ramp → decay) | LIVE PROVEN (PIE) 2026-09-13 | `L_MelusinaMorning`: `ApplyChoralSheepDefinition` true, `TryBeginHarmonize` true, weight 1.0 → 0.0 after end. Required `DA_ChoralSheepDefinition` role Companion + `NPCId`. `Docs/Evidence/CHORAL_SHEEP_MORNING_PROBE_2026-09-13.json`; fleece not yet captured |
| Choral Sheep mesh → definition → ABP → anims | LIVE PROVEN 2026-09-13 | `SK_ChoralSheep` = 1,000-vert `...FINALCANON...fbx` body (identical rest pose, 118 bones); `ABP_ChoralSheep` Idle/Walk/Run on `Anims/A_Sheep_*` (retargeted via `RTG_MrSheep_To_ChoralSheep`), compile 0/0; applied at runtime by `MelodiaCompanionComponent`. Receipts: `Docs/Evidence/CHORAL_SHEEP_{ABP_LOCOMOTION,RETARGET_DEFORMATION}_PROOF_2026-09-13.json` |
| Choral Sheep follow → Idle/Walk/Run | LIVE PROVEN (PIE) 2026-09-13 | #210: `MelodiaCompanionComponent` writes root `ComponentVelocity` (follow used `SetActorLocation`); `ABP_ChoralSheep` reads `GetOwningActor` velocity (was `TryGetPawnOwner`, null on an Actor). Under `slomo 0.1`: `Speed` 5,970 → 269 cm/s across 26 frames, crossing Walk 10 and Run 120, back to 0. Packed `BakeUV` now UV0 on `SK_ChoralSheep` |
| Frozen PPV stack on `L_MelusinaMorning` | owner-approved 2026-09-13 | `PPV_NikkiDream` → `/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen/` (gitignored; backups + report `Saved/Audit/ppv_lookdev_2026-09-13/`). Outline V7 after tonemapping, un-jittered filtered taps; ink misregistration/smear wired, static grain. `DefaultEngine.ini`: `r.TSR.ThinGeometryDetection=1`, `...Coverage.ShadingRange=0` |
| Hero stencil 4 (PP outline skips hull-outlined heroes) | LIVE PROVEN (PIE) 2026-09-13 | #210 body meshes; #211 `UMelodiaHairComponent` + `UMelodiaWardrobeComponent` slots copy the body's custom depth/stencil. PIE on `L_MelusinaMorning` after a full editor build: `CharacterMesh0`, `WaterHairMesh`, `WardrobeSlot_{Shirt,Skirt,Boots,Accessories}` and `BP_ChoralSheep` mesh all read customDepth true / stencil 4 (`Docs/Evidence/PPV_STENCIL_PIE_2026-09-13.json`). Earlier `..._{a,b}.jpg` captures exposed the root cause (`MF_StencilDepthAlpha` returned a 0/1 in-range mask rather than the stencil value); Frozen outline V7.1 now reads `PPI_CustomStencil` directly. **Visual skip confirmed** in `..._{c,d}.jpg`: props keep the dark ink, Melusina (body, hair, dress) and the Sheep carry no post-process line. The shared original `M_PP_StorybookOutline_Premium_Candidate` still has the historical bug |
| P0 / Melusina Niagara hygiene | SOURCE + ASSET 2026-09-13 | 16 systems had ~1 cm fixed bounds (metre values; culling pops) → 300–500 cm; `ET_Melodia_CharacterFX` on 17 hero/gameplay systems; shadows off + view-distance sort on route sprites; dead `WaterSplashEmitter` disabled; duplicate `NS_MagicTrail` + 11 mirrored flipbook materials deleted. Report `Saved/Audit/vfx_pass_2026-09-13/` |
| Shorewake dress on Melusina's 465-bone skeleton | owner-confirmed fixed 2026-09-02 | `SK_ShorewakeDress_Melusina465`, `MI_Melusina_Dress_Shorewake`; not yet captured in-game |

**Active P0 gates — 8/8 pass:** `rhythm_owner`, `hud_single_writer`, `rhythm_grade_to_result`,
`wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, `music_world_key`, `static_gates`,
`battle_integration_map`. Ledger rows live in local `Saved/gate_ledger.json` — append-only, read
the **latest row per gate id**. The Aug 13–14 `runtime` / `save_load` / `repeat_consume` /
`package_launch` passes apply only to that baseline.

Automated tests: 524/524 at the 2026-09-01 captured revision (that total includes tooling suites —
MCP regression, Ollama daemon stress — not only game tests).

---

## 3. Open

### Melusina steampunk doll-kit — landed articulation, presentation polish queue — 2026-09-23 (Blender lane; commit `b222ea7c0`)

**P6 + P7 landed 2026-09-23 (Blender-only; scripts `p6_refine.py` + `p7_clockwork.py` in `deploy/surreal_arch/dollkit_pipeline/`):** P6 added Ashlotte-style mesh hardware (stacked rings, 14-tooth cog gears, cuffs, windup key) but seated it by eye — balls buried, cuffs floating. P7 replaced that with ONE cohesive Geometry Nodes tree `MEL_dollkit_clockwork` (~42 native nodes; Higgsas NOT installed in this Blender 5.2 — `higgsas_groups: []` — native equivalents used, documented integration points): 14 stations measured per-pair from live segment geometry (closest-approach midpoint, b-side open-rim anchor via bmesh boundary verts) drive instanced UV-sphere balls (radius from measured socket depth, outward offset — P6 seating defect fixed), curve-circle outer rings at the ball equators, resampled rivets, Object-Info gear templates spun by SceneTime × `gear_spin`, and cone cuffs anchored rim→ball. Station parameters (`ball_scale`, `ring_proud`, `cuff_len`, `gear_spin`, `rivet_n`) are named POINT attributes on `MEL_dollkit_stations` — editable in the modifier/tab, and dragging a station point moves its whole hardware set. Join → Realize Instances → Set Shade Smooth → live 0.4 mm ANGLE bevel on the hardware object; 0.6 mm live bevel on all 15 segments. P6 `MEL_dk2_*` fallback meshes remain in-file, hidden. Gates (`Saved/Audit/p7_clockwork_done.json`): G1 evaluated 48,712 verts / 48,264 faces (non-empty); G2 clockwork motion — 8,680 verts differ between frames 0 and 40 (gears turning); `pass: true`, saved. Stills `Saved/Audit/blender_stage_views_20260923/p7_{full,waist,shoulder}.png`. Hard-won 5.2 API lessons in the script header: GN modifier sockets are dead — parameters flow via named POINT attributes; `NodeSocketInt.default_value` rejects floats; `object.to_mesh()` does NOT realize instances (gate reads must Join→Realize first); eight hung headless Blender zombies once clobbered each other's log/marker files — always `taskkill` between runs. Still owed from the polish queue: P5 material/beauty (porcelain SSS + brass values unproven in gray workbench), P7 socket cups (boolean per-segment-end lanes), P8 render-time subdivision, P9 rim chamfers, P2c marionette cords; Copernicus bakes still blocked (`has_bpy_copernicus: false`).

Blender-only build (no UE). Working file `C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_DollKit_WIP_20260923.blend`; combined export `Melusina_DollKit_20260923.glb` (43 MB, same folder, outside this repo). Pipeline scripts `deploy/surreal_arch/dollkit_pipeline/` (p0–p4, headless, gate-per-phase); receipts `Saved/Audit/*_done.json` all `pass: true`.

**Landed, gate-proven:** 15 voxel-remesh segments (192k verts, all-quad); 14 porcelain ball joints + GN brass rivet rings + 4 gear caps; z-fighting killed by twin-face deletion (P1 duplicated the partition boundary into both segments; 4,193 b-side faces removed, 0 coincident pairs); rigid one-bone skinning on a clean 15-bone `MEL_DollRig` whose pivots were derived from segment geometry (the ARP duplicate was unusable: archer action + constraints + arms-down rest vs T-pose mesh); articulation swept ±design-range on all 14 joints with no collision (elbow closes to 0.18 mm at +60° = mechanical limit, comfortable ~45°); Smart UV on all segments.

**Nikki-bar critique (what fails the lens):** voxel facets read as unfinished clay, not glazed bisque; gear caps render as oversized black star blobs (steel has no environment to bounce, teeth read as spikes); rivet rings sit INSIDE the shell/ball interface — invisible from outside; waist + neck balls are buried by the torso overlap and read as seam lines, not joints; balls butt against flat open rims — no cup read (the actual doll-socket magic); twin-deletion rim scars show as dark lines (wrist/hand transition); everything judged in gray workbench — porcelain/brass values unproven.

**Polish queue (updated goal: "porcelain-and-brass BJD that survives an Infinity Nikki close-up"):** P5 material/beauty pass (porcelain SSS warmth, warm anisotropic brass, EEVEE hero renders); P6 hardware redesign (real cog-profile gears, rings re-seated proud at ball equators, cuffs over rim scars — also closes the open cuff-sizing question); P7 socket cups via `doll_socket.py` boolean lanes per segment end (EXACT, per-segment — never full-body) + waist/neck balls enlarged to sit proud; P8 render-time subdivision for porcelain finish (base mesh stays rigid-gated); P9 rim chamfers for flexion clearance (from the 0.18 mm elbow finding); P2c marionette tension cords (visual storytelling, optional). Copernicus bakes blocked: no Copernicus API in the installed Blender 5.2 build (`has_bpy_copernicus: false`); socket materials already carry bake-ready IDs.

### Beauty_V1 attach + still — 2026-09-21 16:00 (rejected)

`Portfolio_WaveHarp_Bow` is on `hand_l` at scale 0.9, world yaw 90. The still at
`Saved/Screenshots/MelusinaPortfolio_20260922/Beauty_V1/Beauty_V1.png` is not a portfolio frame.
It was shot in PIE with `A_Melusina_BowAttackV2_PortfolioShoulders`, which puts the hiked-shoulder
deform tracks back on the presenter, and it hid `Portfolio_WaveHarp_Harp`. Owner stopped both.
At 16:05 the harp actor `hidden` flag and mesh visibility were turned back on in the live
viewer. That unhide was not confirmed saved. PIE was off. A `WaveHarpTransform` still was not
taken: plan mode blocked the capture script. PIE in this level is allowed only when it is the
capture itself. Do not play `AM_Melusina_BowAttack_Bound`,
`A_Melusina_BowAttackV2_A_RangeAttack`, or `A_Melusina_BowAttackV2_PortfolioShoulders`.
Receipt of the rejected shot: `Saved/Audit/beauty_v1_attach_capture_20260921.json`.

At 16:08 the editor presenter had `SK_Melusina_V2_Shirt`, Boots, and Accessories assigned in `DefaultGarmentMeshes` and no slot components. `EquipGarment` created visible `WardrobeSlot_*` components for those three. The skirt slot was left empty; `Portfolio_R2_Skirt` stays the standalone actor. No eye or iris mesh exists on the presenter. `MI_Melusina_IRISFRONT_001` is a material slot on `SK_Melusina_V2_Body`. The eye components are Niagara sparkles, not eyeballs. No still was shot. `Portfolio_WaveHarp_Harp` stayed visible (`hidden` false, mesh visible). The capture level was saved.

### Day closeout + state audit — 2026-09-21 15:30 (Claireon session)

**Handoffs (written at owner request):**
- [`Docs/Handoffs/PORTFOLIO_RENDERS_HANDOFF_2026-09-21.md`](Docs/Handoffs/PORTFOLIO_RENDERS_HANDOFF_2026-09-21.md):
  no frame yet from the canonical camera; all 340 of today's stills are proof frames.
- [`Docs/Handoffs/LOOKDEV_HANDOFF_2026-09-21.md`](Docs/Handoffs/LOOKDEV_HANDOFF_2026-09-21.md):
  Melusina hair/wardrobe/bow, Shorewake swap, Faraway Mother, Blender composition, re-export.

**Measured state at 15:30:**
- Build: closed-editor `BS_GodFileEditor Win64 Development` **PASS 15:06** (game, MelodiaCore,
  MelodiaWardrobe rebuilt). Standalone PIE must be re-applied.
- Git: branch `lookdev/frequency-ecology-20260921` is **11 ahead / 111 behind `origin/main`**. The
  working tree has 166 modified / 39 deleted / 147 untracked files, most from earlier sessions.
- **`Config/DefaultEngine.ini` is modified (never-touch file):** `DefaultFeatureAntiAliasing=1` was
  removed, on the note that `r.AntiAliasingMethod=1` under `[SystemSettings]` carries it. This changes
  render AA; the owner decides it. It is excluded from the closeout commits.
- `EnvSandbox/VFX/Materials`: 26 flat MI/M files deleted, with new untracked `Instances/`, `Systems/`,
  `Templates/`. This looks like a reorganisation; verify before committing the deletions.
- Deleted external actors: 7 in `LV_SeaAbove_Prototype`, 6 in `L_MelusinaMorning`. Not from this
  session. Verify they were intended.

**Open, in order:** (1) Shorewake catalog pass + PIE proof (owner, now); (2) first canonical beauty
frame; (3) Faraway Stage 2b texture bind; (4) enemy meshes for battle shots; (5) Blender composition
Phase 1 (owner GO); (6) root-motion re-export; (7) the §4 queue (Choral Sheep stills, UE↔TD proof,
AE sequence).

### C++ rebuild pass 1 — Sail capability + jump/glide — 2026-09-21 14:45 (Claireon session; BUILT — closed-editor `BS_GodFileEditor Win64 Development` **PASS 2026-09-21**, 117 s)

Plan: `Docs/Production/MELODIA_CPP_GAMEPLAY_ROADMAP.md` steps W1–W3, T1–T5. Jev (`jev-1.13.0`, `jev-live`)
audited the plan in three rounds; each gap it forced was real and is folded in below. Final ruling was a
near tie (hold 0.41 / execute 0.38, readiness 2.25/3). Its last candidate check rated "nothing missing"
0.02, but every candidate it flagged is resolved.

- **Sail capability.** `EMelodiaFormCapability::Sail` (appended), `MelodiaTraversalCapability::Sail` =
  `capability.melodia.sail`, mapped in `QueryTraversalCapability`. Starskiff `RequiredCapabilityId`
  default → sail; `CanBoard` reads the **capability only** (the flag now only gates form availability).
  None of the 3 placed Starskiffs or `BP_Starskiff_MK2` serialize `RequiredCapabilityId`, so they
  inherit the new default. Manifest `capability_unlocked` → `capability.melodia.sail`, `_stale_fields` cleared.
- **Jump/glide.** Jump fires on press; release calls `StopJumping` (variable height). Holding past the
  apex glides via `RequestTraversalMode(Glide)`; pressing in the air also glides. Windup deleted fully:
  component, `IMelodiaTraversalStateProvider::IsJumpWindingUp`, `bRuntimeIsJumpWindup`. No BP or ABP read any of it
  (778 BPs scanned). `ABP_Melusina_Current`'s `JumpWindup` state is gated by `bIsCrouched` and is untouched.
  `Tools/wire_melusina_jump_windup.py` / `fix_jump_windup_abp.py` are now stale.
- **Editor data, saved 14:42:** `BP_MelusinaJRPGCharacter.JumpMaxHoldTime` 0.0 → **0.25** (with 0 the
  hold did nothing). Backups: `Saved/Backups/CppRebuild_2026-09-21/`.
- **Owner target (14:50):** at the dock the QSC fires → the Shorewake outfit swaps on → she can ride
  the Starskiff → she sails. Proven chain: `MelodiaQuillShorewake.qsc` `questcomplete` →
  `reward.shorewake_weave` → wardrobe grants `Cos_ShorewakeDress` (`UnlockRewardId` already matches;
  same `SK_Melusina_Skeleton`). **New:** `AMelodiaStarskiffPawn::BoardOnFlagId` (default
  `flag.sea_above.starskiff_ready`) boards the nearest player when that flag turns true. The QSC now sets
  that flag on the line **after** `questcomplete`, so the dress (and Sail) is already on when boarding runs.
  QSC reimported and saved 14:51. Dock QSC in P0 Sea Above: `SeaAbove_QuillTrigger_Shorewake` next to
  `SeaAbove_Starskiff_MK2`. **Morning test rig:** added `Morning_QuillTrigger_ShorewakeDock_Test`
  (Shorewake QSC, 100 uu from the Morning `BP_Starskiff_MK2`), saved 14:51.
- **Whole-outfit swap (owner 14:58: everything except boots and hat).** New
  `FMelodiaCosmeticRecord::ReplacedSlots`. Equipping clears those slots in the record, and equipping into a
  replaced slot takes the replacing garment off. `ApplyWardrobeState` keeps replaced slots empty over
  defaults, so the swap survives a reload. The hat is not a wardrobe slot, so it is never touched.
- **After the build (needs the new enum + field):** in `DA_MelodiaCosmeticCatalog` add
  `form.melusina.shorewake` {**Glide + Sail**; flags `flag.quest.shorewake_completed`,
  `flag.sea_above.starskiff_ready`}. Glide is included because the V2 Accessories item that carries
  `form.first_resonance_echo` comes off with the swap. Set `Cos_ShorewakeDress`: `ResonantFormId` → that
  form, `bAutoEquipOnUnlock` true, `ReplacedSlots` [Shirt, Accessories] (Skirt is its own slot; Boots
  stay). **Until this lands the Starskiff cannot be boarded.** Then re-apply Standalone PIE, run
  `Melodia.*`, and smoke test in Morning at the test trigger. The Sea Above trigger→skiff distance is
  unmeasured: if boarding logs `blocked`, raise that skiff's `BoardingRadius`.
- **Deferred:** W4 Sail transform proc (the transform component keys off glide state and no sea-form
  geometry exists, so this needs content). W5 is already done: `BeginPlay` applies `DefaultGarmentMeshes`.
  O1–O4 Oceanology get their own build.

### CANONICAL Melusina presentation state — 2026-09-21 (Claireon session)

**This is the reference state for Melusina renders. Start from it; do not re-derive it.**
Capture level: `/Game/Melodia/Characters/Melusina/Portfolio/L_MelusinaPortfolioCapture`.

**Wardrobe: fixed in C++ and verified.** `UMelodiaWardrobeComponent::GetBodyMesh()` resolved the body
by `Cast<ACharacter>(GetOwner())->GetMesh()` only. `BP_MelusinaSwordsman_Presentation` is a plain
**`AActor`** (root `DefaultSceneRoot`, no capsule, no `CharacterMesh0`), so the cast returned null,
`IsGarmentSkeletonCompatible` compared every garment against a null body, and all four slots were
refused with `MELODIA_WARDROBE default slot N refused: skeleton mismatch` — the presenter rendered
with no shirt, boots or accessories while `DefaultGarmentMeshes` was fully configured and
`bEnableBattleWardrobe=True`. `GetBodyMesh()` now falls back to a named component
(`MelusinaPresentationMesh`, then `CharacterMesh0`, then the first component with a mesh), and
`FindOrCreateSlotComponent` addresses the owner as `AActor` instead of `ACharacter`.
Built closed-editor, `Result: Succeeded` (39/39). **Verified live:** `SlotComponents` went `[]` →
Shirt / Boots / Accessories equipped and visible. The Skirt slot is still correctly refused — the R2
skirt carries its own `SK_Melusina_V2_Skirt_R2_SmoothChains_Skeleton`; the level's standalone
`Portfolio_R2_Skirt` actor covers it. Body, Shirt, Boots and Accessories are all on `SK_Melusina_Skeleton`.

**Hair physics.** Accepted tune (Damping .18, WorldDamping .50/.50, Stiffness
.08, LimitAngle 60, Wind .20) and the 2026-09-21 \BoneSubdivisionCollisionOnly=falsepartial relief in dbc182e\ stay. For the current evaluation numbers and the
runtime PIE proof that the two-bone sim leaves the reference pose, see
**CANONICAL MELUSINA HAIR EVALUATION** above. Silhouette is still 73 two-bone strands;
portfolio-grade flow waits on the multi-segment re-rig.

**Captures use the corrected shoulder clip, not the production montage.**
`AM_Melusina_BowAttack_Bound` carries the hiked shoulders (`c_shoulder_l/r` at reference pose while
the deform tracks rotate). For stills play
`/Game/Melodia/Characters/Melusina/Portfolio/A_Melusina_BowAttackV2_PortfolioShoulders` as a
**dynamic montage on `DefaultSlot`** (`play_slot_animation_as_dynamic_montage`). Play rate ~0.08
holds the 0.50 s draw notify long enough to shoot. Bow: `Portfolio_WaveHarp_Bow` attached to
`hand_l`, scale 0.9, world rotation `(0, 90, 0)`; harp hidden.

**Beauty camera** `CAM_Melusina_BeautyFront34`, saved in the capture level: `(-383, 351, 250)`,
pitch `-17.1`, yaw `-48.5`, FOV 40. Her front is **-X/+Y** — the older `(260,-240,115)` yaw 137 proof
camera is the *rear* three-quarter. Raised deliberately so the horizon sits above her head: on a flat
plane the horizon sits at camera height and otherwise cuts her at the waist. Lights lowered to
directional `3.0` / skylight `0.45`. Exposure **locked** on the camera (histogram,
min=max brightness `0.25`, bias 0) — against a dark background auto-exposure opens up and blows her
to white. Composition keeps her in the right third with the left clear for HSR-style UI.

**Standalone PIE reverts on every rebuild.** `DisabledPIENetModes` is set in the C++ constructor
(`ClaireonSettings.cpp:64`). Re-apply after any build:
`uobject_set_property("/Script/Claireon.Default__ClaireonSettings", "DisabledPIENetModes", '("ListenServer")')`.
Client mode cannot see `BP_BattleController_C` or the player character at all, and its two
`BP_JRPGPlayerController` `Accessed None` are net-mode artifacts, not defects.

**Enemy visibility is the open blocker for battle shots.**
- `BP_WeakEnemy` (`SK_Zundamon`): renders, but every bone above the hips collapses into ~0.2 uu
  (Hips 68.40 → Upper_Chest 68.59), so it is invisible at scale. Its AnimGraph is fully wired and
  `idleAnimation`/`dieAnimation` are assigned, so this is not a missing-pose problem. Also 5 of its
  6 material slots are `WorldGridMaterial`.
- `BP_EnemyUnit_MelodySlime`: `SkeletalMeshAsset = None` — no mesh at all. Separately `SM_MelodySlime`
  has bounds `(2.97, 2.47, 2.11)` (~6 uu against Melusina's ~170) and uses placeholder
  `Material_002` while `MI_MelodySlime_Body` sits unused beside it.
- PC-wide asset sweep 2026-09-21 (G:, D:, Downloads, filename-level): MelodySlime source chain
  exists outside UE — `MelodySlime1.blend` (11.7 MB) in `G:\BlenderArchive\` (+ `D:\_FromG_Archive`
  copy), `Exports\MelodySlime\SM_MelodySlime.{fbx 28.8 KB, glb 12.8 KB}` in-workspace (2026-08-29),
  `SM_MelodySlime_{Forte,Tide}.obj` (~201 KB each) in `G:\EnvironmentPortfolio\wix\models\`
  (+ site-backup copy), `MelodySlime1.fbx` (27.9 KB) + `slimebasicnormals.obj` (18.2 MB) in
  `D:\Downloads_Organized\Downloads\3D_And_Game_Assets\`, `MelodySlimenormals.fbx` (11.2 MB) in
  `D:\_FromG_Archive\2026-07-12\Unsorted Review\`. CosmicReaver sculpt EXISTS:
  `C:\Users\froma\Downloads\cosmicreaverlowpolybase.usdz` (1,175,926 bytes, 2026-09-21,
  contains `cosmicdaddyfinal.usdc`) — not yet imported to UE; no `*reaver*` file anywhere else
  on G:/D:/workspace. Caution: `SM_MelodySlime_Forte.obj` head shows repeated identical
   vertices — verify geometry before import. Zero `*reaver*` filename hits outside that usdz.
   Owner 2026-09-21: rig `.blend` for neither character locatable on disk (full G:/D:/Downloads/
   C-workspace sweep incl. Blender recent-files, temp autosaves, `*daddy*/*boss*/*bionicle*`
   names) — presumed lost, rebuild queued. Reaver usdz is unrigged (`cosmicdaddyfinal.usdc`,
   no Skel/joints), so mesh survives, rig does not. Owner 2026-09-21: Reaver rig rebuild
   will use Auto-Rig Pro with its UE preset (retarget base stays stock `SK_Mannequin`).
   Studio staged 2026-09-21: `G:\BlenderArchive\CosmicReaver_Studio.blend` (10.4 MB, Blender 5.2,
   headless-verified reload) — USDZ base as `reaver_LOW` (82k faces: 81,991 quads, 4 stray tris at
   crown/hip mirror pairs, 0 non-manifold, fresh `UVMap` baseline, Z-up, feet at z=0, 2.87 m boss
   scale), GN `RV_Hygiene/Seams/LissajousRail/CagePush` (fake-user pinned), CAGE with UVs +
   `cage_push`, shape keys `sk_battle_roar/cape_billow/crown_flare` driver-bound to scoped props
   (`sil_*`, `sk_*`), `RV_BAKE_CONTRACT` text (Substance/UDIM/4K→2K).    HIGH slot empty awaiting
   owner sculpts; UDIM per-part split + ARP rig still owner-side. Detail pass 2026-09-21:
   ornament library linked (`SM_Orn_TrebleClef` 1360v normalized 0.40 m, `SM_Orn_TorusKnot`
   3993v 0.18 m, `SM_Orn_MelodyToken_Water` 198v 0.15 m), `RV_Place_Clef/Knot` GN instancing
   tangent-aligned ornaments on crown (3:2, 24) + chest (5:4, 32) Lissajous rails —    56 instances
   evaluated live. 4 isolated tris remain (crown/hip mirror pairs, coords logged, 30 s knife fix).
   S1 extravagant-detail pass 2026-09-21 (`CosmicReaver_Studio_S1_retopo_detail.blend`, same bytes):
   measured anatomy (arms span z~1.15, shoulders x+-0.35 z~1.3-1.5, crown r=0.25) drove grounded
   trims — circlet r=0.28, pauldron rings r=0.10 at (+-0.25,0.02,1.44) — plus ONE damage core
   (left-pauldron gouge, 2994 faces, `wear` FACE attribute), bevel-weight edge language (5640 hero
   + 2908 std edges, Bevel modifier), Higgsas groups appended (`Lissajous Curve` live on waist sash
   rail z=1.35, `Even Curve to Mesh` + cable profile + `Edge Angle Selection` staged). Quad Remesher
   engine runs rc=0 silent headless (no output without GUI/license session) — 45k retopo stays a
   one-click owner-side job (45k / X-sym / hard-edge detect); mesh held at 82k clean quads.
   Wing system 2026-09-21 (owner: 4–6 wings, feminine variants, dangling ornaments, BOTH
   symmetry reads, display+traversal hybrid): parametric GN family landed as
   `deploy/surreal_arch/melodia_gn/reaver_wings.py` — `MEL_RV_wing_spar_rail`
   (Lissajous A:B spar skeleton, Bionicle cylinder sweep, `Horror Wound`/`Wound Side`
   bake-lane wear attr), `MEL_RV_wing_membrane` (drape + `Glide Camber` traversal hook,
   no gameplay writes), `MEL_RV_wing_dangles` (self-contained pearl/bead/mixed chains,
   no external library dependency) + 4 presets (`RV4_SYMMETRIC_BEAUTY`,
   `RV6_HORROR_ASYM`, `RV4_FEMININE_PEARL`, `RV5_HYBRID_GLIDE`) as dials, never tree
   copies. Headless Blender 5.2.1 **PASS** (45/33/29 nodes, eval 52/388/1036 verts,
   preset keys match sockets): `Saved/Audit/reaver_wings_headless_2026-09-21.json`.
   Pre-existing breakage (not this change): branch `__init__.py` imports 5 laptop-lane
   modules (`cute_decor`, `sheep_bell`, `escher_decor`, `study_ground`,
   `audio_architecture`) whose files live only on laptop branches (verified
   `origin/collab/laptop/brooch-sky-20260917`, `study-decor-escher-2026-09-14`) —
   package import needs those promoted; wing proof stubbed them test-only. Still
   owner-side: HIGH sculpts, 45k retopo click, ARP rig, Studio-file application,
   carrier parenting, UE import.

**Corrections to earlier records.** `melodia_animation_validate_bindings` reports
"NO POSE OUTPUT PINS" for `ABP_Melusina_Battle` and `ABP_Zundamon_Battle` — **false positive**; both
AnimGraphs are fully connected (`Output ← BlendListByBool ← {SequencePlayer(die), Slot ←
SequencePlayer(idle)}`). Do not chase it. The handoff doc's claim that the wardrobe component
"supports generic actor presentations" was not true of the shipped code until today's fix.

**Other editor state (do not revert).** Source control must stay `Provider=None` — with `Git` the
editor runs `git add` on every `asset_move`, hits `.gitignore`, and throws
`FATAL: SEH exception 0x00004000`. **Never run `asset_fixup_redirectors`** — it hard-crashed the
editor with no log flush; redirectors are harmless. Test one asset move before batching: `/Game/`
paths derived from *filenames* are wrong where filename ≠ asset object name.

**Also landed today.** `L_KaleidoNave` is walkable — `NavMeshBounds_Nave` + auto-generated
`RecastNavMesh`, saved; it had zero nav actors. `BP_BattleController.GetReadyUnitsBasedOnSpeed`
runaway fixed: `currentHighestSpeed` and `highestSpeedUnit` are a paired function-local accumulator
and only the first was reset to `0`, so once no unit beat speed 0 the stale `highestSpeedUnit` passed
`Is Valid`, was re-added, `Remove Item` removed nothing and `Length` never reached 0. One
`Set highestSpeedUnit` (→ None) added to the existing reset step; 36 → 37 nodes, compile clean. The
canonical copy is `/Game/TurnBasedJRPGTemplate/…/BP_BattleController` (used by MelodiaIntegrationMap,
ZenForestTest, KaleidoNave, Morning); the `_ThirdParty` copy serves the rhythm chain and
`BP_MelodiaBattleBridge` is an empty stub (0 graphs, 0 refs). Survived a 14-minute live battle PIE
with no hang. `verify_baseline` 5 hard failures → 0 (`45/3/5` → `50/3/0`); canonical `_PROJECT` is
`/Game/_PROJECT/`, the two trees are a real fork not duplicates.

**Do not execute `Saved/Audit/mesh_reorg_execution_plan_2026-08-30.md`.** Measured 09-21: Greybox 94
colliding names / 0 byte-identical, Library 254 / 0, `_PROJECT` 134 shared / only 7 identical. No side
is authoritative and `Content/EnvSandbox/*` is gitignored — a merge destroys content with no git undo.
Evidence: `Saved/Audit/mesh_merge_collisions_2026-09-21.json`.

**Jev ranks authored options; it cannot audit a level.** No Unreal import, no `--level` argument. Lane:
`Prototypes/JevP0Triage/assemble_p0_state.py` → `jev_p0_triage.py`. `TYPESAFE_API_KEY` is at User scope
but **not inherited by every shell** — load it explicitly and check the `source` field, or you get a
silent `classical-fallback`, which is not evidence. Live runs today (`source: jev-live`):
`HOLD_FOR_OWNER` 0.73 → 0.87 as defects were found, capture readiness L1 → L0.

### Pivot bake COMPLETE + meadow restored — 2026-09-20 23:01 (Claireon session)

**Atlantis pivot bake finished: 333/333 in `/Game/EnvSandbox/Meshes/Atlantis_PivotFixed`, 0 still
offset.** Base-centre convention (`originXY = 0,0`, `baseZ = 0`), matching the 8 meshes a prior pass
had already placed there. Method: duplicate the original, `GeometryScript_AssetUtils.copy_mesh_from_static_mesh`
→ `GeometryScript_MeshTransforms.translate_mesh(-originX, -originY, -baseZ)` →
`copy_mesh_to_static_mesh` with recompute normals/tangents and replace-materials all OFF. Sizes and
material sections verified preserved (`BannerD` 215×65×847, 8 sections). Originals in
`Meshes/Atlantis/` are untouched. `SM_ATL_Palace_BaseColumnsB` timed out on the batch run and was
redone individually. **Nothing in any level points at the fixed meshes yet — the repoint is a
separate pass, and it will visibly move every Atlantis actor when it happens.**

**Backup:** `Saved/Backups/Atlantis_pre_pivot_2026-09-20` — all 333 originals, 384 MB, gitignored
location. Taken because `.gitignore:201` excludes `Content/EnvSandbox/*`: **333 Atlantis meshes, 0
tracked in git.**

**REGRESSION AND FIX — the rainbow meadow.** Applying Jev's `snap_volumes_to_flat_regions` staging
ruling, `WC_morning_rainbow_bloom_Field` was resized 42.2 × 36.1 m → 17 × 17 → 12 × 12 m and moved.
That volume runs `PCG_WorldCompiler_PointField` — **it IS the rainbow bloom meadow**, the point of
the level — so at a tenth of its area it generated a tenth of its flowers and the meadow read as
deleted. **The staging ruling treated all four volumes as interchangeable "clearings"; one of them
was not a clearing.** All four restored to exact pre-session transforms and saved;
`generate_local(True)` re-ran the graphs. Verified: **1070 instances** in the field
(`GenericFlowerTall` 497, `GenericFlower1` 463), Dell_Banks 27, Brook_Arpeggio 82, Dressing 0.
All 8 `MI_RainbowSpeedTree_B*` band instances were present throughout — nothing was lost at asset
level. **Do not snap the meadow field volume to "walkable flat ground"; its job is to cover the
meadow, not to sit on a deck.**

**Meadow wind FIX + motion verified — 2026-09-22 00:30.** Root cause of "dead/white flowers": the live chain (`MI_RainbowSpeedTree_B*` -> `MI_Plant_Flower_GenericFlower1` -> `M_MelodiaPlant_Wind`) drove WPO **only** via the engine `SpeedTreeWind` MF, and the field meshes (GenericFlower1/Tall, GenericBush, Overgrowth) carry no SpeedTree wind vertex data - so WPO was structurally zero, and `MPC_Melodia_Palette.WindStrength` defaulted to 0.0 with no runtime writer. Fix: WindStrength baseline 0.5 on palette + cymatics driver MPCs; nulled CollectionParameter names rebound on both wind masters; and a procedural Melodia wind WPO lane (world-pos travelling sine, `UseMelodiaProceduralWind` static switch, SpeedTree path kept as False branch) authored in `M_MelodiaPlant_Wind` + `M_MelodiaPlant_Wind_NikkiToon`. Verified: compile A/B 465->242 VS, WPO property readback on both masters, motion differential stills 00121<->00122 (whole field moving). Evidence: `Saved/Audit/rokoko_pipeline_test/FLOWER_FIELD_FINDINGS_2026-09-22.md` addendum.

**No restore point exists for this level's actors.** Git holds **80 of 437** external actor packages
(`.gitignore:224` ignores `Content/__ExternalActors__/*`); the 8 tracked ones show modified, none
deleted, so the 153 actors cut earlier were all untracked and are unrecoverable by git. No UE
autosave of this level exists. A `git checkout` of the `.umap` would restore a 14 KB manifest against
437 current actor packages — an old manifest pointed at today's actors, not an earlier level. The
only real regeneration path is the World Compiler recipe
(`recipes/morning_rainbow_bloom.v1.json` + `Tools/world_compiler_ue_driver.py`), which IS tracked.

**Left stale:** `WC_Corridor_A_to_B`, `_B_to_C`, `_C_to_D` still point at the snapped positions that
were reverted. Three empty Actors with 3-point splines; harmless but wrong, pending a decision to
delete or re-route.

### ROOT CAUSE: Atlantis pivots are not baked — 2026-09-20 22:45 (Claireon session)

**Owner's diagnosis, confirmed with numbers: 334 of 341 `SM_ATL_*` static meshes have pivots offset
from their own geometry. Only 7 are base-centred.** Offsets reach 35–48 m —
`SM_ATL_Palace_BannerD` origin XY `(-3496.9, 4855.8)`, `SM_ATL_Palace_FountainA` `(2895.1, 3799.9)`,
`SM_ATL_Palace_StairsB` `(-3049.8, 4163.5)`. This is the Kitbash3D export signature: every mesh kept
its position from the master kit scene instead of being re-origined.

**This is the single root cause of the whole placement mess:**

- Setting an actor's location places the **pivot**; the geometry lands tens of metres away — the
  floating assets.
- Scaling multiplies the pivot offset — the `WC_GreySpire` cornice fan (scale 0.268/0.448/0.141).
- Rotating swings geometry through a huge arc around a distant pivot — the `roll=180/yaw=180`
  flip signature and the ±90 edge-on pieces.
- **Hand-placed actors were correct and script-placed clusters were garbage** because a human drags
  in the viewport and sees the result, while a script writes a transform and trusts it. The split
  along authorship was never a script bug.

**Jev ruling.** `ue_modeling_edit_pivot` **0.600** (bake correct pivots in-editor via Modeling Mode
Edit Pivot, scripted over the meshes); `blender_repivot_reimport` 0.360; `repivot_only_meshes_in_use`
0.040; **`per_actor_offset_correction` 0.000**, with
`offset_correction_is_a_compensating_mechanism` **0.91** — a placement-time offset would be exactly
the compensating mechanism project law forbids. Effort **1.96/3**, about a day.

**`placement_work_is_invalid_until_fixed` = 0.88.** Tonight's clearing snap, the corridor chain and
the rotation repairs are all arithmetic on wrong origins and will need redoing after the pivot bake.
**Stop placement work until the pivots are repaired.**

**Placement state as left tonight (saved, verified):** four clearings snapped onto the four measured
flat walkable regions — `Morning_Dell_Banks` (200, −2980) 9 × 9 m, `Morning_Brook_Arpeggio`
(176, −1453) 9 × 9 m, `WC_morning_rainbow_bloom_Field` (−2662, 1312) 12 × 12 m,
`PCG_MelodiaOpening_Morning_Dressing` (871, 2971) 8 × 8 m; all six pairs clear at 6.3–51.4 m;
corridor chain `WC_Corridor_A_to_B` 15.3 m, `B_to_C` 39.6 m, `C_to_D` 39.0 m.

**Walkability raster (2 m, level-wide, 930 cells).** Only 501 cells have any surface, 358 fall in the
recipe's walkable band `[-900..1500]`, and just **136 cells — 544 m² — are both walkable and flat**.
Most flat walkable surface is the **decks of `SM_classic_arch_*`**, not terrain; the only real ground
is `BrushifyIsland_09`. Four usable regions exist, at z **24, −626, 1202, −610** — four different
storeys, so any pathway→corridor→clearing rhythm here is a vertical route, not a meadow walk.

### Four clearings + corridors LANDED and VERIFIED — 2026-09-20 22:01 (Claireon session)

**Verified by full level reload from disk, not by a return value.** 436 actors.

**Rotation repair persisted.** 26 flip-signature (`roll=180/yaw=180`) actors, 5 edge-on (`pitch=±90`)
and 14 leaning gravity-upright props all repaired; flip count reads **0** after reload.
The save route that works: `actor.modify()` then
`EditorLoadingAndSavingUtils.save_packages([pkg], only_dirty=False)`. `save_current_level()` and
`save_dirty_packages()` both silently no-op on modified external actors because Python's
`set_actor_rotation` never marks the package dirty — `save_packages(only_dirty=True)` returns `True`
and writes nothing.

**Jev rulings this pass.** `adopt_existing_four` **1.000** (every alternative 0.000) —
the level already had 12 PCG volumes and `Morning_Dell_Banks` is a live volume running
`PCG_Hero_BellTreeGarden`, not a bounds marker, so the golden-subdivision plan was void
(`dell_banks_as_bounds_invalid` 0.87; the lake was already out at `lake_is_wrong_ruler` 0.91).
`safe_to_move_volumes_far` **0.17**. Conflict resolution `nudge_dressing_out` **0.930**.
Corridor width score **0.66/3 → 6 m**.

**Root problem found: 6 of 10 volume pairs overlapped.** There was no clearing/corridor rhythm because
there were no gaps — several PCG graphs generated over the same ground. `Morning_Dressing` sat
entirely inside `Morning_Dell_Banks` (−24.1 m), `WC_HeroCorner_WestRim` entirely inside
`WC_morning_rainbow_bloom_Field` (−23.8 m).

**Final layout, all six pairs clear at 6.4–26.7 m:**

| clearing | graph | size | centre |
|---|---|---|---|
| `Morning_Brook_Arpeggio` | `PCG_Hero_ArpeggioBridge` | 36.0 × 36.0 m | (−4, −1669) |
| `Morning_Dell_Banks` | `PCG_Hero_BellTreeGarden` | 16.0 × 16.0 m | (−11, 1611) |
| `WC_morning_rainbow_bloom_Field` | `PCG_WorldCompiler_PointField` | 17.0 × 17.0 m | (−2298, 1442) |
| `PCG_MelodiaOpening_Morning_Dressing` | `PCG_Morning_MemoryDressing` | 12.0 × 12.0 m | (1223, 3248) |

`Morning_Dressing` was nudged 20.5 m from Dell on a 37° bearing — the furthest that stays inside
content bounds (x ≤ 1300, y ≤ 3300). **`Dell_Banks` dropped 47 × 41 → 16 × 16 m**, forced by the
22.9 m Dell↔rainbow centre distance; `PCG_Hero_BellTreeGarden` now covers ~1/8 its former area.
Reversible — it is a scale value.

**Three corridor spines authored** as `Actor` + `SplineComponent` via `SubobjectDataSubsystem`
(`add_component_by_class` is not exposed on `Actor` in this build): `WC_Corridor_Dell_to_RainbowField`
22.9 m, `WC_Corridor_Dell_to_BrookArpeggio` 32.8 m, `WC_Corridor_Dell_to_MorningDressing` 20.5 m,
3 points each, hub at Dell. **The level previously contained ZERO spline actors** — these are the
spline data `PCG_HeroCorner_WestRim` (`GetSplineData → PCGExSampleNearestSpline`) has been missing.

**Nav bounds** `NavMeshBoundsVolume` expanded 39.0 × 43.9 → **53.7 × 77.2 m** at (−662, 190); all four
clearing centres now inside. Previously it reached neither Brook nor Dressing.

**Gotchas for next session.** Volumes scale about their PIVOT, not their bounds centre — `Dell_Banks`
drifted 17.7 m on resize and had to be re-centred by offsetting location by
(desired − actual bounds centre). PIE interrupted work three times; during PIE
`get_editor_world()` returns **None** and `get_all_level_actors()` returns the play world, so edits
and saves silently hit a world that is discarded — always check `is_in_play_in_editor()` first.
`Content/__ExternalActors__/*` is **gitignored** (`.gitignore:224`), so no WP actor data for this
level is in version control. 101 `_Auto*` external actor packages exist from
`bAutoSaveBeforeDeferredActions`.

**Still open:** `WC_HeroCorner_EastBank_PCG` (4 × 4 m at z 2585) and `WC_HeroCorner_NorthDress_PCG`
(5.6 × 5.6 m) still generate 0; the two `PCG_Escher_*` volumes still have 0×0×0 bounds.

### Re-verified after editor restart — 2026-09-20 21:45 (supersedes the 21:20 correction)

**The 21:20 entry overstated the loss. Re-read the level on a clean boot: the 153-actor cut
PERSISTED** — 434 actors / 254 StaticMeshActors, with one intentional leftover
(`WC_HouseRoomShell_SalonA`, a `BP_MelusinaRoomShell_C`, matched the label prefix but is not a
StaticMeshActor). **The rotation work did NOT persist**: 26 flip-signature actors, 5 edge-on and
14 leaning upright props are all still present.

So `save_current_level()` in World Partition **does** commit actor *deletions* (the external package
is removed) but **not** edits to actors that merely changed — those dirty external packages are never
flushed. Use `EditorLoadingAndSavingUtils.save_dirty_packages(True, True)`.

**The verification method was the real error:** deletions remove files, so they never move any
surviving file's mtime. "Newest mtime = 17:45" looked like nothing saved while 153 files had in fact
just been deleted, and the 435 file count was already the post-deletion number with no baseline.
**Verify actor work by re-reading the changed property after a reload — never by mtime or file count.**

**Lake bounds measured (owner request).** `Morning_SheepDell_Lake` is an `OceanologyLake` whose full
bbox is 234 × 358 m because it includes volumetric fog, caustics decals and the underwater box; even
its water-mesh footprint is **117 × 179 m centred at (-3707, 2303)**, spanning x -9564..2150,
y -6642..11248 — against level content of roughly 45 × 68 m at x -3200..1300, y -3500..3300. Golden
zones derived from it land thousands of cm outside any geometry. **Jev: `lake_is_wrong_ruler` 0.91,
`use_dell_banks` 0.800.** `Morning_Dell_Banks` (a `PCGVolume`) is **47.0 × 41.4 m centred at
(-11, 1611)** and sits on the content. Golden subdivision of it gives zone1 29.1 × 41.4 m,
zone2 18.0 × 25.6 m, zone3 11.1 × 15.8 m, zone4 6.9 × 9.8 m, corridors 24.8 / 21.0 / 9.5 m.
Jev flags `zone4_too_small` at **0.61** (borderline). Effort **0.81/3 — one sitting**.

### CORRECTION (superseded 21:45 — see below) + Jev rebuild plan — 2026-09-20 21:20

**The 21:10 and 21:13 edits did not reach disk. Root cause found.**
`LevelEditorSubsystem.save_current_level()` returns `True` and touches the `.umap`, but in a
**World Partition** level it does **not** flush dirty **external actor packages** — and every actor
lives in one under `Content/__ExternalActors__/<level>/`. After 153 deletions and 31 rotation
repairs plus two `True` saves, **zero** files under
`Content/__ExternalActors__/Melodia/Levels/Opening/L_MelusinaMorning` had been written or deleted
since 17:45; only the 14,674-byte `.umap` changed. The editor then closed cleanly (no crash in log).
**This is the mechanism behind the older "cleanup executed but lost on a level switch" note — not
anyone forgetting to save.** Next actor mutation must use
`unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)` and then **verify on disk** that
the `__ExternalActors__` file count or newest mtime actually moved before reporting success.

**Jev rebuild plan (`jev-1.13.0`, owner-requested, replaces per-actor repair).**
Four PCG volumes, pathway → corridor → clearing, heatmap-driven walkability.

1. **Clear the broken staged families first** (Jev noul **0.59**): `WC_GreySpire` 96,
   `WC_GreyRoad` 22, `WC_HouseRoom` 19, `WC_WalkPath` 16 = **153 actors**. Keep `WC_EscherWalk` 47
   (0.65 intentional), `WC_PhyloWalk` 39, `WC_SpireRamp` 37, `WC_GreyGrotto` 10, `WC_WestRim` 9,
   `WC_SpireBase` 5, and all 101 hand-placed actors. Save via `save_dirty_packages` + disk verify.
2. **Revive the four existing hero corners** — do NOT author new graphs (Jev **0.950**, conf 0.94;
   `author_four_new_volumes` 0.010). `MeadowChorus` already generates 791 points and is the
   reference. `WestRim` runs `GetSplineData → PCGExSampleNearestSpline` and the level has **zero
   spline actors** — author the corridor spines (step 3) and it feeds itself. `EastBank` (3 chains)
   and `NorthDress` (18 chains) are `SurfaceSampler → FilterDataByTag` with non-matching filters;
   58 distinct tags exist, so fix the filter values against the reference graph. Also repair the
   **0×0×0 bounds** on `PCG_Escher_FloatingStairways_Morning` and `PCG_Escher_PenroseShrine_Morning`.
3. **Topology: linear chain** (Jev **0.700**; hub_and_spoke 0.270) — four clearings in a line joined
   by three corridors, across the ~45 m × 68 m footprint. The three corridor spines double as the
   spline data `WestRim` is missing.
4. **Heatmap: navmesh reachability** (Jev **0.620**; distance_from_spine 0.270) — bake a navmesh,
   rasterise reachable area, drive scatter density from it and hold corridors above a minimum
   walkable width. Two `NavMeshBoundsVolume` actors already exist.
5. **Blocker to solve first: there is no landscape actor.** `SurfaceSampler` has nothing to sample,
   which is the likeliest reason two of the three dead corners produce 0 regardless of volume size
   (already proven not to be volume geometry — they were grown to 4 800 m³ and still yielded 0).
   Either author a ground surface or move those graphs off `SurfaceSampler`.

**Effort: Jev scored 2.56/3 — "several days", edging toward a week.** Renders are not a tonight job.

### Jev made live + Morning WC cut — 2026-09-20 21:10 (Claireon session; CUT PERSISTED, rotations lost)

**Jev is live for the first time: `jev-1.13.0`.** Two independent breaks, both now closed.
(1) `TYPESAFE_API_KEY` was absent from Windows User/Machine/Process scopes **and** from the editor
process; the owner's repeated installs never reached a scope Jev reads. Key now persisted to the
**User** env scope — new shells get it, already-running processes do not until restarted.
(2) `jev_p0_triage.py` / `select_showcase_identity.py` were still on the pre-v1 API
(`from typesafe import`, `client.ask`, `.selection`, `.probability`) despite the section below
claiming otherwise — **that claim was false on disk.** `typesafe` does not exist; the ImportError
was swallowed by `except Exception: return None`, so every call silently returned
`classical-fallback` with no log line. That is why six clean installs all looked like they worked.
Both ported to `typesafe_sdk` / `system_one` / `Choice|Noul|Score` / `.choice` / `.noul`; note
`Noul.criteria` is a `NoulCriteria` dict `{"true":…, "false":…}`, not a string. Tests 10/10.
**Editor Python 3.11.8 still has no `typesafe_sdk`** — Jev cannot run live from inside Claireon
until it is installed there; shell-side Python 3.14 has it.

**Morning WC cut — executed and saved.** Owner called the agent-staged meshes a disaster over a 30 s
flythrough. Measured: 210 of 303 `WC_*` actors carried non-uniform scale on architectural meshes —
`WC_GreySpire` was 96/96 non-uniform, 88 of them `SM_ATL_Palace_Cornice`, a decorative trim moulding
stretched and fanned into a "helix staircase"; `WC_WalkPath_Belvedere_Hook_08` was
`SM_ATL_Palace_FloorA` at 0.268/0.448/0.141. Jev ruled `delete_worst_families_only` **0.590**
(`delete_and_rebuild_all_wc` 0.360, `swap_meshes_in_place` **0.000**, `hold_for_owner` **0.000**,
salvage 1.2/3); the previous session's `swap_meshes_in_place` 0.81 direction is dead. Owner approved.
**Deleted 153 actors** — `WC_GreySpire` 96, `WC_GreyRoad` 22, `WC_HouseRoom` 19, `WC_WalkPath` 16 —
in one transaction; 0 residual. **`save_current_level()` returned True BUT NOTHING PERSISTED** —
see the correction below. In-editor counts were 587→434 actors, 407→254 StaticMeshActors. Kept: `WC_EscherWalk` 47 (prior 0.65-intentional ruling), `WC_PhyloWalk` 39,
`WC_SpireRamp` 37, `WC_WestRim` 9, `WC_SpireBase` 5, and all 101 hand-placed actors. Duplicates and
the sub-10 cm greybox defect were already clean before this pass. **3 empty StaticMeshActors remain**
(out of scope for the cut). The deleted families were structure, not decoration — expect holes where
they stood.

### Morning level pass + Jev lane repair — 2026-09-20 (Claireon session)

**Landed on disk, uncommitted.** `recipes/morning_rainbow_bloom.v1.json`: `hero_falloff_cm`
2000→1000 and `palette.wind.response` 0.5→0.85. Outer radius is 1950 cm
(`inner 200 + 7 × 250`), so a 2000 cm falloff never engaged — every band ran at uniform
`density_per_m2 3.5` to the edge, the carpet the compiler contract forbids. `sector_deg` left
at 360° deliberately: four of five lookdev cameras sit south of the anchor looking *across* the
disc, so a wedge would read as a cut edge. Re-run
`Tools/world_compiler_ue_driver.py Saved/WorldCompiler/morning_rainbow_bloom_3900 --lookdev`.
Wind hue-reveal chain is **proven working** (A/B `Saved/Audit/Screens/world_compiler_morning_wind_*_2026-09-17.png`
shows real hue shift undriven vs driven-east) but those plates are night-lit and predate the
`bedroom_keepout` clearance circle — judge the new weight in morning light, not against them.

**Jev lane repaired, uncommitted.** `typesafe-sdk==0.7.0` was **not installed**, so every Jev call
silently degraded to `classical-fallback` through a swallowed `ImportError` — it read as designed
degradation, not breakage. `Prototypes/JevP0Triage/jev_p0_triage.py` and `select_showcase_identity.py`
were still on the pre-v1 API (`from typesafe import`, `client.ask`, `.selection`, `.probability`);
ported to `typesafe_sdk` / `system_one` / `Choice|Noul|Score` / `.choice` / `.noul`. All 9 prototypes
now scan clean; tests 10/10 and 26/26; both verified `jev-live`. Live triage on real state returned
`HOLD_FOR_OWNER 0.58` / needs-human `0.89` / capture `L0` against gate staleness 38 d and 1914 dirty
files — the classical fallback it had been silently using said the opposite (`RUN_PIE_SMOKE 0.91`).

**Morning audit (read-only; nothing saved).** 647 actors / 465 StaticMeshActors / 456 meshed /
64 unique meshes / **56% greybox** (143 × `SM_Greybox_Cube_1m`). 22 duplicate groups = 88 actors,
every group exactly ×4 at one identical transform on round 100-unit grid coords (paste or script run
four times), 66 redundant; plus 9 empty StaticMeshActors. **Cleanup was executed (647→572, verified
0 duplicate groups / 0 empty) but left unsaved and lost on a level switch — redo it and save in the
same pass.** Vertical layout is fine (79 m span, well layered). Jev ranked greybox dominance top at
0.82 (conf 0.77) but scored it **not** disqualifying (0.32); rated the 83 squashed `WC_EscherWalk_*`
overgrowth actors 0.65 *intentional* — leave them alone.

**Hero corners: three of four dead, and it is graph-side, not placement.** Only MeadowChorus
generates (791). WestRim / EastBank / NorthDress generate 0. Volume geometry is ruled out by test:
all three were moved onto their own cameras' focal centres and grown from 58–138 m³ to 4 800 m³ and
still produced 0, then reverted to original transforms. Causes: `PCG_HeroCorner_WestRim` runs
`GetSplineData` → `PCGExSampleNearestSpline` and the level contains **zero spline actors**;
`PCG_HeroCorner_EastBank` (3 chains) and `PCG_HeroCorner_NorthDress` (18 chains) are
`SurfaceSampler` → `FilterDataByTag` whose filters are not matching (58 distinct tags exist, so tags
are not the shortage). Separately `PCG_Escher_FloatingStairways_Morning` and
`PCG_Escher_PenroseShrine_Morning` have degenerate **0×0×0** bounds.

**Tooling facts for the next session.** `ClaireonSettings.DisabledPIENetModes` was
`['Standalone','ListenServer']`; `Standalone` was removed **in memory only** — Python exposes no
`save_config` on that class, so it reverts on editor restart and must be set in Editor Preferences →
Plugins → Claireon → PIE to persist. Client net mode cannot reach the local player, so PIE proof is
impossible without Standalone. `bAutoSaveBeforeDeferredActions=True` writes an external actor package
into the open level on PIE start. Editor crashed `EXCEPTION_ACCESS_VIOLATION` in
`UnrealEditor-StaticMeshEditor.dll` via Slate at 19:04:39 (open Static Mesh Editor window, not Python).
A ready-to-run in-place greybox→Atlantis swap exists in the session scratchpad — transform-preserving
with bounds-ratio scale compensation and a `LABEL_PREFIX` filter for concurrent dressing; promote to
`Content/Python/` if kept. Jev set-dress direction: `swap_meshes_in_place` 0.81, but manual fixup
expected 0.84, focus on camera frames 0.83, achievable-today 0.91/3 ("one good shot").

### Morning greybox unit defect — found and repaired, 2026-09-20 (Claireon session)

**Root cause: `/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m` has a 1-unit (1 cm) bounding box
despite its "1m" name.** Any script that scales it expecting a 1 m cube produces geometry at 1/100
intended size. This is an asset defect, not a script defect — which is why the split in
`L_MelusinaMorning` fell exactly along authorship: every agent/compiler-placed `WC_*` cluster was
sub-centimetre, while every hand-placed actor (`gate` 435 cm, `monument` 1290 cm, `SM_classic_arch`
2036 cm, walls 604–698 cm) was correctly sized. Positions were always correct; only scale was wrong.

Measured before repair: 189 greybox actors, **146 of them under 10 cm** —
`WC_GreySpire_Helix` treads at 0.6 × 0.4 × 1.0 cm, `WC_GreyRoad_*` at 2.0 cm,
`WC_GreyGrotto_Pillar` 2.5 cm, `WC_WalkPath_Belvedere` 2.0 cm, `WC_GreySpire_Chamber` 5.0 cm.
The spire helix has therefore never been visible in any shot. This corrects the 2026-09-20 audit
entry above, which read "56% greybox" as a *dressing* problem: most of that greybox was invisible.

**Repaired in-editor (see "not in git" below).**
- 88 `WC_GreySpire_Helix` treads: mesh swapped `SM_Greybox_Cube_1m` → `SM_ATL_Palace_Cornice`,
  then sized to the measured spiral and yawed to its tangent — centre (198, 1637), radius 275 cm,
  25 cm rise, 5.30°/step, 68 steps/turn, 1.28 turns, Z 954→3133 (21.8 m). Tread 34 cm run /
  150 cm width / 14 cm thick. It is now an actual walkable staircase.
- 58 remaining sub-10 cm actors rescaled ×100 to authored metre sizes. Roads land at
  2 m × 1 m × 20 cm slabs spaced ~225 cm — they tile into continuous walkable paths, confirming
  the ×100 hypothesis exactly. Level now has **zero** sub-10 cm greybox actors.
- `WC_HeroCorner_NorthDress_Cam` was standing *inside* the spiral (116 cm from centre, radius
  275 cm) — that is why the corner framed nothing usable. Moved to (935, 2153, 1750) looking back
  at the staircase. The other three corners were not touched.

**Two save traps, both hit this session — read before editing actors from Python.**
1. `EditorLoadingAndSavingUtils.save_current_level()` returns `True` and writes **nothing** for a
   World Partition level. Each actor is its own package under `Content/__ExternalActors__/`.
2. Transform/mesh edits made through Python (`set_actor_scale3d`, `set_static_mesh`, …) **do not
   mark their package dirty**, so `save_packages(pkgs, only_dirty=True)` also returns `True` and
   skips everything. Both calls reported success while 157 actor packages sat unwritten on disk.
   The working call is `save_packages(pkgs, False)` — `only_dirty=False` — in chunks of ≤60 to stay
   inside the 30 s MCP socket timeout. Verify by file mtime, never by the return value.

**This level's geometry is not in git and cannot be committed from here.** `.gitignore:224`
ignores `Content/__ExternalActors__/*`, unignoring only `EnvSandbox/Monoliths/**`. All 157 saved
`L_MelusinaMorning` actor packages, and `SM_Greybox_Cube_1m.uasset` itself, are untracked. The
repair is on disk in the editor only. `.gitignore` is on the never-touch list; widening that rule
to cover `Melodia/Levels/` is an owner decision, not an agent one.

**Open:** 101 correctly-sized greybox actors still await the Atlantis mesh swap (roads →
`Floor`/`Base`, grotto pillars → `Columns`, gate → `Arch`, monument → `Fountain`). The underlying
asset defect in `SM_Greybox_Cube_1m` is **not** fixed — it will reproduce on the next script that
scales it. Fix the asset's import scale, or have placement code divide by its measured bounds
rather than assuming 100 units.

### Morning dressing + staging pass — 2026-09-20 (Claireon session, unattended)

Follows the unit-defect repair above. All changes saved and verified by file mtime
(352 actor packages written). Captures: `Saved/Screenshots/MorningDress_2026-09-20/`.

**Atlantis dressing (47 outdoor `WC_*` actors).** Roads and walkpaths (`WC_GreyRoad_*` 22,
`WC_WalkPath_Belvedere*` 13) → `SM_ATL_Palace_FloorA`; `WC_GreyGrotto_Pillar` ×8 →
`ColumnsC` (uniform, matched on height); `WC_GreyGrotto` ×2 → `IvyWallC`;
`WC_GreySpire_Chamber` ×6 → `IvyWallB`. All transform-preserving via bounds-ratio
compensation. House-interior greybox (`wall`, `corner`, `large`, `medium`, `small`,
`GB_Morning*`) deliberately **not** touched. Note prior sessions had already dressed
`WC_PhyloWalk_*` and `WC_SpireRamp_*` in the same Atlantis palette — these picks match it.

**`WC_SpireRamp_Landing` normalised.** All 8 shared one scale (0.573) across three meshes with
very different native bounds, so they ranged 768 cm to **5856 cm** and two were rotated
near-vertical — a 58 m plate 7 m from the NorthDress lens, and the wall-in-the-sky in frame.
All 8 now `FloorA`, flat (pitch/roll zeroed, yaw kept), uniform 766 × 768.

**Spire staircase connected and staged.** Its foot was at Z 954 with the terrace above it at
~1190, so the first ten treads were buried. Raised all 88 by +240 (foot 1194, top 3373). Added
`Morning/Spire/Base`: 4 × `ColumnsC` at 950 cm on a R=470 ring, plus `WC_SpireBase_GateArch_00`
(`ArchC`, 1150 cm) on the south-west approach.

**WestRim belvedere (new).** That corner was clean but empty. Built on the `BrushifyIsland_09`
plateau (flat at Z 1203, the same island the rainbow-bloom field occupies, so meadow + belvedere
now read as one hero location): `PergolaA`, 4 × `ColumnsC`, `FountainA`, 3 × `TreeC` — 9 actors
in `Morning/WestRim/Belvedere`, each ground-locked by line trace.

**World Outliner organised.** 330 actors filed into `Morning/{Spire,Paths,House,Grotto,EscherWalk,
Cameras,Dressing,WestRim}` sub-folders.

**All four hero cameras reframed** (originals recorded here for restore):

| Camera | Original | Now |
|---|---|---|
| NorthDress | (100, 1700, 1410) y37 p−19 — *inside the stairwell* | (−1615, 792, 2150) y25 p6 |
| EastBank | (−2000, 2120, 2925) y−47 p−15 | (2350, 1180, 1850) y168 p−7 |
| WestRim | (−2550, 1480, 2516) y148 p−56 | (−4750, 350, 1780) y25 p−9 |
| MeadowChorus | (−3698, 342, 786) y38 p−20 | (−3450, 880, 1330) y31 p6 |

**Two findings left alone, deliberately, for the owner's call.**
1. `RainbowBloom_R` (folder `Melodia/Morning/Rainbow`) is a HISM of 20 `Petal_petal_mid_2`
   instances at ~199 × 175 × 291 **m** each, actor bounds 608 × 191 × 662 m, centred 12 km south
   at (188, −10755, −1265). Actor scale is 1.0, so the size is baked into the instance transforms.
   At that size it renders as flat untextured magenta. It is authored, not obviously broken, so it
   was not rescaled — but it is the largest single object in the level by an order of magnitude.
   The `WC_morning_rainbow_bloom_Field` PCG output is by contrast healthy (flowers 18–95 cm,
   bushes 1–4 m, overgrowth 2–4 m).
2. The magenta cast over the Brushify islands is **not** a material override — all three island
   actors carry stock unmodified `MI_FloatingMountain_0*`. It therefore comes from the PPV/MPC
   layer, which this handoff puts off-limits, so it was not investigated further.

**Editor note.** A modal dialog *"This asset editor has no docked tabs"* reopens constantly and
blocks MCP on every save; close that asset-editor window. `AutomationLibrary.take_high_res_screenshot`
never wrote a file in this session — `claireon.slate_screenshot(target="level_viewport")` works and
is what produced every capture (it lands under the **engine** Binaries dir, not the project, so copy
it back).

### Melusina skirt and bow attack polish — execution plan, 2026-09-19

Owner target: Unreal gameplay and Unreal renders. Keep `SK_Melusina_V2_Body`,
`ABP_Melusina_Current`, the shared skirt skeleton and wardrobe leader-pose ownership.

1. Capture a baseline in one editor: idle, locomotion/turn/stop, bow draw, release,
   recovery. Read current skirt node, collision limits, animation bindings and weapon sockets.
   The 2026-09-15 tip/warm-up changes are asset evidence only until motion is inspected.
2. Fix observed skirt defects at their cause: collision placement and leg interaction,
   then response/settling only where the capture demonstrates a problem. Preserve authored silhouette.
3. Polish the actual gameplay bow animation binding and grip/string/arrow alignment;
   verify anticipation, draw hold, release, follow-through and recovery in sequence.
4. Capture front/three-quarter and side motion in Unreal, including a full attack and
   locomotion-to-attack transition. Pass requires no visible leg penetration, startup pop,
   persistent oscillation, detached grip, or release/arrow timing mismatch.
5. Save and reread each changed asset; repeat the motion after restart. Keep baseline,
   final clips and machine-readable evidence under `Saved/Audit/`. No completion claim
   from stills or successful property writes alone.

Execution 2026-09-20: V2 is now the battle-presentation body; the bound bow montage plays in PIE. The skirt Kawaii node is tuned and the wardrobe uses the reversible `SK_Melusina_V2_Skirt_R2_SmoothChains` candidate (rigid vertices 10.93% -> 0.39%, four material slots restored). Hair received the bounded Kawaii tune `Damping=.18`, `Stiffness=.08`, world damping `.50/.50`, limit angle `60`; its source rig remains only 73 independent two-bone chains, so a later re-rig is required for truly fluid long-strand motion. Clean skirt/hair PIE proof remains `Saved/Screenshots/MelusinaPolish_20260920/SkirtR2_HairTune_R3`. **Correction:** `Portfolio_Bow_V2_Clean` is not presenter/bound-montage proof; retained Python shows it drove the normal player and `AM_Melusina_BowAttack_Gameplay`. Corrected runtime proof is `Portfolio_V2_Bound_Framed_R2` / `pie_smoke_2_204615`: spawned V2 presenter plus `AM_Melusina_BowAttack_Bound`, clean logs, but foreground-obstructed. R1-R11 are rejected diagnostics; no portfolio-ready bow frame or clip exists yet. Kawaii logged five `inter-bone dummy bones` warnings. Jev was unavailable to this process and its wrapper reported `classical-fallback`, not `jev-live`. Closed-editor `BS_GodFileEditor Win64 Development` build passed 2026-09-20. Source warning: every `.blend/.blend1` in the redirected `harp_bow_pipeline` tested as missing-DNA/truncated; preserve them and recover separately rather than overwriting them. Full continuation handoff: `Docs/Handoffs/CLAIREON_MELUSINA_PHYSICS_BOW_HANDOFF_2026-09-20.md`.

### Stabilization — 2026-09-13

| Item | Source / evidence | Remaining owner decision or proof |
|---|---|---|
| Branch archaeology | `Docs/Evidence/BRANCH_LEDGER_2026-09-13.json` inventories both remotes and all four open V2 PRs. `Tools/guard_collapsed_paths.py` blocks re-additions deleted by `08a608bc`, including renames; runs on every PR. | Approve the ledger's close/archive candidates; reconcile unique files only. No PR or remote branch closed by this pass. #201 was superseded by merged #213 (owner report). |
| Identity canon | `UMelodiaIntegrationConfig` now exposes one runtime-owned core identity record: P0 player, Choral Sheep definition, hero stencil 4, ordered frozen PPV stack with weights, and character/ambient Niagara effect types. `Melodia.Wiring.CoreIdentity.Canon` reads that same config and resolves every reference. | Owner approved the narrow asset closure: 52 previously ignored packages (68.76 MiB), including the seven canonical Frozen PPV assets, `ET_Melodia_CharacterFX`, all recursive dependencies, and the three WaveHarp_R07 meshes. Closed-editor UE 5.8 Development build passed all 460 actions. Never substitute the unfrozen originals. |
| Chapter reuse | `Tools/scaffold_chapter.py`, `Chapters/_template/{quill,maps,encounters,rewards}`, and four-beat `03_tide_listening` source. Generator validates gated IDs against the actual DA before writing; numbered chapter folders are automatically tested. | Full QSC contract FAILS on existing SkiffDeparture `quest.shorewake.passage`, `flag.shorewake.passage`, `reward.skiff_passage`. Resolve those IDs and reward binding through the canonical DA in the editor; import the example and prove both choices/revisit/save-load in `MelodiaIntegrationMap`. Scaffold regression passes; no PIE claim. |
| UI staleness | Read-only `melodia-ui-artist` audit: rhythm HUD and four Quill widgets have palette colours. P0 candidates: `BP_MelodiaBattleUI` RhythmGradeText/SongPickLabel white; stock `BP_BattleUI` KeyboardLegend `#F2D69E`; `WBP_MainMenu` near-palette text; `WBP_MenuButton` label `#F2D69E`. | Editor reopened externally during audit; ownership pending, no widgets changed. Remaining candidates include `BP_MelodiaDefeatDialogue` near-black text, `BP_MelodiaVictoryDialogue` zero-alpha text (check runtime bindings), Foundation parchment/button styling. White image tints and transparent shadows are not automatically defects. |
| G: saved-state mirror | `Tools/mirror_saved_project.ps1` defaults to dry-run; scoped `/MIR`, destination/junction checks, cache/binary/Blender-autosave exclusions. Includes Content (Frozen + Cinematics), Config, Source, Plugins, Saved/Audit, Chapters, specs, Tools and design tokens. Dry logs: `%TEMP%/melodia-mirror-20260913/`. | Proposed destination `G:/BS_GodFile_Mirror/20260913`; initial dry run 119.75 GiB / 55,549 files plus project descriptor, zero failures/extras. Real run awaits owner approval and a saved, closed, stable source. This mirrors the saved local tree, including uncommitted assets; it is not a claim that local tree equals main. |
| World Compiler close-out (2026-09-19) | Live `--skip-scaffold --fx --lookdev` **PASS**. BrushifyIsland SpeedTree + walk dressing; Niagara children forged/placed; lookdev board recaptured (waterline_dolly / website_oblique / top / south / south_fix). | Hue may still read muted if Cymatics wind scalars stay 0 (do not write MPC). Substrate Toon PARK. Recruiter caption: compiler meadow on Brushify, frozen PPV, hue-reveal unproven until PIE wind. |
| Morning Niagara rewire (2026-09-19) | Disk **14:49** + live bind **PASS 2026-09-20**. `rewire_morning_fx.py --effect bind-user`: Petal/Pollen/Mist/Dust SpawnRate plus WindFront `Gust_Leader` `Spawn Count` → `User.WindFrontVisible`. | Hue-reveal is PIE wind only (no MPC). PondMist `*001` cleanup remains. Do not edit EnvSandbox parents. Do not UBT while the editor is open. |
| Git close-out (2026-09-20) | Isolated batches on `wip/pre-restart-working-tree-2026-09-19`; local `main` pointer fast-forward to `origin/main`. Remote PR is the merge vehicle — not a dirty-tree dump. | Park Frozen/MPC/`DefaultEngine.ini`/Humber/EnvSandbox dumps. Branch still 29 behind `origin/main` until a clean merge. Do not merge `feature/b-castle-zen-hism-2026-09-19` (`a98eb1b17`) as the Niagara tip. |

C++ and its asset closure passed a closed-editor UE 5.8 Development build (460/460 actions).
Offline contract suites: 22/22 PASS; collapse/scaffold regression tests: 2/2 PASS. The broader
QSC failure above is deliberately retained. The owner approved narrowly tracking the three
WaveHarp_R07 meshes and the exact recursive dependency closure; no other Cinematics path is
unignored.

**UI inventory, completed read-only:** 144 widget Blueprints / 955 styled widgets,
108 distinct colours / 73 font-size pairs. Raw inventory is local at
`%TEMP%/melodia-ui-audit-all-0913.json`. The table below lists game-facing authored-text
candidates outside the token palette, not verified runtime defects; check bindings,
animations and active screen reachability before changing values. Transparent shadows and
white texture multipliers are excluded. Third-party ArtOfShader/UltraDynamicSky editor
utilities are outside the game's styling scope.

| Folder | Remaining widget candidates (names relative to folder) |
|---|---|
| `/Game/Melodia/UI/` | `BP_MelodiaDefeatDialogue`, `Foundation/WBP_MelodiaUniversalButton`, `WBP_Battle_Results`, `WBP_BlessingBurden`, `WBP_ComicOrrery`, `WBP_DialogueBubble`, `WBP_MainMenu`, `WBP_MelodiaCurrencyRow`, `WBP_MelodiaOpeningSlideshow`, `WBP_MelodiaSettings`, `WBP_MelodiaTokenWallet`, `WBP_MelodiaWallet_Universal`, `WBP_MenuButton`, `WBP_QuestJournal`, `WBP_SaveLoadPanel`, `WBP_Settings`, `WBP_SkillCodex`, `WBP_UltCutIn` |
| `/Game/MelodiaIntegration/UI/` | `BP_MelodiaBattleUI`, `BP_MelodiaRhythmPrompt` |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/` | `BP_ActionTimeBar`, `BP_BattleUI`, `BP_CraftBar`, `BP_DamageTextUI`, `BP_ExpBar`, `BP_HPBar`, `BP_MPBar`, `BP_QuestNotification`, `BP_TurnOrderUI`, `BP_UnitClass` |
| Same stock folder, `Dialogues/` | `BP_BuyItemAmountDialogue`, `BP_CraftDetails`, `BP_CraftItemButton`, `BP_CraftItemRecipe`, `BP_DefeatDialogue`, `BP_DialogueButton`, `BP_EquipmentButton`, `BP_EquipmentStatComparison`, `BP_InfoDialogue`, `BP_ItemButton`, `BP_ItemObtainDialogue`, `BP_ItemUseDialogue`, `BP_LevelUpDialogue`, `BP_QuestButton`, `BP_SellItemAmountDialogue`, `BP_ShopBuyDialogue`, `BP_ShopBuyItemButton`, `BP_ShopSellDialogue`, `BP_SkillButton`, `BP_SkillUseDialogue`, `BP_VictoryDialogue`, `BP_YesNoDialogue` |
| Same stock folder, `MainMenu/` | `BP_EquipmentDetails`, `BP_ItemDetails`, `BP_MenuButton`, `BP_PartyUI`, `BP_PauseMenu`, `BP_QuestDetails`, `BP_SaveButton`, `BP_SkillDetails`, `BP_UnitButton`, `BP_UnitDetails`, `BP_UnitDetailsSummary`, `BP_UnitPartyDetails`, `BP_WearEquipmentUI` |

`WBP_MainMenu`, integration `BP_MelodiaBattleUI`, and stock `BP_BattleUI` are tracked.
`WBP_MenuButton` and `Melodia/VFX/EffectTypes/*` are not tracked at this baseline; source
control inclusion requires the owner's scoped `.gitignore` decision before landing them.

- **Issue #51 — long-chain persistence.** Outfit → Starskiff → encounter → rhythm → Convergence →
  reward → save → quit → relaunch → load → load again, with no duplication. Refresh from current
  `main`; do not merge stale PR #54 wholesale. Audit `RestoreNarrativeRecord*` for partial mutation,
  add repeat-load equality tests, and separate durable vs derived Starskiff/Convergence state before
  any save schema v6.
- **Packaged golden run** of `specs/p0/core_p0_dream_golden_run.v1.json` — not certified.
- **Allowlist is relaxed in editor builds** (`bRelaxedAllowlistInEditor`); run one pass with it off
  before any packaged demo.
- **Owner decision:** retire vestigial `melodiaBattleUI` / `MelodiaUI` vars on `BP_BattleController`.
- **Audio reactivity gap:** `M_Master_Toon_Universal_Alpha` has none of the 14 `Cymatic_*`/`Audio*`
  params, so its 109 instances (incl. Melusina `SW_Dress_P01..P48`) cannot react.
- **Sea Above look-dev:** `W_Glacier_Rock` is a near-black Gaea export (re-export); an unidentified
  writer rewrites `MI_Glacier_Landscape_Layered` weights. Pin Ultra Dynamic Sky before trusting any A/B
  capture on `LV_SeaAbove_Prototype`. Measured 2026-09-12: 11 bounded PCG volumes (largest 83×15×17 m),
  not four giant ones. `PCG_East_AtlantisGrove2` is an exact duplicate of `PCG_East_AtlantisGrove`
  (same transform, seed 42, all 193 instance transforms) — delete it. PCG regenerate + save leaves the
  previous generation's spawned actors on disk: `ResonanceCathedral Music Node0–11` exists three times,
  and the 09-01 set is referenced by no volume on `main` or any branch.
- **Choral Sheep — still owed:** foot-slide check against the ABP thresholds 10/5 and 120/100 at real
  frame rate (the background editor ticks PIE at ~3 fps — test in the foreground or under `slomo`);
  lit-level REST → ROOT_C → hit → REST capture; plug the new UVPackmaster normal maps into
  `MI_ChoralSheep_Body` (they now land on UV0 via `deploy/blender/choral_sheep_export_bakeuv.py`).
  `Retarget/SK_MrSheep` is the retarget source at ~100× scale; never place it in a level.
- **VFX / materials still owed:** Melusina sprite sizes 0.03–0.10 look metre-scale (owner look call);
  sort/shadow sweep on the remaining `VFX/Systems/**` sprite systems; golden-run spec names
  `/Game/L_Melodia_Dreamstate`, which does not exist.
- **Eyewear PRs #205 / #194** each touch protected `.gitignore` and add 16 files under `Saved/`; the
  −1,835 lines are a `Tools/registry_baseline.json` regeneration. Owner review before merge.
- **`cleanup/pbr-twin-landing-2026-09-10` resurrects the docs collapse.** Its snapshot `673a5ddf`
  re-adds 830 of the 840 files `08a608bc` deleted, including `Docs/Career`. Never merge it wholesale;
  promote its real work (MK39 skiff GN, Sea Above external actors, HUD tokens) in scoped PRs.
  `Docs/Career` also sits on ~37 remote branches and in `main`'s history; purging it needs an
  owner-approved history rewrite.

---

### P0 closeout — plan of record, 2026-09-16

**Every gate reads PASS, but the proof is old.** Latest ledger rows (`Saved/gate_ledger.json`,
latest row per id) are all `pass` and `melodia_system_golden_run_preflight` returns `ready`,
yet `runtime` is 08-13, `save_load` / `repeat_consume` 08-14, `package_launch` 09-03 — before
three weeks of `L_MelusinaMorning` and Melusina rig work. **Issue #51 is the only open P0 item**;
draft PR #144 (refuse incompatible `FMelodiaNarrativeRecord` candidates without resetting the
valid record, plus atomicity and repeat-restore tests) is its implementation. Stale PR #54 stays
closed. Starskiff persistence decision (from #144): persist `flag.sea_above.starskiff_ready` and
the spawn tag only — never `bBoarded`, possession or transform. Boarding contract live proof:
`Saved/Audit/starskiff_boarding_proof_2026-09-10.json`.

**Automation, 2026-09-16 (headless `UnrealEditor-Cmd`, `Melodia.` prefix): 97/99 pass.**
Report: `Saved/Audit/p0_closeout_2026-09-16/automation/`.
- `Melodia.Roguelike.Functional.ThreeStagePhysicalRoute` fails headless only: it expects the
  `Using CommonUI without a CommonGameViewportClient` warning, which needs a real viewport.
- `Melodia.Roguelike.Functional.TwentyFiveGenerationSoak` additionally raised
  `Accessed None ... Title` in `BP_SkillUseDialogue` and a `RecoverableFailure` at
  `RD_MelodiaGrove_V1` **with the uncommitted 2026-09-15 `BP_BattleUI` dead-island cut in place**.
  The same test with the committed `BP_BattleUI` failed only on the viewport expectation. That
  cut is therefore held back uncommitted (rollback: `Docs/Audits/ROLLBACK_BP_BattleUI_2026-09-15.json`).
- Do not run automation through Monolith `editor_query run_automation_tests`: latent tests trip
  `Assertion failed: LatentCommands.IsEmpty()` and crash the editor. Use `UnrealEditor-Cmd`.

**PIE, 2026-09-16 (rebuilt editor, `L_MelusinaMorning`, 18 s):** `ok` — 0 Blueprint runtime
errors, 0 Accessed None, 0 fatals; live pawn `BP_MelusinaJRPGCharacter` on `ABP_Melusina_Current`;
13/14 frames valid. `BP_MelusinaJRPGCharacter` already carries #210's stencil 4 (verified live).
On-screen engine warning: **eye-adaptation exposure −5.4 is outside Lumen's safe range [−4, 16]**
("cached lighting … going to be clipped", `r.EyeAdaptation.CachedLightingPreExposure`) — a look
issue for the Morning PPV/exposure, not a P0 blocker. Stills: `Docs/Evidence/P0_CLOSEOUT_2026-09-16/`.

**Phases**
0. *Land on `main`, editor closed.* Branch reconciled with its origin copy and `main` merged in
   (2026-09-16). Binary picks: frozen PPV MIs kept from the 09-15 lock-in; Choral Sheep
   `A_Sheep_Death/Jump/WalkSlow` + `SK_MrSheep_Skeleton` taken from #209 (the owner's 09-16 save of
   the other sheep takes already matched #209 byte-for-byte); `BP_MelusinaJRPGCharacter` kept from
   the 09-16 save, so #210's `CharacterMesh0` custom-depth **stencil 4** must be re-applied in the
   editor. Then PR to `main`, and rebuild `BS_GodFileEditor` with UBT while the editor is closed.
1. *#51 code.* Rebase #144 onto `main`, headless-test the `Melodia.Integration` suites, merge on
   green. Proposed scope cut: #144 + the restart and packaged proofs are the closure; schema v6 and
   the stale-write guard move to P1 unless an audit finds a real race.
2. *Re-prove on current `main`.* Restart proof (save → quit → relaunch → load, real input) and a
   packaged proof (cook to `G:\melodia_packages\`, omit `-map=`); append fresh ledger rows.
3. *Close.* Refresh this file, `front_door_health --age` green, close #51 with receipts.

**Not P0:** `Morning_Bed` on `_Scratch/MI_GemstoneTest_Inst`; 13 house meshes on
`M_Material_003`; three of four `PPV_NikkiDream` blendables at weight 0 (intent unconfirmed);
a second, differently-shaped 18-node BellTree generation under `Morning_Dell_Banks`; shirt
dangle bones; `Content/Textures/` allowlist. Reference:
`Docs/MELUSINA_WARDROBE_PHYSICS_PIPELINE_2026-09-15.md`.

**Held for owner sign-off:** the uncommitted `Config/DefaultEngine.ini` edit (drops the dead
`DefaultFeatureAntiAliasing=1`; live `r.AntiAliasingMethod=1` unchanged) — the pre-commit hook
requires `SKIP_PROTECTION=1`. C: had ~17 GB free on 2026-09-16 and LFS briefly failed with
"not enough space"; cook to G:.

## 4. Owner queue — now

**Thesis:** Creature → Motif → Harmony → World. **Semester (Humber Fall 2026):** First Dream is the
stable technical proof (protect and polish only). Shorewake Calling is the semester artwork.
Choral Sheep is the capstone lane.

**Active owner request — Melusina convergence and portfolio pass:** retain the existing runtime BP as Ultimate; produce a complete 13-system Niagara contact sheet; correct the staged FLIP export/import path; compare the hair source pivot with the verified runtime bind; then capture a polished Unreal portfolio render. Locomotion, Rokoko, and Foundry integration remain owner-confirmed working capabilities.

1. **Choral Sheep UE proof.** REST vs HIT fleece captured 2026-09-20 on the approved Nikki path
   (`MI_ChoralSheep_Body` → `M_Master_Toon_Character`, Chladni child + `T_Chladni_C_ROOT`). PIE
   `ApplyChoralSheepDefinition` / `TryBeginHarmonize` / weight 1.0→0.0 re-proven. Next: owner
   pixel-judge the stills against Board 06. Do not invent a sheep AI.
2. **UE ↔ TD proof.** Phrase bus `RecvFrom` is in the 17:48 DLL. Re-open the editor, PIE, send
   `phrase_bridge` to `:9000`, and read GetCurrentState. Do not rebuild the TD scene. Do not UBT
   while the editor is open.
3. **One 5–10 s AE sequence** — 8s Creature→Motif→Harmony→World mp4 is at
   `Saved/Audit/AE/ship_queue_beat_8s/Melodia_ShipQueue_Beat_8s.mp4`. JSX:
   `C:/MelodiaTouchDesigner/ae/ship_queue_creature_motif_harmony_world.jsx`. Headless AfterFX
   2026 cannot init GPU3 while Unreal holds the adapter — run the JSX after the editor is closed,
   then promote to the site.

Then: the 3–5 minute playable Shorewake route (`Chapters/02_shorewake_calling/`), then Issue #51.

**Task filter:** a task must produce a graded Humber deliverable, a visible portfolio improvement,
or remove a real blocker to one of those (`Docs/Semester/FALL_2026_ACADEMIC_MATRIX.md`).

**Not now:** git archaeology, new frameworks or second authorities, website redesign (showcase soft
freeze since 2026-09-07), or research sweeps. Keep status changes in this file and do not create
another status, handoff, plan, receipt, or session-note document. Oracle / Thirteenth Note
(`Docs/Strategy/ORACLE_*`) is a gated end-of-semester stretch.

---

## 5. How progress is measured

Playable minutes and captured proof — not gates, commits, or documents. As of 2026-09-10 the
authored QuillScript is 16 `.qsc` files, about 500 lines, several of them smoke tests. A session
counts if it adds playable or presentable minutes, or removes a real blocker.

---

## 6. Where things are

| What | Where |
|---|---|
| Game (this repo, **private**, no licence file) | `fromage3900/MelodiaMelusinaV2`, local `C:/EnvironmentPortfolio/BS_GodFile` |
| Website (**public** — serves GitHub Pages; owner decision 2026-09-12) | `fromage3900/my-site` |
| TouchDesigner / AE (private) | `fromage3900/MelodiaTouchDesigner`, `C:/MelodiaTouchDesigner/td/grandmaster_melodia/` |
| AI token treasury (revenue sidecar) | my-site `tools/fromage-webgl-kit/TREASURY_LEDGER.json` — 0 entries, first gate 0/5; never displaces the capstone |
| Accessory / WebGL website lane (isolated) | [`Website/fromage-webgl-kit/`](Website/fromage-webgl-kit/) — floral atelier + commerce embed, DCC `KHR_materials_variants` GLBs. Not the recruiter site. Cloud cannot push `my-site` (403). |
| `C:/EnvironmentPortfolio/` | workspace folder only; its root Git repo is retired |

**The game repo is private; `my-site` is public.** Never commit personal, school, career, or client documents to either.

- **Route maps:** `/Game/Melodia/Levels/Opening/L_MelusinaMorning` →
  `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype` →
  `/Game/EnvSandbox/Environments/L_KaleidoNave`; menu `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu`.
- **Systems test level:** `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` — additive only.
- **Workstations:** Humber lab = primary interactive; home PC = render/bake worker
  (`deploy/render_worker.ps1`); ASUS laptop = auxiliary. `main` is the shared baseline.
  `collab/laptop/longterm` is the laptop Blender/GN lane — never wholesale-merge or delete it
  (`Docs/Production/BRANCH_WORKSTATION_POLICY.md`).
- **Packaging:** cook to `G:` (C: lacks space). `Config/DefaultGame.ini` `MapsToCook` is correct —
  omit `-map=`.
- **Git health:** `python Tools/git_ok.py` — if it prints OK, Git is not the task.
- **Art references:** `Docs/Art/VISUAL_REFERENCE_INDEX.md`. Melusina House GN:
  `MELUSINA_HOUSE_GN_START_HERE.md`.

---

## 7. Traps that keep costing sessions

- **Stale DLL.** Compare `Binaries/Win64/UnrealEditor-BS_GodFile.dll` mtime against the source
  before trusting any PIE result.
- **One editor, one MCP writer** (Monolith port 9316). A second editor logs to
  `Saved/Logs/BS_GodFile_2.log`.
- **Background agents.** OpenCode in Rider (runs a git MCP server), Hermes, and the Melodia
  scheduled tasks (disabled 2026-09-10) have switched branches and committed mid-merge. Check
  before any editor or git work.
- **Material instance writes** need `update_material_instance()` to reach the renderer.
- **Never `load_level` straight after stopping PIE** — teardown is async and crashes the editor.
- **Codex desktop drives the editor too.** `ChatGPT.exe` → `codex.exe` holds its own
  `monolith_proxy.exe`, loads maps, saves, runs `Build.bat BS_GodFileEditor` against an open editor and
  restarts it. `ListAgents`/`SendMessage` do not reach it. Check `monolith_proxy.exe` parents and a
  running `UnrealBuildTool.dll` before closing, rebuilding or PIE-driving.
- **Read-only content files come from Git LFS locking.** `.gitattributes` marks `*.uasset`, `*.umap`,
  `*.blend`, `*.fbx` and 31 more patterns `lockable`, so every checkout, reset or branch switch makes
  them read-only and editor saves fail with "because the file is read-only!". Nobody uses LFS locks
  (`locksverify false`). In each clone or worktree run `git config lfs.setlockablereadonly false`, then
  clear the flag once: `Get-ChildItem Content -Recurse -File | ? IsReadOnly | % { $_.IsReadOnly = $false }`.
- **Monolith `run_python` cannot sleep** — `time.sleep` is intercepted and PCG `generate()` is async, so
  instance counts read in the same call race generation.
- **Headless Blender hangs on user add-ons** — pass `--factory-startup` for `-b` inspection/bake runs.

Stale-agent damage classes (read these before any WC / Jev / Blender / git work):

- **Collapsed docs.** Never resurrect paths deleted in `08a608bc`. CI: `Tools/guard_collapsed_paths.py`. Never wholesale-merge `cleanup/pbr-twin-landing-2026-09-10`. Recover old docs with `git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).
- **Bedroom / Sphere3D meadow.** Live Morning field is flowers on `BrushifyIsland_*` only; dressing on `WC_EscherWalk_*` plus island skirts; bedroom keepout in `recipes/morning_rainbow_bloom.v1.json`. Do not plant `SM_classic_arch_*`, `Sphere3D`, `WC_DellFloor`, or invent a second meadow.
- **Second authorities.** No second World Compiler, MPC writer, Niagara framework, battle manager, phrase bus, Jev, or Monolith.
- **MPC/PPV writes** to “fix” muted hue or lookdev. Hue-reveal proof is PIE wind, not a writer. Frozen PPV stays frozen.
- **Dirty-tree dump.** Isolated PRs only. Morning closeout is `feature/morning-closeout-2026-09-20` (PR #249). Park Frozen PPV, MPCs, `DefaultEngine.ini`, EnvSandbox dumps, and Humber.
- **Blender / G: junctions.** Do not robocopy, junction, or overwrite `harp_bow_pipeline`. Open `C:\EnvironmentPortfolio\MELUSINABACKUPBECAUSEAIAGENTSARERETARDED.blend` (Sep 5, verified) or the v22 recovered stage.
- **Jev confusion.** Jev (`Tools/listening_field/jev_director.py`) is a director over allowlisted sheep/world/`layout_seed` options. It does not drive UE. `recipes/jev_showcase_bloom.v1.json` is a World Compiler recipe whose name is unrelated.
- **Ghost spec / wrong phrase bridge.** Durable spec is [`Docs/Production/LISTENING_FIELD_SPEC_2026-09-20.md`](Docs/Production/LISTENING_FIELD_SPEC_2026-09-20.md). `Content/Python/resonant_world_phrase_bridge.py` is MIDI ecology, not Jev.
- **gitignore `Tools/*` swallowing live lanes.** Keep `listening_field` / `phrase_bridge` / `live_source` un-ignored.
- **Skip `scene_context_cycle`.** Any WC / PCG / Monolith spatial edit requires `scene_context_cycle.begin()` before the first mutation and `end()` after. One editor, Monolith `127.0.0.1:9316` only.
- **UBT while the editor is open.** Closed-editor builds only. A stale `UnrealEditor-BS_GodFile.dll` is how OSC readback stays at bar 0.

---

## 8. Keeping this healthy

**Docs.** This replaces the front-door contradiction checker: one status document cannot contradict
itself.

- A change that alters project status updates this file **in the same PR** (PR template checkbox).
- No new handoff, plan, receipt, scorecard, or session-note files. That narrative belongs in the
  commit or PR body, where it is already dated and attributed.
- A new doc is only for durable reference — pipeline, contract, spec, runbook, bible, research.
  Name it for what it teaches, not for the day it was written.
- Monthly: re-read §2 and §3 against the current build. Delete any claim you cannot point at
  evidence for. Nothing is lost — `git show 7d271c15:<path>`, tag `docs-precollapse-2026-09-10`.

**Git.** `python Tools/git_ok.py` first; if it prints OK, git is not the task. One branch per
reason, named per `CONTRIBUTING.md`. Never let a background agent commit on your behalf — check for
OpenCode (Rider) and Hermes before editor or git work.

**CI.** The doc-policing steps are gone: `repo_governance_guard.py` and `front_door_health.py`
existed to cross-check front-door docs against each other, which a single document cannot fail. PR
CI still runs the protected-asset guard, the echo manifest, the offline contract suites, and the
health scorecard.

**Hygiene.** This repo is private and `my-site` is public. Personal, school, career, and client
documents live in local-only `C:/EnvironmentPortfolio/_offgame/` and never in either repo.

**Weekly, ten minutes:** is §2 still true, is §4 still what you are actually doing, does `git_ok`
pass, and did anything get written this week that should have been an edit to this file?
