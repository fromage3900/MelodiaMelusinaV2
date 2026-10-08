# Sir Melodious: Kawaii Physics spec (tie + crest), 2026-10-03

The plan is written by New Bot. Bone data comes from the live `SK_SirMelodious_Rigged_Skeleton`, which has 128 bones, read on 10/3.

## UPDATE 2:11 PM: tie = existing `spline_01_x`..`spline_03_x` (Study confirmed, 344-vert tie mesh)
Root `c_spline_root_x`, parented to `c_traj`. **Chain direction issue:** in the UE ref pose the chain runs bottom→top. `spline_01_x` is at z5.4 (bottom tip), and `spline_03_x` is at z17.8 (knot). Kawaii pins the root and simulates toward the children, so as-is it would pin the hanging tip and swing the knot. Fix: Study reverses the chain in Blender so `spline_01` sits at the knot under `spine_02_x`/`neck_x` and `spline_03` is the tip, then it ships in Brennan's crest re-import. Until then there's no usable tie sim. Values in KP_Tie below still apply, with RootBone = the knot bone.

## (Superseded) The skeleton has no tie bones yet
The current UE skeleton has no tie chain. Here is what's there, in Sir's 1.10 cm export scale:
- `c_kilt_master_x` → `kilt_0{1..6}_dt_{l,r}` + `c_kilt_0{1..6}_01_{l,r}`. These form a ring of 12 one-link pieces at the neck (z≈20.6, head_x z≈24.8). It's likely the **collar** ruff, so it should be the Vellum/cloth target, not the tie.
- `c_spline_root_x` → `spline_01_x` (z5.4) → `spline_02_x` (z11.5) → `spline_03_x` (z17.8). This is a 3-link ARP spline-IK chain on +Y. It's probably the cloak back or tail, so Study should confirm in Blender.

**Ask (Blender, ARP):** add a 4-bone tie chain under `spine_02_x` or `neck_x`, at the knot on the chest front. Name them `tie_01`..`tie_04`, as deform bones with no `c_` prefix, and make each link roughly equal length. Then skin the tie mesh to them, and export with the crest bones in **one** mesh re-import. Use the existing skeleton, and tick Import Morph Targets for `Crest_Raise`.

## AnimGraph placement (ABP_SirMelodious)
Order: state machine `FlightLocomotion` → KawaiiPhysics (Tie) → KawaiiPhysics (Crest) → Output Pose.
Put the nodes after the locomotion blend so they react to the flap bob and lean, and to the speed blend.

## Node: KP_Tie
| Field | Value |
|---|---|
| RootBone | `tie_01` (dummy tip bone ON, length ≈ last link) |
| Damping | 0.15 |
| Stiffness | 0.05 (tie should swing) |
| WorldDampingLocation | 0.65 (stops it streaming behind at 800 cruise) |
| WorldDampingRotation | 0.5 |
| Radius | 0.4 |
| LimitAngle | 55 |
| Gravity | (0,0,-980) * 0.6, i.e. a lighter, more storybook drop |
| Planar limit | floor off. Spherical limits on `spine_02_x` (r≈4.5) and `neck_x` (r≈2.5) so it doesn't pass through the chest |
| Curves | DampingCurve rising 0.1→0.3 from root to tip, StiffnessCurve 0.2→0.02 |

## Node: KP_Crest
| Field | Value |
|---|---|
| RootBone | `crest_01` (chain crest_01..04 up the clef centre, parent `head.x`/`head_x`) |
| ExcludeBones | none. crest_01 is pinned by the root |
| Damping | 0.25 |
| Stiffness | 0.35 (should spring back so the clef stays readable) |
| WorldDampingLocation | 0.8 |
| WorldDampingRotation | 0.7 |
| Radius | 0.3 |
| LimitAngle | 25 (the clef silhouette must survive any pose) |
| Gravity | (0,0,-980) * 0.25 |
| Curves | StiffnessCurve 0.6→0.25 root→tip so the tip lags one beat-ish |

## Beat hooks (cymatics)
- Add a float `BeatPulse` (0–1, sourced from the clip's `beat` curve that Study is authoring, or from the rhythm manager).
- Drive `KP_Crest` with an extra external force (`KawaiiPhysics_ExternalForce_Simple`), +Z × BeatPulse × 150, so the crest flicks up on each downstroke and Perfect.
- The same `BeatPulse` feeds the `Crest_Raise` morph and the crest MI emissive (warm white on the beat, gold #C9A86A on a Perfect, synced with the HUD reticle).

## Collar and cloak
The collar ring (`kilt_*`) and the cloak are Vellum targets. Houdini's license is down, so Study is doing a Blender cloth bake to bones first. If that bake doesn't land by 3 PM, fall back to a KP_Collar node: RootBone `c_kilt_master_x`, Damping 0.3, Stiffness 0.4, LimitAngle 20, and the 12 children run as short one-link chains.

## UE steps once 💧 frees the editor (New Bot)
1. Brennan does the mesh re-import with crest and tie, then saves.
2. Add KP_Tie and KP_Crest to the AnimGraph with the values above, then compile.
3. Do a PIE check at Speed 0/450/800 together with 💧's 225/625 blend capture.
4. Ctrl+S: Brennan saves `ABP_SirMelodious`. It goes on `lane/sir-melodious-flight`.

