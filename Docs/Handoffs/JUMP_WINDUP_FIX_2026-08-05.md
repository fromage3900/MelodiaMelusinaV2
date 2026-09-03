# Jump wind-up fix — code landed, needs a closed-editor build

## The problem, stated precisely

Melusina's jump anticipation looked skipped. It was not missing and not an animation bug.

`A_Melusina_JumpStart_Mocap_RootX` **exists** (0.75 s at `rate_scale` 1.9 → ~0.395 s effective), sits
in a dedicated `JumpStart` state, and the state machine is built correctly — 0.2 s crossfades, and
`JumpStart → Airborne` is time-remaining-based so the clip is *allowed* to finish.

The cause was input timing. `MelodiaSmokeCharacter.cpp`, `OnJumpStarted()`:

```cpp
bJumpHeld = true;
TimeSinceJumpPressed = 0.0f;
Jump();                 // <- launches on the SAME tick as the input
```

`Jump()` sets `bPressedJump`; `UCharacterMovementComponent` consumes it that tick, applies
`JumpZVelocity 620` and enters Falling. The capsule is airborne before a single grounded frame of the
anticipation can play, so the clip plays *in the air* instead of as a wind-up.

**No Blender work is needed.** The clip is authored and wired.

## Part 1 — C++ (done, unbuilt)

`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSmokeCharacter.{h,cpp}`

- `OnJumpStarted()` no longer launches. A **grounded** press starts a wind-up; airborne presses fall
  through untouched so glide entry and the buffered-jump path keep their current timing.
- `Tick` resolves the wind-up after `JumpWindupTime`, then calls `Jump()`.
- Leaving the ground by any other means during the window (moving platform, knockback, ledge)
  **cancels** it, so the flag cannot stick and strand the AnimBP in the anticipation state.
- Releasing during the wind-up calls `StopJumping()` immediately after the deferred `Jump()` —
  without this a tap would always produce a full-height jump, silently removing variable jump height.

New API:

| Member | Purpose |
|---|---|
| `bool IsJumpWindingUp()` — `BlueprintPure` | drives the AnimBP transition, see Part 2 |
| `float JumpWindupTime` — `EditAnywhere`, default **0.12 s**, clamped 0–0.5 | 0 restores the old behaviour exactly |

Tune `JumpWindupTime` to the **liftoff frame** of the clip, not its full length — the clip is ~0.395 s
effective and using all of it will feel sluggish. 0.12 s is a starting point, not a measured value.

## Part 2 — AnimBP (NOT done, needs the build first)

`ABP_Melusina_Current`, state machine `MelusinaLocomotion`.

The `Idle → JumpStart` transition is currently driven by `bRuntimeIsInAir`. **That alone can never
show a grounded wind-up** — an in-air check only becomes true *after* liftoff, which is the whole bug.
Deferring the launch without changing this just makes the anticipation start later.

Change the rule to:

```
IsJumpWindingUp() || bRuntimeIsInAir
```

- wind-up begins → `IsJumpWindingUp()` true → enters `JumpStart` **while grounded** ✔
- launch fires → wind-up false, in-air true → stays in `JumpStart` until the existing
  time-remaining transition hands off to `Airborne` ✔

`IsJumpWindingUp()` is `BlueprintPure`, so it is reachable via Property Access like the existing bool.

⚠️ Confirm which AnimBP is actually assigned. `ABP_Melusina`,
`ABP_Melusina_Current_BACKUP_20260729` and `_Archive/ABP_Melusina` all exist; `_Current` is the live
one but this was not verified against the character Blueprint.

## Build requirement

**Both changes are reflected types** (`UFUNCTION`/`UPROPERTY`), so UHT must regenerate. Live Coding
**cannot** register these — it only handles function bodies. This needs a **closed-editor build**.

Two `UnrealEditor.exe` instances were running when the code landed, so nothing was compiled or
verified. **The code is unbuilt and untested.**

## Verification, once built

1. PIE, stand still, tap jump. The anticipation should play **with the character still on the
   ground**, then launch.
2. Set `JumpWindupTime = 0` → behaviour must be byte-identical to before the change. This is the
   cleanest proof the fix is opt-in and regression-free.
3. **Tap vs hold** must still differ in height — that is the `StopJumping()` guard working.
4. Jump *onto* a moving platform, and take knockback mid-wind-up: the character must never get stuck
   in the anticipation pose.
5. Glide still entered by holding through the apex — the airborne path was deliberately untouched.

## Known gap, deliberately not changed

The **buffered jump** on landing (`Landed()`, the `TimeSinceJumpPressed <= JumpBufferTime` branch)
still calls `Jump()` immediately with no wind-up. That is intentional: input buffering exists to feel
instant, and adding 0.12 s there would defeat it. The consequence is that a buffered jump shows no
anticipation. If that reads badly on camera, route it through the wind-up too — but expect the jump
to feel less responsive.

## Related, from the same investigation

`UMelodiaTraversalComponent` (`Source/BS_GodFile/MelodiaIntegration/`) **already implements this
pattern** — `BeginJumpWindup()` with a deferred `Jump()` on release, plus its own
`IsJumpWindingUp()`. It is on a legacy, non-Enhanced-Input binding and is not what drives Melusina.
Worth a later decision: unify on one, rather than keeping two wind-up implementations.
