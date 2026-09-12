# Sir Melodious Import Forensics — 2026-07-13

## What was imported

The prepared import route was run using
`F:/_FromG_Archive/cinnbunrender/sirmelodiousalmostdone07.fbx` and the painted
texture sets in `G:/sirmelo`.

- Eight separate skeletal-mesh assets were created under
  `/Game/Melodia/Characters/SirMelodious`.
- Both painted texture sets and two Toon master material instances were created
  under that same character folder.
- The importer was corrected to treat the FBX as a multi-mesh asset rather
  than selecting a material from the import-result list as the primary mesh.

## Critical rig finding

The inspected FBX contains **eight mesh objects, no Armature, and no mesh
parenting**. The two canonical Blender sources inspected for comparison
(`G:/MelodiaMelusina/MelusinaFinalRig/sirmelodious.blend` and
`sirmelodious1.blend`) likewise expose no Armature object. Therefore the
current source set does not prove a gameplay-ready rig or animation source.

This prevents a truthful implementation of switching/flying or animated
companion behavior. It is still suitable for a temporary static/cutscene
presentation once the merged source or correct rig is identified.

## Current save constraint

A live Unreal Editor session held the imported assets open while the commandlet
was assigning material instances. The commandlet was stopped rather than
forcing writes against that session. Run
`Content/Python/import_sirmelodious.py` again only after that editor instance
has released the assets; it is now multi-mesh-aware and will resume from the
existing import.

## Required decision

Provide the actual armature-bearing FBX/Blend if animated companion behavior
is intended for this slice. If the current meshes are approved as a static
introduction, the next task is to assemble their components into a temporary
`BP_SirMelodious` and replace the bedroom perch proxy.
