# Material Instance Closeout — 2026-08-31 (Overnight)

## Status: READY FOR EDITOR (blocked on restart)

---

## ✅ COMPLETED — Copernicus Pipeline (Offline, Pure Numpy)

### Pipeline Script
`Tools/Houdini/copernicus/copernicus_cymatic_parallax.py`

**Maps per variant (9):** BaseColor, Normal, Roughness, Metallic, Height, ORM, Emissive, Iridescence, Opacity

**All 11 variants bake clean at 1024×1024 and 2048×2048.**

### Variant Roster

| # | Variant | Character | Animation | Status |
|---|---------|-----------|-----------|--------|
| 1 | CymaticMarble | Chladni singing stone | Phase shift | ✅ Live |
| 2 | GildedLoom | Fabric + moving gears | Gear rotation | ✅ Live |
| 3 | SilkWaterfall | Silk + flowing water | Water flow | ✅ Live |
| 4 | CavernWeve | Cavern rock + marble + crystals | Subtle phase | ✅ Live |
| 5 | DancingCrystals | Inlaid twinkling crystals | Dance + twinkle | ✅ Live |
| 6 | CherryBlossomWood | Cherry wood + sakura | Sway | ✅ Live |
| 7 | GildedCoral | Coral + nacre + gold | Pulse | ✅ Live |
| 8 | StarlitAbyss | Deep ocean biolum | Twinkle | ✅ Live |
| 9 | FrozenFracture | Cracked ice + frost | Shimmer | ✅ Live |
| 10 | SingingConstellations | Star-map + singing nodes | Sing + twinkle | ✅ Live |
| 11 | FinalDreamweaver | Moonlight fabric + living shadows | Breathe + weave | ✅ Live |

### Overnight Cron Jobs (running forever)
- `copernicus-flipbooks` — every 90m, bakes --frames 16 for motion variants
- `copernicus-pipeline-expand` — every 120m, adds new variants from queue
- `copernicus-session-saver` — every 120m, snapshots to _session_snapshot.txt

---

## 🚫 BLOCKED — Editor Work (needs restart)

### Jellyfish (P0 Sea Above)
1. Wire `MI_Jelly_Bell` → `JELLY_Bell` skeletal mesh (currently unreferenced)
2. Tag jellyfish in `P0_TASK_LEDGER.json` under sea_above_cutscene deliverables
3. Set parallax on jelly MIs: `ParallaxStrength=0.35, ParallaxScale=0.08, ParallaxHeight=0.12`
4. Author `ABP_JellyBell` for 2-bone pulse animation
5. Assemble `BP_Jelly_SeaAbove` (bell + arms + veil) and place in `LV_SeaAbove_Prototype`

### Material Instance Review
1. **Nikki masters** — check parallax params, inline vs MF split, bNikkiHero switch, BaseTint
2. **Fabric MIs** — verify Faraway COPs import, parallax, sheen params
3. **Jelly MIs** — verify parent is `M_Master_Toon_Universal_Alpha` for translucency

### PBR Map Gaps (for future pipeline enhancement)
- Subsurface Color / Thickness (for jelly, skin, leaves)
- Clear Coat (for lacquered wood, wet ice)
- Anisotropy (for fabric weave, hair)
- Sheen (for velvet, silk, fabric)
- Displacement (for tessellation)

---

## 📋 Morning Recovery Steps

1. **Restart editor** — `taskkill /IM UnrealEditor.exe /F` then relaunch
2. **Verify port 9316** — `netstat -ano | grep :9316` should show LISTENING
3. **Run `hermes gateway start`** if gateway is down
4. **Re-run subagents** for jellyfish wiring and material instance reviews
5. **Check Copernicus output** — `ls Saved/Audit/copernicus_cymatic/` should show 11+ variants

---

## 🎵 Skill Documentation

- `melodia-copernicus-parallax` — full pipeline doc with pitfalls, math reference, variant guide
- `melodia-cathedral-builder` — updated to point to copernicus for PBR generation
- `melodia-fabric-cops-pipeline` — Houdini COPs variant (separate, for tilable fabrics)

---

*Generated 2026-08-31 ~03:00 AM. Session context saved to Saved/Audit/copernicus_session_context.md*
