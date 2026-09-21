# Expert review — Shorewake proxy scene (2026-09-17)

## The big catch (fixed): 100x unit mismatch
FBX set authored in cm, imported as m. Figure spanned z -14..184 m; cameras sat inside her shin.
Fix: MelusinaRig object scale 0.01. Figure now z 0.53..2.17 m, seated on bench top 0.68. Lesson: always print world bbox after FBX import, never trust viewport thumbnails.

## Deform integrity: PASS
4 garments, 0 orphan vertex groups, 0 bad indices. Rebind of 3 garments to MelusinaRig verified. 17 bones keyed frame 1.

## Fixed in same pass
- Pose keyed (was unkeyed, would not survive edits).
- Sun angled 50/30 (was flat top-down default) for figure modeling.
- Bench given hull material (was default gray).

## Still owed (non-blocking for panels)
- Render filepath still /tmp default: final VSE assembly script must set absolute output.
- Proxy resolution 50%: final panels at 100%.
- Skirt 24k polys (densest mesh): fine for stills, watch render time x17.
- Sitting pose is rigid FK approx: thighs -85, shins +85, arms reaching. Eye-check fixed_ stills; refine elbows/hands toward lyre if needed.
- Lyre prop does not exist yet: add before panels 06-12 (torus + neck proxy is enough at storyboard grade).
- Reef/bell wake states for panels 09-10: emissive keyframes or duplicate lit/unlit banks.
