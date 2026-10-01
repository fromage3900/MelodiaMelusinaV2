// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AttributeSet.h"
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "Engine/Texture2D.h"
#include "GameplayTagContainer.h"

#include "ACFGASTypes.generated.h"

/**
 *
 */
UENUM(BlueprintType)
enum class ELevelingType : uint8 {
	ECantLevelUp = 0 UMETA(DisplayName = "Do not use Leveling System"),
	EGenerateNewStatsFromCurves UMETA(DisplayName = "Generate Stats From Curves"),
	EAssignPerksManually UMETA(DisplayName = "Assign Perks Manually"),
};

USTRUCT(BlueprintType)
struct FAttributeSerializeKeys : public FTableRowBase {

	GENERATED_BODY()

public:
	FAttributeSerializeKeys() {};

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	FGameplayAttribute Attribute;
};

USTRUCT(BlueprintType)
struct FAttributeSerializeNames {

	GENERATED_BODY()

public:
	FAttributeSerializeNames() { Value = 0.f; };

	FAttributeSerializeNames(const FName& inName, const float inValue)
	{

		AttributeName = inName;
		Value = inValue;
	};

	UPROPERTY(EditAnywhere, Savegame, BlueprintReadWrite, Category = "ACF")
	FName AttributeName;

	UPROPERTY(EditAnywhere, Savegame, BlueprintReadWrite, Category = "ACF")
	float Value;

	FORCEINLINE bool operator!=(const FName& Other) const
	{
		return this->AttributeName != Other;
	}

	FORCEINLINE bool operator==(const FName& Other) const
	{
		return this->AttributeName == Other;
	}
};

USTRUCT(BlueprintType)
struct FAttributeClamps {

	GENERATED_BODY()

public:
	FAttributeClamps() {};

	FAttributeClamps(const FGameplayAttribute& inToClamp,
		const FGameplayAttribute& inMaxValue, bool inClampZero)
	{
		AttributeToClamp = inToClamp;
		MaxValueAttribute = inMaxValue;
		bClampToZero = inClampZero;
	}

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	FGameplayAttribute AttributeToClamp;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	FGameplayAttribute MaxValueAttribute;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	bool bClampToZero = true;

	FORCEINLINE bool operator!=(const FGameplayAttribute& Other) const
	{
		return AttributeToClamp != Other;
	}

	FORCEINLINE bool operator==(const FGameplayAttribute& Other) const
	{
		return AttributeToClamp == Other;
	}
};

USTRUCT(BlueprintType)
struct FAttributeInit : public FTableRowBase {

	GENERATED_BODY()

public:
	FAttributeInit() { InitValue = 1.f; };

	FAttributeInit(const FGameplayAttribute& inAtt, const float inValue)
	{
		Attribute = inAtt;
		InitValue = inValue;
	}

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	FGameplayAttribute Attribute;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	float InitValue;
};

USTRUCT(BlueprintType)
struct FACFAttributeInits : public FTableRowBase {

	GENERATED_BODY()

public:

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	TArray<FAttributeInit> PawnAttributesInit;
};

/**
 * Defines the multiplier applied to a single attribute tag at a given difficulty level.
 */
USTRUCT(BlueprintType)
struct FACFDifficultyAttributeMultiplier {
	GENERATED_BODY()

public:
	FACFDifficultyAttributeMultiplier()
		: Multiplier(1.0f)
	{
	}

	/** The attribute whose base value will be scaled. Uses the GAS attribute directly. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Difficulty")
	FGameplayAttribute Attribute;

	/** The factor to multiply the attribute base value by (e.g. 0.75 for Easy, 1.5 for Hard). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Difficulty")
	float Multiplier;
};

/**
 * DataTable row that maps a difficulty level to a set of attribute multipliers.
 * Each row represents one difficulty level.
 */
USTRUCT(BlueprintType)
struct FACFDifficultyScaling : public FTableRowBase {
	GENERATED_BODY()

public:
	/** The gameplay tag that identifies this difficulty level (e.g. ACF.Difficulty.Easy). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "ACF.Difficulty"), Category = "ACF|Difficulty")
	FGameplayTag DifficultyLevel;

	/** Per-attribute multipliers applied when this difficulty level is active. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Difficulty", meta = (TitleProperty = "Attribute"))
	TArray<FACFDifficultyAttributeMultiplier> AttributeMultipliers;

	// ---- UI ----

	/** Localized name shown in the settings/difficulty selection UI (e.g. "Normal", "Hard"). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Difficulty|UI")
	FText UIName;

	/** Short localized description of the difficulty level shown below the title in the UI. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Difficulty|UI")
	FText UIDescription;

	/** Optional icon representing this difficulty in the UI (e.g. a skull icon for Very Hard). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Difficulty|UI")
	TSoftObjectPtr<UTexture2D> UIIcon;
};

UCLASS()
class ASCENTGASRUNTIME_API UACFGASTypes : public UObject {
public:
	GENERATED_BODY()
	UACFGASTypes();
};
