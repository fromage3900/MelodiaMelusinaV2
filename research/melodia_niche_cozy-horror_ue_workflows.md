# Melodia Melusina — Deep Niche: Cozy→Demented Psych-Horror, Light Gacha, Western Steam (UE 5.8)

**Date 2026-08-23 · Tracks T1-T4 · Top 0.1% UE workflows + niche OSS**

## Thesis
Melodia is cozy pastel→trauma like OMORI/Doki Doki/Yume Nikki on an Infinity Nikki wardrobe bar, but in UE 5.8 Substrate Toon with rhythm-as-ritual and music-as-key. Western Steam white space: cozy-horror JRPG with fashion gameplay is <15 titles >1k reviews.

## T1 — Western Steam Map (prelim)
- **Comps:** OMORI $19.99 (43k Overwhelmingly Positive), Doki Doki free (150k), Pony Island meta arcade, Sea of Stars $34.99, Hi-Fi Rush $29.99, Yume Nikki fam. Sweet spot $24.99-$29.99 premium + cosmetic DLC, no F2P economy.
- **Differentiator:** wardrobe-as-dread + music corrupts room-shell (currently only water consumer `Source/BS_GodFile/Piano/`). Expand to `L_MelusinaMorning` shell.

## T2 — Top 0.1% UE 5.8 Workflows
| Workflow | Elite 2026 pattern | Melodia path | OSS Alt |
|---|---|---|---|
| Substrate Toon | `SubstrateToonBSDF` slab (5.8 Beta, StraySpark 2026-07-03) | `M_Master_Toon_Universal` 916 expr `CURRENT_STATE.md:379` instance-only | `miltoncandelero/ue5-toon-shader-plugin` 65★ |
| Clock | Harmonix Sequencer-integrated (not Quartz) | Dual `Harmonix\|Quartz` `auditor_m3/handoff.md:40`, Harmonix 128BPM beatgrid + Quartz `cos²(BeatPhase·π)` | — |
| PCG | Mesh Terrain nondestructive + PVE Nanite | `WPTerrains/` vs new Mesh Terrain eval | — |
| MCP | Native `UnrealMCP` /mcp 830 tools | Monolith 9316 (16 tools) → bridge to native Toolsets | `ChiR24/Unreal_mcp` 838★, `ue-mcp.com` |
| VRM | runtime MToon+SpringBone | `Imports/Plugins/VRM4U` `vcs.xml:8`, 1921★ 2026-07-22 | — |
| Water | Oceanology FFT + FluidNinja 0.5ms | Bass→Gerstner, BeatPulse→caustics `worker_m3` | — |

## T3 — OSS Toolkit (Adopt/Reference/Skip)
- **Adopt:** `rhythm-game-utilities` 122★ 701 commits (header-only .chart/.midi), `ruyo/VRM4U`, `awesome-vrm` HANA Tool, `WardrobeSystemDocs` DataAsset, `RmonteRodriguez/Gacha-System` weighted array.
- **Reference:** `Boyquotes/psych-horror` Sanity/Tension (port to `UMelodiaNarrativeSubsystem`), `NeoVise Horror Framework` (Fab 2026-05-20), `retrovoid Horror BP Pack` (14 scenarios), `libre-nikki` + OMORI×Yume Nikki fangame + Doki Yume Loop mod 2026-06-20.
- **Skip if <10★ pre-2025:** Demo-ware.

## T4 — Light Gacha Trust
Rates transparent, pity, duplicates→craft, no stamina, no stat power. Ledger-gated: `repeat_consume` PASS `PROJECT.md:92` idempotent `melodia:stat:`, `wardrobe_equip_roundtrip` OPEN must prove pity persistence `echo_run.py`.

## Next: Live Editor Verification
See `research/live_verification_kit.md` + `Tools/verify_p0_live.py`.
