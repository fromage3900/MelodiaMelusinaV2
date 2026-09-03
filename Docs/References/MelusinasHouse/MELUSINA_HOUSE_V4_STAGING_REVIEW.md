# Melusina's House vs Infinity Nikki & Dark Souls — Gap Analysis + Staging Handoff

> Generated 2026-09-03. Staged file: `Saved/MelusinasHouse/House_Mansion_v4_STAGED.blend`
> Renders: `Saved/Audit/melusinashouse/stage_CAM_0*.png`

## Why V4 still "looked bad"

V4 was architecturally correct but visually dead. The audit caught geometry
defects; it never touched the reason a render reads as "bad": **the master
graph joined all 28 systems into one mesh with no per-system material, so
everything rendered as one flat blended surface under a single raw sun with
no ground, no sky, no flora, no atmosphere.** That is not a geometry problem.
It is a material, lighting, and environment problem.

Below is what the two reference games actually do that we did not, and the
fixes now staged.

---

## 1. COMPARISON TABLE

| Principle | Infinity Nikki does | Dark Souls does | V4 did | V4 STAGED does |
|---|---|---|---|---|
| Ground | Meadow, flowers, grass everywhere | Fog, stone floor, ash | None (house floats on void) | Grass ground + stone apron + flora scatter |
| Sky / atmosphere | Pastel gradient, god rays, haze | Ominous fog banks, depth | No world (black void) | Pink→cream gradient sky + bloom |
| Color harmony | Pastel pink/mint/gold | Muted stone + warm candle | One blended blob | Per-system semantic materials |
| Material read | Soft plaster, silk, brass glow | Aged stone, patina, moss | 0 readable materials | 15 materials incl. glow windows |
| Key light | Warm golden hour | Directional shafts | 1 flat raw sun | Warm key + cool fill + pink rim |
| Emissive focal | Whim balloons, dew glow | Torches, windows, embers | None | Warm glowing windows + lanterns |
| Vertical focal | One tower/palace on horizon | Landmark silhouettes | Tower short, swallowed | Tower still short (see polish) |
| Set dressing | Furniture, lamps, mailboxes | Corpses, rubble, candles | None | Lanterns, bench, planters |
| Music as world | (N/A — this is OUR hook) | — | Et-semitone group, unused | Piano path, staff rows, notes, xylo fountain |
| Proportions | Cute, round, oversized flora | Epic scale contrast | 1.7m mannequin only | Mannequin + flora for scale |
| Wayfinding | Glowing paths, photo spots | Environmental breadcrumbs | None | 7 photo cameras staged |

---

## 2. WHAT WAS MISSING (root causes)

1. **No per-system materials.** Join Geometry merged everything; one base
   color won. FIXED: Set Material node inserted before the join for each of
   28 systems (facade→PearlPlaster, roofs→IridescentBlue, windows→glow,
   trim→GoldBrass, etc.).

2. **No environment.** The house hung in a black void. FIXED: 30m grass
   ground with GN flora scatter (tufts + pink/lavender flowers), stone apron.

3. **No lighting design.** One raw sun = flat, blown-out. FIXED: warm key
   sun + cool blue fill + pink rim backlight; pastel gradient sky; bloom.

4. **No emissive life.** FIXED: warm glow material on all windows and
   lanterns — the "lit-from-within" Nikki / DS-candle read.

5. **Below-ground verts.** V4 audit flagged 1,198 verts under z=0. FIXED:
   global LiftGround transform (+0.70) so nothing sinks.

6. **The music hook was invisible.** The project is a rhythm-JRPG; the house
   showed zero musical identity. FIXED (musical set dressing):
   - Piano walkway (20 ivory keys + black-key accents) at the entry
   - Sheet-music railing: posts, brass rails, floating note glyphs in a
     melodic contour over the walkway
   - Staff garden rows: 5 brass staff lines in the rear with a
     rising/falling C-major note melody in aqua glass
   - Glockenspiel fountain: plaster basin, aqua water, 10 pitched brass
     xylo bars ringing it
   - Lantern posts: 5 warm-glow lamp posts (door, path, garden, courtyard)

7. **No staging cameras.** FIXED: 7 named photo cameras (Entry, Hero3Q,
   PianoPath, TowerRise, Garden, Courtyard, StaffRows) matching the Nikki
   "photo beat" language — each a composition the player would stop at.

---

## 3. WHAT THE STAGED FILE GIVES YOU

Collections (open in Outliner to find anything):
- MH_GN_OUTPUT — the parametric master (regenerate-friendly)
- MH_ENV — ground, stone apron
- MH_FLORA_SRC — tuft/flower source meshes feeding the scatter
- MH_MUSICAL — piano keys, staff rows, notes, fountain, lanterns
- MH_CAMERAS — 7 photo cameras
- (default) MH_ENV + scene lighting: SunKey, FillCool, RimPink, MH_Sky

Materials (15, all editable in Shader Editor):
- MH_PearlPlaster, MH_RoofIridescentBlue, MH_GoldBrass, MH_WoodWarm,
  MH_LavenderFabric, MH_AquaGlass, MH_IvoryKey, MH_EbonyKey,
  MH_GrassGreen, MH_FlowerPink, MH_FlowerLavender, MH_LeafGreen,
  MH_StonePath, MH_LanternGlow, MH_WindowWarmGlow

Per-system materials are wired INSIDE the master GN graph (SM_* nodes before
the join), so you can still regenerate and keep the color read.

---

## 4. WHAT YOU SHOULD POLISH / SET-DRESS (handoff checklist)

These are the deliberate next edits. In Blender, open the STAGED blend.

LIGHTING (biggest lever):
- Rotate SunKey for a real golden hour (azimuth behind a camera, low)
- Raise FillCool/RimPink energy to lift shadow side — Nikki reads BRIGHT
- Toggle MH_WindowWarmGlow strength (6) up/down for dusk vs day
- Add MH_Sky strength control for dusk push toward indigo

MATERIALS:
- PearlPlaster: it's near-white now; give it a faint pink tilt (0.97,0.90,0.90)
- RoofIridescentBlue: crank Metallic→0.2 and add a Sheen for the Nikki "satin"
- GoldBrass: keep metallic but soften roughness 0.15–0.3 so it catches light
- Every material: add a subtle Noise→Bump; flat color is what makes CG read cheap

ENVIRONMENT:
- Raise GN_Scatter_Flora Density (currently 6.0) to 12–20 for Nikki density
- Add bushes / hedges / a tree silhouette for scale + framing
- Lay the piano path onto the stone apron; blend key rows into it

SET DRESS (add lived-in / world-consistent props):
- Door: welcome mat, small planter pots, lantern by threshold
- Fountain: floating lily pads / note-shaped leaves in the water
- Gardens: stone bench, topiary, a path of stepping stones to staff rows
- Fence/hedge boundary so the ground doesn't fade to empty

MUSICAL (the differentiator — lean in):
- Make staff-row notes glow faintly (AquaGlass + small emission) like
  "notes are lit where the player walked"
- Add 2–3 more lanterns down the walkway so the piano path glows at dusk
- Optional: key the lanterns / window glow to BPM in-engine later

---

## 5. Known remaining geometry limits (from audit, not staged)

- Tower reaches 10.5m but the massing still reads short for a "landmark";
  consider a taller spire or taller dormer to own the Nikki vertical focal
- Windows are mostly flat planes (Window_Turret_S was rebuilt flat);
  give them depth (frame extrude + glass inset) for real shadow
- Some openings / seams still need Merge-by-distance after boolean edits
