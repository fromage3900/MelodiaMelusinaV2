# GN Builder Audit — Choral Sheep capstone (2026-10-01)

Read-only census of the geometry-nodes surface, run before planning new horn/spiral work.
**Nothing was built or mutated.** All claims below are from reading source on disk, not from
memory or from a prior session's claims.

---

## 1. What exists and is reusable

The house ornament surface is large. Per the skill's own warning, sweeping it *before*
hand-rolling is mandatory — a first pass that hand-rolled a 45-node tree when
`filigree.py` already had the scroll was called out by the owner.

### Dangle family — `deploy/surreal_arch/melodia_gn/cute_decor.py`

13 builders, all present:

| Builder | Tree name | Use for the sheep |
|---|---|---|
| `build_crystal_drop` | `MEL_crystal_drop` | faceted drop terminus |
| `build_pearl_dangl` | `MEL_pearl_dangl` | **already on the sheep** (`PearlDangl_0..2`) |
| `build_pearl_string` | `MEL_pearl_string` | strand between link points |
| `build_star_dangl` | `MEL_star_dangl` | star terminus |
| `build_lace_dangl` | `MEL_lace_dangl` | fabric-lace terminus |
| `build_bead_tassel` | `MEL_bead_tassel` | graduated bead fall |
| `build_crystal_chain` | `MEL_crystal_chain` | linked crystal strand |
| `build_tassel_dangl` | `MEL_tassel_dangl` | tassel terminus |
| `build_bow_dangl` / `build_heart_dangl` / `build_flower_pendant` | — | motif termini (lower priority) |

Also: `build_nikki_bead_string` (`nikki_decor.py`), `build_star_finial` (`profiles.py`),
`build_rv_wing_dangles` (`reaver_wings.py`), `build_skirt_hem_dangl_row` (`skirt_decor.py`),
`build_mother_pearl_bush` (`mother_v3.py`), `build_mh_aaa_lissajous_pearl` (`melodia_house.py`).

**⚠ Scale trap that will bite the horns plan:** the dangl family is *jewellery* scale and
already ships correct — `build_star_dangl` measured 54 × 57 × 1003 mm, `build_lace_dangl`
60 × 80 × 1005 mm. The filament/filigree family is *architectural* (sixpetal rosette 2460 mm,
finial cross 2400 × 2700 × 2000 mm). **Those shapes are good — rescale, do not rebuild.**

### Filigree / spiral — `filigree.py`, `filigree_kit.py`, `ornament_extras.py`

- `build_filigree_spiral` — tapered scroll, stores `FiligreePhase`, shades smooth
- `build_filigree_core` / `_panel` / `_rail_inset` (`filigree_kit.py`) — the reference
  composition pattern: sub-builders take `(tree, props, …)` and return a **geometry socket**;
  the `_group` wrapper owns the interface and links it.
- `ornament_extras.py` (42 KB) — `build_ornament_rosette_sixpetal`, `build_filigree_wreath_ring`,
  `build_filigree_corner_volute`, `build_filigree_finial_cross`, `build_ornament_scallop_band`
- `ornament_strip.py` — `build_gold_ornament_strip` (beads along a curve)
- `mesh_tools.py` — pure-GN bevel/finish suite. **`_wire_mesh_bevel`'s four proportion sockets
  must be set to 0.0** or a 6,189-face mesh inflates 4× and grows 2.5× in world size,
  *independent of Width*.

---

## 2. Phyllotaxis already exists — do not reinvent

**`137.5077°` is already the authored constant in all 7 brooch genomes**, and the brooch
genome is a *portable, validated* pattern (not GN code — a Python design authority that
builders consume; builders "must not hardcode design constants of their own").

```
Saved/Accessories/brooch_lab/genome/brooch_genome.py   # 6 genes 0..1 + sequence + prop block
Saved/Accessories/brooch_lab/genome/melodia_brooch_{v1,v2,comet,halo,mini,nova}_v1.json
Saved/Accessories/brooch_lab/genome/melodia_gala_{tide,umbra}_v1.json
```

Resolved traits available today, per genome:

| Trait | Keys |
|---|---|
| `phyllotaxis` | `angle_deg` (137.5077), plus divergence/pitch siblings |
| `pave` | `site_count`, `border_inner/outer`, `bead_radius`, `voronoi_domain_radius` |
| `crown` | `petal_count` (13), `petal_profile`, `petal_len/wid/thk` |
| `center_bead` | `radius`, `z_squash` |
| `dangles` | `count`, `rim_frac`, `links`, `link_radius`, `link_thick`, `terminal`, `terminal_size` |

`BROOCH_LUXURY_AUDIT_2026-09-17.md:118` also documents a `Pave Even` bool socket: **off =
legacy golden-angle spiral**, on = `theta = i*(2pi/n)`. That switch is the exact precedent for
offering both distributions as an art-directable dial.

Other golden-angle use: `companion_flock.py:12` breathes on golden-angle-staggered phase.

**Conclusion: the phyllotaxis math the user asked for already exists and is proven in a
different asset family.** The correct move is to promote it into a shared module both
brooches and sheep consume — not to author a second copy in sheep code.

---

## 3. The existing sheep horn work — and why it needs replacing, not extending

`s5_bighorn_horns.py` (27,592 bytes) is a **rebuild of `MEL_S5_horns` written 2026-09-25 to
replace a spiral tree the owner rejected.** Its own docstring records the measured defects:

- 3 coils at 0.07 m curl radius = "a cinnamon roll, not a ram horn"
- Root 0.028 → Tip 0.006 is a 4.7:1 cone with **no belly**
- Wobble 0.008 against Curl Radius 0.07 = 11% noise, **visually inert**
- **TWO competing curve families in one tree** (Spherical Spiral AND Lissajous A/B/Delta/Coils)
  driving one output — 13 dials and no decision
- `s5_horns_live.json` recorded **2.63 × 2.15 × 2.37 m on a 1.19 m sheep**, measured
  pre-Align-To-Surface in the wrong frame; never reconciled

Its new design: ONE curve family, base 62 mm · belly 58 mm · tip 8 mm · 1.35 turns · curl
radius 85 mm · 14 growth ridges 3.5 mm deep · cross-section flattens to a 0.35 oval at the tip,
authored as an explicit radius-at-t curve rather than a linear taper.

**The live `MEL_S5_Horns` tree is the BIGHORN rebuild after all — CORRECTION (2026-10-01,
verified live).** This audit initially concluded the rebuild "was authored but not promoted
into canon," because the prep census showed `SheepHorns::S5_Horns` at 45 nodes. **That was my
misread: 45 nodes is the *rebuilt* tree's size, not the rejected one's.** Direct live proof via
MCP 9876:

- all **15 dial names match `s5_bighorn_horns.py` exactly**, `only_in_runner: []`,
  `only_in_live: []` — including the bighorn-only `Belly Dia`, `Tip Flatness`, `Ridge Depth`
  and `Align To Body`
- `has_lissajous: false` — the two-competing-families defect is **gone**
- exactly one curve family: `CurveSpiral` → `StoreNamedAttribute` → `CurveToMesh`
- belly confirmed geometrically: interior stations exceed both ends on radius **and** thickness

Also: `Curl Radius` reads **0.105** live against the docstring's 0.085, and `Turns` **1.25**
against 1.35 — **owner tuning on top of the rebuild.** The docstring records authored intent;
the live values are truth. Do not "correct" them to the docstring.

Full measurements: [`BIGHORN_LIVE_VERIFICATION_2026-10-01.md`](BIGHORN_LIVE_VERIFICATION_2026-10-01.md).
**No promotion is needed.** The horn work reduces to danglers on an already-correct horn.

---

## 4. Current sheep tree census (from the prep receipt, 2026-10-01)

22 trees, all healthy, **zero muted nodes, zero broken trees, zero dangling links**:

| object::modifier | group | nodes | links |
|---|---|---|---|
| `SheepMusicBeads::S5_MusicBeads` | `MEL_S5_music_beads` | 105 | 148 |
| `SheepWreathCollar::S5_FlowerCrown` | `MEL_S5_flower_crown` | 51 | 60 |
| `SheepHorns::S5_Horns` | `MEL_S5_horns` | 45 | 60 |
| `SheepPearlDanglers::S5_Pearls` | `MEL_sheep_pearl_dangl` | 39 | 58 |
| `SheepTailScroll::GN` | `MEL_filigree_spiral_SheepTailScroll` | 31 | 40 |
| `MrSheepFinal_HD::S5_BodySilhouette` | `MEL_S5_body_silhouette` | 31 | 34 |
| `MrSheepFinal_HD::S3_Wool` | `MEL_S3_wool_body` | 28 | 32 |
| `Wool_Cards::S3_Cards` | `MEL_S3_cards` | 21 | 25 |
| `PearlDangl_0..2::GN` | `MEL_sheep_pearl_dangl` | 17 | 21 |
| `ForeheadStar::GN` | `MEL_sheep_star_charm` | 15 | 20 |
| `Wool_Shell::S3_Shell` | `MEL_S3_shell` | 11 | 9 |
| `SheepEarBead_L/R::S5_Bead_Dial` | `MEL_S5_bead_dial` | 9 | 14 |

`SheepTailScroll::GN` already consumes `build_filigree_spiral` — the composition pattern works
in this file and is the template for the horn danglers.

---

## 5. Findings, ranked

1. **The bighorn rebuild is written but not promoted.** Free quality; it replaces a tree the
   owner already rejected on measured grounds. *Highest value per minute of work.*
2. **Phyllotaxis is already authored at 137.5077° in 7 genomes** and consumed by a validated
   portable pattern. Promote it; do not re-author.
3. **No sheep dangle-from-a-curve builder exists.** The 13 danglers are all standalone shapes;
   `SheepPearlDanglers` and `PearlDangl_0..2` were placed by hand. A reusable
   "attach danglers along a host curve" builder is the genuine gap — and
   `ornament_strip.py::build_gold_ornament_strip` (beads along a curve) is the closest prior art.
4. **The two-curve-family defect class is unproven-out.** `melodia_blender_skill` records that
   `DeleteGeometry`'s unlinked Selection defaults TRUE, an unlinked Geometry input is a silent
   no-op, and a `_feed` helper that swallows exceptions makes a missing link indistinguishable
   from a correct one. The rejected horn tree had 13 dials and two curve families — the dials
   were not the problem, the ambiguity was.
5. **Wool is the capstone's real blocker, not the horns.** Per the 2026-10-01 render review the
   fleece reads as surface scratches on a plastic body. Separate from this plan, but it should
   not be lost behind ornament work.

---

## 6. Explicitly not in scope

Wool/fleece authoring, the closed-editor build, UE import, Substance/UVB bake. The
`fluffy_pilot{,2,3,4,5}.py` scripts exist in `gn_v2_20260919/` and remain the wool decision.
