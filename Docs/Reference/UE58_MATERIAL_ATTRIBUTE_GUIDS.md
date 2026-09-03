# UE 5.8 Material Attribute GUIDs — harvested, cross-verified

Needed for `Get/SetMaterialAttributes` automation. `AttributeGetTypes` / `AttributeSetTypes`
are `TArray<FGuid>` and are **NOT** reachable from Python (`MaterialAttributeDefinitionMap`
is not exposed; the properties are not reflected on the expression classes). They ARE
writable via Monolith `material_query set_expression_property` — with a fatal caveat below.

Harvested 2026-08-29 from `MF_MooaToonBaseInput.MaterialExpressionSetMaterialAttributes_0`,
whose `AttributeSetTypes` array maps positionally onto its named input pins.

| Attribute | GUID |
|---|---|
| BaseColor | `69B8D33616ED4D499AA497292F050F7A` |
| Metallic | `57C3A1617F064296B00B24A5A496F34C` |
| Specular | `9FDAB39925564CC98CD2D572C12C8FED` |
| Roughness | `D1DD967C4CAD47D39E6346FB08ECF210` |
| Anisotropy | `55E2B4FBC1C54DB29F11875F7231EB1E` |
| EmissiveColor | `B769B54DD08D4440ABC21BA6CD27D0E2` |
| Opacity | `B8F50FBA2A754EC19EF672CFEB27BF51` |
| OpacityMask | `679FFB172BB5422CAD520483166E0C75` |
| AmbientOcclusion | `E8EBD0ADB1654CBEB079C3A8B39B9F15` |
| Normal | `0FA2821A200F4A4AB719B789C1259C64` |
| Tangent | `D5F8E9CFCDC3468DB10E4465596A7BBA` |
| CustomizedUV1 | `C67B093C2A5249AAABC97ADE4A1F49C5` |
| CustomizedUV2 | `85C15B24F3E047CA8585687201AE0F4F` |
| CustomData0 | `9E502E693C8F48FA94645CFD28E5428D` |
| ShadingModel | `D9423FFFD77E4D828FF9CF5E055D1255` |
| WorldPositionOffset | `F905F895D5814314916D24348C40CE9E` |
| Refraction | `D0B0FA0314D74455A851BAC581A0788B` |

**Cross-verified independently** (same GUID found in unrelated assets, which is why this
table is trustworthy rather than guessed):
- EmissiveColor — matches the value produced by the owner's manual Attribute Set Types dropdown
- Normal + WorldPositionOffset — match `MF_Oceanology.MaterialExpressionSetMaterialAttributes_2`
- OpacityMask — matches `MF_TranslucencyShadowToOpacityMask.MaterialExpressionSetMaterialAttributes_0`
- Refraction — matches `MF_Oceanology.MaterialExpressionGetMaterialAttributes_1`

## ⚠ NEVER WRITE AttributeSetTypes **OR** AttributeGetTypes VIA MONOLITH

Three editor kills on 2026-08-29 establishing this. Both arrays are unsafe. No ordering,
no connection state, and no array size makes either write safe.

### AttributeSetTypes — immediate hard crash, every time

```
Assertion failed: (Index >= 0) & (Index < ArrayNum)   Array.h:1339
  <- FMonolithMaterialActions::SetExpressionProperty()  MonolithMaterialActions.cpp:3603

"Array index out of bounds: 2 into an array of size 2"   2 GUIDs, node HAD connections
"Array index out of bounds: 1 into an array of size 1"   1 GUID, FRESH node, NO connections
```

Scale-invariant: writing N GUIDs indexes `Inputs[N]` while `Inputs` still has length N.
Monolith never resizes `Inputs` first. Connections and ordering are irrelevant.

### AttributeGetTypes — SILENT CORRUPTION, crashes later (worse)

The write appears to succeed and `get_expression_details` reads the new value back. It
leaves the node violating an engine invariant, and the asset detonates when anything
LOADS it — including background asset indexing:

```
Assertion failed: Outputs.Num() == AttributeGetTypes.Num() + 1
  MaterialExpressions.cpp:6633
  <- UMonolithIndexSubsystem::ProcessDeepIndexQueue()  MonolithIndexSubsystem.cpp:1567
```

`Outputs` is not resized to match, so `Outputs.Num() != AttributeGetTypes.Num()+1`. A
material saved after such a write is CORRUPT ON DISK and will assert on every load. This
is more dangerous than the Set crash because the write looks like it worked.

**A `set_expression_property` that returns the value you wrote is NOT evidence of success
for these two properties.** Verify by reloading the asset, or do not write them at all.

### The only supported route

Configure both arrays in the material editor UI: select the node, Details panel →
**Attribute Set Types** / **Attribute Get Types** → `+` → pick by name. Then read the GUID
back with `get_expression_details` if you need it elsewhere. Reads are safe; writes are not.

Upstream fixes: resize `Inputs` before indexing (`MonolithMaterialActions.cpp:3603`), and
rebuild `Outputs` after any `AttributeGetTypes` mutation.
