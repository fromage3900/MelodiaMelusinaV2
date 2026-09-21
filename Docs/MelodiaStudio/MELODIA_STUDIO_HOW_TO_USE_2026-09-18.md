# Melodia Studio — How to Use (2026-09-18)

Product: **Melodia Studio** ("Architecture - Ornament - Genome"); module id
`melodia_studio`; enabled Blender module file `surreal_architecture_gen.py`; every
operator keeps the `surreal_arch.*` prefix. Verified against Blender **5.2.1 LTS** on
this workstation. Every name/key below is read from source, not remembered.

## 1. Install & enable

1. Sync the checkout into the live Blender 5.2 addons tree (repo → live only):

   ```
   python deploy/_sync_addon_to_blender_5_2.py            # install
   python deploy/_sync_addon_to_blender_5_2.py --check    # read-only drift check
   ```

   The installer targets **Blender 5.2** explicitly (`BLENDER_VERSION = "5.2"` in
   `deploy/_sync_addon_to_blender_5_2.py`); it `rmtree`s + `copytree`s the packages
   `surreal_arch`, `surreal_os`, `surreal_world`, `surreal_greybox` and copies the
   monolith `surreal_architecture_gen.py`, then writes
   `melodia_studio_sync_provenance.json`. **Close Blender before syncing** (freeze-doc
   ritual §5) — it replaces the live addon directories.
2. Blender → **Edit ▸ Preferences ▸ Add-ons** → search **Melodia** → enable
   **Melodia Studio**.
3. Confirm: press `Shift+Q` in the 3D Viewport — the main pie should appear.

## 2. The pie is the router

| Keys | Opens | Purpose |
|---|---|---|
| `Shift+Q` | **Main pie** | generate, sub-pies, trim, snap, export, dress |
| `Alt+Q` | Room-shape pie | 7 shapes + More Shapes |
| `Ctrl+Shift+Q` | Window-cutout pie | 8 window shapes |
| `Shift+Alt+Q` | Style-genome pie | 6 DNA axes + presets |
| `Shift+M` | Score pie | score / convergence (`music_ui.py`) |

A **right-click on an object** also offers the Melodia pies (plus Ivy and Score, each
guarded so a missing peer addon cannot break the menu).

### Main pie wedges

- **Generate** — run the active arch type.
- **Room Shape** — opens the room sub-pie.
- **Window** — opens the window sub-pie.
- **Genome** — opens the style-genome sub-pie.
- **Zen Stone Trim** + **Bake Trim**.
- **Snap** + **Snap Overlay**.
- **Export UE5**.
- **Ivy (Bagapie)** + **RQ Ivy Batch** + **Sakura Walk** + **Zen Sakura Plan** (the Dress
  wedge; the mesh-dependent entries show "Select mesh" until a Melodia mesh is active).

### Sub-pies

- **Room** — Rectangle, L-Shape, T-Shape, U-Shape, Circular, Apsidal, Octagon, plus
  **More Shapes** → Hexagon, Ellipse, Superellipse, Freeform Curve.
- **Window** — Rect, Round Arch, Gothic, Ogee, Circle, Rosette, Lintel, Segmental.
- **Genome** — Verticality, Symmetry, Ornament, Structure, Organic, Cosmic, each with
  `+` / `−` nudges; **Presets** → Zen Shrine, Gothic Cloister; **Apply Genome**.

## 3. The N-panel

Everything lives in **one** sidebar tab, **"Melodia Studio"**:

- Only **`SURREAL_ARCH_PT_genome_carousel`** stays top-level — it is the host.
- Every other Melodia panel is re-parented under the carousel with `DEFAULT_CLOSED`
  (see `branding.unify_npanel_categories()`), so the sidebar stays a single tidy list.
- The picker (search + style filter + workflow mode) lives inside the host box.

## 4. Legacy modifier drawer

The old Modifier-tab drawer is hidden by default. In
**Preferences ▸ Add-ons ▸ Melodia Studio**, enable **`show_legacy_modifier_panel`** to
bring it back (it is then labelled "Melodia Studio - Modifier (legacy)"). Leave it off
for the current workflow.

## 5. BagaPie bridge (soft-optional)

The Dress wedge and the Ivy entry talk to the **BagaPie** extension through a thin,
guarded bridge (`bagapie_bridge.py`): one pie leaf (`Ivy`) plus the carousel status.

- **Ivy** — single scatter (`surreal_arch.ivy_scatter`).
- **RQ Ivy Batch** — review-queue batch; runs **dry_run by default**, so it is safe to
  invoke without committing placements.
- If BagaPie is **not** installed, the entries report "unavailable" and the rest of the
  addon is unaffected (every bridge call is guarded with `hasattr(bpy.ops…)`).

## 6. GN builder stack

Geometry-Node builders register into `GROUP_BUILDERS` / `GROUP_METADATA` /
`CATEGORY_META` (`deploy/surreal_arch/melodia_gn/`). Current live registry after this
close-out: **593 builders across 28 categories**, 0 build errors, 2 recorded duplicate-id
clusters (`MEL_escher_belvedere` / `MEL_gb_escher_belvedere`, `MEL_escher_waterfall` /
`MEL_gb_escher_waterfall` — pre-freeze debt, not design).

- Time-driven builders use the **single time seam** (`melodia_gn/time.py`): the group
  exposes **Animated / Time Scale / Time Offset**; `Animated = False` (or Time Scale = 0)
  reproduces the pre-time geometry exactly. The seam animates on the **scene timeline**,
  so motion survives headless render, bake, and linked libraries — Convergence Mode need
  not be running.
- Builders surface through the pies, the N-panel host, and (optionally) Node-Based Tools.

## 7. Export

**Export UE5** (main pie, SW wedge) — run with the target mesh active. The addon writes
the UE5-ready output; UE-side integration is owned by the MelodiaIntegration C++ bridge,
not this addon.

## 8. Troubleshooting

- **A pie leaf does nothing / "Select mesh"** — the active object is not a Melodia mesh
  (needs `obj.surreal_arch_props`). Select a generated mesh first.
- **`[WARN] link_sockets … None` or `'End Location' … on 'Mesh Line'`** — 5.2 socket
  drift in some builders. This is catalogued in
  `Saved/Audit/gn_warn_audit_2026-09-18.md`; it is latent (the tree still builds) and the
  fix is a P0 on `core.link_sockets` (fail loud). It does not block normal use.
- **Pies missing after update** — re-run the sync, then reload the addon (Preferences ▸
  Add-ons ▸ disable/enable). The sync replaces live directories, so Blender must be
  closed during it.
- **Sidebar shows a second Melodia tab** — a stray panel declared its own category; the
  core `unify_npanel_categories()` pass folds it back on reload.

## 9. Verification commands (read-only)

```
# builder registry / gate (headless, exits non-zero on failure)
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup --python Tools/verify_addon.py

# static UI census (no Blender needed)
python deploy/_melodia_audit_studio_ui.py

# live↔checkout drift
python deploy/_sync_addon_to_blender_5_2.py --check
```

Gate A–F and what each proves is documented in
`Docs/Production/MELODIA_STUDIO_FREEZE_2026-09-11.md` §4 (note: its B/C numbers are the
09-11 snapshot; the current tree is green at 593/28/2). The close-out record for this
date is `Saved/Audit/melodia_studio_closeout_2026-09-18.md`.
