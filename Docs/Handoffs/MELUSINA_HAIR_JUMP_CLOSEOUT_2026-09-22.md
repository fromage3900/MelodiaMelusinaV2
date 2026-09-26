# Melusina hair + jump/glide closeout — 2026-09-22

Status authority: [`CURRENT_STATE.md`](../../CURRENT_STATE.md) § **CANONICAL MELUSINA HAIR EVALUATION**.
Commit (local, not pushed): `19fa3bab78e69a02eba19ac17cfd4d07919d9000` on `fix/melusina-wings-emissive-veins`.

## What landed this session

### Closed-editor binary
- `BS_GodFileEditor Win64 Development` **PASS** (after renaming a local that shadowed `USkeletalMeshComponent::AnimClass`).
- One editor after the build. No second compile while open.

### Hair (`UMelodiaHairComponent`)
- Constructor: `bCanEverTick = true`, tick group `TG_PrePhysics`.
- Editor-only `SourceMeshComponent` bind when `ABP_Melusina_WaterHair` is already instanced and parent is `MelusinaPresentationMesh` / `CharacterMesh0`. Does not rewrite the relative, does not touch the mannequin, does not run battle redirect. Game/PIE still uses `BeginPlay` → `BindToOwnerMesh()`.
- CDO test: `Melodia.Melusina.Hair.TickDefaults`.

### Jump / glide (`UMelodiaTraversalComponent`)
- Grounded jump fires on **press** (`Jump()`).
- Release calls `StopJumping()` so hold can use `ACharacter::JumpMaxHoldTime` (no next-tick stop; no `MaxWalkSpeed = 0` on this path).
- While falling, held jump requests Glide once. `bAwaitingGlideTap` removed.
- Feel pass is the owner's. Swim / dive / sprint unchanged.

### Proof (runtime unit — tonight's render pawn)
| Field | Value |
|---|---|
| Level | `/Game/Melodia/Levels/Opening/L_MelusinaMorning` |
| Pawn | `BP_MelusinaJRPGCharacter` (`CharacterMesh0` / `SK_Melusina_V2_Body`) |
| Hair | `WaterHairMesh` on `head_x`; relative saved `(0.0001, 144.1994, -15.9001)` roll `-90` |
| Sample A | t `26.2575` s · `A_DEF_hair_bbone_000` delta `0.1618` cm · yaw `-19.8178` |
| Sample B | t `30.3031` s · delta `0.1638` cm · yaw `-2.6483` |
| Still | `Saved/Screenshots/WindowsEditor/HighresScreenshot00107.png` |

Pass = node writing (offset from reference pose). **Not** portfolio-grade flowing hair.

## Honest ceiling

- Silhouette is still **73 two-bone strands** on `SK_Melusina_Hair_Skeleton`. Multi-segment re-rig (3–5 joints/strand) remains the beauty blocker.
- On this reopen the live ABP still reported `bBoneSubdivisionCollisionOnly=true`. The 2026-09-21 relief (`false` in `13dbc182e`) needs a live re-read before claiming those 220 dummies simulate again.
- Scalp-to-`head_x` during that PIE read `13.5` / `17.6` cm while the bind inverse stayed. Treat as unverified bone choice until someone confirms `hair_root` vs `HairExp_Rig` / strand root in the still.
- Portfolio presenter (`BP_MelusinaSwordsman_Presentation` / `L_MelusinaPortfolioCapture`) was **not** the proof target for this closeout.

## Parked (do not redo tonight as hair “fixes”)

- Root-motion re-export + `BS_Melusina_Locomotion_Hybrid` re-place
- Cornea re-weight; finger-controller decision; hat/lash/shirt re-export
- R2 skirt skeleton consolidation (`Portfolio_R2_Skirt` workaround stays)
- Enemy visibility; environment under the beauty camera
- FLIP / Copernicus / PearlWeave / cook / Niagara bytecode
- Owner jump feel pass on the gameplay pawn

## Files in `19fa3bab7`

- `CURRENT_STATE.md`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaHairComponent.cpp`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaHairComponent.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.cpp`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.h`
- `Source/BS_GodFile/MelodiaIntegration/Tests/MelusinaIntegrationTests.cpp`
