# Material Work Plan & Library Organization

Grounded in a 2026-06-19 survey: **5 "grand" masters, 22 SDF masters, ~117 instances, 11 toon profiles, 13 functions, no dead stubs.** The job now is *organization + finish*, not more sprawl.

## 1. Master hierarchy — the core decision
Right now five "Master_*" materials have overlapping roles. Declare clear lanes and kill redundancy:

| Master | Role | Action |
|--------|------|--------|
| **`M_Master_Toon_Universal`** | **PRIMARY** — every scene (texture⇄procedural hybrid, Nikki, magical-girl, macro/detail, triplanar) | **Canonical.** Finish (rebuild) + MF-refactor. |
| `M_Master_Impressionist_Toon` (+ `_Landscape`) | **Painterly/oil specialist** (distinct LIE brush/impasto look) | Keep as a specialist — *not* redundant. |
| `M_SDF_*` family (22) | **Ornament/architectural procedural** (gothic/baroque kit) | Keep as a family; surface via instances. |
| `M_Master_Toon_Unified` | Earlier universal attempt; texture maps declared but never wired — **superseded by Universal** | **Deprecate** → reparent its instances to Universal. *(confirm first)* |
| `M_Master_SDF_Toon` | Overlaps `M_Toon_SDF` / the SDF family | Audit → merge or deprecate. *(confirm first)* |

**Net target: 1 primary (Universal) + 1 painterly specialist (Impressionist) + 1 SDF family.** That's the lean "one master I reach for, plus two specialists" shape.

## 2. Master-finish sequence (priority order)
1. **Rebuild `M_Master_Toon_Universal`** → applies the committed **macro/detail + magical-girl** (`py setup_master_universal.py`, full path — or I run it headless).
2. **Verify in-editor:** macro variation breaks tiling, detail normal reads close-up, the `MagicalTransform` wipe sweeps hearts/sparkles, no broken pins.
3. **MF-refactor** (now safe post-verify): extract `MF_Nikki`, `MF_Celestial`, `MF_Parallax`, `MF_MacroDetail`, `MF_Magical` — turns the 959-line monolith into composable blocks.
4. **`MPC_Magical`** for the global henshin (one collection param drives every material's `MagicalTransform` together).
5. **Gate `Celestial` off** by default (10 params of scope-creep; specialist, not core).

## 3. Instance organization (~117)
- Reorganize `Instances/Environment/` (76) by theme: `Biomes/`, `Stylized/`, `Magical/`, `Sakura/`.
- Naming cohesion: `MI_<Family>_<Look>`.
- **Reparent** any `M_Master_Toon_Unified` instances → `M_Master_Toon_Universal`, then deprecate Unified.
- Build the sakura set: `py setup_sakura_instances.py` (8 `MI_Sakura_*`, already scripted).

## 4. SDF family disposition (per `TOON_MIGRATION_RUNBOOK.md`)
- **Tier A** (gothic/baroque environment, 16 converted) → **keep**, Substrate-Toon ✅, instance-tune for scenes.
- **Tier B/C** (underwater, math-art, musical/game) → **defer/skip**.

## 5. Cleanup
- **No dead/stub masters found** (survey clean). Skip the deletion pass.
- Only real cleanup: deprecate `Unified` (+ maybe `SDF_Toon`) *after* reparenting instances.

## Do-next (priority)
1. **Rebuild + verify Universal** ← unblocks everything (you run the `py`, or I go headless).
2. **Reparent Unified→Universal instances; deprecate Unified.**
3. **MF-refactor + `MPC_Magical`.**
4. **Sakura material set + scene** (scripts ready).

---
*The library isn't short on materials — it's short on hierarchy. This plan makes Universal the spine, keeps Impressionist + SDF as specialists, and retires the duplicate.*
