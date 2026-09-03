# DeepSeek handoff — Surreal addon toggleables

**Date:** 2026-07-11  
**Branch context:** `feature/recursive-learner` (BS_GodFile)  
**Blender:** 5.1 only  
**Goal:** Continue implementing **toggleable functions** in Surreal (visibility, overlays, accessory/system toggles). Do not expand scope into Melusina cloth/hair or UE ChaosCloth.

---

## Mission (one sentence)

Make Surreal’s “toggle” UI actually control scene/viewport state — especially **collection/object visibility** — and finish the half-wired toggle operators that already exist.

---

## Edit / sync contract (do not break)

| Role | Path |
|------|------|
| **Edit SSOT** | `C:\EnvironmentPortfolio\BS_GodFile\deploy\` |
| Live Blender 5.1 | `C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons\` |
| Sync after edits | `deploy\sync_surreal_to_live.ps1` then F3 → Reload Scripts (or restart Blender) |

Packages: `surreal_architecture_gen.py` (monolith) + `surreal_arch\` + `surreal_os\` + `surreal_world\` + `surreal_greybox\`.

Register overhaul extras in: `deploy\surreal_arch\integration.py` → `register_overhaul` / `_EXTRA_CLASSES`.

---

## What already works (copy these patterns)

| Toggle | `bl_idname` | File | Notes |
|--------|-------------|------|-------|
| Snap overlay | `surreal_arch.toggle_snap_overlay` | `surreal_arch/greybox_overlay.py` (+ pie + `ui.py`) | GPU draw handler on/off |
| Nikki stats checkbox | `surreal_arch.toggle_stats` | `genome_carousel.py` | flips `NikkiWardrobeProperties.show_stats` |
| Graph favorite | `surreal_arch.toggle_graph_favorite` | `genome_carousel.py` | scene string |
| Accessory toggle-all | `surreal_arch.accessory_toggle_all` | `genome_carousel.py` | UI vector only — **not applied to meshes** |
| Feature BoolProps | many `*_with_*` / `show_*` | `surreal_architecture_gen.py` `SurrealArchProperties` | regen-driven |
| Workflow mode | `ui_workflow_mode` | monolith + `ui.workflow_allows_panel` | hides panels |

Stage-side visibility (outside addon UI today):

- `Tools/unhide_stage_review_collections.py` — `set_collection_flags()`, `clear_layer_excludes()`
- `Tools/melodia_stage_shot.py` — `set_collection_render()`
- `Tools/setup_melusina_master_studio.py` — defaults: `Set_Diorama` / `Surreal_Regen_Starlight` **off**

---

## Broken / unfinished (fix these)

1. **`surreal_arch.toggle_genshin`** — operator still exists (~32525 in monolith), UI still calls it (~33833), but it is **commented out of `classes`** (~38744, “removed v2.28”). Either re-register or replace UI with `layout.prop(props, "genshin_style", toggle=True)`.

2. **`accessory_toggles`** (`BoolVectorProperty` size 16 on Nikki wardrobe) — equip/clear UI only. Spawn ops **ignore** the vector. Need `apply_accessory_visibility` that sets `hide_viewport` / `hide_render` on spawned Seq_*/graph children by index.

3. **`surreal_arch.stats_overlay_toggle`** (`stats_overlay.py`) — has register/unregister but is **not** called from `integration.register_overhaul`. Wire it + put a button next to snap overlay in `ui.draw_level_design`.

4. **No in-addon collection visibility operator** — Melodia stage still needs Outliner or Tools scripts. This is the highest-leverage new work.

---

## Melodia stage pins (do not clobber)

- Stage file: `KitbashExport/Melodia_Portfolio_Stage_v4.blend`
- Empty hook: `NOTE_SurrealStarlight` in `Set_Diorama`  
  props: `surreal_genome=nikki_melodia_stage_v1`, `surreal_vibe=starlight_melodia`
- Regen child coll: `Surreal_Regen_Starlight` under `Set_Diorama`
- Library coll: `SurrealArch_Library` stays hidden for plates
- Hair look pin: keep Melusina **`Water (Advance).001`** identity (Komikaze groups already inside); do not FLIP-replace strands or full-append catalog mats over character
- Floor pin: **`Studio_FloorCard`** — do not move (boots intersect for Infold grounded contact)
- MCP port **9877** (not Live Link 9876)

Docs: `KitbashExport/STAGE_README_v4.md` (§ Surreal Arch + toggles).

---

## Implement in this order

### P0 — Stage collection toggles (soft isolation)

**SSOT file:** `deploy/surreal_arch/stage_visibility.py` (mirrored to live Blender 5.1 addons)  
**Register:** `integration.py` via `register_stage_visibility_classes()`

**Soft isolation policy (2026-07-15):**

| Mechanism | Use for stage |
|-----------|---------------|
| `LayerCollection.hide_viewport` / `exclude` | Viewport isolate (Outliner eye — artist-friendly) |
| `Collection.hide_render` | Render isolate (beauty / kitbash plates) |
| `Collection.hide_viewport` | **Never set** for stage presets — hard-locks Outliner |

```text
Operator: surreal_arch.toggle_stage_collection
  props: collection_name (str), viewport (bool), render (bool), clear_exclude (bool)

Operator: surreal_arch.set_stage_visibility_preset
  enum: solo_melusina | diorama_on | starlight_on | beauty_clean
        | review_all | review_queue_solo | sculpt_monetization

Operator: surreal_arch.review_queue_cycle
  direction: -1 Prev | 0 Solo Current | +1 Next
  Soft-shows one Review_Queue child at a time (Asset_*).

Operator: surreal_arch.clear_object_visibility
  "Fix collection toggles" — clears object hides + Collection.hide_viewport
  hard locks on the stage allowlist.
```

Preset behavior:

| Preset | On | Off |
|--------|----|-----|
| `solo_melusina` | Melusina + Nikki + Studio + Cameras | `Review_Queue`, diorama, Surreal regen, WaterFX, … |
| `diorama_on` | + `Set_Diorama` | Review_Queue soft-off |
| `starlight_on` | + Surreal_Regen_Starlight | Review_Queue soft-off |
| `beauty_clean` | Minimal beauty plate | Review_Queue + FX soft-off |
| `review_all` / **Review Queue** | `Review_Queue` + lights/cameras (kitbash subject) | Melusina / Characters soft-off |
| `review_queue_solo` | Only Review_Queue + lights/cameras | Melusina + clutter soft-off |

**UI:** Melodia Studio N-panel → Stage (Solo / Starlight / Beauty): presets + Review Queue parent toggle + Prev / Solo / Next. Shift+G pie: Review Prev / Review Next.

Reuse soft helpers also in `Tools/unhide_stage_review_collections.py` (never hard-lock).

### P1 — Wire accessory toggles → real hide

**File:** `genome_carousel.py`  
After spawn (or via new `surreal_arch.apply_accessory_visibility`):

- Read `NikkiWardrobeProperties.accessory_toggles[i]`
- Map index → sacred-sequence / spawned child naming (`Seq_*` / graph children)
- Set `hide_viewport` + `hide_render` (and optionally collection flags)

### P2 — Register stats overlay

**File:** `integration.py` — call `stats_overlay.register()` / `unregister()`  
**UI:** button beside snap overlay (`surreal_arch.stats_overlay_toggle`)

### P3 — Fix Genshin toggle

Re-add to `classes` **or** delete dead operator and use prop toggle in UI.

### P4 — Library visibility toggle

**File:** `surreal_world/library.py`  
`surreal_arch.toggle_library_visibility` — flip `SurrealArch_Library.hide_viewport` (pieces can stay individually hidden unless “reveal pieces” mode).

### P5 (nice) — Useful extras once P0–P3 land

- Toggle `auto_update` with confirm when leaving ON (expensive regen)
- Toggle helper meshes (Klein/Möbius/Seifert already hide_viewport in monolith — expose operator)
- Toggle `SurrealArch_Library` vs spawn coll in one “LD clean view” preset
- Viewport overlay: show/hide greybox snap + stats as a single “LD HUD” toggle

---

## Acceptance checks

1. After sync + reload, N-panel shows Stage Visibility presets; clicking `solo_melusina` / `starlight_on` changes Outliner eye/camera icons for the named collections (and clears `ViewLayer` excludes when requested).
2. Accessory checkboxes hide/show corresponding spawned pieces without deleting them.
3. Snap overlay + stats overlay both toggle from UI; no console errors on register.
4. Genshin button either works or is removed (no Operator not found).
5. Melusina hair still `Water (Advance)*` with intentional Komikaze groups inside; Lane A clothes hybrids (e.g. `SHAWL.001`) intact — no Lane B full-mat overwrite on character.
6. `Studio_FloorCard` world transform unchanged (boot contact).

---

## Do not do

- Do not edit AppData copies as SSOT (edit `deploy/`, then sync).
- Do not rename stage cameras (`Cam_Beauty`, …) or Melusina collection contracts.
- Do not put FLIP / cloth / FV2 work in this pass.
- Do not force-push; do not commit secrets.

---

## First files to open

```
deploy/sync_surreal_to_live.ps1
deploy/surreal_arch/integration.py
deploy/surreal_arch/genome_carousel.py
deploy/surreal_arch/ui.py
deploy/surreal_arch/stats_overlay.py
deploy/surreal_arch/greybox_overlay.py
deploy/surreal_world/library.py
deploy/surreal_architecture_gen.py   # toggle_genshin ~32525, classes ~38744
Tools/unhide_stage_review_collections.py
Tools/setup_melusina_master_studio.py
KitbashExport/STAGE_README_v4.md
```

---

## Suggested first commit message (when ready)

```
Add Surreal stage visibility presets and wire orphan toggle operators.
```

Good luck — prioritize **P0 stage visibility** so Melodia shooting stops needing Outliner archaeology.
