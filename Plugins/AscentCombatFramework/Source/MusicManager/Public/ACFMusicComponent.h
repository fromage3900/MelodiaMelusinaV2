// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "ACFAITypes.h"

#include "ACFMusicComponent.generated.h"

/**
 * Music manager component that handles music playback based on battle states.
 * Can be used to assign, start, stop, and override music cues dynamically during gameplay.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class MUSICMANAGER_API UACFMusicComponent : public UActorComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UACFMusicComponent();

	/**
	 * Sets a music cue for the specified battle state
	 * @param musicCue The sound cue to associate with the given state
	 * @param battleState The battle state to assign the cue to
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetMusicCueByState(USoundCue* musicCue, EBattleState battleState);

	/**
	 * Plays the music cue associated with the given battle state
	 * @param battleState The state whose cue should be played
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void PlayMusicCueByState(EBattleState battleState);

	/**
	 * Starts music playback using the currently configured state
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StartMusic();

	/**
	 * Stops the current music playback
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StopMusic();

	/**
	 * Starts playing an override music cue, ignoring battle states
	 * @param newMusic The sound cue to play as override
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StartMusicOverride(USoundCue* newMusic);

	/**
	 * Stops the currently playing override music
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StopMusicOverride();

	/**
	 * Returns the music cue associated with the given battle state
	 * @param battleState The battle state to look up
	 * @return Pointer to the associated sound cue, or nullptr
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	class USoundCue* GetMusicCueByState(EBattleState battleState) const;

	/**
	 * Returns the currently playing music cue
	 * @return The active sound cue being played, or nullptr if none
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	class USoundCue* GetCurrntlyPlayingMusic() const
	{
		return currentlyPlayingMusic;
	}

	/**
	 * Checks whether the music system has been started
	 * @return True if music was started, false otherwise
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool GetIsStarted() const
	{
		return bIsStarted;
	}

protected:
	/** If true, music will start automatically on BeginPlay */
	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	bool bAutoStart = true;

	/** Map of music cues associated with each battle state */
	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	TMap<EBattleState, USoundCue*> MusicCueByState;

	/** Duration of fade in/out transitions when changing music */
	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	float FadeTime = 2.0f;

	/** Volume multiplier applied to music playback */
	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	float VolumeMult = 1.f;

	/** Concurrency settings for the music audio component */
	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	class USoundConcurrency* concurrencySettings;

	// Called when the game starts
	virtual void BeginPlay() override;

	virtual void EndPlay(EEndPlayReason::Type reason) override;

private:
	UFUNCTION()
	void HandleStateChanged(const EBattleState& battleState);
	UPROPERTY()
	TObjectPtr<USoundCue> currentlyPlayingMusic;

	UPROPERTY()
	TObjectPtr<UAudioComponent> currentComponent;

	bool bIsStarted = false;

	void StopCurrentMusic();

	void StartMusicInternal(USoundCue* musicToPlay);

	bool IsLocallyControlled() const;
};
