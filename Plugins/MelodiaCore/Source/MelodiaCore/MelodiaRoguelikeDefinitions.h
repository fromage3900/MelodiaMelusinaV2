#pragma once

#include "CoreMinimal.h"
#include "Curves/CurveFloat.h"
#include "Engine/DataAsset.h"
#include "MelodiaRoguelikeAuthorityTypes.h"
#include "MelodiaRoguelikeDefinitions.generated.h"

class AActor;
class UWorld;
class URoomData;

UENUM(BlueprintType)
enum class EMelodiaRewardFamily : uint8
{
	Harmony,
	Crescendo,
	Dissonance
};

UENUM(BlueprintType)
enum class EMelodiaModifierOperation : uint8
{
	Add,
	Multiply,
	Override
};

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaGameplayModifierDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Roguelike") FName StatId = NAME_None;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Roguelike") EMelodiaModifierOperation Operation = EMelodiaModifierOperation::Add;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Roguelike") float Magnitude = 0.0f;
};

UCLASS(Abstract, BlueprintType)
class MELODIACORE_API UMelodiaRoguelikeDefinition : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, AssetRegistrySearchable, Category="Melodia|Identity")
	FName StableId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Identity")
	int32 SchemaVersion = 1;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Entitlement")
	FName ContentPackId = TEXT("Core");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Entitlement")
	bool bRequiresEntitlement = false;

	virtual FPrimaryAssetId GetPrimaryAssetId() const override;

	UFUNCTION(BlueprintCallable, Category="Melodia|Validation")
	virtual bool ValidateDefinition(TArray<FText>& OutErrors) const;

protected:
	virtual FPrimaryAssetType GetDefinitionType() const PURE_VIRTUAL(UMelodiaRoguelikeDefinition::GetDefinitionType, return FPrimaryAssetType(););
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaRoomDefinition : public UMelodiaRoguelikeDefinition
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") TSoftObjectPtr<UWorld> Level;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") TSoftObjectPtr<URoomData> RoomData;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") TArray<FName> TopologyTags;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") TArray<FName> CompatibilityTags;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") int32 MinimumTier = 0;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") int32 MaximumTier = 99;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") float MinimumDissonance = 0.0f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") float MaximumDissonance = 100.0f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") EMelodiaCompanionRequirement CompanionRequirement = EMelodiaCompanionRequirement::None;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Room") bool bFallbackRoom = false;
	virtual bool ValidateDefinition(TArray<FText>& OutErrors) const override;
protected:
	virtual FPrimaryAssetType GetDefinitionType() const override { return FPrimaryAssetType(TEXT("MelodiaRoom")); }
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaRoguelikeEncounterDefinition : public UMelodiaRoguelikeDefinition
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Encounter") FName EnemyId = NAME_None;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Encounter") TSoftClassPtr<AActor> EnemyClass;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Encounter") TArray<FName> RequiredRoomTags;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Encounter") int32 MinimumTier = 0;
	virtual bool ValidateDefinition(TArray<FText>& OutErrors) const override;
protected:
	virtual FPrimaryAssetType GetDefinitionType() const override { return FPrimaryAssetType(TEXT("MelodiaEncounter")); }
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaMutatorDefinition : public UMelodiaRoguelikeDefinition
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Mutator") TArray<FMelodiaGameplayModifierDefinition> Modifiers;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Mutator") TArray<FName> IncompatibleMutatorIds;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Mutator") float MinimumDissonance = 0.0f;
protected:
	virtual FPrimaryAssetType GetDefinitionType() const override { return FPrimaryAssetType(TEXT("MelodiaMutator")); }
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaRewardDefinition : public UMelodiaRoguelikeDefinition
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Reward") EMelodiaRewardFamily Family = EMelodiaRewardFamily::Harmony;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Reward") TArray<FMelodiaGameplayModifierDefinition> Modifiers;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Reward") TArray<FName> EligibilityTags;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Reward") TArray<FName> ExclusionTags;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Reward") int32 StackCap = 1;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Reward") float Weight = 1.0f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Reward") float DissonanceDelta = 0.0f;
	virtual bool ValidateDefinition(TArray<FText>& OutErrors) const override;
protected:
	virtual FPrimaryAssetType GetDefinitionType() const override { return FPrimaryAssetType(TEXT("MelodiaReward")); }
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaRewardPoolDefinition : public UMelodiaRoguelikeDefinition
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Reward Pool") TArray<TSoftObjectPtr<UMelodiaRewardDefinition>> Rewards;
	virtual bool ValidateDefinition(TArray<FText>& OutErrors) const override;
protected:
	virtual FPrimaryAssetType GetDefinitionType() const override { return FPrimaryAssetType(TEXT("MelodiaRewardPool")); }
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaDifficultyDefinition : public UMelodiaRoguelikeDefinition
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Difficulty") FRuntimeFloatCurve EnemyHealthByDepth;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Difficulty") FRuntimeFloatCurve EnemyDamageByDepth;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Difficulty") FRuntimeFloatCurve RewardWeightByDepth;
protected:
	virtual FPrimaryAssetType GetDefinitionType() const override { return FPrimaryAssetType(TEXT("MelodiaDifficulty")); }
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaRunArchetypeDefinition : public UMelodiaRoguelikeDefinition
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Run") int32 ActCount = 2;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Run") int32 StagesPerAct = 6;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Run") bool bOffersEndless = true;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Run") TArray<TSoftObjectPtr<UMelodiaRoomDefinition>> Rooms;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Run") TArray<TSoftObjectPtr<UMelodiaRoguelikeEncounterDefinition>> Encounters;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Run") TSoftObjectPtr<UMelodiaDifficultyDefinition> Difficulty;
	virtual bool ValidateDefinition(TArray<FText>& OutErrors) const override;
protected:
	virtual FPrimaryAssetType GetDefinitionType() const override { return FPrimaryAssetType(TEXT("MelodiaRunArchetype")); }
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaContentPackDefinition : public UMelodiaRoguelikeDefinition
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Content Pack") bool bCosmeticOnly = true;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Content Pack") bool bNarrativeExpansion = false;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Content Pack") TArray<FPrimaryAssetId> IncludedAssets;
protected:
	virtual FPrimaryAssetType GetDefinitionType() const override { return FPrimaryAssetType(TEXT("MelodiaContentPack")); }
};
