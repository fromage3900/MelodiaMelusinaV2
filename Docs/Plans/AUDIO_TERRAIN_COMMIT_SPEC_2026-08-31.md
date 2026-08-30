# Audio Terrain Pipeline — Commit Spec
**Date:** 2026-08-31  
**Source:** git status + file inspection  
**Verdict:** COMMIT — both files are clearly authored (not scratch), never previously committed.

## Files

| File | Lines | Description |
|------|-------|-------------|
| `Docs/Production/BLENDER52_AUDIO_TERRAIN_PIPELINE.md` | 88 | Blender 5.2 audio terrain pipeline guide |
| `deploy/surreal_arch/melodia_gn/audio_terrain.py` | 230 | GN builder implementation (3 builders, presets, handoff) |

## Proposed Commands

```bash
git add Docs/Production/BLENDER52_AUDIO_TERRAIN_PIPELINE.md deploy/surreal_arch/melodia_gn/audio_terrain.py
git commit -m "docs(pipeline): add Blender5 audio terrain pipeline guide + GN script"
```

## Notes

- `audio_terrain.py` is part of the `deploy/surreal_arch/melodia_gn` module — tracked in GN builder family.
- Pipeline uses Blender 5.2 `Sample Sound Frequencies` node — offline authoring lane; Unreal is runtime rhythm authority.
- Batch profiles: preview, region, continent. Handoff via `.audio_terrain_handoff.json`.