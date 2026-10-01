// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"
#include "ACFGASTypes.h"
#include "Components/ACFInventoryComponent.h"
#include "ACFAbilitySet.h"
#include "ACFCCTypes.h"
#include "Game/ACFTypes.h"
#include "Config/ACFEffectsConfigDataAsset.h"
#include "ACFCharacterDataAsset.generated.h"

struct FStartingItem;

/**
 * Data-driven character definition: stats, abilities, equipment, appearance, team, and optional fragments.
 * Combat behaviour and AI-specific data are applied via Fragments (e.g. from AIFramework).
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFCharacterDataAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UACFCharacterDataAsset();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	FText ChatacterName = FText::FromString("AI Character");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Appearence", meta = (TitleProperty = "ComponentTag"))
	TArray<FSkeletalMeshComponentData> MeshComponents;

#if WITH_EDITOR
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
	virtual void PostEditChangeChainProperty(FPropertyChangedChainEvent& PropertyChangedEvent) override;

private:
	void UpdateMaterialArray(FSkeletalMeshComponentData& MeshData);
#endif

public:
	UPROPERTY(EditAnywhere, meta = (Categories = "Teams"), BlueprintReadWrite, Category = "ACF")
	FGameplayTag Team;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|Attributes")
	ELevelingType LevelingType = ELevelingType::ECantLevelUp;

	UPROPERTY(EditAnywhere, meta = (EditCondition = "LevelingType != ELevelingType::EGenerateNewStatsFromCurves", RowType = "/Script/AscentGASRuntime.ACFAttributeInits"), Category = "ACF|Attributes")
	FDataTableRowHandle CharacterRow;

	UPROPERTY(EditAnywhere, meta = (EditCondition = "LevelingType == ELevelingType::EGenerateNewStatsFromCurves"), Category = "ACF|Attributes")
	UCurveTable* AttributesByLevelCurve;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Attributes")
	bool bAffectedByDifficultyLevel = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "LevelingType != ELevelingType::ECantLevelUp"), Category = "ACF|Attributes")
	class UCurveFloat* ExpForNextLevelCurve;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "LevelingType == ELevelingType::ECantLevelUp"), Category = "ACF|Attributes")
	float ExpToGiveOnDeath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "LevelingType != ELevelingType::ECantLevelUp"), Category = "ACF|Attributes")
	class UCurveFloat* ExpToGiveOnDeathByCurrentLevel;

	UPROPERTY(EditAnywhere, meta = (TitleProperty = "ItemClass"), BlueprintReadWrite, Category = "ACF|Equipment")
	TArray<FStartingItem> StartingItems;

	UFUNCTION(BlueprintPure, Category = "ACF|Attributes")
	bool GetInitialAttributes(FACFAttributeInits& OutAttributes) const;

	UFUNCTION(BlueprintPure, Category = "ACF|Attributes")
	TArray<FAttributeInit> GetInitialStats() const;

	UFUNCTION(BlueprintPure, Category = "ACF|Equipment")
	TArray<FStartingItem> GetStartingItems() const { return StartingItems; }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Equipment")
	float Currency = 10.f;

	UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "ACF|Abilities")
	UACFAbilitySet* DefaultAbilitySet;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Abilities", meta = (Categories = "Moveset, Actionset, AbilitySet"))
	TMap<FGameplayTag, UACFAbilitySet*> MovesetAbilities;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Effects")
	TObjectPtr<UACFEffectsConfigDataAsset> CharacterEffectsConfig;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Collision", meta = (ClampMin = "0.0", ForceUnits = "cm"))
	float CapsuleHalfHeight = 88.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Collision", meta = (ClampMin = "0.0", ForceUnits = "cm"))
	float CapsuleRadius = 34.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Instanced, Category = "Fragments")
	TArray<UACFCharacterFragment*> Fragments;

	UFUNCTION(BlueprintCallable, Category = "Fragments", meta = (DeterminesOutputType = "FragmentClass"))
	UACFCharacterFragment* GetFragmentByClass(TSubclassOf<UACFCharacterFragment> FragmentClass) const;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Others")
	bool bShouldAutomaticallyBeSaved = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Others")
	ERotationMode RotationMode = ERotationMode::EStrafing;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Others")
	UTexture2D* CharacterPortrait;
};
