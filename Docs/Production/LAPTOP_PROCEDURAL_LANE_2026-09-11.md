# ASUS Laptop Workstation — Durable DCC Contract

**Status:** CANONICAL LAPTOP / DCC WORKSTATION CONTRACT  
**Workstation branch:** `collab/laptop/longterm`  
**Canonical runtime authority:** `main`  
**Branch policy:** [`BRANCH_WORKSTATION_POLICY.md`](BRANCH_WORKSTATION_POLICY.md)

This document defines what the ASUS Nitro lane is for, how its work is promoted, and what authority it does **not** have.

**For current laptop tasks, priorities, or experiments, read `CURRENT_STATE.md`.** This file must not maintain a parallel execution queue.

> The laptop is a production source lane, not a second game/runtime authority. `main` remains canonical for Unreal/runtime/capstone truth. Promote useful DCC work deliberately; never wholesale-merge workstation or recovery history over `main`.

---

## 1. Lane purpose

Use the ASUS Nitro for:

- Blender 5.2 LTS Geometry Nodes authoring;
- procedural asset and ecology prototypes;
- Blender Python automation for proven authoring tasks;
- audio-reactive geometry experiments;
- lightweight asset / texture experimentation;
- bounded evaluation of lightweight DCC tools such as ArmorPaint;
- on-the-go DCC iteration while Humber/home-PC lanes handle Unreal, heavy baking, builds, and runtime validation.

Do **not** move core UE gameplay, save, combat, quest, UI authority, or canonical runtime state into this lane.

---

## 2. Workstation / Git contract

Preserved workstation branch:

```text
collab/laptop/longterm
```

Rules:

- divergence from `main` is not automatically a defect;
- never auto-delete the branch as stale;
- never wholesale-merge it over `main`;
- compare it to `main` before promotion;
- move only named, reviewed DCC artifacts / utilities through a scoped promotion branch or PR;
- `main` remains runtime truth.

### Sync before work / handoff

```powershell
.\deploy\sync_workstation.ps1
```

Optional lane hydration:

```powershell
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile House
```

Full workstation sync contract: [`TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md`](TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md).

A workstation is not cleanly handed off while the report says `dirty`, `ahead`, `behind`, `diverged`, or `lfs-error`.

---

## 3. Blender baseline

Use **Blender 5.2 LTS** as the preferred baseline for new laptop procedural-authoring work unless an established production `.blend` requires an older version.

Before upgrading an established `.blend`, preserve a known-good copy and verify custom scripts / add-ons.

The durable rule is not to chase Blender features for their own sake. A Blender/GN capability is worth adopting when it creates a reusable, art-directable production result faster or more safely than the current alternative.

---

## 4. Audio-reactive Geometry Nodes contract

Blender audio sampling may be used as a **procedural authoring input**, not as a gameplay beat clock or rhythm authority.

Preferred proof shape:

```text
Melodia audio / stem
  -> authored frequency sampling
  -> a small number of readable control bands
  -> GN fields
  -> geometry / instances / motion
  -> baked/exported DCC result when useful
```

A useful experiment should produce:

- a reusable `.blend` source;
- distinct, art-directed responses rather than generic equalizer motion;
- exposed controls that make artistic sense;
- evidence of the result;
- an explicit decision to promote, park, or reject.

If a GN audio-reactive experiment does not provide a production advantage over Houdini, UE PCG, materials, or authored animation, park it rather than growing a framework around it.

---

## 5. Reusable GN context / Geometry Bundles

Reusable GN context may carry values such as:

```text
Resonance
Density
Scale
Seed
AssetFamily
CymaticStrength
MaterialVariant
```

These values are **Blender authoring state only** until converted into explicit exportable geometry, named attributes, textures, or documented metadata.

```text
GN authoring context
  -> explicit exportable attributes
  -> UE 5.8 PCG / material consumers
```

Do not make UE depend on opaque Blender-only bundle state.

---

## 6. Blender Python automation

Use Blender Python where it saves real production time:

- set exposed GN modifier inputs;
- set seeds / resonance / asset-family parameters;
- generate controlled variants;
- run validation checks;
- batch naming / export preparation;
- capture small evidence sets.

Preferred pattern:

```text
Python
  -> configure existing authored system
  -> generate one controlled variant
  -> validate
  -> export / capture
```

Do not build a generalized automation framework before one real Melodia asset benefits from it.

---

## 7. Lightweight texture-tool evaluation

ArmorPaint or another lightweight texture tool may be evaluated as an **auxiliary laptop option**, not presumed to replace Substance Painter / Sampler.

A valid one-asset benchmark is:

```text
open/import
-> bake
-> paint
-> masks/layers
-> export PBR maps
-> import into UE 5.8
-> inspect material result
```

Evaluate stability, bake quality, layer/mask ergonomics, speed, export consistency, packed-map flexibility, UE round-trip friction, and actual advantage over the existing Substance workflow.

End every evaluation with one durable decision:

- **ADOPT AUXILIARY** — genuinely useful for lightweight laptop painting;
- **PARK** — works but does not beat the existing workflow;
- **REJECT** — maintenance/friction is not worth it.

Do not migrate existing Substance assets merely because another tool is cheaper or lighter.

---

## 8. Terrain / scatter tools

Gaea, World Creator, Geo-Scatter, or similar tools are optional authoring utilities, not authorities.

Use them only where a real Melodia task benefits. Final Unreal environment population remains owned by the established UE/PCG/Houdini/content pipeline.

Tool evaluation belongs in research or the active task context; this contract changes only when a tool earns a durable production role.

---

## 9. Promotion contract — laptop -> Unreal

```text
visual / procedural idea
  -> collab/laptop/longterm
  -> Blender / GN / texture source
  -> validate locally
  -> identify exact promotable artifact
  -> scoped promotion branch / PR
  -> UE import
  -> PCG / material / runtime validation
  -> evidence
  -> main
```

Promotable artifacts may include selected `.blend` source with intentional provenance, FBX/glTF/Alembic/textures, explicit point/mesh attributes, masks/heightfields/cymatic textures, Python utilities with proven use, and evidence captures.

Never move unrelated laptop history merely to promote one useful artifact.

---

## 10. Authority boundaries

The laptop lane must not create replacements for established owners:

- UE gameplay/runtime truth -> `main`;
- UE PCG -> final Unreal procedural assembly / environment population;
- Houdini -> topology/spatial/variant procedural work where it is stronger;
- Nikki Cymatics -> approved Sheep material path;
- Substance -> core texture-authoring stack until a real benchmark changes that decision;
- TouchDesigner -> visual/performance instrument, never gameplay truth;
- Blender audio sampling -> procedural authoring input, not gameplay timing authority.

---

## 11. Recovery / historical work

Old laptop recovery branches are evidence/salvage sources, not task batons.

`recovery/laptop-main-20260904` contains historical house/GN/Blender work and broad old cleanup. Do **not** merge it wholesale; extract only named reviewed work if something unique is still needed.

Closed/superseded laptop reconciliation PRs and branches remain historical unless a specific missing artifact is proven unique.

Canonical recovered house baseline already on `main`:

```text
RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend
```

Do not resurrect recovery branches merely to obtain work already promoted.

---

## 12. Agent rule

Before merge, deletion, salvage, or declaring laptop work absent, establish:

- branch class;
- comparison to current `main`;
- unique intended work;
- destination / promotion path;
- binary / LFS implications;
- evidence that nothing important will be lost.

If those facts are unknown, leave the branch alone and investigate first.

Current assignments and priorities belong only in `CURRENT_STATE.md`.
