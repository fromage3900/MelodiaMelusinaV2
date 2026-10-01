// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFGASTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"

#include "ARSLevelingComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCharacterLevelUp, int32, NewLevel);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnCurrentExpValueChanged, int32, newCurrentExp, int32, delta);

UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTGASRUNTIME_API UARSLevelingComponent : public UActorComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UARSLevelingComponent();

	UPROPERTY(BlueprintAssignable, Category = ARS)
	FOnCharacterLevelUp OnCharacterLevelUp;

	UPROPERTY(BlueprintAssignable, Category = ARS)
	FOnCurrentExpValueChanged OnCurrentExpValueChanged;

	/*used to add exp to the current character and evaluetes levelling up.
		Server Side*/
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ARS)
	void AddExp(int32 exp);

	/* Sets the amount of available perks*/
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ARS)
	void SetAvailablePerks(int32 InPerks);

	/*Enforces a new level*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	void ForceSetLevel(int32 newLevel);

	/*Returns the amount of total experience necessary for level up*/
	UFUNCTION(BlueprintPure, Category = ARS)
	FORCEINLINE int32 GetTotaleExpToNextLevel() const { return ExpToNextLevel; };

	/*Returns the amount of exp gained since last level up*/
	UFUNCTION(BlueprintPure, Category = ARS)
	FORCEINLINE int32 GetCurrentExp() const { return CurrentExps; };

	/*Returns current level of the character*/
	UFUNCTION(BlueprintPure, Category = ARS)
	FORCEINLINE int32 GetCurrentLevel() const { return CharacterLevel; };

	/*Returns the total exps required to reach the provided level from level 0*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	int32 GetTotalExpsForLevel(int32 level) const;

	/*Returns the total exps acquired since level 0*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	int32 GetTotalExpsAcquired() const;

	/*Returns the total exps required to reach the provided level from previous level*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	int32 GetExpsForLevel(int32 level) const;

	/*Returns current level of the character*/
	UFUNCTION(BlueprintCallable, Category = ARS)
	int32 GetExpOnDeath() const;

	/*Returns current level of the character*/
	UFUNCTION(BlueprintPure, Category = ARS)
	FORCEINLINE bool CanLevelUp() const { return GetLevelingType() != ELevelingType::ECantLevelUp; };

	/*Returns current amount of available perks*/
	UFUNCTION(BlueprintPure, Category = ARS)
	FORCEINLINE int32 GetAvailablePerks() const { return Perks; };

	UFUNCTION(BlueprintCallable, Category = ARS)
	void ConsumePerks(int32 numPerks)
	{
		Perks -= numPerks;
	}

	ELevelingType GetLevelingType() const { return LevelingType; }
	void SetLevelingType(ELevelingType val) { LevelingType = val; }
	class UCurveFloat* GetExpForNextLevelCurve() const { return ExpForNextLevelCurve; }
	void SetExpForNextLevelCurve(class UCurveFloat* val) { ExpForNextLevelCurve = val; }
	float GetExpToGiveOnDeath() const { return ExpToGiveOnDeath; }
	void SetExpToGiveOnDeath(float val) { ExpToGiveOnDeath = val; }
	class UCurveFloat* GetExpToGiveOnDeathByCurrentLevel() const { return ExpToGiveOnDeathByCurrentLevel; }
	void SetExpToGiveOnDeathByCurrentLevel(class UCurveFloat* val) { ExpToGiveOnDeathByCurrentLevel = val; }
protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	virtual void OnLevelChanged();

	/*Character Level used for generation if you select Load By Level From Curve or Load By Level and Class From Datatable*/
	UPROPERTY(SaveGame, ReplicatedUsing = OnRep_CharacterLvl, EditAnywhere, BlueprintReadWrite, Category = "ACF|Leveling System")
	int32 CharacterLevel;

	/*Indicates if this character can gain exp and level up and how the stats increase is handles:
	EGenerateNewStatsFromCurves  After leveling up, new stats are generated from AttributesByLevelCurves
	EAssignPerksManually	*/
	UPROPERTY(SaveGame, EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|Leveling System")
	ELevelingType LevelingType = ELevelingType::ECantLevelUp;

	/*For Each level the amount of Exp necessary to Lvl Up*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "LevelingType != ELevelingType::ECantLevelUp"), Category = "ACF|Leveling System")
	class UCurveFloat* ExpForNextLevelCurve;

	/*Exp to be given when this character dies it has not */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "LevelingType == ELevelingType::ECantLevelUp"), Category = "ACF|Leveling System")
	float ExpToGiveOnDeath;

	/*The amount of perks received for each level up*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "LevelingType == ELevelingType::EAssignPerksManually"), Category = "ACF|Leveling System")
	int32 PerksObtainedOnLevelUp = 1;

	/*For Each level the amount of Exp given to the killer. Used Only if this character can level up*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "LevelingType != ELevelingType::ECantLevelUp"), Category = "ACF|Leveling System")
	class UCurveFloat* ExpToGiveOnDeathByCurrentLevel;

private:
	UPROPERTY(SaveGame, Replicated)
	int32 Perks = 0;

	UPROPERTY(SaveGame, ReplicatedUsing = OnRep_CurrentExp)
	int32 CurrentExps;

	UPROPERTY(SaveGame, Replicated)
	int32 ExpToNextLevel;

	UFUNCTION()
	void InitilizeLevelData();

	UFUNCTION()
	void OnLevelUp(int32 newlevel, int32 remainingExp);

	UFUNCTION()
	void OnRep_CurrentExp();

	UFUNCTION()
	void OnRep_CharacterLvl();

	void Internal_AddExp(int32 exp);

	UPROPERTY()
	int32 LastKnownExp = 0;
};
