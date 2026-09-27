# Rokoko → Melusina mocap

**Status (2026-09-27):** the **direct-target lane is canon.** Corrected — this file previously
described a `SK_MocapSource` + IK-retargeter path that the live importer does not use, and
instructed the reader to do the opposite of what production code does. See "Retired path" below.

**Capture budget — read before planning any recording.** Rokoko lists Vision AI at **30 seconds per
month during a trial** for Basic, Plus, and Pro; Starter is also listed at 30 seconds per month.
Five 3-second takes use about half that allowance. **Text-to-Motion generation is listed as
unlimited**, though the number of clips Studio can import depends on the plan. Plan around landing
existing clips before spending the limited Vision allowance. Verified against
[Rokoko pricing](https://www.rokoko.com/pricing) 2026-09-27; the 30s trial figure was already
recorded locally in `Imports/Mocap/Rokoko/Inbox/EXPORT_STEPS.txt`.

**Status authority:** `CURRENT_STATE.md`. **Workflow routing:** `Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md`.
**Evidence + numeric proof:** `Docs/Handoffs/ROKOKO_MELUSINA_ANIM_EVIDENCE_2026-09-22.md`.

## Architecture (live)

```
Rokoko Studio (Vision video, or Text-to-Motion)
        │
        ▼  FBX export, skeleton preset = Mixamo, "Extract Root Motion" CHECKED
Imports/Mocap/Rokoko/Inbox/A_Rokoko_<Motion>.fbx
        │
        ▼  GATE — must run before anything else
Tools/mocap/rokoko_intake_gate.py     → ROOTED | IN_PLACE | NO_HIP
        │                              (Blender, headless, no editor needed)
        ▼  Blender retarget + root-motion inject
Saved/Audit/MelusinaReexport_20260921/out_<Clip>/A_Melusina_<Clip>_Mocap_RootMotion.fbx
        │                              (465 bones, underscore names, x100 cm, 30fps)
        ▼  GUARDED IMPORTER — the only sanctioned import path
Content/Python/import_rokoko_mocap_batch.py
        │  guards: skeleton identity == SK_Melusina_Skeleton
        │          c_spine_02_x cm-probe == -12.84 (rejects metre-scale lands)
        ▼
/Game/Melodia/Characters/Melusina/Animations/Mocap/
        │
        ▼  BIND — Monolith animation_query.set_state_animation
ABP_Melusina_Current → state (Idle / Glide / …)
```

Clips import **directly onto `SK_Melusina_Skeleton`.** The Blender retarget stage already resolves
bone names and rest-pose offsets against the live skeleton, so the UE-side IK retargeter is not part
of this path. The old "do not import directly" instruction was **wrong** — see "Retired path".

## The two gates, in order

**1. Intake gate — is this take worth retargeting?**

```powershell
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup `
  -P Tools/mocap/rokoko_intake_gate.py -- "Imports/Mocap/Rokoko/Inbox"
```

Writes `intake_report_<stamp>.json` beside the input. Verdicts:

| Verdict | Meaning | Action |
|---|---|---|
| `ROOTED` | horizontal travel > 0.5 m/s sustained + > 1 m path range | clear for the retarget lane |
| `IN_PLACE` | translation stripped (treadmill mode) | reject, re-export with Locomotion filter ON |
| `NO_HIP` | no hip/root bone found | inspect manually |

This gate earned its keep on 2026-09-21: it independently verdicted both `BowDraw` takes `IN_PLACE`
before any retarget work, and the later export reports confirmed ~0.05 m of travel. Its predictions
were correct. **Run it. Do not skip to the importer.**

**2. Guarded importer — did it land correctly?**

```python
# live editor, via Monolith run_python or the Python console
import import_rokoko_mocap_batch as m
m.main()
```

Writes `Saved/Audit/rokoko_mocap_import_report.json` with per-clip `ok`, `unit_class`, `spine_y`,
`skeleton`, `length`. It **rejects** a clip on wrong skeleton or a metre-scale land, and does not
silently pass either.

## Architecture (RETIRED — the 2026-07 scaffold)

Everything from this heading to the end of the retired block describes the superseded
`SK_MocapSource` + IK-retargeter lane. **Do not follow it.** `import_rokoko_mocap.py`,
`headless_retarget_mocap.py`, `run_headless_mocap_retarget.ps1` and the `A_Mocap_*` clips are
legacy. Live Link is also not installed — no `LiveLink`/`Smartsuit` entry exists in
`BS_GodFile.uproject`.

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

> **WRONG — corrected 2026-09-27.** The original line here read "Do **not** import Rokoko FBX
> directly onto `SK_Melusina`." The live importer does exactly that, and its skeleton guard plus
> centimetre probe are the sanctioned safety net. See the live diagram at the top of this file.

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

## Naming — the real behaviour (live lane)

The importer requests `A_Melusina_<Clip>_Mocap_RootMotion`, but **UE concatenates the FBX's internal
take name**, producing:

```
A_Melusina_WalkElegant_Mocap_RootMotionMelusina_Mocap_Rig_Action
```

The trailing `Melusina_Mocap_Rig_Action` is the armature object name, not an importer mistake. It is
stable and harmless, but bindings and any script naming a clip must use the full concatenated string.
Do not "fix" the importer to fight this — the FBX take name wins.

Each import also emits per-bone `*_clip_Base_Layer.uasset` strays (13 per clip); 65 currently sit in
the Mocap folder. They are read-only under Perforce; clearing them needs `p4 edit` plus owner
approval (deletion).

## Export settings that matter (live lane)

Per `Imports/Mocap/Rokoko/Inbox/EXPORT_STEPS.txt` (owner-verified 2026-09-21):

- **Locomotion filter = ON** — reconstructs real travel from foot contacts.
- **"Extract Root Motion" CHECKED** (Studio 2.3.2+). This checkbox *is* the root-motion lane.
- **Do NOT use treadmill mode** (wand icon) — it strips foot locking and yields `IN_PLACE`.
- Skeleton preset **Mixamo** · FPS **30** · Body mesh OFF · Face OFF · 2–4 s per take.

With 30 s/month of Vision, every attempt is expensive. **Gate before you export, not after.**

## Binding a verified clip (live lane)

Monolith must be live (editor open, port 9316). One editor session, one state at a time:

```powershell
python .agents/skills/melusina-blender-handkeyed-import/scripts/bind_and_verify.py `
  --state Glide `
  --clip /Game/Melodia/Characters/Melusina/Animations/Mocap/A_Melusina_GlideForward_Mocap_RootMotionMelusina_Mocap_Rig_Action
```

Exit 0 only if `set_state_animation` succeeded, the ABP compiled with 0 errors, the `.uasset` mtime
is fresh, **and** a live re-read shows the new binding. `save_asset` returning success is not
evidence on its own.

**Rate scale is mandatory for travelling clips.** GlideForward measures **217 cm/s**. Bind it
unadjusted against a controller glide speed and the feet slide. Set
`rate_scale = controller_speed / 217` on the montage.

## Known open items (live lane)

- **T-pose actor unidentified.** The only Melusina-class actor that spawned in PIE on 2026-09-22 was
  `BP_MelusinaSwordsman_Presentation`; its anim class was never read before the editor closed.
  Resolve with `mcp__melodia__melodia_animation_get_runtime_abp` — requires Monolith up.
- **`Glide` state is still a placeholder** (`A_Mocap_LittleDance_001`).
- **`BS_Melusina_Locomotion` runs old root-locked in-place clips** (Idle@0 / Walk@180 / Run@420 /
  Sprint@630). Axis values are nominal guesses, never measured. None of the five Rokoko takes feed
  any blendspace yet.
- **`BS_Melusina_Locomotion_Hybrid` is degenerate** — 7 samples with 3 duplicates, referenced only by
  a dangling AnimGraph node nothing live consumes.
- **4 dead AnimGraph nodes** in `ABP_Melusina_Current` (1 BlendSpacePlayer + 3 Slots).
- **Second Inbox consumer.** `deploy/surreal_arch/dollkit_pipeline/rokoko_bone_map.json` points the
  same five FBX at `MEL_DollRig` (15 bones, 14 mapped). Legitimate, but there is no single intake
  contract tying the two target rigs together. Its note says "65 bones"; the intake gate measured
  **52** — the note is wrong.

## Scripts (live lane)

| Script | When |
|---|---|
| `Tools/mocap/rokoko_intake_gate.py` | Blender, headless — **every** Inbox FBX, before retarget |
| `Content/Python/import_rokoko_mocap_batch.py` | Live editor — guarded import of `out_*` FBX |
| `.agents/skills/melusina-blender-handkeyed-import/scripts/bind_and_verify.py` | Monolith live — bind clip → ABP state, with proof |
| `Tools/mocap/verify_blend.py` | Reject zero-filled `.blend` husks before trusting a recovered file |
| `Tools/mocap/rig_gate.py` | Confirm which rig a `.blend` actually contains |

## Traps (live lane)

- **Never bind a clip whose rest pose was never resolved against the live skeleton** — name-matched
  tracks explode the mesh. The Rokoko lane is safe because the Blender stage retargets first; an
  ad-hoc FBX dropped straight at the importer is not.
- **cm-probe passing is not enough.** It validates units on one bone.
- **One `capture_anim_frames` per editor session** — a second call trips the documented
  `!IsRooted()` Monolith crash.
- **Do not hold PIE `UWorld` refs across `run_python` calls.** This caused a fatal
  `World Memory Leaks: 1` on 2026-09-22. Use Monolith `pie_*` C++ actions instead.
- **`.uasset` files are read-only under Perforce** (p4d `localhost:1666`, depot `//Melodia`, client
  `Melodia_ws`). `p4 edit` before writing; never `attrib -R` / `chmod`.

---

*End of retired block. The live lane is everything above it.*
