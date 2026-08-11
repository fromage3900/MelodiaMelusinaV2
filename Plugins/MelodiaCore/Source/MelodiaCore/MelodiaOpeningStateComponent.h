// Runtime state contracts for the authored Melodia opening.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaOpeningStateComponent.generated.h"

UENUM(BlueprintType)
enum class EMelodiaResonanceBondState : uint8
{
	Absent UMETA(DisplayName="Absent"),
	Reunited UMETA(DisplayName="Reunited"),
	Resonant UMETA(DisplayName="Resonant"),
	Strained UMETA(DisplayName="Strained")
};

UENUM(BlueprintType)
enum class EMelodiaDissonanceTier : uint8
{
	Clear UMETA(DisplayName="Clear Resonance"),
	Strain UMETA(DisplayName="Strain"),
	Rupture UMETA(DisplayName="Rupture")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaResonanceBondChanged, EMelodiaResonanceBondState, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaDissonanceTierChanged, EMelodiaDissonanceTier, NewTier);

/**
 * Companion-dependent musical state. It intentionally carries no Sir Melodious asset
 * reference so the opening can be authored before his UE import is complete.
 */
UCLASS(Blueprintable, ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class MELODIACORE_API UMelodiaResonanceBondComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Resonance")
	EMelodiaResonanceBondState BondState = EMelodiaResonanceBondState::Absent;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Resonance")
	FMelodiaResonanceBondChanged OnBondStateChanged;

	UFUNCTION(BlueprintCallable, Category="Melodia|Resonance")
	void SetBondState(EMelodiaResonanceBondState NewState);

	UFUNCTION(BlueprintPure, Category="Melodia|Resonance")
	bool IsSongcraftEmpowered() const;
};

/** Data-driven anchor for Dissonance presentation and encounter bindings. */
UCLASS(Blueprintable, ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class MELODIACORE_API UMelodiaDissonanceComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Dissonance")
	EMelodiaDissonanceTier Tier = EMelodiaDissonanceTier::Clear;

	/** Bounded multiplier intended for explicit Songcraft effects, never timing windows. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Dissonance", meta=(ClampMin="0.0", ClampMax="2.0"))
	float SongcraftScalar = 1.0f;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Dissonance")
	FMelodiaDissonanceTierChanged OnTierChanged;

	UFUNCTION(BlueprintCallable, Category="Melodia|Dissonance")
	void SetDissonanceTier(EMelodiaDissonanceTier NewTier, float NewSongcraftScalar = 1.0f);
};
