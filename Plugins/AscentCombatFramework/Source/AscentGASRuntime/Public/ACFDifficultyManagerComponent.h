// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include <GameplayTagContainer.h>

#include "ACFDifficultyManagerComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDifficultyChanged, FGameplayTag, NewDifficultyLevel);

/**
 * Component that manages the current game difficulty level.
 * Intended to live on the GameState so that it is globally accessible and replicated.
 * The difficulty tag is flagged as SaveGame for persistence and Replicated for multiplayer.
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTGASRUNTIME_API UACFDifficultyManagerComponent : public UActorComponent {
	GENERATED_BODY()

public:
	UACFDifficultyManagerComponent();

	/** Returns the current difficulty level tag. */
	UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
	FGameplayTag GetCurrentDifficultyLevel() const { return CurrentDifficultyLevel; }

	/**
	 * Sets the current difficulty level and broadcasts OnDifficultyChanged.
	 * Should be called on the server (authority).
	 */
	UFUNCTION(BlueprintAuthorityOnly, BlueprintCallable, Category = "ACF|Difficulty")
	void SetDifficultyLevel(const FGameplayTag& NewDifficultyLevel);

	/**
	 * Force-broadcasts OnDifficultyChanged with the current difficulty value, even if the
	 * value has not changed. Use this after the property has been mutated via a path that
	 * bypasses SetDifficultyLevel (e.g. SaveGame deserialization), so listeners (such as
	 * enemy attribute components) can re-apply difficulty scaling.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Difficulty")
	void BroadcastCurrentDifficulty();

	/** Fired whenever the difficulty level changes (on server and clients via OnRep). */
	UPROPERTY(BlueprintAssignable, Category = "ACF|Difficulty")
	FOnDifficultyChanged OnDifficultyChanged;

	/**
	 * Called when the component is loaded from a save game.
	 * Broadcasts the restored difficulty so listeners can re-apply scaling.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF|Difficulty")
	void OnComponentLoaded();

protected:
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION()
	void OnRep_DifficultyLevel();

	/** The current game difficulty. Saved and replicated. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, SaveGame, ReplicatedUsing = OnRep_DifficultyLevel, meta = (Categories = "ACF.Difficulty"), Category = "ACF|Difficulty")
	FGameplayTag CurrentDifficultyLevel;
};
