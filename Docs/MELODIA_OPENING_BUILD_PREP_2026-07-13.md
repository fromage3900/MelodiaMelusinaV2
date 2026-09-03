# Melodia Opening Build Prep

**Status:** Ready for editor build after current character-animation ownership is released.

## Source finding

The examined Blender candidates under `G:\MelodiaMelusina\MelusinasBedroom\` are not an
importable bedroom set. `melusinashouseassets4/5/6.blend` and the `separate` variants
contain only a default cube, camera, and light as scene objects. Do not bulk-import them.
The read-only audit tool is `Tools/audit_melusina_bedroom_blend.py`; its report writes to
`Saved/Audit/melusina_bedroom_blend_audit.json`.

## Use existing Unreal assets first

| Opening role | Existing candidate | Build decision |
|---|---|---|
| Dreamstate bridge | `/Game/Melodia/_PROJECT/MelusinasHouse/SM_venetianbridge` | Use for the first bridge blockout. |
| Bedroom shell | `SM_room1`, `SM_room2`, `SM_corridor` | Compose a one-room sanctuary; do not author a full house. |
| Wall framing | `SM_wallhi`, `SM_wallmid`, `SM_wallshort`, curved-wall variants | Use only to close silhouettes/camera angles. |
| Window / atmosphere | existing wall/lancet assets, Starry Night sky materials | One intentional dream-facing opening. |
| Desk / lamp | MagiciansLibrary `SM_Desk*`, `SM_Wall_Lamp*` | Optional secondary storytelling props. |
| Bed / save point | no confirmed bed mesh | Use a temporary readable proxy, then replace with authored bed asset. |
| Sir Melodious perch | no confirmed perch mesh | Use a small custom/proxy perch until the companion import determines his scale. |

## Editor build order

1. Create `L_Melodia_Dreamstate` with bridge, start/end triggers, sky, and safe collision.
2. Create `L_MelusinaMorning` with one room, bed proxy, empty perch, player start, and
   fixed wake-up camera.
3. Add the deterministic Dreamstate -> bedroom transition and skip/input recovery path.
4. Apply Clear and Strain visual/audio presets; do not add complex PCG or combat to either
   level yet.
5. When Sir Melodious is imported, replace perch proxy, place him in the reunion beat, and
   validate scale/follow/visibility.
6. Only after these maps are stable, connect the bedroom exit to the later garden/encounter
   chapter and reuse the proven `ZenForestTest` battle contract.

## Do not do in this pass

- Do not modify `BP_Melusina`, her AnimBP, or retarget assets while that lane is owned.
- Do not turn the bedroom into a World Partition or PCG-heavy level.
- Do not move the combat smoke loop out of `ZenForestTest` before a full PIE handoff.
- Do not import placeholder Blender scenes as production content.
