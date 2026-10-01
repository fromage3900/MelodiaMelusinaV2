// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFGASTypes.h"
#include "ARSLevelingComponent.h"
#include "AbilitySystemComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include <GameplayTagContainer.h>

#include "ACFGASAttributesComponent.generated.h"

class UGameplayEffect;
class UAbilitySystemComponent;
class UDataTable;
class UACFDifficultyManagerComponent;

/**
 * Component that manages the initialization and runtime handling of character attributes
 * using the Gameplay Ability System (GAS).
 * It supports applying starting effects, loading data from DataTables, and assigning perks.
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTGASRUNTIME_API UACFGASAttributesComponent : public UARSLevelingComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFGASAttributesComponent();

    /**
     * Uses a specified number of perks to increment the given attribute.
     * Will do nothing if the player doesn't have enough available perks.
     *
     * @param attribute The attribute to be increased.
     * @param numPerks The number of perks to assign to the attribute (default: 1).
     */
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ARS)
    void AssignPerkToAttribute(FGameplayAttribute attribute, int32 numPerks = 1);

    /**
     * Gets the DataTable row that defines this character's base attribute values.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FDataTableRowHandle GetCharacterRow() const { return CharacterRow; }

    UFUNCTION(BlueprintPure, Category = ACF)
    UCurveTable* GetAttributesByLevelCurve() const { return AttributesByLevelCurve; }

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetAttributesByLevelCurve(UCurveTable* InAttributesByLevelCurve) { AttributesByLevelCurve = InAttributesByLevelCurve; }

    UFUNCTION(BlueprintPure, Category = "ACF|Attributes")
    bool IsAffectedByDifficultyLevel() const { return bAffectedByDifficultyLevel; }

    UFUNCTION(BlueprintCallable, Category = "ACF|Attributes")
    void SetAffectedByDifficultyLevel(bool bInAffectedByDifficultyLevel) { bAffectedByDifficultyLevel = bInAffectedByDifficultyLevel; }

    /**
     * Re-applies difficulty scaling to base attributes defined in the init DataTable or level curves.
     * Call after save load once the difficulty manager holds the restored level.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|Attributes")
    void RefreshDifficulty();

    /**
     * Sets the DataTable row handle used to initialize this character's attributes.
     * This is typically set from editor or during character creation.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetCharacterRow(FDataTableRowHandle val);

    /* this function should be called ONLY ON SERVER,*/
    UFUNCTION(BlueprintCallable, Category = ARS)
    virtual void InitializeAttributeSet();

    void InitAttributesFromLevelCurves();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    /**
     * Initializes the attributes for this character using the DataTable row.
     * Called on BeginPlay and/or when data is assigned dynamically.
     */
    virtual void InitAttributesValue();

    void InitAttributesFromDT();

    /**
     * Applies any permanent GameplayEffects (such as passive bonuses) to the character.
     */
    virtual void ApplyPermanentEffects();

    /*If this is set to true, InitializeAttributeSet is called automatically On BeginPlay serverside.
    If false you have to manually initialize this component when needed*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|Init")
    bool bAutoInitialize = false;

    /**
     * GameplayEffects that should be applied permanently when the component is initialized.
     * Useful for passive stat boosts or initial modifiers.
     */
    UPROPERTY(EditAnywhere, Category = "ACF|Init")
    TArray<TSubclassOf<UGameplayEffect>> StartingEffects;

    /**
     * Handle to the row in the attribute initialization DataTable.
     * This defines the base attribute values for this character.
     * RowType is enforced to be ACFAttributeInits.
     * The DataTable and row name on this handle are used to initialize base attribute values.
     */
    UPROPERTY(EditAnywhere, meta = (EditCondition = "LevelingType != ELevelingType::EGenerateNewStatsFromCurves", RowType = "/Script/AscentGASRuntime.ACFAttributeInits"), Category = "ACF|Leveling System")
    FDataTableRowHandle CharacterRow;

    /**
     * Handle to the row in the attribute initialization DataTable.
     * This defines the base attribute values for this character.
     * RowType is enforced to be ACFAttributeInits.
     */
    UPROPERTY(EditAnywhere, meta = (EditCondition = "LevelingType == ELevelingType::EGenerateNewStatsFromCurves"), Category = "ACF|Leveling System")
    UCurveTable* AttributesByLevelCurve;


    /**
     * Called when the component is loaded from a save or initialized at runtime.
     * Can be overridden in Blueprint to customize loading behavior.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ARS)
    void OnComponentLoaded();

    /**
     * Called when the component is saved (e.g. for persistence systems).
     * Can be overridden in Blueprint to customize save behavior.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ARS)
    void OnComponentSaved();

    UFUNCTION(BlueprintPure, Category = ACF)
    UAbilitySystemComponent* GetOwnerAbilityComponent() const;

	/**
	 * When true, base attribute values are multiplied by the
	 * difficulty scaling defined in the Difficulty Scaling DataTable (Project Settings > Ascent GAS Settings).
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|Attributes")
	bool bAffectedByDifficultyLevel = false;

private:
    void InitStats();

    UDataTable* GetAttributeToSave() const;

    /** When true, InitAttributesValue skips DataTable/curve init so saved attribute values are preserved. */
    bool bLoaded = false;

    UPROPERTY()
    TObjectPtr<UAbilitySystemComponent> abilityComp;

    UPROPERTY(Savegame)
    TArray<FAttributeSerializeNames> SaveableAttributes;

    UPROPERTY()
    TArray<FActiveGameplayEffectHandle> permanentEffects;

    UPROPERTY()
    TObjectPtr<UDataTable> allAttributes;

	/**
	 * Returns the difficulty scaling row matching the current game difficulty level, or nullptr
	 * if no difficulty is set or no matching row exists in the DataTable.
	 * The returned pointer is owned by the DataTable and remains valid for the DataTable's lifetime.
	 */
	const FACFDifficultyScaling* GetCachedDifficultyScaling() const;

	/** Returns the multiplier for a specific attribute from the given scaling row. Returns 1.0 if not found. */
	static float GetMultiplierForAttribute(const FACFDifficultyScaling& Scaling, const FGameplayAttribute& Attribute);

private:
	/** Called when the game difficulty level changes at runtime. */
	UFUNCTION()
	void OnDifficultyLevelChanged(FGameplayTag NewDifficultyLevel);

	UPROPERTY()
	mutable TWeakObjectPtr<UACFDifficultyManagerComponent> CachedDifficultyManager;
};
