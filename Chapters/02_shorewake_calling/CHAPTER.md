# Chapter 02 — Shorewake Calling

Status: DRAFT-B (bible skeleton; every claim below traces to a path on unified main)
Reference: `Docs/Production/WORLDBUILDING_LOOKDEV_PLAN_2026-09-06.md` §1 chassis.
World-building contract: `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`.
Source beat: `TODO.md` "Shorewake calling + Starskiff departure."
Pilot of: `Chapters/CHAPTER_TEMPLATE.md`.

## Tier
Chapter (semester artwork lane). First Dream remains the integration proof; this unit is not required to clone the six-phase P0 script.

## Seven metadata fields
1. **Narrative Question** — Can clothing and a played phrase carry Melusina from grief-tinged longing into first wonder at sea?
2. **Mechanical Focus** — Wardrobe as travel gear (Dawn Chorus → Shorewake) plus one music-as-key phrase that opens the Starskiff departure route.
3. **Character Focus** — Melusina; Choral Sheep stays presentation-only until skinned.
4. **Location** — `L_KaleidoNave` terrace/quay → `LV_SeaAbove_Prototype`.
5. **Visual Signature** — Shorewake dress at the tide-line, Starskiff departure, Sea Above membrane pulse.
6. **Persistent Change** — Shorewake calling flag/quest, Shorewake dress already owned via wardrobe catalog, previewed skiff-charm reward, `shorewake_first_tide` resonance intent, Sea Above travel already allowlisted.
7. **Exit Image** — Starskiff leaving the quay into Sea Above while the membrane answers the song.

## Player-loop stages used
Player Input; Overworld Traversal; Interaction & Triggers; Narrative Layer; Capability / Instrument Unlocks; Encounter Decision (optional reef choir); Combat Setup / Rhythm / Post-Combat only if `encounter.shorewake.reef_choir` is entered; Progression & Checkpoint; Return to World.

Combat is not mandatory pacing. Victory and Fled both resume Quill once.

## C++ owners touched
Narrative/Quill; Wardrobe; Starskiff; canonical save; Phoenix/JRPG + rhythm only if the reef encounter runs; UI Bridge for whatever surface is already the single writer. No new subsystem.

## Chladni / TouchDesigner
Presentation-only. Sea light reads `MPC_Melodia_Palette`; Nikki-chain parents remain the lookdev path. TouchDesigner is not required to ship this chapter and must not own quest, save, or traversal truth.

## Logline
Melusina hears the sea calling her name at the tide-line, dresses for the water
(Dawn Chorus → Shorewake), and departs on the Starskiff from KaleidoNave's terrace
into LV_SeaAbove_Prototype — where the membrane pulse answers her song.

## Emotional movement (the feeling-arc rule: music follows feeling)
grief-tinged longing → resolve → first wonder. This chapter teaches the player that
outfits ARE travel gear (Glide/Dash → the Swim-capable Shorewake reads as water-ready)
and that a played phrase opens a route (music-as-key, one rung deeper than P0's piano).

## Route
| Leg | Map | Authority | Notes |
|---|---|---|---|
| 1 | `/Game/EnvSandbox/Environments/L_KaleidoNave` | exists, P0-proven | terrace trigger (reuse encounter-authority pattern) |
| 2 | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype` | **already in TravelLevelIds** (27-ID delta) | dressed-map gate pass 09-03; membrane pulse 16s cycle live |
Dreaming transition in/out via existing travel verb — no new system.

## Quill beats (draft; allowlist delta in encounters.json, NOT authored into DA yet)
1. `MelodiaQuillShorewake.qsc` — EXISTS with a wired trigger fixture (isolated space,
   f407220f) but carries ZERO melodia: notifications yet. It is presentation text;
   the beat verbs below are what chapter-close adds.
2. Authored intents (new, need allowlist entries before merge):
   - `melodia:flag:flag.shorewake.calling:true` (post-beat-1)
   - `melodia:quest:quest.shorewake.calling` (questcomplete after Starskiff departure)
   - `melodia:travel:/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`
   - `melodia:reward:reward.shorewake.skiff_charm` (grants the Cos_ accessory, see assets)
   - `melodia:stat:shorewake_first_tide:melodia_resonance:5` (idempotent per intent id)
3. Music-as-key rung: one Piano phrase on the Starskiff's lyre host →
   `APCGHeroMusicGraphHost::OnPatternCompleted` → typed result opens the departure
   route. Reuses the proven `music_world_key` seam exactly; pattern density differs,
   grading stays classical.

## Encounter
One authored encounter at the tide-line (choral-sheep-shepherds of the reef? TBD in
route.md pass 2) riding `battle_integration_map` authority. Rhythm overlay on top of
stock command input, per the locked seam. Victory/Fled both resume Quill once.

## Assets (all verified present on main)
| Need | Asset | State |
|---|---|---|
| Water outfit | `SK_ShorewakeDress_*` (retargeted Melusina465, Magical variants) + `MI_Melusina_Dress_Shorewake` | rigged; canonical usdc at `Saved/` (270k v, 28 mats) |
| Animated fabric | `T_DressShorewake_ScaleMask`, `T_DressShorewake_ScaleShimmer` + PearlWoven 16-frame set | **needs MF_FlipbookScrub (specs/materials/MF_FlipbookScrub.v1.json)** |
| Boat | Starskiff kit: hull/brass/cushion/wake-emission MIs, regal bake, `T_Starskiff_Brass_Patina_Mask` (pair with SurrealFabric BrassPatina 6x5 atlas) | imported 09-05, dressed |
| Reef | SeaAbove/Prototype/Reef kit (kelp/coral/starfish OBJs, MI_SeaAbove_Cloth_Banner) | present; height-aware PCG live |
| Dressing | `PCG_SeaAbove_BellTreeGarden` | present |
| Cosmetics row | `Cos_` id for Shorewake dress EXISTS in catalog (0038 commit added it); new charm row needed for reward | one-row delta |

## Score
Theme: "Shorewake Calling" — 128BPM marpeggiomelody family already load-bearing on
the music clock; chapter gets one new pattern set (ranked density via quantum lane is
permitted: pre-play only). Beat-map source stays Harmony/MusicClock imported MIDI.

## Lookdev (tier plan per §4 of the lookdev plan)
SeaAbove surfaces get T1 pastel-grade via their Nikki-chain parents (already reparented
in convergence); Reef cloth banner gets T2 rim+twinkle; Starskiff wake emission is the
ONE exempt asset (reads as water-light, leave sticker-free). PPV: reuse the certified
PPV_NikkiDream stack; chapter may add one weight-shifted blend, never a new master.

## Exit criteria (chapter-complete definition — mirrors golden run)
Fresh slot → tide-line beat visible → travel works (allowlist, no silent no-op) →
one encounter with typed result → phrase-opens-route visibly → save/restart → no
duplication. A human plays it. No new subsystem may be needed to explain a failure;
if one is, it's a defect, logged to §5 of the lookdev plan, not a feature.

## Open questions (owner)
- Does Chapter 2 ship before or after the fall-term reframe? (Bible is written to be
  term-presentation-ready either way.)
- Choral Sheep is PRESENTATION_ONLY until skinned — recruit beat stays cameo.
