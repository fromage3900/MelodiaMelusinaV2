# Quaternius Animation Source Provenance

**Status:** Source motion library staged for Cascadeur retargeting.
**Do not treat this file as proof that Melusina has imported animation yet.**

## Source

- Publisher: Quaternius
- Pack: Universal Animation Library, Standard
- Product page: `https://quaternius.itch.io/universal-animation-library`
- Publisher page: `https://quaternius.com/packs/universalanimationlibrary.html`
- Download route: itch.io free Standard download, name-your-own-price set to zero
- Downloaded archive SHA-256: `CC73FC4E495B82958207316596317A3F40B9FA38065BDE1027937452DA537724`
- Staged source file: `Imports/Animations/Cascadeur/Source/Quaternius/UAL1_Standard.fbx`
- Staged FBX SHA-256: `21B32D912DA3CB93426D974FB945E86F5B2E86970ACD2CE89905E0FBF9F1DCC2`
- Staged Melusina target: `Imports/Animations/Cascadeur/Target/SK_Melusina_Cascadeur_Target.fbx`
- Target FBX SHA-256: `5D32258BAF505513532105F592EC8DC4E10B37D48396F9DAF9927D7343DC7C93`
- Target export: live `/Game/Melodia/Characters/Melusina/SK_Melusina` via Monolith `mesh_query:export_mesh`

## License

The archive includes `License.txt` and `README.txt`, both identifying:

`CC0 1.0 Universal (CC0 1.0) Public Domain Dedication`

License URL: `https://creativecommons.org/publicdomain/zero/1.0/`

The publisher page also states that the assets are free for personal,
educational, and commercial projects. CC0 permits copying, modification,
distribution, and commercial use, subject to the limitations described by the
license deed. Preserve this provenance record with the project.

## Contents Used

`UAL1_Standard.fbx` is the in-place/root-motion-disabled source variant. The
pack contains a universal humanoid rig and a broad set of locomotion, combat,
emote, sitting, swimming, crawling, and death motions. The Standard download
is the free subset; Pro and Source tiers are not required for this pipeline.

A read-only Blender inventory confirmed the FBX is 30 fps and exposes named
takes including `Idle_Loop`, `Walk_Formal_Loop`, `Jog_Fwd_Loop`, `Sprint_Loop`,
`Jump_Start`, `Jump_Loop`, `Jump_Land`, `Sword_Attack`, `Sword_Idle`,
`Dance_Loop`, `Death01`, `Hit_Chest`, `Hit_Head`, `Sitting_Idle_Loop`,
`Spell_Simple_Shoot`, and `Swim_Fwd_Loop`.

## Integration Decision

This FBX is **not** in `Imports/Animations/Cascadeur/Inbox/` and must not be
passed to `import_cascadeur_animation.py` directly. It does not use
`SK_Melusina_Skeleton`.

Use it as a Cascadeur source rig:

1. Import the Quaternius FBX as the source character.
2. Import the current body export for `SK_Melusina_Skeleton` as the target.
3. Generate AutoPosing rigs for both characters.
4. Retarget only the selected source clip to Melusina.
5. Polish contacts, silhouette, and Melusina's bard identity on the target rig.
6. Export the target animation from Cascadeur as a new body-only FBX.
7. Put the target FBX and a new sidecar manifest in `Inbox/`.
8. Run the manifest validator, then the direct-skeleton Unreal importer.

No Quaternius skeleton, mesh, hair, skirt, gameplay notify, or root-motion
setting is allowed to replace Melusina's production contract.

## License Limits

CC0 does not imply endorsement, trademark rights, or a warranty from Creative
Commons or Quaternius. Do not market the imported motion as authored by
Quaternius or imply endorsement. This project uses the motion as modified
source material and retains this record for attribution and audit purposes.
