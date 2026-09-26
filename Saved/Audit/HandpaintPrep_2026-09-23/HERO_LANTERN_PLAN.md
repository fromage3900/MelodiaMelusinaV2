# HERO PLAN — ZenLantern (sole focus)

Goal: the ZenLantern becomes the showcase hero prop of the handpaint set — authored
geometry detail, morphing states, and audio-reactive shine under the cymatic ×
Infinity Nikki lens. Every step is additive to tonight's paint surface; nothing here
invalidates the staged `ZenLantern.fbx` (3,270 f, authored UVMap, `vcol_melodia`).

Current state (all verified 2026-09-23):
- Mesh `zenlantern_Retopo_lanternfinal.004`: 3,270 f / 3,316 v, authored UVMap, beveled + weighted-normal polished.
- `vcol_melodia`: R AO-wear ok · G eaves=1.0 · B height falloff · A fire box (42–60% h).
- Hi-poly unrecoverable (stage v14) → **self-bake asset**; detail must be authored, not projected.
- Blend carries stage-compositing setup: view-layer exclusion + holdout + `W_Melodia_FadeDayNight` world. Headless work must force-reset visibility (pattern already in `vertex_paint.py` / `export_fbx.py`).

---

## L1 — Geometry expansion → `zenlantern_V2` (duplicate, never edit the paint original)

New mesh `zenlantern_V2` (target <15k f), in priority order:

1. **Fire box panel seams** — 4–6 bool-inset panels with 2-segment bevels on the fire box (the A-zone; panels give the emissive something to sit inside). Weighted normal after each bool group.
2. **Umbrella roof rib rings** — 8 radial ribs + 2 trim rings, built with Roof Generator v3.1 (21 roof types; pick a pagoda-tier profile) or direct GN curve sweep; conform to the existing roof silhouette exactly.
3. **Base molding stack** — 2 torus-ish molding rings on the pedestal (Curve → bevel, fastest).
4. **Eave charm row (GN decoration)** — `MEL_skirt_hem_dangl_row`/`MEL_skirt_hem_charm` builders, instanced on the eave rim curve, G-mask-aligned (these read from the same vcol G zones). Charms are SEPARATE objects parented to V2, so they can sway without shape keys.
5. **Higgsas finishing** — v13 Distribution/Falloffs to break perfect symmetry (one replaced roof tile, two missing charms — Nikki storytelling).

## L2 — UV perfection AFTER expansion (answer: yes, and in this exact order)

The authored UVMap survives expansion; we extend, not rebuild:

1. **Pin existing islands** — select all current UVs → pin (UV editor → Pin). They were authored; they don't move.
2. **Unwrap only new geometry** — select V2 new faces (panel seams, ribs, moldings) → unwrap Follow Active Quads (conformal) off a matched active quad, or Smart Project with island margin 0.02 into a dedicated "detail" atlas region.
3. **Texel-density equalize** — Higgsas Geometry Measure (or built-in Texel Density op): bring new islands to the same density as authored ones (~the 3,270-f baseline); scale islands, never stretch.
4. **Lightmap UV2** — leave to UE import (`generate_lightmap_uvs=true`, already the manifest default); do NOT hand-author UV2 in Blender.
5. **Validation gate** — Substance UV-checker pass + `uv_report.json` (island count, density variance <10%, zero overlapping new islands vs authored set). Paint happens ONCE, after this gate — that is why expansion precedes painting.

Then **refresh `vcol_melodia`** by re-running `vertex_paint.py --asset 02` on V2 (AO re-bake covers new cavities; rules auto-extend to ribs/charms via bbox fractions).

## L3 — Shape keys (true morph states, authored on V2, exported as FBX morph targets)

Shape keys on the low mesh are cheap (3–15k f) and are the lantern's "living" layer:

| Shape key | What moves | Range | UE driver (read-only) |
|---|---|---|---|
| `SK_FlameBreath` | fire box panels + core scale 0→+8%, A-zone | 0..1 | `BeatPulse` → emissive + morph (breathing idle) |
| `SK_RoofLift` | roof tier +15 cm, reveals inner glow | 0..1 | `BeatPhase` crest one-shot (open on musical phrase) |
| `SK_CharmSway_L/R` | charm row tilt ±12° (charm objects, shape-keyed as one row) | -1..1 | `BassIntensity` → sway amplitude |
| `SK_DawnDusk` | roof + fire box warm tint swap prep (geometry-neutral; paired with material) | 0..1 | `W_Melodia_FadeDayNight` pattern (GN_PARIS_DayNightFacade precedent) |

Guardrails: shape keys ONLY on V2 (original untouched); basis = polished rest state; FBX export carries morph targets (verified path — reaver high already proves morph FBX exports work). In UE these become static-mesh morphs — no skeletal rig, no animation asset, no second audio writer.

## L4 — Making it truly shine (layered, all read-only consumers of MPC_Melodia_Palette)

Stack, bottom-up, in `MI_Handpaint_ZenLantern`:
1. **Handpainted base** (tonight's Substance pass — stone body, Nikki palette per `paint_guide.md`).
2. **Cymatic emissive layer** — `T_Cymatic_FrozenFracture_Emissive` multiplied into A-zone (fire box) via vcol A; `BeatPulse × vcol B` drives intensity (material graph: VertexColor.A × MPC BeatPulse → Emissive).
3. **Iridescence rim** — FrozenFracture_Iridescence on roof ribs + charm edges (thin-film on bevels only).
4. **Warm core light** — point light component hooked at fire box, intensity = f(BeatPulse), color from the audio palette (canonical palette — no second writer).
5. **Niagara micro-sparkles** — G zones emit 2–3 petal-sparkle sprites on beat (reuses `NS_Melodia_PetalLoop` family, lookdev-tuned; reads palette only).
6. **Night lookdev** — staged in L_FallenMoon dusk layer against `W_Melodia_FadeDayNight`; the lantern is the cymatic beacon of the set.

## L5 — Evidence gates (repo standard, no prose-only claims)

- G1: V2 mesh + `uv_report.json` (density variance, overlap check) → contact sheet vs original.
- G2: morph FBX re-import proof (4 shape keys present, deltas applied) → `Saved/Audit` receipt.
- G3: vcol refresh report on V2 (A coverage ≥40% fire box, G covers eaves+ribs).
- G4: UE lookdev capture (editor session, single instance) with palette-driven pulse ON vs OFF pair.

## Sequencing

- **Tonight-compatible:** nothing above blocks handpainting. Paint the ORIGINAL lantern if you want; V2 lands as the hero upgrade and gets its own paint pass after G1 (order: L1 → L2 → paint once → L3 → L4).
- **Next Blender session:** L1+L2 (one session, ~half a turn each with the established headless pipeline).
- **Then:** L3 morphs + re-export; L4 in UE with the import manifest row already staged.
