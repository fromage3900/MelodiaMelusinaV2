# Wave 0 + Wave 1 session record — office prop kit (2026-10-01)

Laptop session. Every number below was produced by a run on this tree, Blender
**5.2.1 LTS** (hash 9e2066aef7ef, 2026-08-25), headless `--factory-startup`.
Prose is not a row: each claim cites its command.

Plan: `Docs/Production/BRUTALIST_FILM_HEADLESS_PLAN_2026-10-01.md`
Brief: `C:/Users/brenn/Downloads/Office Things.docx`

---

## 1. Delivered

| Artifact | Path | State |
|---|---|---|
| Coverage manifest generator | `Tools/office_prop_coverage.py` | parses the .docx, emits CSV + JSON |
| Coverage table | `Docs/Production/OFFICE_PROP_COVERAGE_2026-10-01.csv` | **105 catalog rows**, 9 owners, 4 claimed |
| Parsed brief (machine) | `Saved/Audit/office_prop_brief_2026-10-01.json` | assignments + catalog |
| First prop builder | `deploy/surreal_arch/melodia_gn/office_props.py` | `GN_OFFICE_DeskCluster`, **189 nodes** |
| Health script | `deploy/_melodia_health_office_props.py` | **PASS problems=0** |
| Stager + 5 shots | `deploy/_melodia_stage_office_props.py` | blend + 5 PNGs + manifest |
| Registry wiring | `__init__.py` import, `CATEGORY_META['office_props']`, `.gitignore` `!` line | done |

### Brief parse (measured, not read)

```
owners        : 9
catalog rows  : 105
claimed rows  : 4 (Sukhbir -> Bookshelves, Desk Drawers, Telephones, Televisions)
P0 candidates : 47   (catalog rows whose words appear in an owner's assignment)
dont-need rows: 1   (Cabling Systems, the owner's own annotation)
```

Two parser bugs found and fixed by running it rather than reading it:
`Zania (Modeling)` — the discipline suffix broke an equality match and dropped a
whole owner and every prop they owned; and the 3-column Word table flattens to
reading order, so an owner name belongs to the **preceding** item, not its own
line. Reading it as a property of its own line reported "0 claimed", which is
the exact quiet-wrong this brief already suffers from.

---

## 2. Builder — measured

`GN_OFFICE_DeskCluster`: worktop on two legs, drawer pedestal with reveals,
24-inch monitor on a stand with a proud screen face, keyboard, mouse, mouse pad,
5-star task chair with a push dial. Every sub-prop behind its own toggle.

```
tree='GN_OFFICE_DeskCluster' nodes=189
link_failures: none for this tree
link graph: acyclic
params: 17/17 present
math ops=[('ADD',16),('COSINE',5),('DIVIDE',8),('MULTIPLY',33),('SINE',5),('SUBTRACT',5)]
verts/polys (defaults): 294/242
bbox x -0.700..0.700  y -0.350..0.350  z 0.000..1.089
Desk Height 0.74 -> 1.10: zmax 0.940 -> 1.300
Desk Width 1.40 -> 2.00: span 1.400 -> 2.000
toggle deltas: Pedestal 24, Monitor 32, Keyboard 8, Mouse 86, Mouse Pad 8, Chair 112
Chair Push 0 -> -0.50: verts 294 -> 294, ymin -0.350 -> -0.666
problems=0
PASS
```

**Researched dimensions land exactly.** Desk Width 1.400 m → measured span
1.400. Bare-desk bbox collapses to exactly ±0.700 × ±0.350. Floor at z = 0.000.
Sizing is imported by the health script from `office_props`, never retyped.

---

## 3. Four defects found by the gate, all real

Every one of these produced a tree that **built, evaluated and looked
plausible**. None threw. This is the argument for asserting dimensions rather
than "did it produce verts".

**3a. SetPosition is an OFFSET, not a placement.**
`GeometryNodeSetPosition.Position` moves every vertex by the vector. A desk top
authored around the origin collapsed to a single point at x=0 while gaining z.
`Selection` left on = applied to all; off = no-op, and the whole cluster then sat
at the origin with a plausible-looking bbox. Fixed by using
`GeometryNodeTransform.Translation`, which is absolute and composes.

**3b. A Group Input output reads 0.0 at build time.**
In 5.2, `NodeGroupInput.outputs['Desk Width'].default_value` is `0.0` even
though the interface item holds `1.4`. Wired straight into `Mesh Cube > Size`,
the cube collapses. `brutalist_cubicles` gets away with it only because its
sockets feed Math nodes, which evaluate at modifier time from the interface
default. Every socket-sized dimension here therefore passes through a `mathn()`.

**3c. An evaluated modifier caches.** Writing the interface default after a
modifier has evaluated changes nothing measurable. All three staged variants
first reported an identical **294 verts** — including `DESK_Bare`, which should
be 56. Measuring on a throwaway object bound to the same tree resolves it. The
warning line added to the stager is what caught it.

**3d. `new_geometry_tree` reuses and purges by name.** Three variants sharing
`GN_OFFICE_DeskCluster` each purged the previous tree, so every staged modifier
pointed at whichever tree was built last. The saved .blend showed flat slabs and
the camera framed empty space. Fixed with a unique tree name per staged object.

---

## 4. Staged output

```
Saved/Blend/OFFICE_DESK_REVIEW_2026-10-01.blend
Saved/Audit/office_desk_shot_{three_quarter,front_elevation,low_macro,
                               variant_monitor_off,variant_bare}.png
Saved/Audit/office_desk_stage.json
```

Verified from the **saved .blend**, not from the staging session:

```
DESK_Standard      tree=GN_OFFICE_DeskCluster_DESK_Standard     verts=294
     world bbox x -2.300..-0.795  y -0.355..0.350  z 0.000..1.089
DESK_MonitorOff    tree=GN_OFFICE_DeskCluster_DESK_MonitorOff   verts=262
     world bbox x -0.300..1.205   y -0.355..0.350  z 0.000..0.930
DESK_Bare          tree=GN_OFFICE_DeskCluster_DESK_Bare         verts=56
     world bbox x 1.700..3.100    y -0.350..0.350  z 0.000..1.089
```

Three distinct trees, three distinct vert counts, dials live in the file.
Vision read of `three_quarter` confirms desk + monitor on stand + keyboard +
pedestal + chair.

---

## 5. Gates

| Gate | Command | Result |
|---|---|---|
| Office props | `blender -b --factory-startup --python deploy/_melodia_health_office_props.py` | **PASS problems=0** |
| No regression, office block | `... _melodia_health_brutalist_office.py` | **PASS problems=0** |
| No regression, cubicles | `... _melodia_health_brutalist_cubicles.py` | **PASS problems=0** |
| Preset audit | `python deploy/_melodia_preset_audit.py` | **0 shadowed keys, 0 brand orphans**, 3 packs 5/5 |
| Material gate | `blender ... Tools/verify_brutalist_materials.py` | **MATGATE PASS 11 checks, 0 failed** |
| Registry census | `blender ... Tools/melodia_studio_census.py` | see §7 |

---

## 6. Repo state — READ ONLY, no git mutation performed

Per the 2026-09-06 pipeline law the laptop is not an integration point.
Measured before any decision:

- local `main` is **652 behind** `origin/main` (`b195820d` vs `504581c7`)
- `HEAD` (`collab/laptop/brooch-sky-20260917`) has **diverged**: 8 commits not on
  `origin/main`, 641 the other way; its remote is `gone`
- `brutalist_city.py`, `brutalist_roofs.py`, `brutalist_uv.py`,
  `higgsas_pipeline.py`, two health scripts, `Tools/higgasas_verify.py`,
  `Tools/verify_contact_sheets.py` and the ribbon/bow docs are **untracked** —
  the 2026-09-25 and 09-26 work is on disk but not committed
- 216 paths dirty;61 `.uasset` are LFS pointer bumps

**Nothing was committed, staged, merged, rebased or pushed.** One `.gitignore`
`!` line was added (`Tools/office_prop_coverage.py`), which is a working-tree
edit, not a git operation — without it the new tool is silently untracked, the
same failure recorded in the 09-25 audit §8.1.

Also verified: `only_live` (files present in the AppData install and absent from
the checkout, which `sync()` would `rmtree`) is **empty**, so a one-way install
is safe whenever it is next run. The live addon is 3 files behind the checkout
and is missing `core.link_sockets`' self-link rejection.

---

## 7. Open

1. **Registry baseline re-cut** — `GN_OFFICE_DeskCluster` is new. Census must
   show 1 new / 0 lost, then `Tools/verify_full_registry.py` re-cuts
   `Tools/registry_baseline.json` in the same change (studio freeze rule 3).
2. **Live addon sync** — Blender closed, then
   `python deploy/_sync_addon_to_blender_5_2.py`, then re-gate.
3. **Wave 1 remainder** — 7 of 8 archetypes built: `GN_OFFICE_TaskChair`,
   `GN_OFFICE_MonitorBank`, `GN_OFFICE_ShelfUnit`, `GN_OFFICE_StorageStack`,
   `GN_OFFICE_BreakroomCounter`, `GN_OFFICE_ServiceUnit`, `GN_OFFICE_Panel`
   (blinds have **no owner** — `venetian_kit.py` is a loggia archetype, 82 lines,
   not blinds, correcting the 09-25 audit).
4. **Wave 3** — 8 interior materials missing (carpet, laminate, drop ceiling,
   troffer, powder coat, screen emissive, polypropylene, whiteboard gloss).
5. **No git operation is authorised by this record.**