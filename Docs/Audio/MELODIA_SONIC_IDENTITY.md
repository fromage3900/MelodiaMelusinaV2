# MELODIA SONIC IDENTITY

Status: Draft (in progress)
Target: "Elastic Glass" - melodic, whimsical, precise

## References
| Reference | Pull | Avoid |
| :-- | :-- | :-- |
| SOPHIE - BIPP | Rubber-y, elastic transients, bouncy plucks | Maximal drops/screeches, heavy sub-bass |
| A.G. Cook / PC Music | Cute synthetic timbre with clinical edge, melodic pitched percussion | Swapping materials per hit, losing instrument identity |
| Iglooghost | Whimsical micro-glitching, airy overtones | Noisy/glitchy chaos that muddies dense phrases |
| WaveHarp (Content/Melodia/Audio/WaveHarp/*) | North star - melodic, intimate scale | Orchestral swells, losing precision |

## Pillars
| Pillar | Goal | Implementation |
| :-- | :-- | :-- |
| Elastic Glass | Blend of plucked glass, silk strings, very lightly processed plastic | Base on harp/plucked bell; aim for bouncy not metallic/crisp |
| Melodic Percussion | Hits feel pitched, not percussive | Leverage grade/lane/timing in HitMetaSound; use pitch for melody |
| Tactile Micro-Glitch | Whimsical without messy | Only on misses/specific accents; restraint |
| Intimate & Dry | Up close and precise | Mostly dry; let buses handle space |
| Graded by Intensity | Same material across grades | Scale attack/brightness/decay; mute/dull for miss rather than swap instrument |

## Forbidden
- Boomy impacts, 808s
- Cinematic reverb wash
- Orchestral swells
- Metallic clang
- Drum/percussive kit sounds
- Aggressive sub-bass

## Seed Prompt (ElevenLabs Sound Effects)
```
Elastic glass harp pluck. Rubber-y, bouncy attack. Silky body with airy bell harmonics. Melodic, not percussive. Dry, mono, intimate. No metallic clang, no sub impact, no drum, no reverb wash, no orchestral swell.
```

## Generation Plan
1. Generate 3-5 seeds with above prompt; pick one house seed
2. Derive hit_perfect/great/good/miss from seed (same material, intensity/brightness/decay only)
3. A/B in-engine against HitMetaSound (UMelodiaRhythmHitAudioComponent)
4. Fan out to UI/foley once approved

## File Layout
- `Content/Melodia/Audio/Generated/SonicIdentity/` - new variants (do not overwrite until tested)
- `Docs/Audio/MELODIA_SONIC_IDENTITY.md` - this doc
