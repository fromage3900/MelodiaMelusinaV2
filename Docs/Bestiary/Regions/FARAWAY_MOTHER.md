# Faraway Mother — textile ecology (P1)

**Region bestiary status:** IDENTIFIED DIRECTION / BOUNDED CANDIDATE ROSTER  
**Chapter position:** P1, following Sea Above (per [Daily Canon Audit](../../Art/DAILY_CANON_AUDIT_2026-08-29.md)).  
**Environmental thesis:** *fabric may be landscape; geography may be draped anatomy*.

## Species philosophy

Poitou is inhabited; Faraway Mother feels like its **landscape has become animate**. Silk mountains, velvet valleys, seams, lace bridges, and tense cloth should visually explain its inhabitants. Creature interaction leans toward **calming, lulling, or retuning**, not lethal combat. No dolls and no conventional violent monster roster.

The Mother is wounded; the smaller beings echo vulnerabilities in the fabric on a gentler scale. Material should indicate ecology first, not a lineup of themed toys.

## Roster and approvals

| Species / family | Role under discussion | Status | Disposition |
|---|---|---|---|
| **[Les Emmaillotés](../Creatures/LES_EMMAILLOTES.md)** | Swaddled living textile beings; off-beat unwrap / lull to comfort | **CANON — APPROVED DESIGN** for original core; bear-like exterior is a candidate | First dedicated art / encounter reference |
| Lace Wings | Ambient lace fauna that may echo seam direction | RESEARCH CANDIDATE | Passive dressing only if it serves a proven route; avoid overlap with Poitou's Doily Moth |
| Méduses du Silence / Hush Jellies | Suspended cloth bells, quiet zones, possible musical response | RESEARCH CANDIDATE | Reserve traversal-platform behavior until existing mechanic fits |
| Seam Eels | Moving seam-curve cues, telegraphed rhythmic breach | DEFERRED CANDIDATE | No immediate encounter implementation |
| Bobbin Choir | Spools with an out-of-tune call-and-response | DEFERRED CANDIDATE | No new puzzle framework |
| Voilettes | Veil-fog presence / atmospheric obstruction | DEFERRED CANDIDATE | Atmospheric study only; no stealth system |

**Only Les Emmaillotés have explicit owner-approved species identity in this pass.** The presence of other candidates here is not approval for a six-enemy production backlog. The earlier proposed “two interactive + one ambient” allocation is a planning suggestion, not a canon roster decision.

## Existing pink/lavender HoudiniForge candidates — owner identification (2026-10-26)

The owner rediscovered ChimeSnail, PearlJellybell and JellybellQueen models from the HoudiniForge collection and is considering the pink/lavender forms for **Faraway Mother**. These already have tracked UE staging packages and animation-family folders; they are **existing asset reuse candidates**, not a newly commissioned bestiary family or confirmed Faraway inhabitants. Their original work context was Ocean Cathedral/Aeolian. Preserve Les Emmaillotés' priority and no-dolls/nonviolent identity. See [Carillon recovery dossier](../Creatures/CARILLON_FAMILY_RECOVERY.md). Pending: choose exactly which variant(s) fit, verify original source and UE behavior, and make any Faraway child material look without overwriting Gaudy masters.

## Musical/geographic connection

The authored Faraway Mother's existing Chladni basis is `(3,5)`; nodal seam corridors are derived offline by its PCG/Hython field. Keep placement conditional on verified world-space mapping, traversability, and current asset availability. A signed `F=0` contour is *not* itself a safe walkable path.

[Production integration spec](../../Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md) defines authority:
- **Houdini/Hython:** deterministic static spatial assets, field textures, offline bakes.
- **TouchDesigner/Embody:** presentation-only modulation from the existing semantic music lane.
- **Unreal:** actual gameplay, timing, encounters, saves, placement decisions.
- **World Compiler:** existing world-composition authority. Do not replace it.

The P1 live return path is **not yet proved** by the spec; do not label these creatures as cooked or in-engine without a separate PIE proof.

## Art and audio anchor

Outer materials: warm muslin, antique ivory linen, lace and soft mohair where appropriate. Inner/structural materials: burgundy velvet, rose-toned folded textile, fine warm-gold stitch repair. Atmospheric palette: pearl, lavender, muted blue, warm blush. Tactile beauty coexists with asymmetry, wear, tension, and vulnerability.

Ambient sound should be musical and world-readable rather than stock monster vocalization. Reuse existing rhythm/audio-response infrastructure. No second metronome, no creature-specific global audio bus, no full runtime Vellum dependency.

## Non-goals

No expansion of chapter length, no new universal ecology engine, no new animal-rig factory, no additional playable instrument, no multi-creature boss encounter, no doll roster, no forced acquisition of all candidate species.

## Build/reference foundation

- [Faraway P1 field spec](../../Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md)
- [Fabric mountain build and coordinate rules](../../Art/FARAWAY_MOTHER_FABRIC_MOUNTAIN_BUILD_2026-09-02.md)
- [Vellum offline textile archetypes](../../Houdini/FoundryDay_2026-09-24/11_FARAWAY_MOTHER_VELLUM.md)
- [Houdini protected master rule](../../Houdini/HOUDINI_LANE_MAP_2026-10-09.md)
- `Houdini/FarawayDrape.hip` contains protected authored `FARAWAY_DRAPE_GRID`, `TENSION_MASK`, and `Cymatic_BeatPulse` work; experiment on copies. No new tooling task is authorized by this document.
