# GN Builder Taxonomy — Gold-Ivory/Pink Editorial (2026-08-25)

**Addon:** `deploy/surreal_architecture_gen.py v2.131.0` — 165 GN builders, 12 stack categories, 19 families, 42 genomes, 72 library meshes, 33/165 preset coverage (20%)

**Tokens:** `wix/melodia-tokens.css` gold `#C9A86A`, ivory `#FFF8EE/#F8ECD6`, sakura pink `#E7C9CE/#D6A9B0`, rose `#E8A9A1`, astral `#8AA9D6`, iris `#6E5AA6`

---

## 1. Stack Categories (12) — Keep as NAV, Color by Pillar

| # | Category ID | Label | Count | Pillar (dot) | Usage |
|---|-------------|-------|-------|--------------|-------|
| 1 | GREYBOX | * Greybox / Level Design | **44** | **Grotto gold** `#C9A86A` + lavender `#9F94C6` | Level shells, rooms, corridors — the tandem plan hosts these; snaps to terrain via `tandem_bridge.snap_plan_to_field` |
| 2 | FOUNDATIONS | Foundations | 23 | gold ivory default | Trim/slab bases — pairs with GREYBOX |
| 3 | ASIAN | Asian | 16 | gold ivory | Pagodas, screens — zen pillar alternative |
| 4 | CIVIC | Civic | 15 | gold ivory | Gates, arches |
| 5 | GOTHIC | Gothic | 15 | **Cathedral cosmic** `#66D9FF` / iris | Nave/rose — `GOTHIC_NAVE_CROSSING` style |
| 6 | ZEN | Zen | ~9 families | **Zen pink sakura** `#E7C9CE` | `zen_kairo`, `zen_shrine` axis — maps to `ZEN_SHRINE` composer |
| 7-12 | ArtDeco, ArtNouveau, Baroque, Brutalist, Byzantine, etc | (6× ~8) | plaza/nikki lavender/sakura | Niche—show as filtered sets behind picker search |

**Rule:** GREYBOX stays dominant (44) — expose as default in Tandem City plan picker (`castle/village/grid_city`). Heavy categories get `chrome_kicker` + pillar dot in panel; light categories remain picker-only (search `/_tandem_plan/`).

## 2. Families (19) — Figma-Style Card Deck

* **Zen 9** (`zen_kairo_enclosure_v1` … `zen_tea_garden`) — pink `pillar_zen.png` 24px dot
* **NikkiMirage/Florawish/Heartcraft** (5+4+4) — rose/parchment `#F2E6CF`
* **Gothic 3** (`gothic_chapter_house_v1` etc) — astral `#8AA9D6`
* **Asian 2, Romanesque 2, Sci-Fi 2** — iris/gold variants
* *Remaining 9 families* singletons — grouped under "Curio" in picker to avoid long list

## 3. Genome Transforms (42)

* `axis_compression` 15, `recursive_interior` 14, `vertical_stretch` 8, `organic_twist` 3, `axis_displacement` 1, `none` 1
* Visual: `vertical_stretch` gets elongated preset card (taller `preset_*.png` stub); `recursive_interior` gets layered rings icon

## 4. Coverage & Health

* **Preset coverage 33/165 (20%) — 100 looks** — chrome grid shows 6 hero cards first (`preset_walkable_*`, `preset_cathedral_wide`) with rose-gold accent dots per family; remaining 27 via `style_picker` search. Add coverage bar later in Management panel.
* **P0 heroes smoked 2026-08-13 headless** — keep; P2 fingerprint trees 12 — use for regression

## 5. Organization Actions (Done)

* Generated chrome `melodia_chrome/` (512×8 gold_rule soft rose dot, 512×48 header_void ivory→plum with pink wash + gold speckles, 6 preset cards 256×160 parchment + gold border + rose row, 4 pillar dots 24×24, starlight_gold)
* `melodia_chrome.py` now provides `chrome_header(pillar)` — GREYBOX/grotto gets gold, GOTHIC gets astral, ZEN gets sakura; callers: `studio_panel` cathedral, `gaea_panel` grotto, `tandem` zen
* `audit_gn_builders.py` regenerates `Saved/Audit/gn_triage_20260825.json` on each chrome sync; hook in `tools/figma_sync.py --chrome` (local) and post-kit sync autosync
* **Do NOT move GN builder .py files** — taxonomy is picker/pillar coloring, not filesystem churn. Surreal monolith stays at `deploy/`.

## 6. Autosync Wiring

```
tokens.json -> wix/melodia-tokens.css (SSOT, warm gilded)
     ↓
tools/generate_chrome_icons.py  reads tokens.css, emits melodia_chrome/*.png + pillar_*.png + preset_*.png
     ↓
addon_utils._load_icons()  picks up melodia_chrome/ (512×8 etc) alongside melodia_icons/
     ↓
melodia_chrome.chrome_header/chrome_preset_grid  uses gold/pink dots per pillar
     ↓
tools/figma_sync.py --chrome  (no FIGMA_TOKEN needed) regenerates chrome + gn triage;
post-sync hook regenerates chrome after any kit/motion export automatically
```

Run: `python tools/generate_chrome_icons.py` or `python tools/figma_sync.py --chrome --dry-run`

---
*Generated from `generated/surreal_architecture_catalog.json` + `deploy/surreal_architecture_gen.py` parsing, `wix/melodia-tokens.css` 2026-08-20.*
