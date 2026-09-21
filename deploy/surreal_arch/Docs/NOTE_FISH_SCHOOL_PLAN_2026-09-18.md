# Note Fish School — "Melody Aquarium" — extended build plan (2026-09-18)

Status: **P0 probes done; P1 fish template LANDED (builds, gates pass, clay reads done).**
Polish list in §13, close-out/renders/texture/UE in §14-17. School assembly (P2) next.
No commits made.

One line: a school of seven note-creatures, one per Melodia element, swimming a closed
lissajous current with animated UVs driving the flow of their patterns — a loop-native
website piece that also re-skins as note-birds on a staff wire.

---

## 1. Discovery (done, before writing anything)

- Registry has no fish / school / bubble / globe builders. Closest neighbours: eel
  silhouette (`MEL_eel_silhouette`, white_current), lantern orbit (`MEL_aest_zen_orbit`),
  metronome pillar (`MEL_music_metronome_pillar`), chime family (`chimes_gn.py`).
- **Reuse, do not rebuild:**
  - body = nested `MEL_music_note_head` (Has Stem/Flag off → clean ellipse body),
    nested-group pattern per `music.py::_ensure_group_node` + `chimes_gn.py::_refresh_group_refs`.
  - module-local helper set mirrors `chimes_gn.py` (`_math`, `_combine`, `_store_named`,
    `_export_tail`, `_refresh_group_refs`, `_switch_geo`).
  - tail flag construction recipe from `music.py` flag (bezier → circle profile → CurveToMesh).
  - materials: copy-on-first-use like `melodia_house.py::_ensure_all_materials`.
- Registration surface: `melodia_gn/__init__.py` import wave block (before
  `_rebuild_derived_data()` at line 146), `presets.py` entry, optional `music_ui.py` panel.

## 2. P0 probe results — verified on Blender 5.2.1 LTS (factory-startup)

Logs: `Saved/Audit/note_school/probe_20260918_194141.txt`, `probe2_20260918_194417.txt`,
`probe3_20260918_194808.txt`. Scripts beside them (probe_note_school.py / probe2 / probe3).

| Claim | Verdict | Detail |
|---|---|---|
| Repeat zone | **NO single node.** Pair `GeometryNodeRepeatInput` + `GeometryNodeRepeatOutput` | `rin.pair_with_output(rout)` ok. Iterations via `rin.inputs["Iterations"]`; index via `rin.outputs["Iteration"]`; items via `rout.repeat_items.new("GEOMETRY", name)` (item has `.name`, no `.data_type` attr — socket appears as `Item_0` / the given name). In-repo precedent: `melodia_house.py:663-689`. Accumulation must be explicit (see §4). |
| MenuSwitch | ok | `ms.enum_items.new("RIBBON")` adds; items renamable via `.name`; outputs = item names (`['Output','FORK','B','RIBBON']`); set `inputs['Menu'].default_value` to an item NAME **after** naming; `data_type="GEOMETRY"`. Fallback: IndexSwitch (`ix.index_switch_items.new()`, precedent `melodia_city_gen.py:311`). |
| Align Euler to Vector | **`FunctionNodeAlignEulerToVector`** (function node — the `GeometryNode…` id does not exist) | in `[Rotation, Factor, Vector]`, out `[Rotation]`; `node.axis = "X"` works; precedent in 3 modules (`aesthetic_fx.py:3216`, `geometry_extras.py:693`, `water.py:361`). |
| UV Unwrap | **Field node, NO geometry socket** (operates on active geometry context) | in `[Selection, Seam, Margin, Fill Holes, Method, Iterations, No Flip]`, out `['UV']`. Methods: `'Angle Based'` / `'Conformal'` / `'Minimum Stretch'` (human names, not uppercase). Precedent: `eyewear.py:108-132` (UV → StoreNamedAttribute Value). |
| SampleCurve | ok | in `[Curves, Value, Factor, Length, Curve Index]`, out `[Value, Position, Tangent, Normal]`. |
| SetSplineCyclic / CurvePrimitiveLine / MeshLine / MeshToCurve / CurveToMesh / SetCurveRadius | ok | socket names as expected. |
| StoreNamedAttribute | ok | `data_type` includes `FLOAT2`; `domain` includes `CORNER`. |
| SceneTime | ok | outputs `[Seconds, Frame]`. |
| CaptureAttribute (multi-item) | ok | `cap.capture_items.new("VECTOR", name)` → FLOAT_VECTOR. |
| SplineParameter / SampleNearestSurface / RandomValue / SetMaterial / RealizeInstances / CurveSetHandles | ok | RealizeInstances now has `[Geometry, Selection, Realize All, Depth]`. |
| SampleSoundFrequencies | ok | in `[Sound, Time, All Channels, Channel, Low, High, FFT Size, Window Function]`, out `[Amplitude]` — reserved for v2. |
| SDF chain (MeshToSDFGrid → GridToMesh) | ok, but **build-time only** (see §5). |
| Node census via `bpy.types.Node.__subclasses__()` | **returns nothing in 5.2.1 background** | The skill's census snippet fails headless; probe by explicit id instead. (Feed back to skill later.) |

## 3. Design — fish anatomy

Design units = metres (Blender scene scale), school footprint ≈ 2.6 m.

| Part | Build | Notes |
|---|---|---|
| Body | nested `MEL_music_note_head`, Has Stem=False, Has Flag=False, Scale≈0.9 | long axis +X = swim axis (the note head is already an ellipse with a −15° tilt — that tilt becomes the fish's character) |
| Eye | small UV sphere bead, gold material | reads as note-dot + eye |
| Tail | repeat-zone segment chain (default 5), styles: RIBBON / FORK / STAR | segments along the tail line with analytic joint positions; per-segment flap with lag `(j+1)*0.15` (proven chain-lag pattern) |
| Side fins | two small swept ribbons (bezier → circle profile → CurveToMesh), lens taper via SetCurveRadius | flutter = rotation with phase lag |
| Dorsal accent | optional tiny star tip (`MEL_music_*` star note language) | style-dependent |

Per-fish materials: 7 element materials (pearl base + element tint) + gold eye.
Element → tint mapping: Forte gold / Radiant pale warm / Arcane violet / Tide cyan /
Stone slate / Gale mint / Umbral deep indigo (final hexes at build, matched to brooch palette).

## 4. Design — school, path, motion

**Path (closed by construction):** analytic 3D lissajous
`P(t) = ( A·sin(2πt + φx),  A·w·sin(4πt),  h·sin(2πt + φz) )` with weave `w` (default 0.55),
height `h` (0.28). Built `MeshLine(256) → SetPosition(Position=…) → MeshToCurve →
SetSplineCyclic` (the verified wire path — `GeometryNodePointsToCurve` does not exist).

**Fish i (unrolled, 7 fish):** factor
`f_i = MODULO((Frame − 1) · SwimCycles / LoopFrames + i/7, 1)`
→ `SampleCurve.Position` (translate), `SampleCurve.Tangent` → `FunctionNodeAlignEulerToVector`
(axis X) + yaw wiggle `sin(2π·(WiggleCycles·t + phase_i)) · WiggleAmp`
(bob optional on Z at `BobCycles`). All cycle counts are integers → seam closes.

**Repeat-zone tail (the accumulation idiom):**
```
rin.outputs[item]  (geometry so far)
  → join( , new segment j)         # j = rin.outputs["Iteration"]
  → rout.inputs[item]              # carried to next iteration
final = rout.outputs[item]
```
Joint positions are analytic (no state item needed). Fallback if accumulation misbehaves:
unrolled 5 segments or instanced segments on a mesh line.

**Solo Index** (int, −1=all): each fish subtree ends in a switch so one fish can be rendered alone.

## 5. Design — animated UVs (the centrepiece)

Two stored channels, both `FLOAT2` / `CORNER`, per fish (unrolled → phase is a constant, no fields needed):

1. **`UVMap`** — analytic cylindrical map of the body: `u = atan2(z, y)/2π + 0.5`,
   `v = (x − x_min)/(x_max − x_min)` (nose→tail). Static. Export variant: `Auto UV` bool →
   `UVUnwrap` field node (`Method = "Minimum Stretch"`), UV → Store Value (eyewear pattern).
2. **`UVFlow`** — base map + `(0, flow)` where
   `flow = MODULO((Frame − 1) · FlowCycles / LoopFrames + i/7 · PhaseSpread, 1)`.

**The three rules that make it loop-safe (write these into the build):**

- **Integer cycles.** `FlowCycles` integer → at frame `N+1` the offset wraps to exactly the
  frame-1 value (`MODULO(2.0, 1.0) = 0.0` exactly) → the seam is *exact*, not approximate.
- **Periodic-in-v materials.** Any pattern used on `UVFlow` must be periodic with period 1 in
  the flow direction: wave/checker with **integer** scale, or math on `sin(2πn·v)`. Scrolling by
  +1.0 UV then reproduces the pattern exactly, and the sawtooth wrap reads as *continuous flow*
  (the 0.98 → 0.0 step is invisible when the pattern is periodic).
- **The swim-in-place illusion.** The streak pattern flows nose→tail while the fish rides the
  lissajous — two motions, one seam.

Material contract (scene-side): body materials read `Attribute("UVFlow")` → Wave Texture
(Vector input, integer Scale) → subtle colour/emission sheen mix. Materials authored/ensured by
the shot script (copy-on-first-use names `MEL_fish_<element>`).

## 6. Creative 5.2 node usage (status)

| Node | Where | Status |
|---|---|---|
| Repeat Zone (input/output pair) | tail segment chain | API proven (§2); accumulation gate G2 |
| MenuSwitch | Tail Style (RIBBON/FORK/STAR) | proven; fallback IndexSwitch |
| SampleCurve + SetSplineCyclic + MeshLine→MeshToCurve | lissajous path ride | proven |
| CaptureAttribute (multi-item) | carry flap phase through tail curve→ribbon; fallback = recompute from SplineParameter | API proven; propagation through CurveToMesh = P1 check |
| SceneTime | every motion + UV flow | proven |
| StoreNamedAttribute ×2 (FLOAT2/CORNER) | UVMap + UVFlow | proven |
| FunctionNodeAlignEulerToVector | fish orientation to tangent | proven |
| UVUnwrap field node | export UV path (behind bool) | proven (eyewear precedent) |
| SplineParameter / SetCurveRadius | fin + tail taper | proven |
| Raycast | **E2 experiment**: phyllotaxis scale rows seated with downward raycast (never SampleNearestSurface-in-Value — the measured trap) | optional |
| **Excluded:** SimulationZone | loop determinism: sim state must provably close frame N+1 == frame 1; cannot be proven → excluded from v1 | — |
| **Excluded:** SDF chain in the live tree | re-cooks per frame; use as a **build-time study tree** (`MEL_music_note_fish_sdf`, E1) whose mesh can later be baked as the template | — |
| **Deferred v2:** SampleSoundFrequencies | reactive dial; requires the audio segment to divide the loop exactly | — |

## 7. Interface params (school)

| Param | Type | Default | Range |
|---|---|---|---|
| Scale | float | 1.0 | 0.2–3.0 |
| School Radius | float | 1.2 | 0.3–5 |
| Path Weave | float | 0.55 | 0–1 |
| Path Height | float | 0.28 | 0–1 |
| Swim Cycles | int | 1 | 0–4 |
| Loop Frames | int | 96 | 24–480 |
| Wiggle Amp | float | 8° | 0–25 |
| Wiggle Cycles | int | 6 | 0–24 |
| Bob Amp | float | 0.04 | 0–0.3 |
| Bob Cycles | int | 3 | 0–24 |
| Flow Cycles | int | 2 | 0–8 |
| Phase Spread | float | 1.0 | 0–2 |
| Tail Segments | int | 5 | 1–12 |
| Tail Style | menu | RIBBON | RIBBON/FORK/STAR |
| Solo Index | int | −1 | −1…6 |
| Element Palette | bool | True | — |
| Show Path | bool | False | — |
| Motes | bool | False | sparkle drift cloud |
| Auto UV | bool | False | SLIM unwrap for export |
| Realize for export | bool | False | house convention |
| Music Influence + Freq A/B + Amplitude | auto (new_geometry_tree) | static warp, seam-safe (no SceneTime) | — |

Single-fish builder `MEL_music_note_fish` exposes: Scale, Tail Style, Flow Cycles, Loop Frames,
Element menu (material pick).

## 8. Files, ids, registration

- `melodia_gn/note_school.py` — new module. ids:
  - `MEL_music_note_fish` — "Note Fish" (single, template + hero stills)
  - `MEL_music_note_school` — "Note Fish School (7 Elements)"
  - category `music` (Musical Notation) — alternative `effects` = one-arg change.
- `melodia_gn/__init__.py` — add `from . import note_school  # noqa: F401` in the 2026-09-14
  wave block, **before** `_rebuild_derived_data()` (line 146).
- `melodia_gn/presets.py` — `BUILDERS_PRESETS` entry:
  `SCHOOL_SEVEN_ELEMENTS`, `SCHOOL_SOLO` (Solo Index 0), `SCHOOL_DENSE` (wiggle 12, flow 4, weave 0.8).
- optional: `music_ui.py` curated panel entry (hard-listed ids near line 526/559).
- `Tools/verify_note_school.py` — gates G1–G6 harness.
- `Tools/note_school_web_anim.py` — stage + camera + render (models `brooch_web_anim.py`,
  reuses `brooch_sky.py` for sky variants).
- Outputs: `Saved/Website/NoteSchool/` (stills/, frames/, mp4/webm/poster + README).
- Audit: `Saved/Audit/note_school/` (probes, gate logs).

## 9. Phases tonight (commands)

- **P0 probes — DONE** (§2).
- **P1 fish template** — write module skeleton + `build_music_note_fish`; headless build,
  realize, vert count > 0; clay still. (~40 min)
- **P2 school** — path, 7 fish, motion, UV channels, materials, params. (~60–90 min)
- **P3 verify** — `blender -b --factory-startup --python Tools/verify_note_school.py` (G1–G6).
- **P4 sync + gates** (same session, from ADDON_AUTHORITY doc):
  ```
  python deploy/_sync_addon_to_blender_5_2.py            # LIVE ADDON SYNC: OK
  cp <file> C:/Users/brenn/melodiamelusinav2/deploy/surreal_arch/melodia_gn/
  cp <file> "$APPD/melodia_gn/"                           # live install
  md5sum <three copies> | awk '{print $1}' | uniq -c      # must print "3 <hash>"
  blender -b --factory-startup --python Tools/verify_addon.py        # GATE RESULT: PASS (6/6)
  cp Tools/registry_baseline.json Saved/Audit/registry_baseline_pre_note_school_2026-09-18.json
  blender -b --factory-startup --python Tools/verify_full_registry.py   # re-cut baseline
  blender -b --factory-startup --python Tools/melodia_studio_census.py -- --json Saved/Audit/census_2026-09-18.json
  ```
- **P5 render loop** — `blender -b --factory-startup --python Tools/note_school_web_anim.py -- --loop turntable --sky auto --frames 96 --res 1080x1350 --samples 32 --out P:/MelodiaMelusinaV2-Laptop/Saved/Website/NoteSchool`
  then seam check (`Saved/Audit/web_seam_check.py`) and ffmpeg encode (mp4/webm/poster).
  Render ≈ 9–10 s/frame on the 1050 Ti → 96 frames ≈ 15 min. One Blender at a time.

**Build-order gotchas already known (from the skill, still apply):**
- Set every interface default **before** assigning the GN modifier (socket state freezes at
  tree-assignment); the shot script builds fresh, so it controls order.
- No `BoundBox` inside the tree (gate F forbids BoundBox over unrealized instances).
- Realize instances before counting verts in every verifier.
- `new_geometry_tree` now purges+reuses datablocks — safe for live rebuilds.

## 10. Gates

| Gate | Assert |
|---|---|
| G1 | school tree builds; evaluated (realized) verts > 0; 7 fish present |
| G2 | repeat-zone accumulation: verts(Tail Segments=3) < verts(=5) < verts(=7) — proves per-iteration append |
| G3 | attributes present on evaluated mesh: `UVMap` and `UVFlow`, FLOAT2, CORNER |
| G4 | `UVFlow` animates: frame 1 vs mid-loop differs (mean |Δ| > 0.1) |
| G5 | `UVFlow` seam **exact**: frame 1 vs frame 97 max|Δ| == 0; render f1 vs f97 pixel-hash equal (decoded buffer, not PNG bytes); f1 vs f48 differs |
| G6 | motion seam: mean\|f97 − f1\| / adjacent < 2.5× |
| G7 | addon gate 6/6 + baseline re-cut + census PASS (lost 0 / new 0) |
| G8 | sync md5 `3 <hash>` on all three copies |

## 11. Risks & fallbacks

| Risk | Fallback |
|---|---|
| Repeat-zone accumulation semantics differ from spec | unrolled segments / instanced segments |
| MenuSwitch enum wiring fights | IndexSwitch (`index_switch_items.new()`) or two chained Switch nodes |
| Capture attribute lost through CurveToMesh | recompute phase from SplineParameter |
| SLIM unwrap slow | stays behind `Auto UV` bool (OFF by default) |
| EEVEE noise on 1050 Ti | 32 samples (motion hides noise), 1080×1350 |
| Seam pop despite math | G5/G6 catch it; the frac rule is the fix, not easing |

## 12. Stretch (after tonight)

- v2 reactive dial (SampleSoundFrequencies; audio must divide the loop).
- E1 SDF body study tree (build-time only) → optional baked template.
- E2 phyllotaxis scale rows (raycast-seated).
- Note-birds skin on a staff wire (same kit, hop + chirp wiggle).
- Layer the school over the brooch scene as a halo (element colors already match).

---

## 13. P1 status + polish list (evidence-based)

**Polish APPLIED 2026-09-18 (late session):** all five items landed in
`MEL_music_note_fish` (tree now 86 nodes, 730 verts): mouth (dark plum nose
curl), tapering peduncle + forked two-lobe tail, rounded fin tips, eyes 0.145 r
nudged forward/down, slight body taper (0.88 at tail end), UVFlow v-range
extended to cover the tail lobes. Gates re-run: all pass, seam still exact 0.0
at f97. Live staging re-verified (step4-step7 in Saved/Audit/note_school/):
a fish-tree rebuild re-mints interface identifiers and kills the school's
nested-group links — rebuild the school tree + rebind modifier inputs after any
rebuild. Fish Scale 0.42 eave test: fish occlude behind the roof lip from the
hero camera; kept 0.30.

**Landed:** `melodia_gn/note_school.py` -> `MEL_music_note_fish` (registered, "music").
Verified by `Tools/verify_note_school.py`: verts 550 / 6 clean islands (body 114, eyes
2x128, fins 2x60, tail 60); UVMap + UVFlow FLOAT2/CORNER; UVFlow animates (mean |d| 0.979
f1->f48) and the seam is EXACT (max |d| 0.0 at f97). Clay reads: `Saved/Audit/note_school/
fish_look_{side,tq,top,front}.png`.

**Defect found + fixed on the way:** a `MeshCircle` linked into `CurveToMesh::Profile Curve`
converts to a ONE-point profile and silently sweeps 1-vert-per-ring slivers (tail/fins were
10-vert wires, not tubes). Correct profile = `CurvePrimitiveCircle` (or MeshToCurve first):
10-point path x 6-vert profile = 60 verts, measured. **Same latent defect sits in
`music.py`'s note-head flag** (MeshCircle profile; invisible because `Has Flag` defaults OFF).

**Polish list (from the clay reads, all dials/small part fixes — no new features):**
1. Mouth: one small swept smile near the nose (instant character).
2. Tail: taper the ribbon toward the tip + slight fork; soften the arc (currently reads
   as a stem/pipe).
3. Eyes: nudge forward + down (currently high on the head), add a tiny highlight bead.
4. Fins: round the tips (currently flat-paddle).
5. Body: slight taper toward the tail for hydrodynamics (keep note-head identity).
6. UVFlow bands: verify contrast at render scale (material side).

## 14. Komikaze verdict (measured 2026-09-18)

- **Present on this machine:** `P:/Installers/Downloads_2026-09-11/Komikaze v2.1.5/.../
  Komikaze 2.1.5 (Blender 4.2).blend` (216 MB; 228 materials / 293 node groups; the code's
  G: path is the desktop's copy). Probes: `probe_komikaze{,2,3,4}.py` + logs in this folder.
- **Usable:** materials append into 5.2.1 (deps auto-pull; the 4.2->5.2 load repairs a few
  node links), EEVEE renders them (cel/gradient colors show).
- **Not yet plug-and-play:** the cel shaders read a `World Color + Light Source TINT` group;
  the file ships a Sun + World + a `Fake Lit` collection. A first cel test rendered without
  hard bands -> needs one focused setup pass (find the library's demo rig, wire the light
  source, freeze a small "Komikaze look" recipe script).
- **Tonight's reliable look:** in-house (toon outline + our PBR/emissive + Melusina Sky v3);
  Komikaze = next deep-dive, not a tonight dependency.

## 15. Renders (the website set)

- Stills: hero set on the dark editorial field (front / three-quarter / macro) + per-element
  solo variants (Solo Index) — new `Tools/note_school_shots.py` modeled on the brooch rig.
- Loops: `turntable` + `sweep` via `Tools/note_school_web_anim.py` (camera-driven; the piece
  never moves); seam check with `Saved/Audit/web_seam_check.py` (ratio < 2.5x), ffmpeg
  mp4/webm/poster -> `Saved/Website/NoteSchool/`.
- Lock the single-fish look FIRST (it is 7x the same fish), then build the school (P2).

## 16. Texture breakdowns + close-out

- Intake contract (website queue): `Saved/Portfolio/Intake/NoteFishSchool/` — beauty/ +
  breakdown/ + machine-written manifest.json + LEDGER row, produced ONLY by a committed
  intake script (pattern: `Saved/Audit/brooch_intake.py`).
- Texture-specific breakdowns: UV layout sheet (Auto UV path), material-ID map, UVFlow band
  visualization, wire/clay views — same frame + camera as the beauty they pair with.
- Detailed painting route: GLB export for ArmorPaint (`Saved/ArmorPaint/`, pattern:
  `Tools/armorpaint_bake_pipeline.py`) when actual texture maps are wanted.

## 17. UE prep

- Export: realized + modifiers applied GLB -> `Exports/NoteSchool/` + manifest (dims in mm,
  vert/poly counts, per-material spans, UV channels). Materials keep their names
  (`MEL_fish_*`) for UE-side master-material mapping (desktop work); preview look =
  `ue_proxy_kit` `MEL_NPR_Halftone` ("Komikaze signature look").
- **GN motion does NOT transfer.** Export the static base + UV channels; in UE the flow is a
  material panner on the UV channel; fish motion would be WPO/skeletal (v2). State this in
  the manifest so nobody ships a "dead" asset.
- `blender_to_unreal` 2.2.2 is installed on this machine (extensions/user_default) if a fuller
  transfer is wanted; the project's standard for props is the hand-rolled GLB contract route.

## 18. Close-out gates (additions)

- NEW per-part gate (this is what the slivers slipped past): island census — exactly 6
  islands with min verts >= 60 per appendage; add to `Tools/verify_note_school.py`.
- Then: sync 3 copies (md5 `3 <hash>`), addon gate 6/6, baseline re-cut, census PASS.
- Commits: P:/C: repos, ONLY with explicit owner approval per the git pipeline law.
