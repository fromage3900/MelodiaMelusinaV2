# Polished EEVEE Komikaze — Render Prototype Plan (Updated 2026-09-07 — Full Spin)

> For Humber AN311 final year + Melusina portfolio. Replaces any plan that says to run the lost tools. Now spun with every thread from your semester prep, git safety, and studio pipeline.

## 0. Why this plan exists
You asked for polished, not experimental. The old portfolio pipeline promised `batch_eevee_komikaze_portfolio` + `komikaze_stage_looks` — both gone July 2026, only 50KB/8KB .pyc left, hidden by `Tools/*` gitignore (LOST_TOOL_SOURCES_2026-08-14.md). This rebuilds on what still sings: v22 stage + `melodia_stage_shot.py` + Lane A hybrids.

## 1. What we have today (verified)
- **Live stage:** `Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend` (Blender 5.2, port 9876)
- **Working one-click:** `Tools/melodia_stage_shot.py` — EEVEE_NEXT, 1600x2000, Nikki/Jewelry/Silhouette, Cam_Beauty → `my-site-clean/generated/assets/`
- **Komikaze alive on character:** `SHAWL.001` (Principled + Halftone → Shader to RGB → Mix 0.5) + `Water (Advance).001` on hair
- **Humber spine:** Sem5 Capstone 1 / Career Connections + Sem6 Capstone 2 / Portfolio — this plan feeds all four

## 2. What "polished" means (shipping bar)
- Halftone gradation smooth, no banding at 100% crop
- Outline consistent on hair/shawl rims, no breaks
- Reads in warm Nikki *and* cool Jewelry lights
- EEVEE_NEXT 64 samples, no fireflies, clean alpha
- Boots grounded through `Studio_FloorCard` Z -0.2935 by design — never move floor

## 3. 7 Polished Prototypes (build in order — each is a reel shot)

**P1 — Beauty Hybrid (baseline)**
`melusina` solo, Lane A only, `beauty`+`nikki`+`Cam_Beauty`. Reproduce `melusina_beauty_eevee_20260715_01.png` iter07 on v22. Pass: histogram delta <5%, hair intact.

**P2 — Glam Wardrobe**
`outfit:<OutfitId>` (Wardrobe_<id>). Clone SHAWL.001 graph to outfit mats, don't catalog-replace. Pass: same ink density at skirt panel 100% crop. Humber hook: becomes Portfolio reel shot #5 (hero).

**P3 — Diorama / Set Full-NPR**
`Set_Diorama` / `Studio_FloorCard` full Komikaze (Lane B — full replace OK *only* on sets). Rebuild set-only append filtered to Studio/Set. Pass: paper grain + halftone, no spill onto Asset_melusina when composited.

**P4 — Portfolio Sheet (deliverable)**
4-up: front / three_quarter / portrait / macro, same lights. Writes to `generated/assets/character/melusina_eevee_beauty_34.png` family. Pass: 1600x2000, <2min headless, passport JSON.

**P5 — Silhouette / Mood (new idea)**
Same beauty but `silhouette` lights (rim 900, key 40) + `Cam_Beauty` low. For Capstone mood poster + ArtStation cover. Pass: rim reads, halftone still visible in shadow.

**P6 — Turntable Loop (new — for Humber dailies + reel)**
8-frame 360° around Melusina (45° steps, 1600x2000, 24fps mp4). Uses P1 setup, auto-aim per frame. For Career Connections industry night. Pass: clean loop, no light pop.

**P7 — Material Study Card (new — for tech art jobs)**
1 image: 3 spheres + 1 cloth swatch showing Komikaze mix 0.0 / 0.3 / 0.5 / 0.7. Proves you understand the hybrid. Pass: labeled, becomes Portfolio breakdown sheet.

## 4. How we rebuild (don't decompile)
New `Tools/eevee_komikaze_polish.py` — thin wrapper on melodia_stage_shot.py:
1. `ensure_stage()` v22
2. keep `setup_eevee()` 64 samples
3. character: VERIFY `Linear Gradient (Halftone)` exists, don't overwrite
4. set: safe `bpy.data.node_groups` append only to `Studio_*`/`Set_*`
5. reuse `LIGHT_RECIPES` Nikki/Jewelry/Silhouette
6. batch loop → PNG + passport (skip if module missing), log to `Humber_FinalYear_Prep/renders/`

No `uncompyle6` on 3.13 .pyc — rewrite is faster and proven.

## 5. Spun-in: Your semester systems
- **Tracker:** prototypes map to `Humber_FinalYear_Tracker.xlsx` — P1/P5 → Capstone lookdev, P2/P4/P7 → Reel Shots, P6 → Career Connections. Fill Deadlines sheet as syllabi drop.
- **Weekly Routine:** Mon/Wed Life Drawing 5/6 keeps line weight that makes halftone *feel* right. Thu dailies = screen P1 vs P5. Sun 30m review = backup renders.
- **Git safety (from your .gitignore review):** new script must be `!Tools/eevee_komikaze_polish.py` allowlisted, or invert `Tools/` rule per LOST §7 — otherwise next delete is silent. Commit PNGs to `Saved/Portfolio/` (already allowlisted `!Saved/Portfolio/`) not `surreal_sweep/` (gitignored).
- **3-2-1 Backup:** Git for .py/.blend source + Drive + 1TB external for renders/video. 32GB RAM, SSD, Wacom — your Tech_Checklist.md.

## 6. Spun-in: Studio pipeline ideas
- **Houdini/Copernicus idea:** bake a tileable halftone paper grain via COPs, feed as overlay in Komikaze group — tilable, not screen-space banding
- **Daemon idea:** overnight `melodia-daemon-monitor` cron — render P6 turntable at 2am, publish to `Saved/Portfolio/` by morning
- **Wardrobe retopo idea:** P2 outfits go through `melodia-wardrobe-retopo` before hybrid — dense sculpts kill EEVEE ink lines
- **Shader idea:** move halftone thresholds to `melodia-shader-rider` params so you can A/B 0.45 vs 0.55 without rebuilding graph
- **Catalog idea:** log every prototype mat in `Saved/Audit/melusina_komikaze_hybrid_inventory.json` (missing since Aug 14) — rebuild that audit

## 7. Week plan (Humber-friendly)
- **Day 1:** P1 beauty on v22 vs iter07 reference (`_site_aside_untracked/`)
- **Day 2:** P2 outfit clone + P7 study card (one graph, two outputs)
- **Day 3:** P3 set NPR rebuild (isolate to Studio/Set only)
- **Day 4:** P5 silhouette + P6 turntable (overnight render)
- **Day 5:** P4 sheet + site dry-run (`my-site-clean/generated/`), push to ArtStation

## 8. Commands (Blender 5.2, headless)
```
blender Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend -b -P Tools/melodia_stage_shot.py -- --preset beauty --lights nikki --subject melusina
blender v22.blend -b -P Tools/melodia_stage_shot.py -- --preset beauty --lights nikki --subject outfit:dawn_chorus
blender v22.blend -b -P Tools/eevee_komikaze_polish.py -- --sheet  # P4
blender v22.blend -b -P Tools/eevee_komikaze_polish.py -- --turntable  # P6
```

## 9. Risks & guards
- Allowlist gap — new tool lost same way if not allowlisted
- Never move Studio_FloorCard, never full-replace Water (Advance) hair
- 5.1 paths dead — 5.2 only
- `MELODIA_ALLOW_STAGE_SAVE=1` to save stage, else read-only
- Large boots sit through floor by design — don't "fix" it

## 10. Done when
- P1-P7 PNGs/MP4 on disk, 1600x2000, no banding, hair intact, set grain visible
- Sheet + study card + turntable in `Humber_FinalYear_Prep/renders/` + `Saved/Portfolio/`
- `eevee_komikaze_polish.py` committed (not just .pyc), audit JSON regenerated
- Tracker updated, ArtStation + LinkedIn ready for Career Connections

Next: want me to draft `Tools/eevee_komikaze_polish.py` and fire P1 tonight? Say go and I won't ask again — I'll just render.
