# PPV Stack Audit + How to Make Post-Process Visible in Renders

Live audit, 2026-08-20. Monolith 0.20.3 · UE 5.8 CL-55116800 · editor live on :9316.
Every finding below came from the running editor, not from docs.

---

## PART 1 — WHY PPVs DON'T SHOW UP IN RENDERS

### The mechanical cause

Every Monolith capture action renders in an **isolated preview world**. A
`PostProcessVolume` is a *level actor*. Preview worlds contain no level actors,
so there is no PPV to apply — the volume isn't "disabled", it structurally
does not exist in that render.

Verified by reading each action's own schema:

| Action | Required input | Level? | Can show a PPV |
|---|---|---|---|
| `editor.capture_scene_preview` | `asset_path` + `asset_type` | no | **never** |
| `editor.capture_with_overlay` | `asset_path` (StaticMesh only) | no | **never** |
| `editor.capture_material_grid` | `material_paths[]` | no | **never** |
| `editor.capture_sequence_frames` | `asset_path` (niagara) | no | **never** |
| `editor.capture_anim_frames` | asset | no | **never** |

Not one of them accepts a level. That is the whole problem — it is an API
surface limitation, not a settings mistake.

### The three paths that DO render post-process

Confirmed present in the live `editor` namespace (49 actions):

**1. `editor.capture_pie_movement_clip` — the practical answer.**
Captures the **PIE viewport**, which is a real game view of a real level with the
full post-process chain applied. Params: `map` (level asset path),
`duration`, `capture_interval` (0.05–5s), `output_path`. Poll with
`editor.poll_pie_smoke` for frame paths. This is the only *built-in* action that
produces a PPV-correct image.

**2. `editor.run_python` — full control (recommended for hero plates).**
Real `IPythonScriptPlugin` execution; I used it throughout this audit. Lets you
drive `HighResShot`, which is what actually belongs in a portfolio:

```python
import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level('/Game/EnvSandbox/Environments/L_KaleidoNave')
# realtime ON is mandatory — see the gotcha below
unreal.SystemLibrary.execute_console_command(None, 'r.ScreenPercentage 100')
unreal.SystemLibrary.execute_console_command(None, 'HighResShot 3840x2160')
```

`HighResShot` renders through the editor viewport's full post-process pipeline —
PPV blendables, bloom, grade, everything. Output lands in
`Saved/Screenshots/WindowsEditor/`.

**3. `editor.run_console_command`** — same idea, one command at a time.

### GOTCHA found live: the viewport is not realtime

```
editor.get_viewport_info -> {"realtime": false, "resolution": {"width": 0, "height": 0}}
```

With `realtime: false`, time-driven post-process does not advance. The Ink
material reads `BeatPulse`, `InkBass/Mid/Treble`, `VictoryPulse` from
`MPC_Melodia_Palette`, and Starry Night reads UDS time-of-day — all of which
**freeze or read stale** in a non-realtime viewport. Any capture taken now would
show a static, possibly wrong frame of an animated effect.

Fix before capturing: toggle realtime (`Ctrl+R` in the viewport) or use PIE,
which is always realtime.

### Also relevant: stencil requirement

`Config/DefaultEngine.ini:20` documents that
`CustomDepth-with-Stencil` (mode 3) is **required** by
`M_PP_StorybookOutline`'s per-object style path. If a build ever drops that
setting, the outline silently stops masking correctly.

---

## PART 2 — THE LIVE PPV STACK (as it exists right now)

Current level: **ZenForestTest**. One volume found:

```
PPV_Dreamprint_Candidate
  enabled       true
  unbound       true      (affects whole level)
  priority      25.0
  blend_weight  1.0
```

| Slot | Blendable | Weight | Domain | Status |
|---|---|---|---|---|
| 1 | `MI_StarryNight_VanGogh` | 1.00 | **MD_SURFACE** | **BROKEN — silently ignored** |
| 2 | `MI_MeluColorGrade_PortfolioHero` | 0.18 | MD_POST_PROCESS | OK, compiles |
| 3 | `MI_StorybookOutline_Premium_Hero_Dream` | 0.57 | MD_POST_PROCESS | OK, compiles |

All three blendables are `BL_SCENE_COLOR_AFTER_TONEMAPPING`.

### DEFECT 1 — a surface material is wired into the PPV

`MI_StarryNight_VanGogh` resolves to base
`M_Melodia_StarryNight_UDS_Candidate`, whose `material_domain` is
**`MD_SURFACE`**, not `MD_POST_PROCESS`.

UE only applies blendables whose domain is Post Process. A surface material in
the stack is **silently dropped** — no error, no warning, it just never renders.
Slot 1 at weight 1.0 has been doing nothing.

The correct asset already exists:

| Candidate | Domain |
|---|---|
| `MI_StarryNight_Hero` | **MD_POST_PROCESS** ✓ |
| `M_PP_StarryNightOverlay_Candidate` | **MD_POST_PROCESS** ✓ |
| `M_Melodia_StarryNight_UDS_Candidate` | MD_SURFACE ✗ (currently wired) |

`setup_nikki_render_post_process.py:88` already names `MI_StarryNight_Hero` as
the preferred `starry_night` blendable. The live level does not match its own
canonical setup script.

### DEFECT 2 — M_PP_MelodiaInk does not compile

```
is_compiled: false
compile_errors: ["(Node Custom) Custom material Custom missing input 2 (SceneColor)"]
num_pixel_shader_instructions: 0
expression_count: 76
```

Root cause, read from the graph: the Custom node `MaterialExpressionCustom_7`
declares **42 inputs** but only **38 are wired**. The four unwired ones are, in
declaration order:

| Index | Input | Wired |
|---|---|---|
| 0 | `UV` | ✓ ViewportUV from ScreenPosition_4 |
| **1** | **`SceneColor`** | **✗ MISSING** |
| **2** | **`cR`** | **✗ MISSING** |
| **3** | **`cB`** | **✗ MISSING** |
| **4** | **`smeared`** | **✗ MISSING** |
| 5–41 | BeatPulse … InkPaperColor | ✓ all 37 wired |

This is exactly the UE 5.8 failure mode documented in the
`unreal-material-auditing` skill: Custom nodes compile to
`CustomExpression0(FMaterialPixelParameters Parameters)`, and **by-name globals
are not in scope** — `SceneColor` must be an explicitly wired named input, it
cannot be referenced implicitly. The HLSL body reads `SceneColor`, `cR`, `cB`
and `smeared`, so all four need `SceneTexture`/graph expressions wired in.

Blast radius — all 3 profile instances inherit the broken master:
- `MI_MelodiaInk_PortfolioHero`
- `MI_MelodiaInk_GameplayStandard`
- `MI_MelodiaInk_Narrative`

### DEFECT 3 — live stack ≠ canonical script

`setup_nikki_render_post_process.py` defines the canonical stack as:

| Role | Canonical material | Canonical weight | Live |
|---|---|---|---|
| `dreamprint_ink` | `MI_MelodiaInk_PortfolioHero` | 1.0 | **absent** (broken master) |
| `melusina_grade` | `MI_MeluColorGrade_PortfolioHero` | **0.69** | 0.18 |
| `starry_night` | `MI_StarryNight_Hero` | 1.0 | wrong asset (surface) |

The live volume is also named `PPV_Dreamprint_Candidate`, while every script in
`Content/Python/` looks up the label **`PPV_NikkiDream`**
(`setup_nikki_render_post_process.py:106`, `apply_dream_candidate_ppv.py:62`,
`apply_zenforest_v5_outline.py:21`, `audit_nikki_render_post_process.py:18`).

**Consequence:** those scripts will not find this volume. They will spawn a
*second* `PPV_NikkiDream` at priority 10.0 alongside the existing one at 25.0.
Higher priority wins, so the canonical volume would be overridden by the
candidate — a confusing double-volume state. Do not run those scripts against
this level until the naming is reconciled.

Net effect right now: of three intended effects, **one renders** (the outline at
0.57), one is silently dropped (starry night), and one cannot compile (ink).
The grade renders at roughly a quarter of its canonical weight.

---

## PART 3 — WHAT TO DO, IN ORDER

### To capture PPV-correct renders today (no fixes needed)

1. Toggle viewport realtime ON (`realtime: false` right now).
2. Load the level, then `HighResShot` via `editor.run_python`.
3. Or use `editor.capture_pie_movement_clip` with an explicit `map`.

Do **not** use `capture_scene_preview` / `capture_material_grid` for anything
where post-process matters — architecturally impossible.

### Before an NVIDIA hero plate, fix in this order

1. **Swap slot 1** to `MI_StarryNight_Hero` (post-process domain). One-line fix,
   restores a whole effect that is currently dead.
2. **Decide the grade weight** — 0.18 live vs 0.69 canonical. Owner call; the
   0.69 comment says "restrained", so 0.18 may be deliberate recent tuning.
3. **Fix `M_PP_MelodiaInk`** — wire `SceneColor`, `cR`, `cB`, `smeared` as named
   Custom inputs. Until then the entire ink/vine/halftone layer cannot render.
   This is the biggest visual gap: it *is* the "dreamprint" look.
4. **Reconcile the PPV label** — either rename the live actor to `PPV_NikkiDream`
   or update the scripts. Leaving both invites a double-volume conflict.

### Ordering note

Fixes 1 and 2 are safe and reversible. Fix 3 is real graph surgery on a
76-expression master with 3 dependent instances — given the project is unstable,
do it in isolation and verify with `get_compilation_stats` before capturing.

---

## Verification method for every claim

| Claim | How verified |
|---|---|
| Capture actions are preview-only | `describe_query.action_schema` per action |
| `run_python` / PIE paths exist | `monolith_discover("editor")`, 49 actions |
| Viewport not realtime | `editor.get_viewport_info` |
| PPV state + blendable weights | `run_python` over `EditorActorSubsystem` |
| Domains (`MD_SURFACE` vs `MD_POST_PROCESS`) | `run_python`, walked instance→parent chain |
| Ink compile failure | `material_query.get_compilation_stats` |
| 42 declared vs 38 wired inputs | `material_query.export_material_graph`, `custom_hlsl_nodes` + `connections` |
| 3 dependent instances | `material_query.list_material_instances` |
| Canonical stack + label | `Content/Python/setup_nikki_render_post_process.py` |
| Stencil requirement | `Config/DefaultEngine.ini:20` |

Nothing was changed in the editor. This audit is read-only.
