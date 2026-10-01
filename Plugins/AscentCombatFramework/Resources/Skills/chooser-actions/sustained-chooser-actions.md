# Sustained Chooser Actions

## Overview

**Sustained Chooser Actions** combine the **Chooser Action system** (weighted random montage selection with filters) with **Sustained Action mechanics** (hold/release input patterns). This enables GAS-predicted charged attacks with animation variety.

## Architecture

### Class Hierarchy

```
UACFAction (Base GAS Ability)
  └─ UACFChooserAction (Deterministic montage selection)
      └─ UACFSustainedChooserAction (Hold/release mechanics)
          └─ UACFArcherySustainedAction (Archery-specific implementation)
```

### Key Features

- ✅ **GAS Client-Side Prediction**: Zero perceived lag for animations
- ✅ **Deterministic Selection**: Client and server select identical montage using GAS prediction key
- ✅ **Instant Visual Feedback**: Client-side montage jumps, bow string release, arrow visuals
- ✅ **Server Authority**: Projectile spawning and damage remain server-controlled
- ✅ **Charge Mechanics**: Hold duration affects projectile velocity/damage
- ✅ **Network Optimized**: Minimal replication, maximum responsiveness

---

## UACFSustainedChooserAction

**Base class** for all sustained chooser actions. Provides hold/release mechanics on top of chooser-based montage selection.

### Properties

```cpp
/** State of the sustained action */
UPROPERTY(BlueprintReadOnly, Category = "ACF")
ESustainedActionState ActionState = ESustainedActionState::ENotStarted;

/** Tag of the action to trigger when released (optional) */
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
FGameplayTag ReleaseActionTag;

/** Priority of release action */
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
EActionPriority ReleaseActionPriority = EActionPriority::EHigh;
```

### Methods

#### `PlayActionSection(FName sectionName)`

Jumps montage to specified section with **instant client-side prediction**.

**Implementation:**
- Client: Jumps section **locally immediately** + sends Server RPC
- Server: Receives RPC and also jumps section
- Result: Zero perceived lag on client

```cpp
void UACFSustainedChooserAction::PlayActionSection(FName sectionName)
{
    // Always jump section locally for instant response
    if (ACharacter* Owner = GetCharacterOwner())
    {
        if (UAnimInstance* AnimInstance = Owner->GetMesh()->GetAnimInstance())
        {
            if (UAnimMontage* ActiveMontage = AnimInstance->GetCurrentActiveMontage())
            {
                AnimInstance->Montage_JumpToSection(sectionName, ActiveMontage);
            }
        }
    }

    // Also send to server to ensure sync
    if (GetCharacterOwner() && GetCharacterOwner()->GetLocalRole() < ROLE_Authority)
    {
        Server_PlayActionSection(sectionName);
    }
}
```

#### `GetActionElapsedTime() const`

Returns time elapsed since action started. Used for charge calculations.

```cpp
float GetActionElapsedTime() const
{
    if (ActionState == ESustainedActionState::EStarted || ActionState == ESustainedActionState::EReleased)
    {
        return GetWorld()->GetTimeSeconds() - startTime;
    }
    return 0.f;
}
```

#### `ReleaseAction()`

Called when input is released. Can trigger a follow-up action via `ReleaseActionTag`.

```cpp
void ReleaseAction()
{
    if (ActionState == ESustainedActionState::EStarted)
    {
        ActionState = ESustainedActionState::EReleased;

        if (ReleaseActionTag.IsValid() && GetActionsManager())
        {
            EndAbility(CurrentSpecHandle, CurrentActorInfo, CurrentActivationInfo, true, false);
            GetActionsManager()->TriggerAction(ReleaseActionTag, ReleaseActionPriority);
        }
    }
}
```

### Lifecycle

1. **OnActionStarted**: Sets `ActionState = EStarted`, starts elapsed time tracking
2. **Hold Phase**: Montage loops, charge builds
3. **Release Event**: Triggers via gameplay event
4. **OnActionEnded**: Resets `ActionState = ENotStarted`

### Important: ActionState Synchronization

**Problem:** `OnActionStarted` only runs on **server** in networked games. Client's `ActionState` can become stale.

**Solution:** Reset `ActionState` in gameplay event handlers (e.g., Nock event) that run on both client and server via AnimNotify.

```cpp
// In child class OnGameplayEventReceived
if (eventTag.MatchesTagExact(NockEventTag))
{
    // Reset ActionState to Started (fixes client state desync)
    ActionState = ESustainedActionState::EStarted;

    // Server-only logic...
}
```

---

## UACFArcherySustainedAction

**Archery-specific implementation** with charge mechanics and bow integration.

### Properties

```cpp
/** Gameplay tag for nock event (default: "Archery.Nock") */
UPROPERTY(EditDefaultsOnly, Category = "ACF|Archery")
FGameplayTag NockEventTag;

/** Gameplay tag for release event (default: "Archery.Release") */
UPROPERTY(EditDefaultsOnly, Category = "ACF|Archery")
FGameplayTag ReleaseEventTag;

/** If true, charge time affects projectile velocity */
UPROPERTY(EditDefaultsOnly, Category = "ACF|Archery")
bool bUseChargeMultiplier = true;

/** Minimum charge multiplier (at 0 seconds) */
UPROPERTY(EditDefaultsOnly, Category = "ACF|Archery")
float MinChargeMultiplier = 0.5f;

/** Maximum charge multiplier (at MaxChargeTime seconds) */
UPROPERTY(EditDefaultsOnly, Category = "ACF|Archery")
float MaxChargeMultiplier = 2.0f;

/** Time to reach max charge (seconds) */
UPROPERTY(EditDefaultsOnly, Category = "ACF|Archery")
float MaxChargeTime = 2.0f;
```

### Charge Calculation

```cpp
float GetChargeMultiplier() const
{
    if (!bUseChargeMultiplier)
    {
        return 1.0f;
    }

    const float elapsedTime = GetActionElapsedTime();
    const float chargePercent = FMath::Clamp(elapsedTime / MaxChargeTime, 0.0f, 1.0f);
    return FMath::Lerp(MinChargeMultiplier, MaxChargeMultiplier, chargePercent);
}
```

### Event Flow

#### Nock Event (AnimNotify in "Default" section)

```cpp
if (eventTag.MatchesTagExact(NockEventTag))
{
    // Reset ActionState to Started (fixes client state desync)
    ActionState = ESustainedActionState::EStarted;

    // Server only: Nock arrow on bow
    if (BowActor && HasAuthority(&CurrentActivationInfo))
    {
        BowActor->NockArrow();
    }
}
```

**Execution:**
- **Both Client & Server**: AnimNotify fires, resets ActionState
- **Server Only**: Nocks arrow, spawns visual on bow
- **Replication**: `NockedArrow` replicates to clients → `OnRep_NockedArrow()` → pulls bow string

#### Release Event (Input release via Blueprint Server RPC)

```cpp
if (eventTag.MatchesTagExact(ReleaseEventTag))
{
    // Prevent double-shooting on server only
    if (ActionState == ESustainedActionState::EReleased && HasAuthority(&CurrentActivationInfo))
    {
        return;
    }

    const float chargeMultiplier = GetChargeMultiplier();

    // SERVER: SHOOT ARROW
    if (BowActor && HasAuthority(&CurrentActivationInfo))
    {
        // Destroy nocked arrow visual
        if (BowActor->GetNockedArrow())
        {
            BowActor->GetNockedArrow()->Destroy();
            BowActor->CancelNockedArrow();
        }

        // Shoot with charge multiplier
        BowActor->ShootArrowSmart(EShootTargetType::WeaponTowardsFocus, chargeMultiplier);
    }

    // BOTH CLIENT & SERVER: INSTANT VISUAL FEEDBACK
    PlayActionSection(FName("End")); // Jump to End section

    if (BowActor)
    {
        // Release bow string animation
        if (UACFBowAnimInstance* BowAnimInst = BowActor->GetBowAnimInstance())
        {
            BowAnimInst->ReleaseString();
        }

        // Hide nocked arrow on client immediately
        if (BowActor->GetNockedArrow() && !HasAuthority(&CurrentActivationInfo))
        {
            BowActor->GetNockedArrow()->SetActorHiddenInGame(true);
            BowActor->CancelNockedArrow();
        }
    }

    ActionState = ESustainedActionState::EReleased;
}
```

**Execution:**
- **Server**: Shoots arrow (spawns projectile), destroys nocked arrow, releases string, jumps to End
- **Client**: Jumps to End section immediately, releases string, hides nocked arrow (instant feedback)
- **No Wait**: Client doesn't wait for server replication → zero perceived lag

---

## Blueprint Setup

### Input Configuration

**Attack Input (Press)**
```
On Pressed:
  └─ Trigger Action: "Actions.Attack.Bow" (Priority: High)
```

**Attack Input (Release)**
```
On Released:
  └─ Custom Event: "ServerReleaseArrow" (Run on Server, Reliable)

ServerReleaseArrow Implementation:
  ├─ Get Ability System Component
  ├─ Trigger Gameplay Event: Tag = "Archery.Release"
  └─ (This runs on server)

Local Execution (also on released):
  ├─ Get Ability System Component
  └─ Trigger Gameplay Event: Tag = "Archery.Release"
      (This runs on client for instant feedback)
```

**Why Both Calls?**
- **Local call**: Client jumps to "End" section immediately (instant animation)
- **Server RPC**: Server receives event, shoots arrow authoritatively

### Montage Structure

```
Montage Sections:
  ├─ Default (draw bow, auto-transition to Loop)
  │   └─ AnimNotify: ANS_NockArrow (triggers "Archery.Nock" event)
  │
  ├─ Loop (hold pose, loops infinitely)
  │
  └─ End (release animation)
```

**Important:**
- ❌ **Don't** put `AN_ReleaseArrow` notify in "End" section (would cause double-shooting)
- ✅ Release is triggered by **input only** via ServerReleaseArrow RPC

### Action Configuration (Blueprint)

```
Class: ACFArcherySustainedAction_BP
Parent: UACFArcherySustainedAction

Properties:
  ├─ ChooserTable: DT_Archery_Draw_Chooser
  ├─ WeightColumnIndex: 0
  ├─ RepeatProbabilityMultiplier: 0.5
  ├─ NockEventTag: "Archery.Nock"
  ├─ ReleaseEventTag: "Archery.Release"
  ├─ MinChargeMultiplier: 0.5
  ├─ MaxChargeMultiplier: 2.0
  └─ MaxChargeTime: 2.0 seconds
```

---

## Network Architecture

### What Runs Where

| Operation | Client | Server | Notes |
|-----------|--------|--------|-------|
| **Montage Selection** | ✅ Predicted | ✅ Predicted | Same GAS prediction key = same montage |
| **Montage Playback** | ✅ Immediate | ✅ Immediate | Starts instantly on both |
| **Montage Section Jump** | ✅ Immediate | ✅ via RPC | Client jumps locally, sends RPC |
| **Bow String Pull** | ✅ Replicated | ✅ Authoritative | NockedArrow replication triggers OnRep |
| **Bow String Release** | ✅ Immediate | ✅ Immediate | Direct BowAnimInstance call |
| **Arrow Visual Hide** | ✅ Immediate | ❌ | SetActorHiddenInGame (local only) |
| **Arrow Spawn/Shoot** | ❌ | ✅ Only | Server authority prevents cheating |
| **Charge Calculation** | ✅ Local | ✅ Local | Both calculate independently |

### Network Flow Diagram

```
CLIENT                          SERVER
──────                          ──────
[Press Input]
  ├─ TriggerAction ────────────────────────────────────> [ActivateAbility]
  ├─ ActivateAbility                                      ├─ Select Montage (Seed: PredictionKey)
  ├─ Select Montage (Seed: PredictionKey)                └─ Play Montage
  └─ Play Montage
                                                          [AnimNotify: Nock]
  [AnimNotify: Nock]                                      ├─ ActionState = EStarted
  ├─ ActionState = EStarted <────────────────────────────┤
  └─ (no bow action)                                      └─ NockArrow() → spawns visual
                                                              └─ NockedArrow replicates ──────> [OnRep_NockedArrow]
  [OnRep_NockedArrow]                                                                          └─ PullString()
  └─ PullString()

[Hold Input]
  └─ Loop section plays
                                                          [Hold Input]
                                                          └─ Loop section plays

[Release Input]
  ├─ TriggerGameplayEvent("Archery.Release") ─────┐
  ├─ ServerReleaseArrow RPC ───────────────────────┼──> [OnGameplayEventReceived]
  └─ [OnGameplayEventReceived]                     │     ├─ Calculate charge
      ├─ Calculate charge                          │     ├─ Shoot arrow (authoritative)
      ├─ PlayActionSection("End") (immediate)      │     ├─ Destroy NockedArrow
      │   └─ Montage jumps to End locally          │     ├─ PlayActionSection("End")
      ├─ ReleaseString() (immediate)               │     │   └─ Send Server RPC
      ├─ Hide NockedArrow (immediate)              │     ├─ ReleaseString()
      └─ ActionState = EReleased                   │     └─ ActionState = EReleased
                                                   └───> [Server_PlayActionSection RPC]
                                                          └─ Montage jumps to End
```

### Key Network Optimizations

1. **Montage Selection**: Uses GAS prediction key as random seed → deterministic → no replication needed
2. **Section Jumps**: Client jumps immediately + RPC → instant feedback, server sync
3. **Bow Visuals**: Client updates immediately via direct calls → no replication lag
4. **Arrow Shooting**: Server-only → prevents cheating

---

## Common Issues & Solutions

### Issue: Client Montage Stuck in Loop

**Symptom:** Montage doesn't jump to "End" section on client.

**Cause:** `PlayActionSection()` only sent Server RPC, didn't jump locally.

**Fix:** Client now jumps section locally before sending RPC (implemented in base class).

### Issue: Bow String Doesn't Release

**Symptom:** Arrow shoots but bow string stays pulled.

**Cause:** Waiting for `NockedArrow` replication to trigger `OnRep_NockedArrow()`.

**Fix:** Client directly calls `BowAnimInst->ReleaseString()` on release event (no waiting).

### Issue: Nocked Arrow Stays Visible After Shot

**Symptom:** Arrow visual remains attached to bow after shooting.

**Cause:** Client waiting for server's `NockedArrow = nullptr` to replicate.

**Fix:** Client immediately hides arrow via `SetActorHiddenInGame()` on release event.

### Issue: ActionState Desync on Client

**Symptom:** Client's `ActionState` stuck at `EReleased`, blocks subsequent shots.

**Cause:** `OnActionStarted()` only runs on server in networked games.

**Fix:** Reset `ActionState = EStarted` in Nock event handler (runs on both via AnimNotify).

### Issue: Double-Shooting on Server

**Symptom:** Two arrows spawn when releasing.

**Cause:** Release event triggered twice (local client call + server RPC).

**Fix:** Early return check: `if (ActionState == EReleased && HasAuthority())`. Client can process multiple times for animation, server shoots once.

---

## Performance Considerations

### Memory
- ❌ No extra replication overhead (uses existing GAS prediction)
- ✅ Minimal state tracking (just `ActionState` + `startTime`)
- ✅ Temporary arrow visuals cleaned up on release

### Network Bandwidth
- ✅ Montage selection: **0 bytes** (deterministic, no replication)
- ✅ Section jumps: **Small RPC** (just section name)
- ✅ Arrow shooting: **Standard projectile replication** (unavoidable)

### CPU
- ✅ Charge calculation: **Trivial** (simple lerp)
- ✅ Client prediction: **No extra cost** (GAS handles it)

---

## Extending the System

### Creating Custom Sustained Chooser Actions

1. **Inherit from `UACFSustainedChooserAction`**

```cpp
UCLASS()
class UMyCustomSustainedAction : public UACFSustainedChooserAction
{
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, Category = "Custom")
    FGameplayTag MyEventTag;

protected:
    virtual void OnGameplayEventReceived_Implementation(const FGameplayTag eventTag) override
    {
        if (eventTag.MatchesTagExact(MyEventTag))
        {
            // Reset state for client sync
            ActionState = ESustainedActionState::EStarted;

            // Your custom logic...
            if (HasAuthority(&CurrentActivationInfo))
            {
                // Server-only authoritative gameplay
            }

            // Client-side instant feedback
            PlayActionSection(FName("CustomSection"));
        }

        Super::OnGameplayEventReceived_Implementation(eventTag);
    }
};
```

2. **Override charge mechanics if needed**

```cpp
virtual float GetCustomChargeValue() const
{
    float elapsed = GetActionElapsedTime();
    // Your custom charge formula
    return FMath::Pow(elapsed / MaxChargeTime, 2.0f); // Exponential charge
}
```

3. **Add custom instant feedback**

```cpp
// In release event handler
if (MyWeapon)
{
    // Client: Instant visual feedback
    if (!HasAuthority(&CurrentActivationInfo))
    {
        MyWeapon->PlayEffectLocally();
    }

    // Server: Authoritative gameplay
    if (HasAuthority(&CurrentActivationInfo))
    {
        MyWeapon->ExecuteAbility();
    }
}
```

---

## Debugging

### Enable Verbose Logging

In `DefaultEngine.ini`:
```ini
[Core.Log]
LogArchery=Verbose
LogACF=Verbose
```

### Key Logs to Watch

```cpp
// Action lifecycle
LogArchery: Warning: ACFArcherySustainedAction::OnActionStarted - ActionState=1, HasAuthority=1

// Release event
LogArchery: Warning: Release event received! ActionState=1, HasAuthority=0

// Arrow shooting
LogArchery: Warning: Shooting arrow! NockedArrow=BP_DY_Arrow_C_0
LogArchery: Warning: Destroyed and cancelled nocked arrow

// Section jump
LogArchery: Warning: Set ActionState to EReleased, jumped to End section
```

### Common Log Patterns

**Good:**
```
Client: Release event received! ActionState=1, HasAuthority=0
Client: Set ActionState to EReleased, jumped to End section
Server: Release event received! ActionState=1, HasAuthority=1
Server: Shooting arrow! NockedArrow=BP_DY_Arrow_C_0
Server: Destroyed and cancelled nocked arrow
```

**Bad (ActionState desync):**
```
Client: Release event received! ActionState=2, HasAuthority=0  ← STUCK AT EReleased!
Client: Already released on server, ignoring event  ← BLOCKED!
```

**Fix:** Add `ActionState = EStarted` in Nock event handler.

---

## References

- [GAS Prediction Documentation](https://github.com/tranek/GASDocumentation#concepts-p)
- [Chooser Actions Guide](./chooser-actions-guide.md)
- [ACF Base Actions](../Source/ActionsSystem/Public/)
- [Archery System](../Source/ArcherySystem/)

---

## Changelog

### v1.0.0 (2025-01-10)
- Initial implementation of `UACFSustainedChooserAction`
- Added `UACFArcherySustainedAction` with charge mechanics
- Fixed client-side montage section jumps
- Fixed ActionState desync on clients
- Added instant visual feedback for bow string and nocked arrow
- Optimized network architecture for zero perceived lag

---

**Author:** Insodimension
**Last Updated:** January 10, 2025
