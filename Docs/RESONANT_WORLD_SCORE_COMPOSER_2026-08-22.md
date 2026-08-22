# Resonant World Score Composer — 2026-08-22

The asset constellation answers “which existing things belong here?” The score
composer answers “what happens here, musically, when Melusina arrives?”

`Content/Python/resonant_world_score.py` produces a deterministic 16-beat
phrase for one `(seed, movement, chunk, archetype)` tuple. Each score contains:

- an eight-beat call and eight-beat response;
- four music-clock stages: Invocation, Unfolding, Threshold, Release;
- a seam-safe west-to-east route whose endpoints reuse the generator's shared
  chunk anchors;
- pitch, scale degree, energy, gesture, and world action per event;
- existing music, material, ornament, VFX, and wardrobe references per event;
- a replay key and sparse-edit identity without writing save state.

The six authored grammars are deliberately different:

| World verb | Grammar | Magical behavior |
|---|---|---|
| Bloom | `petal_fan` | flowers answer a return to tonic |
| Weave | `constellation_hem` | a sky-thread becomes a route |
| Conduct | `tide_chord` | water carries a chord to memory |
| Compose | `cadence_stair` | placed tone voxels rise into architecture |
| Drift | `ribbon_mirage` | the route answers the player's silhouette |
| Resolve | `beautiful_dissonance` | tension becomes a survivable portal |

## Why this is the right Infinity Nikki-adjacent translation

The useful pattern is not copying a costume or a quest. It is the relationship
between a styled appearance, a readable ability/world verb, and a scene-preview
moment. [Infinity Nikki's official ability-design notes](https://infinitynikki.infoldgames.com/en/news/155)
describe abilities as being designed from an outfit's theme and movement style;
its [current official preview notes](https://infinitynikki.infoldgames.com/en/news/560)
also expose scene preview, effect toggles, imported styling schemes, and
ability-outfit styling. Melodia translates that relationship into
“voicing” an authored musical movement: the wardrobe changes the color and
interpretation of a route, while the canonical form/traversal authority still
owns capability.

## Quantum boundary

The score inherits the existing two-candidate movement selector. It does not
use quantum logic to choose an individual voxel, grade input, drive traversal,
or grant rewards. Q# remains an optional simulator backend with a classical
baseline and a persisted trace. Microsoft's Q# documentation supports the
separation between writing/simulating/estimating a quantum program and using it
in an application; [the Q# overview](https://learn.microsoft.com/en-us/azure/quantum/qsharp-overview)
and [resource-estimator documentation](https://learn.microsoft.com/en-us/azure/quantum/overview-resources-estimator)
reinforce that
hardware/error-correction costs are a separate architectural concern. Research
on quantum map generation is treated as an exploration input, not as evidence
of runtime quantum advantage.

## Commands

```powershell
$env:PYTHONPATH = 'Content/Python'
python Content/Python/resonant_world_score.py `
  --seed 3900 --movement petal_cantata --chunk-x 0 --chunk-y 0 `
  --archetype SakuraDreamer

python Content/Python/resonant_world_score.py `
  --seed 3900 --all-movements
```

MCP callers use `melodia_resonant_world_get_score`. It is a read-only
`melodia.resonant_world.score.v1` surface. A successful score compile is still
not PIE proof; fresh Echo/PIE evidence must identify the score ID, constellation
ID, loaded proof map, beat-stage events, route/traversal request, and captured
frames/logs before a runtime gate is recorded.

## Lookdev handoff order

The first camera/material review should use the existing asset constellation for
`petal_cantata` and `petal_fan`, with Sakura terrain and rose-window/blossom
voicing. The next review should use `liquid_cathedral` and its water profile,
then `cadence_cathedral` with ebony/ivory piano references. The composer reports
the exact selected references in every event so webfront/lookdev can reject
missing or placeholder assets rather than guessing.

Requested clean capture targets (not present in the current checkout yet):

- `breakdown_niagara_sakura_ambience_1920x1080.png`
- `pcg_zen_shrine_axis_route_proof_1920x1080.png`
- `breakdown_baroque_escher_ornament_1920x1080.png`
- `materials_nikki_surface_polish_2048x2048.png`

These are deliverables for a healthy UE/Blender capture lane, not filenames to
fake in the webfront. Each capture must carry an absolute source path, selected
asset references, material-instance changes, lighting state, and a clean
standalone frame with no editor chrome or debug overlays.
