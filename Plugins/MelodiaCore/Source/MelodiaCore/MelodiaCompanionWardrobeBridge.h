#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaCompanionWardrobeBridge.generated.h"

class UActorComponent;

/**
 * Result of a companion presentation request.
 *
 * The request is presentation-only by default. The two Granted values are the
 * only successful results that may follow an explicit prototype-grant opt-in.
 */
UENUM(BlueprintType)
enum class EMelodiaCompanionWardrobeRequestResult : uint8
{
	RejectedInvalidProfile,
	RejectedNoWardrobeProvider,
	RejectedNoOwnedCosmetic,
	RejectedPrototypeGrantFailed,
	RejectedPresentationFailed,
	AppliedOwnedCosmetic,
	GrantedAndAppliedPrototypeCosmetic
};

/**
 * Companion-owned request describing which presentation cosmetics are acceptable.
 *
 * This is a request, not an ownership record. Empty or malformed profiles fail
 * closed. PreferredCosmeticIds are considered in authored order; the first
 * already-owned entry that can present successfully wins. No save state is
 * written on that default path.
 *
 * Prototype grants are deliberately explicit and require all three fields:
 * bAllowPrototypeGrant, PrototypeGrantCosmeticId, and PrototypeGrantId. The
 * grant id is a caller-owned receipt for the prototype request, not a generated
 * fallback. The wardrobe subsystem remains the only owner of the resulting
 * durable ownership state.
 */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaCompanionWardrobeProfile
{
	GENERATED_BODY()

	/** Stable identity for diagnostics and authored companion data. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Wardrobe")
	FName ProfileId = FName(TEXT("ChoralSheep"));

	/** Ordered, presentation-only candidates. The first successful owned entry wins. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Wardrobe")
	TArray<FName> PreferredCosmeticIds;

	/** Must be true before any prototype ownership grant is even considered. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Wardrobe|Prototype")
	bool bAllowPrototypeGrant = false;

	/** Cosmetic to grant when the caller explicitly enables the prototype path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Wardrobe|Prototype")
	FName PrototypeGrantCosmeticId;

	/** Explicit caller-provided receipt required by the prototype grant path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Wardrobe|Prototype")
	FName PrototypeGrantId;

	/** Validates the request without consulting wardrobe or save state. */
	bool IsValid(FText* OutError = nullptr) const;
};

/**
 * Core-owned presentation seam implemented by wardrobe presentation components.
 *
 * Core owns the request contract so companion code does not depend on the
 * MelodiaWardrobe module. Wardrobe owns the implementation and remains the only
 * authority allowed to grant or persist cosmetic ownership.
 */
UINTERFACE(BlueprintType)
class MELODIACORE_API UMelodiaCompanionWardrobeInterface : public UInterface
{
	GENERATED_BODY()
};

class MELODIACORE_API IMelodiaCompanionWardrobeInterface
{
	GENERATED_BODY()

public:
	/** Applies a request through the implementing wardrobe presentation component. */
	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Companion|Wardrobe")
	EMelodiaCompanionWardrobeRequestResult RequestCompanionWardrobe(
		const FMelodiaCompanionWardrobeProfile& Profile);
};

/**
 * Optional caller-side component for a companion actor.
 *
 * It never auto-requests on BeginPlay. A companion or an authored prototype must
 * explicitly call RequestPresentation, which keeps wardrobe presentation and
 * prototype grants out of implicit construction/save paths.
 */
UCLASS(Blueprintable, ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class MELODIACORE_API UMelodiaCompanionWardrobeBridge : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaCompanionWardrobeBridge();

	/** Component implementing UMelodiaCompanionWardrobeInterface, normally the actor's wardrobe component. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Wardrobe")
	TObjectPtr<UActorComponent> WardrobeProvider = nullptr;

	/** Request used by RequestPresentation(). It defaults to the fail-closed path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Companion|Wardrobe")
	FMelodiaCompanionWardrobeProfile PresentationProfile;

	/** Assigns only an object that implements the Core-owned wardrobe interface. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Companion|Wardrobe")
	bool SetWardrobeProvider(UActorComponent* NewProvider);

	UFUNCTION(BlueprintPure, Category="Melodia|Companion|Wardrobe")
	bool HasWardrobeProvider() const;

	/** Explicitly requests the currently authored profile; there is no BeginPlay request. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Companion|Wardrobe")
	EMelodiaCompanionWardrobeRequestResult RequestPresentation();

	/** Explicitly requests a supplied profile, useful for authored companion variants. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Companion|Wardrobe")
	EMelodiaCompanionWardrobeRequestResult RequestPresentationWithProfile(
		const FMelodiaCompanionWardrobeProfile& Profile);

	UFUNCTION(BlueprintPure, Category="Melodia|Companion|Wardrobe")
	EMelodiaCompanionWardrobeRequestResult GetLastRequestResult() const { return LastRequestResult; }

private:
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Melodia|Companion|Wardrobe", meta=(AllowPrivateAccess="true"))
	EMelodiaCompanionWardrobeRequestResult LastRequestResult = EMelodiaCompanionWardrobeRequestResult::RejectedNoWardrobeProvider;
};
