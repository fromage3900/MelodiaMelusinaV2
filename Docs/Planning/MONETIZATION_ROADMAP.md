# Monetization Roadmap — BS_GodFile / Melodia

**Status:** In progress  
**Last updated:** 2026-07-16  
**North star:** A sustainable revenue stream from environment-art products that funds portfolio development and commissions pipeline.

---

## Guiding Principles

1. **Portfolio-first, monetization second.** The game (Melodia) and the Melusina character are portfolio pieces — never sold. Monetization comes from the *tooling and kitbash products* built around them.
2. **Ship one SKU, learn the pipeline.** SKU #1 validates the entire Gumroad → ZIP → delivery → marketing flow. Nothing else matters until it's live.
3. **No engine lock-in.** Products must be stock-UE or stock-Blender compatible. No MooaToon fork dependency. FBX + standard materials only.
4. **Separate product assets from portfolio assets.** `Products/` owns sellable content; `Content/EnvSandbox/` owns portfolio content. Cross-contamination requires explicit movement.

---

## Phase 0 — SKU #1: Gothic Ornament Kitbash (Now)

**Target:** SKU #1 live on Gumroad.  
**Est. effort:** 10–14 hours  
**Target price:** $14 launch → $18 list  

### Workstream A — Geometry Fixes (Blender)

| Task | Est. | Done? |
|------|------|-------|
| A1 — TorusKnot: remesh from 0-face curve shell to solid kitbash | 2h | |
| A2 — FiligreeRing: decimate from ~97k to 5–12k, UV, Base/Trim mats | 2h | |
| A3 — CrownMolding: cap density, verify manifold, export unit scale | 1h | |
| A4 — UV + Base/Trim on 4 hero meshes (RoseWindow, VaultRibs, OculusFrame, SpiralStaircase) | 2h | |
| A5 — UV + Base/Trim on P2 lissajous (WovenRing, RosetteMedallion, GothicTracery, PendantFinial) | 2h | |
| A6 — UV on P3 modular (DoorArchway, ColumnCapital, QuatrefoilArch, CorbelBracket) | 1h | |

### Workstream B — SKU #1b: Musical Ornament Kitbash (Sibling)

| Task | Est. | Done? |
|------|------|-------|
| B1 — Hand-remake TrebleClef + MusicalCorner | 2h | |
| B2 — Replace MelodyToken 01–03 placeholders with beauty meshes | 1h | |
| B3 — Polish SheetMusicRail, MusicalDivider, NoteBeam, NoteHead, PearlJewel | 1h | |

**Melodia Studio / GN sync — 2026-07-16:** Blender 5.1 live add-on now has the polished Melodia GN path synced from deploy: music builders, sheet rail, ornament builders, `label_tree`, and `try_apply_melodia_gn` route first. The builder catalog at `Saved/Audit/melodia_gn_builder_catalog.md` records all 39 registered builders as gold/works, including `ARCH` and registered `CASTLE_*` routes plus fixes for `MEL_arch`, `MEL_portico`, and `MEL_gazebo`.

Review queue helpers now available for SKU review:
- Melodia Studio carousel: `surreal_arch.solo_object` for local-view isolate.
- Melodia Studio: **Ivy (Bagapie)** via `surreal_arch.ivy_scatter`, with Blender 5.1 socket rebind.
- Remaining backlog: `FILIGREE_*` monolith rewrites stay deferred; do not block SKU #1 unless a specific sell mesh depends on them.

Smoke before publish/package:
- Verify Melodia Studio GN stack routes musical builders through MEL_* where intended.
- Test `SHEET_MUSIC_RAIL`, `TREBLE_CLEF`, `NOTE_HEAD`, ornament builders, `ARCH`, and representative `CASTLE_*` in Blender 5.1.
- Use Solo Object / Review Queue / Ivy controls only for soft review and marketing prep; do not save over Melusina or stage blends from agent automation.

### Workstream C — Package & Publish

| Task | Est. | Done? |
|------|------|-------|
| C1 — Re-export all 15 gothic FBX → KitbashExport/OrnamentalMeshes/ | 0.5h | |
| C2 — Re-export all 10 musical FBX → KitbashExport/MusicalOrnamentalMeshes/ | 0.5h | |
| C3 — Mirror FBX to Products/OrnamentKitbash/FBX/ and Products/MusicalOrnamentKitbash/FBX/ | 0.5h | |
| C4 — Capture 6 store screenshots (product, hero detail, in-scene) | 1h | |
| C5 — `package_ornament_kitbash.py --zip` (gothic) | 0.5h | |
| C6 — `package_musical_kitbash.py --zip` (musical) | 0.5h | |
| C7 — Upload to Gumroad, set `store_live=true` | 0.5h | |
| C8 — Update social upload kit captions to include "Buy Now" CTA | 0.25h | |

### Revenue projection (SKU #1)

| Scenario | SKU #1 | SKU #1b | Total |
|----------|--------|---------|-------|
| Launch price | $14 | $10 | $24 |
| List price | $18 | $14 | $32 |
| Bundled discount (20% off) | $14.40 | $11.20 | $25.60 |
| Break-even at launch price | 1 sale | 1 sale | 2 sales |

---

## Phase 1 — Soft-List SKUs (After SKU #1 Ships)

Inventory prioritized by effort-to-revenue ratio. Each SKU should ship within 2–4 hours of focused work.

| # | SKU | Effort | Price | Contents | Status |
|---|-----|--------|-------|----------|--------|
| 1 | Stylized Props Mini | 2–3h | $9 | Lean ZIP ~17.6 MB; Brick2 low retopo pending; highs excluded | Partially ready |
| 2 | Gothic Arch / Lancet | 2–4h | $5–8 | EnvSandbox greybox arches | Needs packaging |
| 3 | Greybox Blockout (47) | 4–6h | $12–15 | SM_Greybox_* curated set | Needs allowlist review |
| 4 | Melodia House Modular | 3–5h | $10–12 | _PROJECT allowlist | Needs curation |
| 5 | Stylized Cross Prop | 1–2h | $5 | Packaged zip on G:\ | Needs testing |
| 6 | Enchanted Forest | 3–5h | $8–12 | Existing pack | Needs review |
| 7 | Zundy Modular | 8–12h | $15–20 | Import from ZUNDYMONSKITCHEN | Needs stage setup |
| 8 | Fantasy Weapons Mini | 2–4h | $8–10 | Optional F:\ staging | Needs inventory |

**Potential revenue (all 8 at list, single sales):** $72–96 total.

**Strategy:** Ship in batches of 2, staggered 1–2 weeks apart, to maintain store presence without overwhelming support.

---

## Phase 2 — Long-Term Health (Parallel, Non-Negotiable)

Infrastructure that keeps the project sellable and recoverable.

| # | Item | Est. | Priority | Notes |
|---|------|------|----------|-------|
| H1 | Commit or backup Melodia Melusina (~770 MB, 324 files) | 1h | **Critical** | Highest work-loss risk in the project |
| H2 | Consolidate dual Greybox trees (root/ vs EnvSandbox/) | 2–3h | High | 89 overlapping names, 709 vs 156 files |
| H3 | Resolve Grotto orphans (4 missing M_SDF_* parents) | 1–2h | Medium | Bioluminescence, BubbleColumn, CoralBranching, FloatingNotes |
| H4 | Save ZenForestTest.umap now that NTFS journal is fixed | 0.25h | Medium | Unpersisted actors |
| H5 | Add longevity-rule checks to run_verify.ps1 | 1h | Medium | Enforce no-DDC, clean tree, one-change |
| H6 | Add asset-pipeline hardening to CI (regeneration contracts, editor-only prohibition) | 2h | Low | From ASSET_PIPELINE_HARDENING doc |

---

## Phase 3 — Portfolio & Commission Pipeline

After product revenue is live, use it to fund portfolio-quality output.

| # | Item | Est. | Revenue driver |
|---|------|------|----------------|
| P1 | Complete L_Template showcase level | 4–6h | Portfolio → commissions |
| P2 | Complete L_SakuraPath with Zen shrine + water + PCG scatter | 8–16h | Portfolio → commissions |
| P3 | 3–5 hero stills + 1 flythrough per environment → ArtStation | 2–4h per set | Portfolio → commissions |
| P4 | Update Wix site with real portfolio pieces, link Gumroad | 4–6h | Cross-channel funnel |
| P5 | Write commission rate card (environment art, tech art, materials) | 1h | Direct revenue |
| P6 | Publish rate card on site, enable contact form | 1h | Direct revenue |

### Commission rate card (recommended starting rates)
- Environment art (full scene): $500–2000 depending on scope
- Technical art / material setup: $100–300 per material
- PCG graph design: $200–800 per graph
- Blender → UE asset pipeline setup: $150–400 per asset family

---

## Phase 4 — Recurring Revenue (Optional, Not Before Phase 3)

| # | Option | Est. effort | Monthly revenue potential | Notes |
|---|--------|-------------|--------------------------|-------|
| R1 | Monthly kitbash drops ("Medieval Vol 2", "Baroque Vol 1", etc.) | 4–8h/mo | $50–200 | Build on SKU pipeline |
| R2 | Commission retainer (3–5h/week recurring client) | 12–20h/mo | $800–3000 | Needs client base |
| R3 | Tutorial / breakdown content | 4–8h per video | Indirect | Patreon/gumroad possible |

---

## Timeline

```
Week 1-2: Phase 0 (SKU #1) — geometry fixes, export, package, ship
Week 2-3: Phase 1 SKU 1-2 (Stylized Props + Gothic Arch)
Week 2:   Phase 2 H1-H2 (Melusina backup, greybox consolidation)
Week 3-4: Phase 1 SKU 3-4 (Greybox Blockout + House Modular)
Week 3:   Phase 2 H3-H5 (Grotto orphans, ZenForest save, verify hooks)
Week 4-5: Phase 1 SKU 5-6 (Cross Prop + Enchanted Forest)
Week 5-6: Phase 3 P1-P3 (L_Template, L_SakuraPath, hero stills)
Week 6-7: Phase 3 P4-P6 (site update, rate card, contact form)
Week 8+:  Phase 1 SKU 7-8 (Zundy + Weapons) as bandwidth allows
          Phase 4 evaluated based on Phase 0-3 revenue
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Melodia Melusina lost (untracked ~770 MB) | Low | **Catastrophic** | Commit or external backup before any other work |
| Blender recovery gap (no v15, no PRE_225030) | Medium | High | Accept v14 as nearest; don't re-save stage blends |
| TorusKnot unfixable from 0-face curve shell | Low | Medium | Remove from SKU, replace with equivalent mesh |
| Gumroad payout delays / account issues | Low | Medium | Test with $1 listing first |
| No commission inquiries | Medium | Low | Build portfolio quality first, then market |
| UE 5.x upgrade breaks products | Medium | Medium | Products use FBX + stock materials only |
| Git operations too slow on large untracked set | High | Low | Use `.gitignore` + LFS patterns; partial commits |

---

## Open Questions (Needs Decision)

1. **Bundle or individual?** — Ship SKU #1 + #1b as separate listings, or one "Ornament Megapack" at $24?
2. **Gothic + Musical — same listing or separate?** Current Gumroad listing is musical-only. Create a second listing for gothic?
3. **License type?** — Standard Gumroad (commercial use, no resale) OK, or need extended license?
4. **Attribution required?** — No for paid assets; CC-BY for free portfolio content?
5. **Commission rate card — publish openly or quote-on-request?** Published rates set expectations but limit negotiation.

---

## External Links

- [Gumroad listing (musical)](Products/MusicalOrnamentKitbash/listings/gumroad.md) — $14 launch / $18 list
- [Monetization geometry fix list](Docs/MONETIZATION_GEOMETRY_FIX_EXPORT_2026-07-12.md) — P0-P3 per-mesh detail
- [Social upload kit](_github_deploy/wix/SOCIAL_UPLOAD_KIT.md) — crops, captions, post policy
- [Website dream shader review](_github_deploy/wix/WEBSITE_DREAM_SHADER_REVIEW.md) — site design
- [Sandbox long-term plan](Docs/SANDBOX_LONGTERM_PLAN.md) — longevity rules
- [Project health 24h](Docs/PROJECT_HEALTH_24H.md) — pass/fail table
- [Asset pipeline hardening](Docs/ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md) — production rules
