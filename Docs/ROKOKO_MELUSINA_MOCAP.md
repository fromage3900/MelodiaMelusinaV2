# Rokoko → Melusina mocap setup

**Status:** Pipeline scaffolded 2026-07-12. Existing batch retarget (`RTG_Mocap_to_Melusina`) is the game path. Rokoko feeds it via FBX (and optionally Live Link for preview).  
**Phone + scan companion:** [`MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md`](MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md) — Live Link = preview on `SK_MocapSource` only; shipping clips = FBX inbox → retarget.

## Architecture

```
Rokoko Studio (suit / gloves / face)
        │
        ├─ Live preview (optional) ── Epic Live Link + Rokoko Smartsuit plugin
        │                              → drive SK_MocapSource (Newton / preview mesh)
        │                              → bake Animation Sequence when happy
        │
        └─ FBX export ──► Imports/Mocap/Rokoko/Inbox/*.fbx
                              │
                              ▼
                    import_rokoko_mocap.py
                              │
                    A_Src_Rokoko_<Take>
                    /Game/Melodia/Mocap/Source/Anims
                              │
                    RTG_Mocap_to_Melusina
                              │
                    A_Mocap_Rokoko_<Take>
                    /Game/Melodia/Characters/Melusina/Animations/Mocap
                              │
                    ABP_Melusina / montages / blend spaces
```

Do **not** import Rokoko FBX directly onto `SK_Melusina`. Always go through `SK_MocapSource` + IK retargeter.

Blender Live Link (port **9876**, Melodia mesh sync) is a different system — leave it alone for mocap.

## Folders

| Path | Role |
|------|------|
| `Imports/Mocap/Rokoko/Inbox/` | Drop new Rokoko FBX takes here |
| `Imports/Mocap/Rokoko/CharacterRef/` | Store exported `SK_MocapSource` FBX for Rokoko Studio character profile |
| `Imports/Mocap/*.fbx` | Legacy / prior capture batch (already wired) |
| `/Game/Melodia/Mocap/Source/` | `SK_MocapSource`, `IK_MocapSource`, `Anims/A_Src_*` |
| `/Game/Melodia/Mocap/RTG_Mocap_to_Melusina` | IK Retargeter → Melusina |
| `/Game/Melodia/Characters/Melusina/Animations/Mocap/` | `A_Mocap_*` game clips |

## One-time setup checklist

### A. Unreal plugins

1. Run (from repo):

```powershell
powershell -ExecutionPolicy Bypass -File Tools\setup_rokoko_livelink_plugins.ps1
```

That enables Epic **LiveLink**, **LiveLinkHub**, **LiveLinkControlRig** in `BS_GodFile.uproject`.

2. Install **Rokoko Studio Live** for **UE 5.8**:
   - Fab: [Rokoko Studio Live](https://www.unrealengine.com/marketplace/en-US/product/rokoko-studio-live), or
   - GitHub: [rokoko-studio-live-unreal-engine releases](https://github.com/Rokoko/rokoko-studio-live-unreal-engine/releases) → put `Smartsuit` under `Plugins/`
3. Restart the editor. Confirm **Edit → Plugins**: Live Link + Rokoko/Smartsuit enabled.
4. **Window → Virtual Production → Live Link** — Rokoko source should appear when Studio is streaming.

### B. Character profile in Rokoko Studio (bone match)

Rokoko FBX must match `SK_MocapSource_Skeleton` or retarget quality suffers.

1. In UE: open `/Game/Melodia/Mocap/Source/SK_MocapSource` → **Asset Actions → Export**.
2. Save FBX to `Imports/Mocap/Rokoko/CharacterRef/SK_MocapSource.fbx` (no morph targets needed).
3. In Rokoko Studio: **Characters** → import that FBX → drag onto your actor.
4. Calibrate T-pose / shoulder width to Melusina’s proportions as best you can.
5. Export body takes as FBX using that character (not a random Mixamo/Manny profile unless you build a new RTG).

### C. First test take

1. Record a short idle or walk in Rokoko Studio.
2. Export FBX → `Imports/Mocap/Rokoko/Inbox/IdleTest.fbx`
3. In Unreal (editor open), run Python:

```python
import import_rokoko_mocap as r
r.main(import_only=False)  # import + retarget Rokoko-prefixed clips
```

Or import only, then close the editor and run:

```powershell
powershell -ExecutionPolicy Bypass -File Tools\run_headless_mocap_retarget.ps1
```

4. Open `A_Mocap_Rokoko_IdleTest` on `SK_Melusina` / `BP_Melusina` and verify spine/neck.
5. Report lands at `Saved/Melodia/rokoko_import_report.json` (import) and `Saved/Melodia/retarget_report.json` (headless batch).

## Naming

| Rokoko file | Source anim | Melusina anim |
|-------------|-------------|---------------|
| `Inbox/WalkLoop.fbx` | `A_Src_Rokoko_WalkLoop` | `A_Mocap_Rokoko_WalkLoop` |

Keep verb names aligned with combat hooks when you can: `Idle`, `Walk`, `Run`, `Dodge`, `Stab`, `HitReact`, `Victory`.

## Live Link preview (optional)

1. Rokoko Studio: enable Unreal livestream (5.4+).
2. UE Live Link panel: confirm Rokoko subject.
3. Preview on **source** mesh / Newton / a dedicated preview actor — not production `BP_Melusina` until chains are proven.
4. Bake → `A_Src_Rokoko_*` → same retarget path as FBX.

Custom Melusina live drive (advanced): Rokoko’s “export character → Studio → Retarget Component / Live Link Pose” flow. Prefer bake+retarget for shipping game clips.

## Known gate — neck hierarchy

If Melusina’s spine/head still warps on retargeted takes, finish the ARP skeleton rewire (`Docs/MELUSINA_NECK_RIG_HIERARCHY_BUG_2026-07-11.md`) before recording a large Rokoko library. Otherwise you re-retarget everything after the skeleton swap.

## Scripts

| Script | When |
|--------|------|
| `Tools/setup_rokoko_livelink_plugins.ps1` | Once — enable Epic Live Link in `.uproject` |
| `Content/Python/import_rokoko_mocap.py` | Editor open — import Inbox FBX (+ optional retarget) |
| `Content/Python/headless_retarget_mocap.py` | Editor closed — all `A_Src_*` → `A_Mocap_*` |
| `Tools/run_headless_mocap_retarget.ps1` | Wrapper for headless retarget |

## Next after first good take

1. Walk / run / idle → locomotion blend space samples.
2. Combat verbs → montages on `BP_Melusina` (Stab / MercyStab / FairyWand / Twirl pattern).
3. If Rokoko bone names diverge from `SK_MocapSource`: duplicate `RTG_Mocap_to_Melusina` → `RTG_Rokoko_to_Melusina` and remap chains once.
