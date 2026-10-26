# Carillon / LittleGuys — source recovery and safe commit checklist

**Date:** 2026-10-26  
**Purpose:** Recover the owner's pre-existing editable assets safely; **not** generate or import another creature roster.  
**Companion record:** [Carillon family recovery sheet](Creatures/CARILLON_FAMILY_RECOVERY.md).

## Important: many Unreal files already exist in Git main

Before claiming an asset was never committed, verify the relevant `Content/Staging/HoudiniForge/` package against current Git and the owner's actual UE project. At read time, main contains:
- `Carillon/Creatures/` — four Arch/Awake pairs.
- `Gaudy/` — ChimeSnail, PearlJellybell and Queen Arch/Awake variants v2/v4 and Dingle.
- `LittleGuys/MusicBoxMimic/` — Arch/Awake.
- `Anim/` — nine family folders × ten `.uasset` entries.
- `Enemies/` — seven pre-existing staged Carillon BPs.

These are Git LFS-managed references, **not** proof the editable originals are preserved. Do not create replacement assets merely because FBX/.blend files are missing from main.

## Tomorrow: scoped local read-only inventory (Windows PowerShell)

Use your existing authorized checkout and do **not** assume a PC drive path:

```powershell
Set-Location <YOUR_MELODIA_REPO_ROOT>
git branch --show-current
git status --short
git lfs ls-files | Select-String 'HoudiniForge'
git ls-files 'Content/Staging/HoudiniForge/*'
```

Search the known gitignored local lane first, then your personal Blender/Houdini working folders:

```powershell
$root = 'Saved/Staging/GrokPrep/houdini_forge'
if (Test-Path $root) {
  Get-ChildItem -LiteralPath $root -Recurse -File |
    Where-Object { $_.Extension -in '.blend','.blend1','.hip','.hipnc','.hdalc','.fbx','.obj','.json','.exr','.png','.md' } |
    Select-Object FullName, Length, LastWriteTime |
    Sort-Object FullName
}
```

Focus expected patterns:
- `cutie_gn/carillon/`, `cutie_gn/carillon_v2/`, `cutie_gn/bell_creature/`
- `ue_stage_pack/cutie_v3_ready/`, `ue_stage_pack/lookdev/`, `ue_stage_pack/lookdev/anim/`
- `blessed_hda/carillon/out/`, `blessed_hda/carillon_swarm/`
- `lookdev/gaudy/uvwork_v5/`, `lookdev/gaudy/textures_v4/`
- `Carillon_parts_shared.json`, `SCALE_CHECK.md`, `ANIM_CLIPS.md`, `CONTRACT.md`, `stage_manifest.json`, `RIG_PLAN.md`

**Do not modify, bulk-copy or clean** the source until you have an actual file list and checksum/size notes. `Saved/` is gitignored intentionally; do not `git add -f Saved/...` wholesale.

## Compare one variant at a time

| Source family | Minimum evidence | Primary risk |
|---|---|---|
| Carillon giant bells | latest editable Blender/Houdini source, export manifests, corresponding Arch/Awake FBX | wrong version or stale v1 C4/G4 frame |
| ChimeSnail / PearlJellybell / Queen | owner editable scene, material/UV source, Gaudy v4 texture provenance | overwriting artwork with a stale/garbled rebake |
| MusicBoxMimic | v3 edited scene and two state exports | losing lid/eye difference |
| Hydra | original fifth variant source or deliberate archive decision | silently fabricating a nonexistent UE asset |
| Anim rigs | local `SKM_<Creature>_anim.fbx`, seven takes and skeleton rig maps | animation import / skeleton mismatch |
| Dingle | preserve LOD/rig separately | treating NPC as a hostile enemy by assumption |

For each recovered piece record: working name, absolute local source path privately, file type, size/hash, latest authored file date, screenshot thumbnail, Arch/Awake counterpart, master material, source licence/author, whether the UE package opens, and eventual intended versioned destination. **Never publish private absolute PC paths in a public repo**.

## Safe stage and review

1. Save a recoverable backup of editable originals **before** moving/repackaging anything.
2. Compare against `Docs/HoudiniForge/SOL_HANDOFF.md` and `Docs/HoudiniForge/ENEMY_WIRING_LIVE_2026-10-15.md`; honor saved/unsaved boundaries.
3. Check relevant LFS hydration *selectively* instead of blindly pulling the entire project.
4. Put verified source and its manifest in a narrowly named versioned **source folder agreed with current repo conventions**; use Git LFS for sizable binary art assets and existing hooks. Do not accidentally commit gigabytes of caches, EXRs, test renders or duplicate FBXs.
5. Do not alter running UE editor scenes. Verify one target actor via a controlled single-editor session. In UE check package existence, mesh/material slot fidelity, physics asset, skeleton/socket presence, animation clips, notify FX, blueprint refs, and bounds.
6. Record an exact PIE result or mark **NOT TESTED**. A committed Blueprint is not equivalent to live successful enemy logic.
7. Preserve original source/animation as canonical; any Faraway Mother colour/material retune goes in a **separate non-destructive child lookdev variant** after owner approval.
8. Only after reconciliation should bestiary `SOURCE VERIFIED` / `LIVE PROVEN` labels advance.

## P0/P1 no-scope rule

This recovery is an **asset preservation task**. It does not add new Poitou mandatory encounters, P1 bosses, or compendium runtime screens. The Carillon line historically targeted Sea Above Ocean Cathedral; small pink/lavender LittleGuys are only Faraway Mother visual/region candidates.

## Relevant repo documents

- [HoudiniForge handoff](../HoudiniForge/SOL_HANDOFF.md)
- [2026-10-15 enemy wiring state](../HoudiniForge/ENEMY_WIRING_LIVE_2026-10-15.md)
- [Aeolian inventory](../HoudiniForge/AEOLIAN_INVENTORY_v1.md)
- [Melodia Compendium Bible](../References/Narrative/MELODIA_COMPENDIUM_BIBLE.md)
