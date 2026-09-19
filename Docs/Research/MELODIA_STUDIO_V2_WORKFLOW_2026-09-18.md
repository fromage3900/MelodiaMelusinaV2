# Melodia Studio V2 — Blender workflow research (2026-09-18)

Design-reference synthesis for the final Melodia Studio V2 addon. Every claim below is
sourced from fetched documentation or a live probe on this workstation (Blender 5.2.1
LTS, hash `9e2066aef7ef`). Where a fetch failed it is stated rather than papered over.

## Sources actually retrieved

- Blender 5.2 LTS Manual — Geometry Nodes Introduction
  `https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/introduction.html`
- Blender 5.2 LTS Manual — Node-Based Tools
  `https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/tools.html`
- Blender 5.2 LTS Manual — How to Create Extensions (manifest spec)
  `https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html`
- Blender Extensions listing — BagaPie (v11.0.12, updated Sept 2026)
  `https://extensions.blender.org/add-ons/bagapie/`
- **Failed fetch:** `https://www.bagapie.com/` (site unreachable from here). BagaPie
  details below come from its official Extensions platform listing instead.

## 1. BagaPie — the industry peer for a pie-first GN addon

BagaPie ships **50+ tools for architecture and environment** and its entire interaction
model is **three pie menus**:

- **Main Pie = `J`** — object tools
- **Edit Mode Pie = `D`** — modelling tools
- **GeoPack Pie = `V`** — user's own custom tools

"Select an object, press J, pick a tool and BagaPie does the rest." Its tools are
Geometry-Node node groups: Scatter / Scatter Paint / Scatter presets (auto-generated
previews), Ivy Gen, Effector, Array (line/grid/circle/curve), Architecture (wall, window,
column, beam, stair, floor, handrail, fence, siding), Edit-Mesh (bool-through, tessellate,
insert circle), and group management. **GeoPack** stores assets + node trees in a
shareable package; those node trees appear as tools in the `V` pie, and GeoPack can save
**how BagaPie pre-configures the node tree and any custom actions** ("Zip Tool"). It
declares `files` + `network` permissions.

Release note that matters to us: **11.0.12 (Sept 6 2026) — "Node group inputs now display
correctly in Blender 5.2."** A peer addon hit exactly the 5.2 node-group-input breakage our
own `link_sockets` WARN classes describe (`gn_warn_audit_2026-09-18.md`).

## 2. Blender Node-Based Tools — a second surface beyond the N-panel

A GN node group can be a **tool** invoked from a Blender menu, not only a modifier:

- Set the node tree **sub-type to "Tool"**; the group then appears in the 3D Viewport's
  **Non-Assets menu**. Existing modifier groups convert by enabling **Tool Usage** in the
  sidebar (optionally disabling Modifier Usage) and setting **Supported Modes & Object
  Types**.
- **Tool inputs** = sockets on the Group Input node; they surface in the **Adjust Last
  Operation** panel when the tool runs.
- To move a tool to a custom menu / share it: **Mark as Asset** → Asset Browser → drop it
  into a catalog named after the target menu → save as an asset bundle → copy into an
  asset library. Then it works in any blend-file.
- **Tool-only nodes:** 3D Cursor, Mouse Position, Viewport Transform, Active Element,
  Selection, Set Selection, Face Set, Set Face Set. **Not supported in tool context:**
  Simulation Zone, Viewer Node (modifier-context only). Inspection is unsupported in the
  tool context; shape keys are removed if a tool runs on a mesh.

## 3. Extensions platform — packaging model

A public V2 must ship as an **extension**, not a legacy `bl_info` addon:

- `blender_manifest.toml` **required**: `schema_version`, `id`, `name`, `tagline`
  (<=64 chars), `version` (semver), `type` ("add-on"), `blender_version_min` (>=4.2.0),
  `license` (SPDX), `maintainer`.
- **Optional**: `blender_version_max`, `website`, `copyright`, `tags`, `platforms`,
  `wheels`, and `permissions` (`files`, `network`, `clipboard`, `camera`, `microphone` —
  each needs a <=64-char reason).
- `[build]` table: `paths` / `paths_exclude_pattern` (gitignore-compatible; defaults
  exclude `__pycache__/`, `.git`, `*.zip`).
- CLI: `blender --command extension build` and `blender --command extension validate`
  (validate also accepts a built `.zip`). Publishing updates is CI/CD-driven; self-hosted
  "extensions repositories" are supported for private distribution.

## 4. What this means for Melodia Studio V2 (gap analysis)

| Pattern | Where Melodia Studio stands | V2 action |
|---|---|---|
| Pie-first routing | Already the design: Shift+Q main, Alt+Q room, Ctrl+Shift+Q window, Shift+Alt+Q genome, Shift+M score | Keep — a 50+-tool peer (BagaPie) validates the approach |
| GN tools as menu tools | Builders registered in `GROUP_BUILDERS`, surfaced via pies/N-panel | Also expose key chains as **Tool-subtype** groups for Adjust-Last-Operation |
| Shareable tool packages | `GROUP_BUILDERS`/`GROUP_METADATA` registry | Consider a "GeoPack"-style asset-bundle export |
| Extension packaging | legacy `bl_info` dict in `__init__.py` | Add `blender_manifest.toml` **only if V2 ships publicly** (P2) |
| Headless certification | `Tools/verify_addon.py` (A–F) + `deploy/_melodia_health_*.py` | Wire the gate into extension CI/CD if published |
| 5.2 socket drift | `link_sockets` swallows failures as WARNs | **Fix first** (audit P0): fail loud so drift cannot hide |

## 5. Bottom line

The V2 interaction model (pie router + one N-panel host) is aligned with the strongest
peer in this space. The two concrete forward moves are (a) expose the best builder chains
as **Node-Based Tools** so they gain menu + Adjust-Last-Operation presence, and (b) if the
addon is ever made public, repackage as an **extension** with `blender_manifest.toml` and
put `verify_addon.py` behind extension CI. Neither is required for the current private
workflow; both are cheap to adopt because the registry already exists.

## 6. Open follow-ups

- Retry `bagapie.com` when network allows, for its GeoPack authoring details.
- Prototype one builder chain as a Tool-subtype group and confirm it appears in the
  Non-Assets menu and Adjust Last Operation on 5.2.1.
- Run `blender --command extension validate` against a draft manifest in a scratch copy
  before committing to public packaging.
