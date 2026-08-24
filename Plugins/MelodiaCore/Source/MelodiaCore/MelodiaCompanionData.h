#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaNPCData.h"
#include "MelodiaResonanceGardenData.h"
#include "MelodiaCompanionWardrobeBridge.h"
#include "MelodiaCompanionData.generated.h"

class UAnimInstance;

UENUM(BlueprintType)
enum class EMelodiaCompanionBehaviorState : uint8
{
	Idle,
	Follow,
	Graze,
	Harmonize,
	Seek,
	Rest
};

UENUM(BlueprintType)
enum class EMelodiaCompanionInteractionKind : uint8
{
	Graze,
	Harmonize,
	Guide
};

/** Additive companion identity layered over the existing Melodia NPC contract. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaCompanionDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion")
	FName CompanionId = FName(TEXT("ChoralSheep"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion")
	FText DisplayName = FText::FromString(TEXT("Choral Sheep"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion")
	FText Description = FText::FromString(TEXT("A gentle woolly companion that follows resonance through the garden."));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|NPC")
	FMelodiaNPCDef NPCDefinition;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|Style")
	TSoftObjectPtr<UMelodiaStyleGenomeAsset> StyleGenome;

	/** Optional presentation request; empty means the actor/bridge profile is used. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|Wardrobe")
	FMelodiaCompanionWardrobeProfile WardrobeProfile;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|Fur")
	FMelodiaFurProfile FurProfile;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|Animation")
	TSoftClassPtr<UAnimInstance> AnimationBlueprint;

	/**
	 * Mesh alignment belongs to the definition asset, not a placed level actor.
	 * A replacement rig therefore needs only the reserved mesh path plus this
	 * single definition; no Blueprint or map rewiring is required.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|Presentation")
	FTransform MeshRelativeTransform = FTransform::Identity;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|Music")
	FName MusicalMotif = FName(TEXT("choral_wool"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|World")
	TArray<FName> HabitatTags;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|Interaction")
	TArray<EMelodiaCompanionInteractionKind> SupportedInteractions;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|Movement", meta=(ClampMin="0.0"))
	float FollowDistance = 180.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion|Movement", meta=(ClampMin="0.0"))
	float FollowAcceptanceRadius = 75.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion")
	bool bNonCombat = true;

	bool IsValid(FText* OutError = nullptr) const;
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaCompanionDefinitionAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Companion")
	FMelodiaCompanionDefinition Definition;

	virtual FPrimaryAssetId GetPrimaryAssetId() const override;
};
