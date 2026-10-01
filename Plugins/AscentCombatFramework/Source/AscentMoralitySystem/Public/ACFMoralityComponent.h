// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACFMoralityComponent.generated.h"

USTRUCT(BlueprintType)
struct FMoralityPoint {
	GENERATED_BODY()

public:
	// The alignment tag representing a moral stance
	UPROPERTY(Savegame)
	FGameplayTag Alignment;

	UPROPERTY(Savegame)
	float Points;
	FMoralityPoint()
		: Points(0)
	{
	}
	FMoralityPoint(FGameplayTag InAlignment, int32 InPoints)
		: Alignment(InAlignment)
		, Points(InPoints)
	{
	}

	// Overloading == operator for easy comparison based on GameplayTag
	FORCEINLINE bool operator==(const FMoralityPoint& Other) const
	{
		return this->Alignment == Other.Alignment;
	}

	FORCEINLINE bool operator!=(const FMoralityPoint& Other) const
	{
		return this->Alignment != Other.Alignment;
	}

	FORCEINLINE bool operator==(const FGameplayTag& Other) const
	{
		return this->Alignment == Other;
	}

	FORCEINLINE bool operator!=(const FGameplayTag& Other) const
	{
		return this->Alignment != Other;
	}
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnMoralityChanged);

/**
 * Morality component that manages a character's morality points and alignments.
 * Allows tracking and modifying moral stances using GameplayTags.
 * Needs to be attached to Player Controller
 */

UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTMORALITYSYSTEM_API UACFMoralityComponent : public UActorComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UACFMoralityComponent();

protected:
	/** Called when the game starts */
	virtual void BeginPlay() override;

	/** Replicated array storing morality points associated with different alignments */
	UPROPERTY(SaveGame, ReplicatedUsing = OnRep_MoralityPoints)
	TArray<FMoralityPoint> MoralityPoints;


private:

	/** Handles morality point replication */
	UFUNCTION()
	void OnRep_MoralityPoints();

public:
	/** Event triggered when morality points change */
	UPROPERTY(BlueprintAssignable, Category = "Morality")
	FOnMoralityChanged OnMoralityChanged;

	/**
	 * Adds morality points to a specified alignment.
	 * @param Alignment - The alignment to modify.
	 * @param Points - The number of points to add.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void AddMoralityPoint(FGameplayTag Alignment, float Points);

	/**
	 * Retrieves the morality points associated with a specific alignment.
	 * @param Alignment - The alignment to check.
	 * @return The number of morality points.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float GetMoralityPoints(FGameplayTag Alignment) const;

	/**
	 * Determines the alignment with the highest morality points.
	 * @return The alignment tag with the highest points.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FGameplayTag GetMoralityAlignment() const;

	/**
	 * Resets all morality points.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void ResetMorality();

protected:
	/** Handles property replication for networked gameplay */
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
