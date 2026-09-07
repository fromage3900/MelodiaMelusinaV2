#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaSharedAuthorityInterfaces.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaTraversalComponent.generated.h"

class ACharacter;
class UCharacterMovementComponent;
class UMaterialInstanceDynamic;
class UMeshComponent;
class UMaterialParameterCollection;
class UMelodiaWaterNiagaraBridgeComponent;
class UMelodiaWaterAudioBridgeComponent;
class UMelodiaWaterUnderwaterPostProcessComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaGlideStateChanged, bool, bIsGliding);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaSwimStateChanged, bool, bIsSwimming);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaDiveStateChanged, bool, bIsDiving);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaFloatValueChanged, float, NewValue);

UENUM(BlueprintType)
enum class EMelodiaTraversalMode : uint8
{
	Grounded UMETA(DisplayName = "Grounded"),
	Glide UMETA(DisplayName = "Glide")
};

UENUM(BlueprintType)
enum class EMelodiaTraversalRequestResult : uint8
{
	Accepted UMETA(DisplayName = "Accepted"),
	AlreadyActive UMETA(DisplayName = "Already Active"),
	RejectedContext UMETA(DisplayName = "Rejected: Context"),
	RejectedOwner UMETA(DisplayName = "Rejected: Owner"),
	RejectedResource UMETA(DisplayName = "Rejected: Resource"),
	RejectedCapability UMETA(DisplayName = "Rejected: Capability"),
	UnsupportedMode UMETA(DisplayName = "Unsupported Mode")
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaTraversalRequestResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Traversal")
	EMelodiaTraversalRequestResult Result = EMelodiaTraversalRequestResult::UnsupportedMode;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Traversal")
	EMelodiaTraversalMode RequestedMode = EMelodiaTraversalMode::Grounded;

	/** Stable diagnostic key for UI, telemetry, and fixture assertions. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Traversal")
	FName BlockReason = NAME_None;

	bool WasAccepted() const
	{
		return Result == EMelodiaTraversalRequestResult::Accepted
			|| Result == EMelodiaTraversalRequestResult::AlreadyActive;
	}
};

/**
 * Exploration-only movement adapter for the canonical Melusina pawn.
 * Input-context authority remains in UMelodiaInputContextSubsystem; this
 * component only applies traversal while exploration movement is allowed.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaTraversalComponent : public UActorComponent, public IMelodiaTraversalStateProvider
{
	GENERATED_BODY()

public:
	UMelodiaTraversalComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	bool IsGliding() const { return bIsGliding; }

	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	bool IsJumpWindingUp() const { return bJumpWindingUp; }

	/** Visual windup progress; jump force is intentionally not charge-dependent. */
	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	float GetJumpWindupNormalized() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	bool IsSprinting() const { return bIsSprinting; }

	/** True during the brief dash impulse window (ground, or mid-air while gliding). */
	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	bool IsDashing() const { return bIsDashing; }

	/** True while swimming on water surface. */
	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	bool IsSwimming() const { return bIsSwimming; }

	/** True while diving underwater. */
	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	bool IsDiving() const { return bIsDiving; }

	/** Current mode exposed to world-facing gates and presentation BPs. */
	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	EMelodiaTraversalMode GetTraversalMode() const;

	/**
	 * Native movement authority for the first capability contract. The request is
	 * fail-closed and currently supports Grounded and Glide only. Sprint, swim,
	 * and dive remain input/native-only until their own transition contracts exist.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Traversal")
	FMelodiaTraversalRequestResult RequestTraversalMode(EMelodiaTraversalMode RequestedMode);

	/** Restore the canonical grounded state; safe to call more than once. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Traversal")
	void ResetTraversalState();

	/** Context passed to the module-neutral capability provider when enabled. */
	UFUNCTION(BlueprintPure, Category="Melodia|Traversal|Capabilities")
	FName GetTraversalCapabilityContextId() const { return TraversalCapabilityContextId; }

	UFUNCTION(BlueprintCallable, Category="Melodia|Traversal|Capabilities")
	void SetTraversalCapabilityContextId(FName ContextId) { TraversalCapabilityContextId = ContextId; }

	/** Normalized traversal-local stamina for a lightweight HUD bar. */
	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	float GetGlideStaminaNormalized() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	float GetGlideStamina() const { return GlideStamina; }

	/** Breath/stamina for diving (0-1). */
	UFUNCTION(BlueprintPure, Category="Melodia|Traversal")
	float GetBreathNormalized() const;

	/**
	 * Hands wing opacity and visibility to another presentation authority.
	 *
	 * WHY THIS EXISTS: SetWingPresentation drives the wing material's `Opacity`
	 * scalar as a binary 0/1 and forces component visibility to match. That is
	 * correct while glide state is the ONLY thing wings mean. It stops being
	 * correct once an outfit reveal also owns that scalar -- this component
	 * writes 0 in its own BeginPlay and again on every StopGlide, so a wardrobe
	 * reveal animating the same parameter would be silently erased the first time
	 * the player landed. The player sees wings vanish permanently with nothing in
	 * the log.
	 *
	 * When claimed, this component stops writing wing opacity and visibility
	 * entirely, but KEEPS broadcasting OnGlideStateChanged -- glide state is still
	 * this component's truth to report, it just no longer decides how the wing
	 * looks. UMelodiaMagicalTransformComponent claims this in its BeginPlay and
	 * releases it in EndPlay.
	 *
	 * Traversal movement is unaffected either way; this is presentation only.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Traversal|Presentation")
	void SetWingPresentationOwnedExternally(bool bOwnedExternally);

	UFUNCTION(BlueprintPure, Category="Melodia|Traversal|Presentation")
	bool IsWingPresentationOwnedExternally() const { return bWingPresentationOwnedExternally; }

	/** Presentation hook for an AnimBP or a wing component not tagged for auto-discovery. */
	UPROPERTY(BlueprintAssignable, Category="Melodia|Traversal|Presentation")
	FMelodiaGlideStateChanged OnGlideStateChanged;

	/** Fired when swimming state changes (surface enter/exit). */
	UPROPERTY(BlueprintAssignable, Category="Melodia|Traversal|Presentation")
	FMelodiaSwimStateChanged OnSwimStateChanged;

	/** Fired when diving state changes (submerge/surface). */
	UPROPERTY(BlueprintAssignable, Category="Melodia|Traversal|Presentation")
	FMelodiaDiveStateChanged OnDiveStateChanged;

	/** Fired when water proximity changes (0-1). */
	UPROPERTY(BlueprintAssignable, Category="Melodia|Traversal|Water")
	FMelodiaFloatValueChanged OnWaterProximityChanged;

	/** Normalized water events consumed by Niagara, fluid, material, and audio adapters. */
	UPROPERTY(BlueprintAssignable, Category="Melodia|Traversal|Water")
	FMelodiaWaterContactEventSignature OnWaterContactEvent;

private:
	void BindTraversalInput();
	void HandleJumpPressed();
	void HandleJumpReleased();
	void FinishReleasedJump();
	void HandleSprintPressed();
	void HandleSprintReleased();
	void HandleStrafePressed();
	void HandleDivePressed();
	void BeginJumpWindup();
	void CancelJumpWindup();
	void SetSprinting(bool bShouldSprint);
	void ApplyCurrentMovementSpeed();
	bool IsCapabilityAvailableForMode(EMelodiaTraversalMode RequestedMode, FName& OutBlockReason) const;
	void CancelTraversalState();
	void StartGlide();
	void StopGlide();
	void StartDash();
	void FinishDash();
	void StartSwim();
	void StopSwim();
	void StartDive();
	void StopDive();
	void PublishWaterContact(EMelodiaWaterContactType EventType, float Intensity, const FVector& ImpulseVelocity = FVector::ZeroVector);
	void UpdateWaterState(float DeltaTime);
	void ResolveWingPresentation();
	void SetWingPresentation(bool bVisible);
	void RestoreMovementDefaults();

	TWeakObjectPtr<ACharacter> OwnerCharacter;
	TWeakObjectPtr<UCharacterMovementComponent> Movement;
	bool bInputBound = false;
	bool bSuppressWaterPresentation = false;

	/** Set via SetWingPresentationOwnedExternally; see that function for why. */
	bool bWingPresentationOwnedExternally = false;
	bool bIsGliding = false;
	bool bJumpWindingUp = false;
	bool bAwaitingGlideTap = false;
	bool bJumpHasLeftGround = false;
	bool bSprintInputHeld = false;
	bool bIsSprinting = false;
	bool bIsDashing = false;
	bool bMovementDefaultsCaptured = false;

	/**
	 * Opt-in during the migration window. Promoted traversal fixtures should set
	 * this true so input and Blueprint requests share the same capability gate.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Traversal|Capabilities",
		meta=(AllowPrivateAccess="true"))
	bool bRequireCapabilityProviderForGlide = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Traversal|Capabilities",
		meta=(AllowPrivateAccess="true"))
	FName TraversalCapabilityContextId = NAME_None;
	double JumpWindupStartedAt = -1.0;
	float SavedGravityScale = 1.0f;
	float SavedAirControl = 0.35f;
	float SavedMaxWalkSpeed = 0.0f;
	FRotator SavedRotationRate = FRotator::ZeroRotator;
	bool bSavedOrientRotationToMovement = false;
	bool bSavedUseControllerRotationYaw = false;
	float GlideStamina = 0.0f;
	float TimeSinceGlideStopped = 0.0f;

	/** Swimming/diving state */
	UPROPERTY(Transient)
	bool bIsSwimming = false;

	UPROPERTY(Transient)
	bool bIsDiving = false;

	float SwimStamina = 0.0f;
	float Breath = 1.0f;
	float TimeSinceSwimStopped = 0.0f;
	float WaterLevelZ = 0.0f;
	float WaterMotionEventAccumulator = 0.0f;

	/** Last tension published to the reactivity channel, gated by hysteresis so
	 *  the per-frame proximity update does not spam Publish() on every tick. */
	float LastPublishedExplorationTension = -1.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Water|Presentation", meta=(ClampMin="0.12", ClampMax="1.0"))
	float WaterMotionEventInterval = 0.28f;

	/** Set when a dive impulse is live; cleared on cooldown expiry. */
	float DiveCooldownUntilTime = 0.0f;

	/** Timer that clears the dive flag after the visual window. */
	FTimerHandle DivePersistTimer;

	/** Water proximity tracking */
	UPROPERTY(Transient)
	class UMaterialParameterCollection* WaterProximityMPC = nullptr;

	/** Auto-created consumer keeps the canonical Melusina pawn wired to water VFX. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Water|Niagara")
	bool bAutoCreateWaterNiagaraBridge = true;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWaterNiagaraBridgeComponent> WaterNiagaraBridge = nullptr;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Water|Audio")
	bool bAutoCreateWaterAudioBridge = true;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWaterAudioBridgeComponent> WaterAudioBridge = nullptr;

	/** Auto-created camera bridge drives MI_Water_Underwater_Post_Default. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Water|Underwater")
	bool bAutoCreateWaterUnderwaterPostProcess = true;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWaterUnderwaterPostProcessComponent> WaterUnderwaterPostProcess = nullptr;

	/** True only after a native Water Body query has supplied a surface. */
	bool bHasAuthoritativeWaterSurface = false;
	bool bWaterProximityActive = false;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Water", meta=(ClampMin="0.0", ClampMax="1.0"))
	float WaterProximityEnterThreshold = 0.35f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Water", meta=(ClampMin="0.0", ClampMax="1.0"))
	float WaterProximityExitThreshold = 0.2f;

	/** Set when a dash impulse is live; cleared on cooldown expiry. */
	float DashCooldownUntilTime = 0.0f;

	/** Timer that clears the dash flag after the visual window. */
	FTimerHandle DashPersistTimer;

	UPROPERTY(Transient)
	TObjectPtr<UMeshComponent> WingMesh = nullptr;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> WingMaterials;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Movement", meta=(ClampMin="100.0", ClampMax="800.0"))
	float NormalWalkSpeed = 380.0f;

	/** Matches the authored sprint sample in BS_Melusina_Locomotion. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Movement", meta=(ClampMin="100.0", ClampMax="1200.0"))
	float SprintSpeed = 630.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Movement", meta=(ClampMin="90.0", ClampMax="1080.0"))
	float ExplorationRotationRateYaw = 600.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Movement")
	bool bApplyExplorationRotationTuning = true;

	/** Horizontal dash impulse applied along the current movement input direction
	 *  (falls back to facing when idle). Ctrl-triggered; mid-air valid while gliding. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Movement", meta=(ClampMin="100.0", ClampMax="2000.0"))
	float DashImpulse = 900.0f;

	/** Cooldown between dashes so the move stays cadenced, not mashable. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Movement", meta=(ClampMin="0.05", ClampMax="5.0"))
	float DashCooldownSeconds = 0.7f;

	/** How long the dash skeletally reads (stamina-presentation window). */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Movement", meta=(ClampMin="0.05", ClampMax="1.0"))
	float DashPersistSeconds = 0.22f;

	/** Duration used to normalize the poise animation; release always jumps once. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Input", meta=(ClampMin="0.05", ClampMax="2.0"))
	float JumpWindupVisualDuration = 0.4f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Feel", meta=(ClampMin="0.05", ClampMax="1.0"))
	float GlideGravityScale = 0.16f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Feel", meta=(ClampMin="0.0", ClampMax="1.0"))
	float GlideAirControl = 1.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Feel", meta=(ClampMin="100.0"))
	float GlideTerminalFallSpeed = 240.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Feel", meta=(ClampMin="0.0", ClampMax="600.0"))
	float GlideActivationLiftSpeed = 190.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Feel", meta=(ClampMin="0.0", ClampMax="600.0"))
	float GlideActivationForwardBoost = 165.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Stamina", meta=(ClampMin="0.5", ClampMax="15.0"))
	float MaxGlideStamina = 3.5f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Stamina", meta=(ClampMin="0.05", ClampMax="5.0"))
	float GlideStaminaDrainPerSecond = 1.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Stamina", meta=(ClampMin="0.05", ClampMax="10.0"))
	float GlideStaminaRegenPerSecond = 1.5f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Stamina", meta=(ClampMin="0.0", ClampMax="3.0"))
	float GlideStaminaRegenDelay = 0.45f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Stamina", meta=(ClampMin="0.0", ClampMax="2.0"))
	float MinimumGlideStartStamina = 0.25f;

	/** Swimming/diving config */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="0.5", ClampMax="15.0"))
	float MaxSwimStamina = 5.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="0.05", ClampMax="5.0"))
	float SwimStaminaDrainPerSecond = 0.5f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="0.05", ClampMax="10.0"))
	float SwimStaminaRegenPerSecond = 1.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="0.0", ClampMax="3.0"))
	float SwimStaminaRegenDelay = 0.5f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="0.5", ClampMax="15.0"))
	float MaxBreath = 10.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="0.05", ClampMax="5.0"))
	float BreathDrainPerSecond = 1.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="0.05", ClampMax="10.0"))
	float BreathRegenPerSecond = 2.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="100.0", ClampMax="2000.0"))
	float SwimSpeed = 400.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="100.0", ClampMax="2000.0"))
	float DiveImpulse = 800.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Swimming", meta=(ClampMin="100.0", ClampMax="2000.0"))
	float SurfaceJumpImpulse = 600.0f;

	/** Optional auto-wiring: tag the authored wing mesh component MelodiaWings. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Presentation")
	FName WingComponentTag = TEXT("MelodiaWings");

	/** The tagged wing material must expose this scalar and use a translucent blend mode. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Presentation")
	FName WingOpacityParameter = TEXT("Opacity");

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Traversal|Presentation")
	bool bHideWingMeshWhenNotGliding = true;
};
