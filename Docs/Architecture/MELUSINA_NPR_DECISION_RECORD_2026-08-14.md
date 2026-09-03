# Melusina NPR Decision Record

## Decision

Use the existing Substrate toon material instances as the production baseline.
The V2 importer maps Blender source material slots to approved Melusina
instances and never creates or edits material masters.

## Deferred alternatives

- **MooaToon:** isolated benchmark only. Adoption requires a measured quality
  or performance improvement that justifies a second shading convention.
- **NextCAS-UE:** isolated cloth/blendshape experiment. It is not a dependency
  of V2 skeletal deformation, outfit import, leader pose, or battle runtime.

## QA gate

Check material visibility and outline behavior on body, shirt, skirt, boots,
and accessories in reference pose and PIE. Reject WorldGrid, placeholder,
V2Test, Marble, or material-master assignments. Dynamic skirt cloth remains off
until deformation and animation compatibility are stable.
