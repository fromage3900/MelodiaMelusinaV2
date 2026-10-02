# Phyllotaxis Spiral System — plan (2026-10-01)

**Status: BUILT AND PROVEN 2026-10-01.** `deploy/surreal_arch/melodia_gn/phyllotaxis.py`
lands two builders — `MEL_phyllotaxis_spiral` and `MEL_phyllotaxis_pave` — with
`Tools/wardrobe_pipeline/phyllotaxis_proof.py` at **16/16 gates**, including a new
flatness gate that exists because of the bug below. Companion to
[`GN_BUILDER_AUDIT_2026-10-01.md`](GN_BUILDER_AUDIT_2026-10-01.md).

## The premise to accept first

**Phyllotaxis already exists in this repo, proven in a different asset family.**
`137.5077°` is the authored constant in all 7 brooch genomes, behind a portable validated
pattern (`brooch_genome.py`: 6 genes 0..1 → resolved traits) that builders consume without
hardcoding their own constants.

So this plan is **not** "author a spiral." It is **"promote a working spiral into a shared
module that both brooches and the sheep consume, then add the distributions brooches lack."**
A second copy of the golden-angle math inside sheep code would be the exact defect the
GN-builder skill warns about.

---

## 1. The shared module

`deploy/surreal_arch/melodia_gn/phyllotaxis.py` — the single authority.

**Hard requirement: mirror the composition pattern from `filigree_kit.py`.** Sub-builders take
`(tree, props, …)` and return a **geometry socket**; a `_group` wrapper owns the interface and
links it. Return `tree`, **never** a `(tree, gin, gout)` triple — a triple opts into the
auto-applied Universal Music pass and grows music sockets the tree does not use.

### API

```python
def _phyllo_points(tree, loc, count, angle_deg=137.5077, start_deg=0.0,
                   divergence_deg, radius_start, radius_step, inward=False) -> socket
def build_phyllotaxis_spiral(group_name="MEL_phyllotaxis_spiral")   # wrapper, returns tree
def build_phyllotaxis_pave(group_name="MEL_phyllotaxis_pave")       # fill, not outline
```

### Dials

| Dial | Default | Note |
|---|---|---|
| `Count` | 144 | int, needs explicit wide range `(…, 0, 99999999)` or the default max (100) fits no seed |
| `Angle` | 137.5077 | the constant, art-directable |
| `Divergence` | 22.5° | polar step; **137.5077 and 22.5 are independent** and both needed |
| `Radius Start` / `Radius Step` | 0.0 / 0.002 | |
| `Inward` | false | bool; sunflowers converge, most ornaments diverge |
| `Size Ramp` | 0.0 | 0 = uniform, >0 = scale by index — the sunflower effect |
| `Size Base` | 0.002 | |

**Two distributions, as a bool, following the `Pave Even` precedent**
(`BROOCH_LUXURY_AUDIT_2026-09-17.md:118` — off = legacy golden-angle, on = `theta = i*(2pi/n)`):

| Socket | Off | On |
|---|---|---|
| `Even` | golden-angle, `theta = i * 137.5077°` | `theta = i * (2pi/n)` |

Rationale: brooches want even pave so the field reads as a set stone; a sheep horn's growth
ridges want the organic golden-angle irregularity. One builder, one dial.

### Construction notes — read before writing

- **Do not use `Index % step < 0.5` for any per-point selection.** GN `MODULO` is float, the
  fractional part clusters, and the `FRACT(Factor/step) < 1/step` replacement is worse because
  `Factor/step < 1` makes `FRACT` the identity — every point passes (a requested 9 scrolls
  became 46,170 verts). **Use `Curve to Points` with `Count` set, and instance once per point.**
  It sidesteps the entire class.
- **Any binary Math node must write BOTH operands.** `ShaderNodeMath` inputs[0] *and* [1] both
  default to 0.5, so a bare-constant Math silently computes `0.5 * K` — three deg→rad factors
  were halved this way, turning `Arc Span 280°` into 140° while the tree built and passed gates.
  Use a `_const`/Value node for constants.
- **Compute known-constant arithmetic in Python, not a socket chain.** A correct 3-node chain
  planted a finial at z 2.835 against a crest peaking at 1.867, because a chain is only as good
  as every link's reading of the dial default. Sockets when a value must track a live dial;
  literals for constants.
- End with **Realize Instances** — `to_mesh()` and `bound_box` see nothing on the instances domain.
- Store `audio_amplitude` (POINT) if the tree feeds the audio lane, via
  `GeometryNodeStoreNamedAttribute`.
- `ShaderNodeClamp`: input is `Value`, **output is `Result`** — `outputs["Value"]` raises
  KeyError. There is no Math CLAMP in 5.x.
- `core.sock(node, "W")` for TexNoise — `inputs["W"]` raises KeyError in 5.2 while iteration
  shows it.

### Proof gate

`Tools/wardrobe_pipeline/phyllotaxis_proof.py`, per the house pattern. Must assert:

1. Both trees **construct** in `bpy.data.node_groups` — registry PASS means nothing.
2. **Point count == Count** (not "looks about right"). This is the gate that catches a selection
   expression that passed everything while emitting the wrong number.
3. **Angular separation** between consecutive points == 137.5077 ± 0.01° when `Even` is off,
   and `2pi/n` ± 0.01° when on.
4. **Radius monotonicity** matches `Inward`.
5. **Neutrality:** dial defaults evaluate to the base. (This gate exists because dial defaults
   at 1.0 caused a real 17% mesh bloat elsewhere — the wiring was already zero-at-zero.)
6. **The tree is not orphaned:** walk `tree.links` and assert every node created has a consumer.
   A built-but-unconsumed tree passes every size and material gate, because it contributes
   nothing to them.

Purge the cached module before proving — `del sys.modules[m] for m == pkg or pkg.*`, re-import,
`assert pkg.__file__.startswith(REPO)`. A headless sweep of a repo `deploy/` tree otherwise
silently measures the stale AppData copy.

---

## 2. Promote into the brooch genomes

**Do not fork the JSONs.** The genomes are the brooch design authority; the 7 files already
carry `traits.phyllotaxis.angle_deg`. What changes:

- `brooch_genome.py::derive_traits()` gains `divergence_deg`, `radius_start`, `radius_step`,
  `size_ramp` as derived traits, so a genome can regenerate its own spiral from genes alone.
  That is the whole point of the pattern — a genome must be able to reproduce its phenotype.
- One new genome: `melodia_sheep_horn_v1.json` in **family `Horn`**, genes mapped from the
  horn's intent (`verticality` high for sweep, `organic_growth` for ridge irregularity,
  `structural_logic` for the belly). Sheep consumes it directly; brooches keep theirs.

---

## 3. Sequence

| Step | Work | Gate |
|---|---|---|
| 1 | `phyllotaxis.py` with `_phyllo_points` + spiral wrapper | 6-point proof passes |
| 2 | `build_phyllotaxis_pave` (fill mode) | point count == `site_count` from a genome |
| 3 | `derive_traits` extension; verify all 7 existing genomes still resolve | `validate_genome` clean, resolved traits unchanged |
| 4 | `melodia_sheep_horn_v1.json` + `brooch_genome.py manifest` | manifest renders |
| 5 | Sheep: a scratch tree that spirals beads along a horn curve | renders, count matches |

**Step 3 is the regression gate and must not be skipped.** Extending `derive_traits` touches
every existing genome; if a resolved trait changes, seven authored brooches silently shift.

---

## 4. Definition of done

- `phyllotaxis.py` in repo `deploy/` **and** byte-identical in AppData (`cp` then `cmp`) — the
  repo copy does not auto-load.
- 6-point proof green, including point count and angular separation as *numbers*.
- All 7 existing genomes resolve with **unchanged** traits (diff the manifests before/after).
- `melodia_sheep_horn_v1.json` exists and its manifest reads cleanly.
- A sheep-tree scratch spiral renders and is visually judged by the owner.

## 4b. What the build actually cost (4 defects, all silent)

Recorded because each passed a naive proof and each was found only by looking at
a render or a measured number:

1. **`MeshLine`'s default `Offset` is `(0,0,1)`.** The "flat" spiral was a corkscrew
   spanning z 0…169. Count, angle, radius and orphan gates all passed; from above it
   rendered as one 10 px dot. Fix: zero the Offset, and gate on z-span < 1e-6.
2. **A GEOMETRY `Switch` fed a `Points` socket yields empty with no error.**
   `RealizeInstances` does not convert a Points cloud. Fix: `PointsToVertices` per branch.
3. **`Even` was a silent lie in the pave** — the socket existed, the branch was hardcoded.
4. **A point cloud has no faces**, so a correct spiral renders nothing until it is
   instanced or swept.

Also: a group node captures interface defaults at creation, so writing
`tree.interface` after the node exists does nothing — write the node's own input.

## 5. Traps carried in from the skill, restated because they have all cost real time

- **`DeleteGeometry`'s unlinked `Selection` defaults TRUE** — deletes everything. Always link it.
- **An unlinked Geometry input is a silent no-op**, not an error; Blender reads it as empty.
- **`Merge by Distance` does not accept an `Instances` socket** despite the input being named
  `Geometry` — Realize first. A 79-node piece measured exactly the band alone with every
  ornament branch silently empty, and 18 gates passed.
- **A dial socket is never `None`** — `if x is not None` is always true. Derive a plain bool.
- **A house module you never imported is a no-op that passes every gate** — every module a branch
  reaches for must be in the import list, and a missing module must raise, never return None.
