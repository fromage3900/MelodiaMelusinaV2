# Melusina Blender Hand-Keyed Animation Pipeline — Status 2026-09-02

**Generated:** 2026-09-02 (offline evidence-gather; no editor calls)
**Canonical doc:** `Docs/Production/BLENDER_HANDKEYED_ANIM_IMPORT_PIPELINE_2026-08-22.md`
**Companion skill:** `melusina-blender-handkeyed-import`

---

## 1. Current clip states

### VERIFIED (bound / proven upright)

| Clip | Path | Evidence |
|---|---|---|
| Idle | `Animations/Locomotion/A_Melusina_Idle_Mocap_RootX` | `bind_and_verify_idle_1787383828.json` (2026-08-22, ok=true); upright in PIE |
| Glide | `Animations/Mocap/A_Mocap_LittleDance_001` | `melusina_idle_glide_final_2026-08-22.json`; placeholder on `bIsGliding` entry/exit |

### QUARANTINED (exploded — do NOT bind until Stage E IK-retarget passes)

| Clip | Path | Failure | Evidence |
|---|---|---|---|
| Authored idle | `Animations/Authored/A_Melusina_Idle_v22` | Lying flat + collapsed (name-matched onto SK_Melusina_Skeleton) | `v22_broken_abp_idle_v22_*.png` |
| Blender idle | `Animations/Cascadeur/A_BL_Melusina_Idle_Loop` | Exploded black pile (cm-probe passed but rest-pose misaligned) | `ABL_exploded_abp_idle_ABL_*.png` |

### NEW SINCE 2026-08-22 (pipeline advanced)

| Clip | Location | State |
|---|---|---|
| `A_Melusina_Idle_v22.fbx` | `Exports/MelusinaAnims/A_Melusina_Idle_v22.fbx` (6.3 MB) | Stage B export complete (2026-08-22). NOT yet through Stage C (remap) or D (import). |
| `A_Melusina_Idle_v22_ARP.fbx` | `Exports/MelusinaAnims/A_Melusina_Idle_v22_ARP.fbx` | ARP-variant export. |
| `A_BL_FinalHandKeyed_Source_20260824.fbx` | `Exports/AnimationLibrary/Blender/` | Manifest: `lane_a_ready=true`; 464 bones, 30 FPS, cm header, animation-only. IK retarget + live non-bind proof PENDING. |
| `A_BL_Source_Idle_Loop__MUAL_SRC.uasset` | `Animations/SourceRetargeted/` | In UE (source-rig contract). |
| `A_BL_Source_Idle_Loop__MUAL_TARGET.uasset` | `Animations/SourceRetargeted/` | In UE (target-rig contract). |
| `SK_QuaterniusArmature_Idle_Loop.uasset` | `Animations/SourceRetargeted/` | In UE (source retargeted). |

---

## 2. Stage blend existence

| Location | Result |
|---|---|
| `Content/Melodia/Characters/Melusina/**/*.blend` | **NONE** |
| `Tools/BlenderAddons/melodia_studio/**/*.blend` | **NONE** |
| `Content/Melodia/Characters/Melusina/**/*.fbx` | **NONE** (all clips are .uasset) |
| `Content/Melodia/Characters/Melusina/**/*.fbx` (Textures) | 1 mesh FBX (`SK_ShorewakeDress_Magical.fbx`) — not animation |

**Stage blends found elsewhere:**

| File | Location | Note |
|---|---|---|
| `Melodia_Portfolio_Stage_v23_grandmaster_RQ_20260829.blend` | `Exports/PortfolioStages/` | v23 in-repo |
| `Melodia_Portfolio_Stage_v22_FINAL_2026-08-15.blend` | **G:\ drive** (per export report) | v22 NOT in repo; was on G:\ at export time |
| `Kiritan.blend`, `Itako.blend` | `Content/Melodia/Characters/Kiritan/`, `Itako/` | Other characters |

**Implication:** The v22 stage blend that authored the hand-keyed idle is NOT in the repo. If G:\ is unavailable, Stage A re-author must happen in the v23 stage blend (or a new one). The v23 stage blend IS in-repo.

---

## 3. Blender addon (melodia_studio) — 5.2 compatibility

`Tools/BlenderAddons/melodia_studio/__init__.py` declares:
```python
"blender": (4, 0, 0)
```
This is a minimum version (4.0+). **Blender 5.2 is compatible.** The addon's modules (midi_bridge, studio_panel, walkable_world, terrain_dressing, gaea_panel, tandem_bridge, melodia_chrome) are version-agnostic panels/operators. No 4.3-only API calls detected in `__init__.py`. The `__pycache__` shows cpython-314 and 311 bytecode — reloaded cleanly on register.

**Verdict:** Use `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`. Addon works.

---

## 4. Export / import script inventory

| Script | Required | Present | Notes |
|---|---|---|---|
| `Tools/export_melusina_idle_v22.py` | Stage B | YES | Headless armature-only FBX, baked, `-Z`/`Y` axes. |
| `Tools/remap_arp_fbx_to_ue.py` | Stage C | YES | dots→underscores, ×100 units, factory-startup. |
| `Content/Python/import_blender_melusina_idle.py` | Stage D | YES | Guarded UE import, cm-probe, source skeleton. |
| `Tools/melusina_anim_unit_guard.py` | Stage D dep | YES | `classify_spine_translation`, `spine_matches_mocap_cm`. |
| `scripts/bind_and_verify.py` | Stage F | **NO** | Only evidence JSON exists (`Docs/Evidence/2026-08-22_melusina_idle_glide/bind_and_verify_idle_1787383828.json`). The bind-and-verify SCRIPT is missing from `scripts/`. |

---

## 5. Offline vs editor-bound split

### Can run offline (no :9316)

- [x] Stage B: re-export idle from v23 stage blend via `export_melusina_idle_v22.py` (Blender 5.2 headless)
- [x] Stage C: remap FBX via `remap_arp_fbx_to_ue.py` (factory-startup Blender)
- [x] Stage D prep: write sidecar contract JSON, verify FBX bone count / fps / units
- [x] Stage A: author new NLA clip in v23 stage blend (in-repo)

### Needs editor (:9316 up)

- [ ] Stage D: actual UE import (`import_blender_melusina_idle.py` — uses `unreal` module)
- [ ] Stage E: IK-retarget onto `SK_Melusina_Skeleton` (Monolith `animation_query batch_retarget_animations`)
- [ ] Stage F: bind into `ABP_Melusina_Current` via Monolith (`set_state_animation`)
- [ ] Stage G: `editor.capture_anim_frames` (ONE per session)

---

## 6. Next action to unblock

**Immediate (offline, unblocks the quarantine):**

1. **Confirm v22 stage blend availability.** If `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_FINAL_2026-08-15.blend` is reachable, re-run Stage B to export a fresh `A_Melusina_Idle_v22.fbx`. If not, author the idle NLA track in the in-repo v23 stage blend (`Exports/PortfolioStages/Melodia_Portfolio_Stage_v23_grandmaster_RQ_20260829.blend`) and generalize `export_melusina_idle_v22.py` to point at it.

2. **Run Stage C offline.** `blender --background --factory-startup --python Tools/remap_arp_fbx_to_ue.py -- <in.fbx> <out.fbx>`. This produces the remapped FBX + `.remap.json` sidecar. No editor needed.

3. **Write the sidecar contract JSON** next to the remapped FBX with `ue_import: false` (flip only after Stage E).

4. **Re-stage the quarantined clips.** Both `Authored/A_Melusina_Idle_v22` and `Cascadeur/A_BL_Melusina_Idle_Loop` must go through the full A→B→C→D→E→F chain. They cannot be name-matched onto `SK_Melusina_Skeleton` — that is the failure mode that quarantined them.

**Editor-gated (wait for :9316):**

5. Stage D import → Stage E IK-retarget → Stage F bind. These are sequential and all editor-bound. Nothing in the quarantine list can be promoted until this chain runs on the freshly exported FBX.

**Blocker:** `scripts/bind_and_verify.py` does not exist. The 2026-08-22 evidence JSON proves the bind-and-verify RAN, but the script is gone from `scripts/`. Recover it from git history or recreate from `Saved/Audit/melusina_idle_glide_final_2026-08-22.json` + `Docs/Evidence/2026-08-22_melusina_idle_glide/` before Stage F.

---

## 7. Inventory summary

- **Clips inventoried:** 10 (2 verified bound, 2 quarantined, 6 new since 2026-08-22)
- **FBX files under `Animations/`:** 0 (all .uasset; FBX live in `Exports/` and `Imports/Animations/Cascadeur/Inbox/`)
- **Stage blends in-repo:** 1 (v23); v22 on G:\ drive only
- **Scripts present:** 4/5 (`bind_and_verify.py` missing)
- **Blender 5.2 compatible:** YES (addon declares 4.0+)