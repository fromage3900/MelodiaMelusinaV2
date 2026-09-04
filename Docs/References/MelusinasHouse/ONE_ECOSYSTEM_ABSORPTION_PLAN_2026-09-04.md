# MELODIA STUDIO — ONE ECOSYSTEM ABSORPTION PLAN (v2)

**Date:** 2026-09-04 night
**Supersedes:** MELODIA_STUDIO_MONOLITH_OVERHAUL_PLAN_2026-09-04.md (the
strangler/seam plan — rejected by owner: it federates two systems forever
instead of ending with one).
**Commitment:** one codebase, one registry, one param model, one UI, one
verifier. The monolith file ends as a thin compatibility shell, then retires.

---

## 0. What exists (measured tonight)

| Component | Numbers |
|---|---|
| `surreal_architecture_gen.py` | 38,596 lines · v2.131 · 643 bpy.props (576 in the props group) · 29 panels · 104 operators · 276 `build_*` functions · 900 `tree.nodes.new` sites (GN authoring) · 561 `getattr(props,...)` fallback reads · 149/209 ids have curated `_ARCH_PARAM_SPEC` · 53 presets · 16 styles · 9 material builders |
| Builder families (by count) | core/misc 87 · aesthetic 70 · greybox 41 · civic 19 · experimental 15 · euro 14 · asian 9 · scifi 8 · zen 7 · castle 6 |
| `deploy/surreal_arch/` package | 63 modules / ~35k lines · 268+ `register_builder` ids · own presets.py (3,652 lines) · own UI (ui.py picker) · integration.py (908 lines) patches INTO the monolith: kit lambdas, panel draw overrides, operator wraps |
| `melodia_studio` panel addon | 6,722 lines, separate bl_info ("Melodia Studio" v1.5), MIDI bridge, terrain, walkable world — same N-panel name as the monolith |
| Already-proven kit pattern | gothic_kit/zen_kit/etc: `build_x(tree, M, props, base_x)` functions injected into the monolith via `register_kit` — 33 builders already live OUTSIDE the monolith file this way |

Key structural facts that make absorption tractable:

1. Monolith builders are GN node-authoring functions with signature
   `(tree, props, base_x)`. Package builders are GN node-authoring functions
   with signature `(tree_name) -> (tree, gin, gout)`. Same fundamental act —
   create GeometryNode nodes. The port = change how params arrive (explicit
   add_*_param sockets instead of the props blob) + wrap in
   `new_geometry_tree()` + `register_builder()`.
2. 643 props exist but only 378 are read, and 149 ids have curated param
   specs listing exactly which props each builder consumes. The per-builder
   param lists are already written down — the port does not have to guess.
3. The package registry already supports: categories, hidden/role flags,
   presets, universal music pass, TreeStats, GN Stack UI, verifier hooks.
   It is the kernel. There is nothing to invent — only to populate.
4. Cross-builder composition exists in both systems (monolith builders call
   each other via `build_x(tree, props)`; package `_ensure_group_node`
   nests registered groups). Port keeps composition by nesting the
   registered group, not by re-calling the function body.

---

## 1. Target architecture (the end state)

```text
deploy/surreal_arch/                    ONE addon: "Melodia Studio"
  __init__.py                           register(): props, UI, registry
  melodia_gn/
    core.py                             THE kernel: register_builder, params,
                                        categories, derived data, verifier hooks
    builders/
      core_forms.py                     TOWER, ORGANIC, PILLAR, DOME, ARCH …
      greybox.py                        GREYBOX_* + GB_* (41) — shells STAY HERE
      euro_classical.py                 gothic/baroque/romanesque/venetian (14)
      asian.py                          cn/kr/jp (9)
      zen.py                            zen (7)
      castle.py                         castle (6)
      civic.py                          town/village/props (19)
      experimental.py                   escher/penrose/klein/fractal… (15)
      scifi_fx.py                       scifi (8)
      aesthetic_fx.py                   70 AESTHETIC_* effect passes
      materials_gen.py                  9 material builders
    facade.py   ui.py   presets.py      panels/operators/presets (single surface)
    compat/
      monolith_props.py                 SurrealArchProperties (643 props) +
                                        _ARCH_PARAM_SPEC + preset application
      monolith_dispatch.py              arch_type enum → registry id lookup +
                                        (tree, props) adapter that binds props
                                        onto group input sockets
  melodia_studio_panel/ (absorbed)      midi bridge, terrain, walkable world
surreal_architecture_gen.py             COMPATIBILITY SHIP only (see §5), then
                                        replaced by a 200-line loader
```

Rules of the end state:

- ONE registry: `melodia_gn.core.GROUP_BUILDERS`. Every piece — whether born
  in the package or absorbed from the monolith — is a registered builder id
  with a category, a param schema, and a preset entry.
- ONE param model: builders declare explicit params (add_float_param etc.).
  The props blob survives only inside compat/monolith_props as the UI's
  state store, mapped onto group sockets by the dispatch adapter. Builders
  NEVER read the blob again.
- ONE dispatch: the monolith's arch_type enum becomes a VIEW over the
  registry (enum items generated from GROUP_METADATA, or the picker reads
  the registry directly). `_KIT_DISPATCH`, `melodia_gn_route.py`, and the
  catalog_dispatch sync all delete — they exist to bridge two registries,
  and there is only one.
- ONE UI: the rebrand decision lands for real — one "Melodia Studio" N-panel
  (Architecture / Music Geometry / Resonant World / Catalog & Export tabs),
  assembled from ui.py + the picker, with the melodia_studio panel addon
  absorbed as the Resonant World section. Legacy `surreal_arch.*` operator
  names become forwarding aliases.

---

## 2. The port unit (what "absorb one builder" means)

For a monolith function `build_window(tree, props, base_x)`:

1. Copy the body into `builders/euro_classical.py` (or its family module).
2. Replace `props.X` reads with group sockets: declare
   `add_float_param(tree, "Window Width", default, min, max)` etc. —
   defaults copied from the bpy.props definition (line-anchored, so values
   are exact), names humanized ("window_width" → "Window Width").
3. Wrap: `def build_window_group(group_name="MEL_window"): tree, gin, gout =
   new_geometry_tree(group_name) … _link(tree, <geom>, gout.inputs)`.
   Internal `tree.nodes.new` bodies port nearly verbatim (900 sites total;
   the code style is compatible — safe_node wraps it).
4. Cross-builder calls (`build_ogee_arch(tree, props)` inside build_window)
   become `_ensure_group_node(tree, "MEL_ogee_arch", build_ogee_arch_group, loc)`
   with param mapping — the call target must already be ported. This makes
   port ORDER a dependency graph, resolved family by family bottom-up.
5. Register with the family category + a preset entry carrying the old
   prop defaults so the UI reproduces the old look exactly.
6. Update `builders/__init__.py` imports; run the family gate (§4).

Estimated scale: 276 functions; the mechanical transform (props→sockets,
wrap, register) is ~70% of each port; composition rewiring ~20%; param
defaults extraction ~10%. The aesthetic 70 are the easiest (5 shared props:
aest_scale/intensity/density/layers/seed — one template ports all).

---

## 3. Phase ladder (each phase leaves Blender fully working)

### P0 — Safety net (before any port)
1. `Tools/verify_full_registry.py`: headless; iterate EVERY registered id
   (package + monolith enum), generate, realize, vert count + bbox + error
   → `registry_baseline.json`. Committed. This is the contract: after every
   phase, re-run and diff — no id may vanish or lose geometry.
2. Same harness records the monolith's GENERATE path (props → tree) per id,
   so absorbed builders can be A/B-compared: old path bbox/verts vs new
   registry path at mapped params. Tolerance: bbox within 1e-3, vert count
   within 5% (SDF/randomness), or exact where deterministic.
3. Git: G1 of the old plan (promote mh6 fix to main) FIRST — the shell fix
   must be in the codebase being absorbed. Then sync_workstation both
   machines, installer, verifier green. This is the frozen starting line.

### P1 — Kernel consolidation (package side, no monolith changes)
1. core.py: add param-schema metadata to register_builder (id → ordered
   param list with defaults/min/max) — extracted automatically from
   new_geometry_tree socket declarations. This gives the registry the
   introspection the props blob used to provide.
2. presets.py: merge contract — one BUILDERS_PRESETS entry per id, schema-
   validated against the param schema (verifier enforces).
3. `melodia_gn/builders/` package skeleton + import wiring + verifier
   extension (counts, categories, param schema presence).
4. Gate: verifier green; zero behavior change; Blender session smoke
   (create one builder from GN Stack).

### P2 — Absorb by family, easiest first (each is a standalone PR-sized batch)
Order chosen by risk × payoff:
1. **aesthetic_fx.py (70)** — 5 shared params, pure geometry passes,
   composable. Also unblocks the music-pass integration story for all
   absorbed builders.
2. **scifi_fx.py (8)** — same shape, tiny.
3. **zen.py (7) + castle.py (6) + asian.py (9)** — self-contained kit
   families; zen_kit.py already proves the pattern (20 builders already
   outside).
4. **euro_classical.py (14)** — gothic/romanesque already kit-shaped;
   baroque/venetian port with them.
5. **civic.py (19) + experimental.py (15)** — leaf builders, few internal
   calls.
6. **core_forms.py (87)** — the hardest: densest cross-calls and prop
   reads. Ported LAST, in dependency order (callers after callees), using
   the call graph extracted in P0.
7. **greybox.py (41)** — ported alongside the shell convergence ladder
   (C1–C4 of the shell plan): mh6 stays THE exterior shell,
   greybox_room_kit stays interior/corridor; the monolith's
   `_gb_rect_room_shell` family dies into `greybox.py` with the room ids
   routed onto the converged builders. THIS is where the three-shell
   problem actually ends.
Per-family gate: P0 harness A/B (old generate vs new registry at mapped
params) + GN Stack smoke + presets round-trip + M0-style diff (no other id
changed). Batch lands as ONE commit per family, narrow-promoted to main.

### P3 — One dispatch
1. compat/monolith_dispatch.py: arch_type enum ids map to registry ids
   (name mapping table generated in P0). The generate() path becomes:
   look up registry id → create modifier → set group input sockets from
   props via the param schema. The 276 dispatch entries and _KIT_DISPATCH
   delete from the monolith file.
2. Universal passes (twist/wave/music/venetian deformation/bevel) become
   post-registration modifiers applied by the operator — same nodes, moved
   out of tree-authoring into the operator layer where they belonged.
3. Gate: full 209-id sweep through the NEW path vs baseline; picker
   generates every id; room-graph presets still spawn/snap.

### P4 — One UI
1. Absorb melodia_studio panel addon into the package (Resonant World
   section): midi_bridge, terrain, walkable world move under
   `melodia_gn/resonant/` with their bl_info merged.
2. ui.py + picker become the single N-panel (the rebrand decision:
   Architecture / Music Geometry / Resonant World / Catalog & Export).
   Legacy `surreal_arch.*` operators re-registered as thin aliases calling
   the new ids (external scripts, hotkeys, muscle memory keep working).
3. Panels: 29 → 4 tabs. The 104 operators keep their bl_idnames where
   referenced by presets/graphs; new canonical names alias them.
4. Gate: full UI walkthrough script (open every tab, run one op per tab);
   verifier counts UI surfaces; manual smoke by owner.

### P5 — The shell retires
1. surreal_architecture_gen.py reduces to: bl_info + loader that imports
   the package + compat shims for anything still referencing monolith
   module globals (grep-audited). Target < 500 lines.
2. One release: merged addon + retirement note + AGENT_START_HERE /
   cockpit / discovery docs updated to the single-surface story.
3. The file is kept one release for third-party imports, then deleted.

---

## 5. What this fixes that the seam plan didn't

- One registry — routing tables (_KIT_DISPATCH, catalog_dispatch sync,
  melodia_gn_route) become unnecessary and get deleted, not maintained.
- One param model — builders own explicit schemas; the props blob stops
  being a hidden 643-field global that any function can mutate (the
  `props.gothic_width = …` mutation inside build_window is exactly the bug
  class this kills).
- One presets layer — schema-validated, not two parallel tables.
- One UI — the rebrand happens in code, not just labels.
- Dead code dies honestly — porting is line-by-line; the 16 dead builders
  and 8 stubs simply don't get ported (logged, not silently dropped).
- Verifier becomes complete — one harness covers every id end to end.

## 6. Schedule reality (game-dev semester)

- P0: 1 session (harness + G1 promotion + baseline).
- P1: 1 session.
- P2: one family per overnight run; aesthetic→scifi→kits→euro→civic→
  experimental ≈ 6 overnights; core_forms is 2–3; greybox rides the shell
  ladder. Full P2 ≈ 2 weeks of overnight runs, each morning reviewing the
  A/B diff report.
- P3: 1–2 sessions after core_forms + greybox land.
- P4: 1–2 sessions.
- P5: 1 session.
Total ≈ 3–4 calendar weeks with the machine doing nights — comfortably
inside a semester, and Blender stays fully usable the entire time because
every phase is additive with the compat layer intact.

## 7. Standing rules (inherited, unchanged)

- P: SSOT → C: → AppData three-copy sync + md5 after every edit;
  sync_workstation.ps1 + installer between machines.
- Narrow git promotion: named files vs main, relevant test, discovery doc
  updated. Never wholesale-merge recovery branches.
- Prose is not a ledger row: every gate gets a dated PASS line here.
- Blender must keep working after every phase — additive only, compat
  shims until P5.

## 8. Ledger

| Gate | Status | Evidence |
|---|---|---|
| G1 mh6 fix → main | OPEN | — |
| P0 baseline harness + registry_baseline.json | OPEN | — |
| P1 kernel param-schema + presets merge | OPEN | — |
| P2 aesthetic_fx (70) | OPEN | — |
| P2 scifi_fx (8) | OPEN | — |
| P2 zen/castle/asian (22) | OPEN | — |
| P2 euro_classical (14) | OPEN | — |
| P2 civic + experimental (34) | OPEN | — |
| P2 core_forms (87) | OPEN | — |
| P2 greybox + shell convergence (C1–C4) | OPEN | — |
| P3 single dispatch | OPEN | — |
| P4 single UI + panel addon absorbed | OPEN | — |
| P5 monolith retires (<500 lines) | OPEN | — |
| mh6 shell defects fixed | **DONE 2026-09-04** | v0_final_verify.log PASS; P: 3f1d4460 |
