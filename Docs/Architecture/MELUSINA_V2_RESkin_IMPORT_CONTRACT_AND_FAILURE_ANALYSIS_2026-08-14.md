# Melusina V2 Reskin and Import Contract

## Authority

The authoritative source is the bound v22 stage:

`G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend`

The export pipeline reads that file and never saves it. The isolated export
copy repairs null armature targets, joins separated pieces where required,
preserves source weights and morphs, removes only non-contract groups, and
normalizes weights before writing output.

## Contract proof

- Five pieces: Body, Shirt, Skirt, Boots, Accessories.
- Canonical target: `/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton`.
- Bone count: exactly 465.
- Names: underscore-sanitized semantic contract names.
- Scale: centimetres.
- Used deform groups: zero unmatched after remap.
- Zero-weight vertices: zero in the staged report.
- Body morphs: 120 shape keys preserved in the staged copy.
- Helper drop set: exactly the seven documented IK helpers.
- Source materials are recorded in each sidecar and must map to approved
  Melusina material instances under the existing Materials folder.

The actual mesh group list is validated from Blender vertex assignments; the
Unreal skeleton pointer is not used as proof of mesh usage.

## Observed failure and containment

The required ARP FBX operator is not available in the current headless Blender
session (`no ARP FBX export operator found`). The export tool therefore fails
closed by default. An explicit `--allow-blender-fbx` run produced review-only
staging FBXs and sidecars, but the report marks `promotion_allowed=false` until
an approved ARP export is available.

The shirt contained four weighted ARP hair-control groups. They are not part
of the canonical body contract; they are removed only on the isolated export
copy and the drop is recorded. Skirt/accessory helper groups such as Pin and
SimplyPin are treated the same way when they are weighted but outside the
contract. No source Blender data is modified.

## Unreal gate

`Content/Python/import_melusina_wardrobe_contract.py` imports only skeletal
meshes under `/Game/Melodia/Characters/Melusina/Outfits/V2/`, binds them to the
existing skeleton, preserves morph targets, applies only approved material
instances, and rejects missing sidecar proof, unmatched groups, placeholder
materials, static meshes, or a new skeleton. The original body, current ABP,
hybrid BlendSpace, Quaternius clips, hair runtime, and socket setup remain
rollback assets.

Pawn promotion is deliberately not automatic. It requires all five pieces,
preview/PIE evidence, a healthy Unreal editor, and the ARP export gate.
