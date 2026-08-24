#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaCompanionData.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "MelodiaCompanionComponent.generated.h"

class AActor;
class UMelodiaCompanionWardrobeBridge;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaCompanionStateChanged, EMelodiaCompanionBehaviorState, PreviousState, EMelodiaCompanionBehaviorState, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaCompanionInteractionEvent, EMelodiaCompanionInteractionKind, Interaction);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaCompanionResonancePulseEvent, float, Intensity);

/**
 * Lightweight exploration companion controller.
 *
 * This component owns presentation-safe state transitions and a deterministic
 * follow/seek motion fallback. A future StateTree/Mass adapter can consume the
 * same public state contract without creating a second companion authority.
 */
UCLASS(Blueprintable, ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class MELODIACORE_API UMelodiaCompanionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaCompanionComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion")
	TSoftObjectPtr<UMelodiaCompanionDefinitionAsset> CompanionDefinition;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Movement")
	TObjectPtr<AActor> FollowTarget = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Movement")
	TObjectPtr<AActor> GuidanceTarget = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Movement")
	bool bDriveOwnerTransform = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Movement", meta=(ClampMin="0.0"))
	float FollowInterpSpeed = 3.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Music", meta=(ClampMin="0.0", ClampMax="2.0"))
	float RhythmResponse = 0.75f;

	/** Optional bridge used only by an explicit wardrobe presentation request. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Wardrobe")
	TObjectPtr<UMelodiaCompanionWardrobeBridge> WardrobeBridge = nullptr;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Companion")
	FMelodiaCompanionDefinition ActiveDefinition;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Companion")
	EMelodiaCompanionBehaviorState CurrentState = EMelodiaCompanionBehaviorState::Idle;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Companion|Music")
	float ResonanceIntensity = 0.0f;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Companion")
	FMelodiaCompanionStateChanged OnStateChanged;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Companion")
	FMelodiaCompanionInteractionEvent OnInteractionStarted;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Companion")
	FMelodiaCompanionInteractionEvent OnInteractionFinished;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Companion|Music")
	FMelodiaCompanionResonancePulseEvent OnHarmonizePulse;

	UFUNCTION(BlueprintCallable, Category="Melodia|Companion")
	bool ApplyCompanionDefinition();

	UFUNCTION(BlueprintCallable, Category="Melodia|Companion")
	bool SetCompanionDefinition(UMelodiaCompanionDefinitionAsset* InDefinition);

	UFUNCTION(BlueprintPure, Category="Melodia|Companion")
	const FMelodiaCompanionDefinition& GetActiveCompanionDefinition() const { return ActiveDefinition; }

	UFUNCTION(BlueprintPure, Category="Melodia|Companion")
	FName GetCompanionId() const { return ActiveDefinition.CompanionId; }

	UFUNCTION(BlueprintCallable, Category="Melodia|Companion")
	bool RequestState(EMelodiaCompanionBehaviorState NewState);

	UFUNCTION(BlueprintCallable, Category="Melodia|Companion")
	bool BeginInteraction(EMelodiaCompanionInteractionKind Interaction);

	UFUNCTION(BlueprintCallable, Category="Melodia|Companion")
	void EndInteraction(EMelodiaCompanionInteractionKind Interaction);

	UFUNCTION(BlueprintCallable, Category="Melodia|Companion|Movement")
	void SetFollowTarget(AActor* NewTarget);

	UFUNCTION(BlueprintCallable, Category="Melodia|Companion|Movement")
	void SetGuidanceTarget(AActor* NewTarget);

	UFUNCTION(BlueprintPure, Category="Melodia|Companion|Movement")
	FVector GetDesiredNavigationLocation() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Companion")
	bool SupportsInteraction(EMelodiaCompanionInteractionKind Interaction) const;

	/** Applies an authored presentation profile without changing durable wardrobe state. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Companion|Wardrobe")
	bool RequestWardrobePresentation();

	/**
	 * Applies the definition's mesh, optional animation class, and alignment to
	 * the owner's primary skeletal mesh component. This is intentionally
	 * definition-driven so a rig can be reimported at its reserved path without
	 * changing a level or Blueprint.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Companion|Presentation")
	bool ApplyCompanionPresentation();

protected:
	UFUNCTION()
	void HandleRhythmSignal(const FMelodiaRhythmReactivitySignal& Signal);

	void SetStateInternal(EMelodiaCompanionBehaviorState NewState);
	void DriveOwnerToward(const FVector& DesiredLocation, float AcceptanceRadius, float DeltaTime);
	class USkeletalMeshComponent* FindPresentationMeshComponent() const;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaRhythmReactivitySubsystem> ReactivitySubsystem = nullptr;

	UPROPERTY(Transient)
	float LastBeatPulse = 0.0f;
};
