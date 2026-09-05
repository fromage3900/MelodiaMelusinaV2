# Melusina House cross-workstation source

This folder is the temporary Git LFS handoff surface for the current canonical Melusina House Blender source while the shared Perforce cutover is not yet available to both workstations.

## Current canonical source

`MelusinasHouse_V7_Base.blend`

- Git LFS tracked + lockable through the repository's `.gitattributes`.
- Only one workstation edits it at a time.
- Lock before editing:
  `git lfs lock RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend`
- Commit and push the handoff branch before switching machines.
- Unlock only after the pushed edit is visible remotely.

Historical house versions remain on `recovery/laptop-main-20260904` and are not part of the everyday sync surface.

When the Perforce shared-server/cutover acceptance gates are complete, this source should move to the canonical Perforce RawArt depot rather than creating a second permanent authority.
