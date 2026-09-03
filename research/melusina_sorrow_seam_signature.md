# Signature Feature — Melusina's Sorrow Seam

**Pitch:** Your dress remembers what you couldn't play.

Melusina's sheer Trail + Shawl (OIT `M_Fabric_Melusina` `research/melusina_shine_fabric_booth.md:1`) is not cosmetic — it's a **living memory veil**. Cozy at rest, it frays with dread and mends with music. No stat, no damage, pure story cloth.

## Why no one else has this

- **Wardrobe as trauma journal:** Most games sell skins. Melusina's shawl encodes your rhythm memory across sessions — a single persistent fabric that frays on tension and only heals when you *play* the world. Uses existing `FMelodiaNarrativeRecord.ConsumedIntentIds` idempotency `PROJECT.md:92` + `MelodiaWardrobe` `DA_MelodiaCosmeticCatalog` — no new save authority.
- **Cozy→demented via cloth:** Kawaii hair `ABP_Melusina_WaterHair` `hair_root` `KAWAII_PHYSICS_PLACEMENT_AUDIT:13` already floats. The veil adds OIT translucency `specs/materials/m_fabric_melusina.v1.json:53` + `DreadPresence→MadokaRealityWarp` `TENSION:108` warp. At Dread 0 → byte-identical pastel; at Dread 1 → subtle peripheral jitter + desat + dark thread Sheen, never jumpscare.
- **Music heals, rhythm mends:** Piano phrase `challenge.first_resonance_echo.completed` `ORCHESTRA_CONVERGENCE:251` fully restores the veil and unlocks Glide — same flag that already gates wardrobe. Battle rhythm grade (Perfect/Great) adds `Iridescence 0.02` repair; Good/OK holds; **no miss penalty ever** `DECISION_LOG:016`. So music-as-key and rhythm-as-care converge on the *same cloth*.

## How it plays (1 loop)

1. **Explore:** Veil breathes to `BeatPulse = cos²(BeatPhase·π)` `AUDIO_IMMERSION_PLAN:60` — gentle.
2. **Battle tension:** `TensionSustain` 4.0/0.35 `TENSION:22` → `DreadPresence` frays veil (warp + dim). Pure presentation; damage still stock JRPG `PROJECT.md:10`.
3. **Result:** Grade → mending. Stored as `melodia:flag:sorrow_seam_mended.<session>` (idempotent IntentId) + cosmetic sheen bump on `MI_Fabric_Melusina_Trail` instance — visible in wardrobe preview, not in numbers.
4. **Heal:** Play `first_resonance_echo` on `APCGHeroMusicGraphHost` `ORCHESTRA_CONVERGENCE:140` → `CommitWorldChallenge` → veil pristine + Glide. Expensive to earn, free to feel.

## Horror register (tasteful)

At high Dread, veil's iridescence at screen edge shows faint *echo-Melusinas* — your past runs' silhouettes, spawned as Niagara `AudioReactiveFX` sprites reading `DissonanceAmount` `research/melusina_shine_plan.md:1` row 9. No input, no chase, just "the dress saw you before."

## Tech (already built, just wired)

- **Mater:** `M_Fabric_Melusina` OIT `Shawl 10 / Trail 20` `m_fabric_melusina.v1.json:46` + `MF_MelodiaIridescenceSheen` sheen + `MF_Madoka` dread warp `TENSION:108`.
- **Physics:** Kawaii limits `DA_Melusina_HairCollisionLimits` `KAWAII:47` for hair; veil uses `WindMask` + vertex color `R=phase` `m_fabric_melusina:130` (no sim, cheap).
- **Wardrobe:** New cosmetic `Cos_Trail_SorrowSeam` on `Trail` slot, default on MelusinaV2, `resonant_form_id` null (decorative only until healed) — honors `specs/wardrobe/wardrobe_catalog_manifest.v1.json:62` pattern.
- **Persistence:** `melodia:flag:sorrow_seam_state.<mended|frayed>` via `UMelodiaNarrativeSubsystem` — survives save/load `save_load` PASS `PROJECT.md:92`.

## What makes it special

Infinity Nikki proves wardrobe as fantasy; OMORI proves cozy can hold trauma; Melusina proves **the dress can hold the player's own hesitation** and be healed by playing music. Light gacha sells *alternate* veils (different weaves), but the Sorrow Seam is the free, soul-bound one you mend yourself — Western Steam trust intact.

