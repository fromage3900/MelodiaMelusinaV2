# Generator contract cards - Poitou (2026-10-21)

A card is the WHOLE brief for one generator. The next model reads the card, not the canon. If a
card cannot be written without re-reading the style contract, the card is incomplete.

**The rule that makes this work:** every generator writes into the EXISTING merged output
(`output_generated`) and adds a NAMED PRIM GROUP. It never adds an HDA output, never touches a
Content asset, never touches the level, never touches the UE-side HDA asset. So the whole
programme can be authored, gated and committed with **zero editor interaction**, and the owner
does ONE cook at the end.

**Read-only, in this order:** build contract section 12 (traps + the measured size table) ->
section 13 (the ordered plan) -> section 14 (the live-UE research and the staging pipeline) ->
the one card below.

---

## TEMPLATE

```
NAME         : <file>.vex          (snip/, included with kit.vex)
GROUPS       : <prim group names the gate must see>
OUTPUT       : merged into output_generated (merge_generated_elements) - NEVER a new output index
MATERIALS    : existing project material paths only
PARMS        : the HDA parms it reads, and their defaults
KIT FUNCTIONS: the kit.vex functions it uses, and any it adds
ACCEPTANCE   : the gate line it must satisfy AND the placement assertion it must pass
DO NOT TOUCH : existing Content assets, the level, the UE-side HDA asset, the owner's editor
TRAPS        : the axis rule, the VEX landmines (section 12.3), the attribute set (section 14.3)
```

---

## CARD 1 - `bond.vex` (the brick bond + the rubble core)

Jev's ruling on the original goal: `NEED_BOND_AND_RUBBLE_CORE_PATTERN`. The chaine/arase band is
currently a plain course of boxes and the core behind the ashlar leaf is a solid box, so "brick
generation" is a band, not a system. This card builds the real thing.

**NAME** : `snip/bond.vex` (git, `Tools/Poitou/snip/`, included as `kit.vex` + `bond.vex`)

**GROUPS** : `bond_course`, `rubble_core` - both must appear in
`Tools/Poitou/poitou_intheme_gate.py` `REQUIRED_GENERATED_GROUPS`, or the gate fails.

**OUTPUT** : merged into `output_generated` via `merge_generated_elements`. No new output index.

**MATERIALS** (existing, project paths only):
- the brick: `/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Arase_Brick.MI_Poitou_Arase_Brick`
- the ashlar leaf: `/Game/Melodia/Meshes/Poitou/M_Tufa_Stone_Blocks.M_Tufa_Stone_Blocks`
- the rubble core: `/Game/Melodia/Meshes/Poitou/M_Limestone_Rubble_Core.M_Limestone_Rubble_Core`

**PARMS** (add to the `f_mas` folder of `build_poitou_hda.py`):
- `bond_brick_length` 0.24 m (a brick, two to a 0.6 m module with a half-lap return)
- `bond_brick_height` 0.08 m (one brick course)
- `bond_bond_type` 0 = stretcher, 1 = English bond (alternate courses turn 90 degrees)
- `bond_joint` 0.01 m (the mortar joint between bricks, tighter than the 0.02 m stone joint)

**KIT FUNCTIONS** : add two to `snip/kit.vex` and use them everywhere else:
- `kit_bond_course(vector origin; vector along; vector normal; float length; float y0; ...)` -
  lays one course of bricks in the bond, with the half-lap return and the per-brick length and
  value jitter, writing the `bond_course` group and the vertex paint (mortar joints get the
  lower lime-wash value).
- `kit_rubble_core(vector origin; vector along; vector normal; float length; float height; ...)` -
  replaces the solid core box with a rubble pattern: jittered cells at the leaf/core interface
  (voronoi or a jittered grid, whichever is cheaper), each cell a small proud stone, the
  `rubble_core` group.
Then `kit_wall_stone` calls `kit_bond_course` for the band course and `kit_rubble_core` for the
core, so every wall in the level - the revetment, the abbey nave, the westwork, the narthex, the
apse, the foundations, the quay - gets the bond and the rubble for free. **That is the point of
the kit: one change, every wall.**

**ACCEPTANCE**
- the gate sees `bond_course` and `rubble_core`, with no engine-default material and no
  off-palette material;
- the brick bond's repeat is an exact sub-multiple of the 0.6 m module (0.24 x 0.08 -> 2.5 bricks
  per module, so the bond must carry the half-lap, not butt-joint at the module line);
- the placement assertion to add with it: the bond course's y positions are all multiples of
  0.08 m and the course count per 0.6 m stone course is 7 (0.6 / 0.08 = 7.5 - the bond must
  handle the half course, which is exactly where a real bond shows);
- and the line that actually matters: **one screenshot of a revetment wall and one of the abbey
  nave from the P0 route**, so the joint pattern is judged by eye, not by a count.

**DO NOT TOUCH** : any existing asset in `Content/`, the level, `poitou_layout_live_v6.uasset`, the
owner's editor session. The 8 MIs stay unbound until the owner approves the binding. Nothing in
this card removes content.

**TRAPS**
- the axis rule: the divisor triple is `(srcX, srcZ, srcY)` and the **up** divisor must equal the
  mesh's measured Z size. The bond is GEOMETRY, not instancing, so it is mostly about how the
  generated geometry is oriented: the kit's `along` is the run direction, `normal` is the outward
  face, and the up axis is always `set(0,1,0)`.
- VEX landmines (section 12.3): no 2-D array literals, no `fmod`, `addvertex` takes a prim index,
  write the group as a prim STRING attribute named `element`, and a .vex file must have **no BOM**.
- emit the attributes in section 14.3: `unreal_nanite_enabled`, `unreal_nanite_position_precision`,
  `unreal_nanite_trim_relative_error` (the 1 cm brick joints are below Nanite's default error and
  will be eaten unless the error is tightened), `unreal_output_name`, `unreal_collision_mode`.
- the palette authority is the **style contract**, not the MA proposal: the brick is
  `MI_Poitou_Arase_Brick`, and if it needs a tint, take it from the style contract's palette.

---

## CARD 2 - `house.vex` (the village house shell) - the NEXT card, not yet written up

Jev: `foundations_verdict = SHALLOW_NEEDS_REAL_FOUNDATION_TYPES`, and the style contract section
3a names the walls to reuse (`MEL_wall_straight/_corner/_with_door/_with_window/_multi_window/
_t_join`, round arches only, never an ogive), the balais (`MEL_half_timber_wall`, W 4.8-9.6,
H 3.0-5.0, step drop 0.6-1.2 toward the water), the damp baseboard at **0.4-0.8 m**, and
`MEL_retaining_wall` for the quay. The house points already carry yaw, footprint and height, so
the generator is configuration rather than invention. Write the card when the bond lands: the
baseboard is a bond course, and the wall modules are a bond pattern on a different module size.
