# Brutalist Office Film — Headless Blender Build Plan (2026-10-01)

**STATUS 2026-10-01: Wave 0 DONE, Wave 1 IN PROGRESS (1 of 8 archetypes).**
Session record with every measured number:
`Saved/Audit/OFFICE_PROPS_WAVE0_WAVE1_2026-10-01.md`

| Wave | State | Evidence |
|---|---|---|
| 0 — lock the brief | **DONE** | `Tools/office_prop_coverage.py` parses the .docx → **105 catalog rows, 9 owners, 4 claimed, 47 P0**; `Docs/Production/OFFICE_PROP_COVERAGE_2026-10-01.csv` |
| 1 — prop archetypes | **1/8** | `GN_OFFICE_DeskCluster` — 189 nodes, **PASS problems=0**, 294v, width lands on the researched 1.400 m exactly |
| 2 — clutter | not started | — |
| 3 — interior materials | not started | 8 surfaces missing |
| 4 — stage + shotlist | **partial** | stager + 5 shots exist for the desk only; the S01–S05 shotlist table is still to write |
| 5 — intake | not started | — |

Remaining Wave 1: `GN_OFFICE_TaskChair`, `GN_OFFICE_MonitorBank`,
`GN_OFFICE_ShelfUnit`, `GN_OFFICE_StorageStack`,
`GN_OFFICE_BreakroomCounter`, `GN_OFFICE_ServiceUnit`, `GN_OFFICE_Panel`.

Replaces the "film brief not locked" block in
`Saved/Audit/BRUTALIST_CONVERGENCE_AUDIT_2026-09-25.md` §6 with a targetable brief.
Source of the brief: `C:/Users/brenn/Downloads/Office Things.docx` — a team prop
breakdown, **107 catalog items** plus a **9-owner assignment list**.

Every number below was produced by a run on this tree, Blender **5.2.1 LTS**
(hash 9e2066aef7ef, 2026-08-25), headless `--factory-startup`. Prose is not a row.

---

## 0. What the brief actually is

The doc is two things stacked:

| Block | Content | Use |
|---|---|---|
| Assignment list | 9 named owners → ~85 named props (Arianna: chairs/monitors/desks/clocks; Zania: coffee machine, fridge, mugs; Kay: watercooler, cubical walls, plants; Pearl: shelving, books, blinds, donuts; Kane: security cams, laptops, phones, water servers; Selma: first aid, fire extinguisher, bins; Elif: files/boxes, lamps, pillows; Oscar: toilet supplies, vending, storage boxes; Emilio: pencil box, fruit bowl, magazine shelf, garbage bags) | **the film's prop list**. Owners are humans doing modelling — we supply the parametric base, not finished art. |
| Master catalog | 107 rows, A–W alphabetical (`Access Cards` … `Workstations`), several already spoken for (`Desk Drawers` → Sukhbir, `Televisions` → Sukhbir, `Telephones` → Sukhbir) | **the coverage denominator**. This is what the GN prop kit must answer to. |

Two rows carry the owner's own annotation: `Cabling Systems < dont need`.
Honour it — do not build cable trays or conduit runs as film assets. Keep them
as set dressing only if a shot demands it.

**Read:** this is an *interior-office* brief. The existing brutalist work is
exterior-first (city, office block, roofs) with one interior system
(CubicleFarm). The gap is interior props.

---

## 1. Current state — measured

### 1a. What already exists and is green

| Asset | Tree | Measured |
|---|---|---|
| Office block | `GN_BRUTALIST_OfficeBlock` | 268 nodes, 17/17 params, **PASS problems=0** (re-run today, 29 s wall) — 904v/658p, pilotis off 656v zmax 21.40 → on 904v zmax 25.60, toggle deltas Stair Tower 56 / Roof Plant 104 / Formwork 144 |
| Cubicle farm | `GN_BRUTALIST_CubicleFarm` | 335 nodes, 18/18 params, **PASS problems=0** — 2098v/1518p, rows 1/3/8 = 1106/2098/4578v, Drift 0→1 pure translation (xmax 5.12→9.65), toggle deltas Monitor 192 / Chair 864 / Overhead Bin 24 / Ceiling Grid 200 / Plants 402 |
| City block | `GN_BRUTALIST_CityBlock` | 4 presets, P4b per-lot massing nesting still open |
| Roof | `GN_BRUTALIST_Roof` | 6 styles, first real Higgsas consumers |
| Materials | `brutalist_materials.py` | 15 surfaces × 2 looks (PBR / Komikaze), material gate **11/11** incl. depsgraph evaluated-mesh inspection |

Registry census today: **603 registered builders** (base: live AppData addon,
`--factory-startup`). Preset library: 157 builders / 492 presets, 0 shadowed keys.

### 1b. The prop gap is real and it is total

I dumped the full registry and filtered on office vocabulary. **Zero standalone
office-prop builders exist.** No `MEL_chair`, no `MEL_desk`, no `MEL_monitor`,
no `MEL_laptop`, no `MEL_filing_cabinet`, no `MEL_cooler`, no `MEL_vending`,
no `MEL_whiteboard`, no `MEL_blind`, no `MEL_carpet_tile`. The closest hits are
`MEL_crate_pile`, `MEL_door_frame`, `MEL_window_frame`, `MEL_street_lamp`,
`MEL_greybox_pipe_run` — none of them office props.

`CubicleFarm` does build a desk, monitor, chair, bin and plants — but **inline, per
cell, non-addressable**. They cannot be instanced into a conference room, cannot
be re-dressed, and cannot be shot on their own. The audit already named this
(§5f) and it is still exactly true.

Envelope pieces that must be **reused, not rebuilt** (all present):
`MEL_greybox_elevator_shaft`, `MEL_greybox_stair_block`, `MEL_greybox_corridor`,
`MEL_greybox_corridor_bend/_cross/_t/_door_end`, `MEL_greybox_room_kit`,
`MEL_greybox_openings`, `MEL_ceiling_tile`, `MEL_floor_tile`, `MEL_door`,
`MEL_door_frame`, `MEL_window`, `MEL_window_frame`.

One correction to the 09-25 audit: it lists `venetian_kit.py` as existing "for
blinds". It is 82 lines and contains `build_venetian_loggia_bay` — a loggia
archetype, not a blind. **Blinds have no owner. Build them.**

### 1c. The live addon is behind the checkout

```
differing: melodia_gn\brutalist_city.py, melodia_gn\brutalist_roofs.py, melodia_gn\core.py
only_live (would be DELETED by sync): []      <- safe to sync
```

The live install is **missing** `core.link_sockets`' self-link rejection (the
2026-09-30 fix for the city group evaluating to 0 verts), `brutalist_city._style_is`,
and `brutalist_roofs` plant-deck instancing. `only_live` is empty, so per
convergence Rule 1b this is a normal one-way install, **not** a live-ahead case.

**Consequence for this plan: headless work must run against `deploy/`, not the
live addon.** Every health script already defaults to `sys.path.insert(0, DEPLOY)`
and only reads AppData when `MELODIA_AUDIT_LIVE=1`. Leave that default. Sync to
live only at close-out, Blender closed, then re-gate.

### 1d. Two ignore traps that will eat deliverables

1. `.gitignore:226` is `Tools/*`. **Every new `Tools/*.py` needs its own `!` line**
   in the same change, or it is untracked-but-not-ignored and one `git add -A`
   ships or loses it silently. Known-in-the-audit, still unfixed.
2. `.gitignore:5` is `Saved/` with `!Saved/Audit/` at line 7. Git cannot
   re-include a child of an excluded directory, so **new files in `Saved/Audit/`
   do not appear in `git status`** and need `git add -f`. Evidence lands on disk
   either way; commit needs the flag.

---

## 2. Build plan — five waves

Each wave ends in a gate that can fail. No wave starts before the previous
wave's log is written.

### Wave 0 — Lock the film brief (no Blender)

Fill `Humber_FinalYear_Prep/Capstone_Walkthrough_AssetList.md`: logline, asset
rows, shot table. Without it every wave below is guesswork and the audit's §6
"untargetable" block stays true.

Then derive, from the 107-row catalog, a **coverage manifest**:
`Docs/Production/OFFICE_PROP_COVERAGE_2026-10-01.csv`, one row per catalog item:

```
catalog_item, gn_builder_id (or REUSE:<id> or DEFER), shot_ids, owner, priority
```

Priority rule: **P0 = anything in the assignment list** (those are the props a
named human is waiting on), P1 = catalog items visible in a wide interior,
P2 = catalog items needing a character to justify.

Machine-generate it with a committed script
(`Tools/office_prop_coverage.py`, pure Python, parses the docx text dump) — never
hand-maintained, same rule as the intake manifest.

### Wave 1 — Prop kit foundation, one builder per archetype

New module `deploy/surreal_arch/melodia_gn/office_props.py`, category
**`office_props`**, registered in `melodia_gn/__init__.py`, labelled in
`CATEGORY_META`. One tree per archetype so a film can dial one prop without
rebuilding a room.

Wave 1 set — the archetypes that carry the assignment list:

| Builder id | Covers catalog rows | Real-world size (research FIRST, per skill law 1) |
|---|---|---|
| `GN_OFFICE_DeskCluster` | Workstations, Computer Peripherals, Desk Pads/Pads, Mouses/Keyboards | desk 1400×700×740 mm, top 25 mm | **BUILT + PASS** |
| `GN_OFFICE_TaskChair` | Office chairs | seat 460×460 at 450 mm, gas lift 100 mm stroke, 5-star base ⌀700 | chair is inside DeskCluster; standalone tree still to extract |
| `GN_OFFICE_MonitorBank` | Televisions/Large Monitors, Computers, Peripherals | 24" 16:9 panel 531×298 mm, bezel 6 mm |
| `GN_OFFICE_ShelfUnit` | Shelving, Bookshelves, Pantry Shelving | 900×300×1800 mm, 5 shelves |
| `GN_OFFICE_StorageStack` | Storage Boxes/Cases, File Boxes/Crates, Binders, Folders | A4 box 330×240×310 mm |
| `GN_OFFICE_BreakroomCounter` | Coffee Tables, Refrigerators, Kettle, Coffee Machine | counter 1800×600×900 mm |
| `GN_OFFICE_ServiceUnit` | Vending Machines, Water Servers, Water coolers | vending 1000×800×1830 mm |
| `GN_OFFICE_Panel` | Blinds/Curtains, Bulletin Boards, Whiteboards, Planning Boards, Posters, Signage | blind 1200 mm drop, 50 mm slat pitch |

Envelope stays on the greybox builders. Cubicle partitions and the waffle ceiling
stay on `CubicleFarm`. **Do not fork them.**

`GN_OFFICE_DeskCluster` is the keystone — the desk, monitor, keyboard, mousepad,
mug and papers are one tree with toggles, because that is how a shot will frame
them. Same pattern as `CubicleFarm`'s cell, but standalone and instanceable.

### Wave 2 — Clutter and dressing rows

Second module pass, same file: `GN_OFFICE_ClutterScatter` (paper trays, sticky
notes, pens, folders, cables-as-scatter, bins, first-aid, fire extinguisher,
pillows, cushions, plants), `GN_OFFICE_PlantRow`, `GN_OFFICE_FruitBowl`,
`GN_OFFICE_MagazineShelf`. Instanced via point clouds, density as a dial, and
**measured** by the count assertion the scatter emits.

### Wave 3 — Materials for the interior

`brutalist_materials.SURFACES` has 15 exterior surfaces. The audit §5d names the
interior gap: **no carpet, laminate, powder-coat, drop-ceiling, troffer,
fluorescent or screen material exists.** Add as new SURFACES entries — they are
built twice from one function (PBR + Komikaze) by construction, so they cannot
drift:

```
laminate, carpet_tile, acoustic_ceiling, troffer, powder_coat, screen_emissive,
polypropylene, whiteboard_gloss
```

Then re-run the material gate. It resolves Base Color backwards through the mix
chain, so a `Base_Color` typo in a new surface fails the gate instead of
rendering grey. That gate is the reason the whole family reads correctly; keep
it as the CI gate for new surfaces.

### Wave 4 — Stage, contact sheets, shotlist

New stager `deploy/_melodia_stage_gn_office.py`, copied from
`_melodia_stage_gn_brutalist.py` (its `frame_bbox` / `isolate` / `add_label` /
`compose_sheet` helpers are the reusable part).

Produces three deliverables per run:
1. `Saved/Blend/OFFICE_FLOOR_REVIEW_<date>.blend` — labelled collections, one
   node group per object so two presets never fight over socket defaults.
2. `Saved/Audit/office_sheet_*.png` — camera-parented text tiles (tiles carry
   their own labels; no legend to lose).
3. `Saved/Audit/office_stage_manifest.json` — per object: builder, preset, nodes,
   params, verts, bbox, material. The numbers behind the pictures.

**Shotlist** — this is the artifact the brief has been missing. One row per shot:

```
shot_id, duration_s, camera_move, framing, set, required_builders, dials, render_preset
```

Cover, in this order:
- **S01 establishing, 5 s, slow push** — open plan from the corridor mouth. Needs
  `CubicleFarm` + `Ceiling Grid` + `DeskCluster` instances + `Panel` blinds.
- **S02 hero acting, 8 s** — one workstation, the assignment-list cluster. Needs
  `DeskCluster` + `TaskChair` + `MonitorBank` at close focal distance.
- **S03 detail inserts, 2 s each** — coffee machine, water cooler, shelving,
  filing. Needs Wave 2. Cheapest shots, build them first for the animatic.
- **S04 service wall, 6 s** — vending + water server + bins. Reads the
  "information security infrastructure" row.
- **S05 exterior bookend, 5 s** — `GN_BRUTALIST_OfficeBlock` front, already green.
  Costs nothing; do not rebuild it.

Render presets per shot from `brutalist_materials.LOOKS`: interiors want
**Komikaze** (the film is NPR), exteriors can stay PBR for the animatic and flip
for final.

### Wave 5 — Intake + gate close-out

`Saved/Portfolio/Intake/<AssetId>/` per the existing contract: beauty set +
workbench wireframe/clay breakdown + machine-written `manifest.json` +
`LEDGER.jsonl` row. Produced by a committed script only.

---

## 3. Gate list — run every wave, log every result

All headless, all `--factory-startup`, all exit-code-bearing.

| # | Command | Asserts |
|---|---|---|
| G1 | `python deploy/_melodia_preset_audit.py` | 0 shadowed keys, 0 brand orphans |
| G2 | `blender -b --factory-startup --python Tools/melodia_studio_census.py -- --json Saved/Audit/census_<date>.json` | registry total vs `Tools/registry_baseline.json`: **0 lost, 0 unexpected new**. New builders require a baseline re-cut in the same change. |
| G3 | `blender -b --factory-startup --python Tools/verify_addon.py` | gates A–G. **Tests the LIVE install** — sync P:→live first or it will fail on bugs already fixed. |
| G4 | `blender -b --factory-startup --python Tools/_addon_headless_verify.py` | construction + evaluation of every id |
| G5 | `blender -b --factory-startup --python Saved/Audit/audit_brutalist_topology.py` | verts/edges/faces/tris, loose verts, non-manifold edges, zero-area faces, ngons, islands, material slots, UV maps at every preset |
| G6 | `blender -b --factory-startup --python Tools/verify_brutalist_materials.py` | 11/11 — what colour actually reaches Base Color, plus depsgraph evaluated-mesh inspection |
| G7 | `blender -b --factory-startup --python deploy/_melodia_health_brutalist_{office,cubicles}.py` | the four live builders stay PASS problems=0 |
| G8 | `blender -b --factory-startup --python deploy/_melodia_health_gn_links.py` | dropped links across all trees. **Currently FAIL exit 1, 19 pre-existing trees** — none brutalist. Record it as a known-open baseline, do not attribute new breakage to it. |
| G9 | `python -c` file-set diff, checkout ↔ live, both directions | `only_live` empty before any sync |

**Health-script contract:** `EXPECTED_MATH` / `EXPECTED_BOOL` are **minima**
(`got < need`). Adding nodes is safe; removing operations fails. Write new
health scripts to the same shape — assert dials, not snapshots.

---

## 4. What a prop health script must assert

The existing two are the model. For each new builder:

- build succeeds; `core.link_failures()` empty; **link graph acyclic**
- every declared param is a real interface socket
- real geometry (verts > 0 after `inst_realize`, depsgraph re-fetched)
- **the dials do what they claim**: toggling `Chairs` off genuinely removes the
  chair geometry (a cubicle `Chair` toggle is worth 864 verts — assert the delta,
  not "it built")
- a dimension lands on its researched real-world size within tolerance
- no sentinel verts (`|coord| > 1e6`)

Two failure classes that a green build hides, both already paid for in this repo:
a **silently-rejected math op** (`operation='EQUAL'` does not exist on Blender's
Math node — it is COMPARE with `inputs[2] = 0`), and a **self-link** that Blender
accepts as a legal cycle and then evaluates the whole group to 0 verts.
`core.link_sockets` now rejects the second; the first is caught only by
counting ops in the health script. Write both assertions.

---

## 5. Open items carried forward

1. **`brutalist_kit.py` is still a live third authority** (`integration.py:204`,
   used at 269/466/499) and `blender_brutalist_gn/` is an ungated parallel
   authority. Convergence is the one part of the 09-25 plan not executed. Blocked
   because it touches shared files other lanes use — owner call.
2. **UVs still absent** on the brutalist family. `brutalist_uv.py` exists and
   `NTTriplanar UV Mapping` is the identified route. If the film exports textured
   props to UE this becomes blocking; for NPR stills it is not.
3. **Contact sheets not re-rendered** with the current facade / roof looks.
4. **18 TP_* toon profiles, 59 masters on disk** in `Content/EnvSandbox/Materials/`
   — the UE-side toon spine. The Blender side is deliberately *not* the toon spine:
   it is PBR + Komikaze. Do not port UE Substrate Toon into Blender; the handoff
   is export-side and belongs to `Tools/export_decor_armorpaint.py` territory.
5. **No git operation of any kind** is authorised by this plan. Every wave is
   write-and-verify only. Baseline re-cuts and ignore-rule `!` additions are
   *proposals* to the owner, applied on approval.

---

## 6. First runnable command

```bash
cd /p/MelodiaMelusinaV2-Laptop
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
    -b --factory-startup --python deploy/_melodia_health_brutalist_office.py
```

Last measured today: **PASS problems=0**, 29 s wall, 268 nodes, 17/17 params.
If this ever prints anything else, stop — the floor is not trustworthy and no
wave above it should start.