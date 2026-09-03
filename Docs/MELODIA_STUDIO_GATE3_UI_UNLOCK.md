# Melodia Studio — Gate 3 UI unlock

**Status:** Unlocked (2026-07-12)  
**Prerequisite:** [`Saved/Audit/melodia_studio_gate2_ready.json`](../Saved/Audit/melodia_studio_gate2_ready.json) `ok: true`

Detailed UI integration (panel IA, Figma icons/tokens, demoting legacy monolith draws) is a **separate pass**. Do not mix it into branding/sync work.

## Unlocked baseline

- Preferences name: **Melodia Studio**
- Module id unchanged: `surreal_architecture_gen`
- Operators: `surreal_arch.*`
- Single N-panel tab: **Melodia Studio**
- Overhaul + smoke + quality props healthy

## Working UI strip (2026-07-12)

Shipped for ASAP use (see `Saved/Audit/melodia_studio_ui_working.json`):

| Panel order | Panel | What works |
|-------------|-------|------------|
| 0 | **Studio · Stage** | Soft stage presets (Solo/Diorama/Starlight/Beauty/Review Queue) + Review Prev/Next/Solo + Fix collection toggles |
| 1 | **Studio · Wardrobe** | Starlight CTA + genome carousel |
| 2 | **Studio · Accessories** | Toggles sync `hide_viewport`/`hide_render` on Seq_/atom objects |
| 3 | **Studio · Photo** | Capture / photo tools |
| 10–12 | Picker / Level Design / Melodia GN | Generate + snap/stats overlays |

Ops: `surreal_arch.starlight_popup`, `set_stage_visibility_preset`, `toggle_stage_collection`, `review_queue_cycle`, `clear_object_visibility`, `stats_overlay_toggle`.

**Soft isolation (2026-07-15):** Stage presets use `LayerCollection.hide_viewport` + `Collection.hide_render` only — never `Collection.hide_viewport` hard locks. Review_Queue children step one-by-one via `review_queue_cycle`.

## Synced additions (2026-07-16)

Live Blender 5.1 add-on has the deploy-synced Melodia GN polish:
- 39/39 registered Melodia GN builders are gold/works; catalog: `Saved/Audit/melodia_gn_builder_catalog.md`.
- Music builders, sheet rail, ornament builders, `label_tree`, and `try_apply_melodia_gn` route first.
- `ARCH` and registered `CASTLE_*` routes are wired through Melodia GN; `MEL_arch`, `MEL_portico`, and `MEL_gazebo` fixes are in.
- Studio carousel has **Solo Object** (`surreal_arch.solo_object`) for local-view isolate.
- Studio has **Ivy (Bagapie)** (`surreal_arch.ivy_scatter`) with Blender 5.1 socket rebind.

Review / smoke queue:
- Confirm Melodia Studio GN stack draw and modifier visibility in Blender 5.1.
- Route-check `SHEET_MUSIC_RAIL`, `TREBLE_CLEF`, `NOTE_HEAD`, ornament builders, `ARCH`, and one representative `CASTLE_*`.
- Confirm Review Queue Prev / Solo / Next, Solo Object, and Ivy (Bagapie) without hard-locking collections.
- Keep `FILIGREE_*` monolith rewrites deferred.

## Next polish (optional)

1. Figma icons via `icon_loader.py`
2. Demote leftover monolith PROPERTIES drawers
3. Collapse Pattern / Live Link under Studio accordion

See branding: [`deploy/surreal_arch/branding.py`](../deploy/surreal_arch/branding.py) · stage: [`stage_visibility.py`](../deploy/surreal_arch/stage_visibility.py).
