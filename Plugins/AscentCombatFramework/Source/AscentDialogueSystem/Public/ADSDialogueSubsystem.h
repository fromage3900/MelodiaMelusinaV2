// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ADSTypes.h"
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include <GameplayTagContainer.h>
#include <Subsystems/EngineSubsystem.h>

#include "ADSDialogueSubsystem.generated.h"

/**
 *
 */
class UADSDialoguePartecipantComponent;
class UADSWorldDialogue;

/**
 * Dialogue Subsystem that manages participants and provides integration with TTS.
 * Runs as a UEngineSubsystem, so it's available globally in the project.
 */
UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSDialogueSubsystem : public UEngineSubsystem {
	GENERATED_BODY()

public:
	/**
	 * Returns the dialogue component of the provided participant.
	 * @param participant - GameplayTag of the participant to search for
	 * @return Pointer to the participant component if found, nullptr otherwise
	 */
	UFUNCTION(BlueprintCallable, Category = ADS)
	UADSDialoguePartecipantComponent* FindParticipant(const FGameplayTag& participant) const;

	/**
	 * Returns the default tag used for player responses in dialogues.
	 * @return Default player response GameplayTag
	 */
	UFUNCTION(BlueprintCallable, Category = ADS)
	FGameplayTag GetDefaultPlayerResponseTag() const;

	UFUNCTION(BlueprintCallable, Category = ADS)
	bool StartWorldDialogueFromActors(const TArray<AActor*>& participants, UADSWorldDialogue* dialogue);

	UFUNCTION(BlueprintCallable, Category = ADS)
	bool StartWorldDialogue(const TArray<UADSBaseDialoguePartecipantComponent*>& participants, UADSWorldDialogue* dialogue);

	UFUNCTION(BlueprintCallable, Category = ADS)
	void StopAllWorldDialogues();

	UFUNCTION(BlueprintPure, Category = ADS)
	bool IsPlayingWorldDialogue() const;

	/**
	 * Registers a participant so it can be referenced in dialogue graphs.
	 * @param participant - Dialogue participant component to register
	 */
	void RegisterParticipant(UADSDialoguePartecipantComponent* participant);

	/**
	 * Unregisters a participant by tag, removing it from the subsystem.
	 * @param participant - GameplayTag of the participant to remove
	 */
	void UnregisterParticipant(const FGameplayTag& participant);

	/**
	 * Returns all available TTS voice names currently cached or retrieved from API.
	 * @return Array of available voice names
	 */
	TArray<FString> GetAvailableVoiceNames() const;

	/**
	 * Updates the selected voice ID in the participant from the cached names.
	 * Should be triggered when the user selects a voice name in the editor.
	 */
	void UpdateVoiceIDFromName();

	/** Checks if the cache is valid for the given API key */
	bool IsCacheValid(const FString& CurrentAPIKey) const { return TTSVoiceCache.IsValid(CurrentAPIKey); }

	/** Clears the voice cache */
	void ClearVoiceCache() { TTSVoiceCache.Clear(); }

	/** Updates the voice cache with new values */
	void UpdateVoiceCache(const TArray<FString>& NewVoiceNames, const TMap<FString, FString>& NewVoiceNameToID, const FString& APIKey)
	{
		TTSVoiceCache.Update(NewVoiceNames, NewVoiceNameToID, APIKey);
	}

	/**
	 * Attempts to find the voice configuration for a given participant tag.
	 * @param ParticipantTag  The gameplay tag identifying the participant.
	 * @param outConfig       The voice configuration found, if any.
	 * @return True if a configuration exists for the provided tag, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ADS)
	bool TryGetParticipantVoiceConfig(FADSVoiceSettings& outVoiceConfig, const FGameplayTag& participantTag) const;

	/** Tries to resolve a VoiceID from a given VoiceName */
	bool GetVoiceIDByName(const FString& VoiceName, FString& OutID) const
	{
		if (const FString* FoundID = TTSVoiceCache.VoiceNameToID.Find(VoiceName)) {
			OutID = *FoundID;
			return true;
		}
		return false;
	}

	// Event triggered when a dialogue starts
	UPROPERTY(BlueprintAssignable, Category = ADS)
	FOnDialogueStarted OnDialogueStarted;

	// Event triggered when a dialogue ends
	UPROPERTY(BlueprintAssignable, Category = ADS)
	FOnDialogueEnded OnDialogueEnded;

private:
	/** Map of registered participants indexed by their GameplayTag */
	UPROPERTY()
	TMap<FGameplayTag, UADSDialoguePartecipantComponent*> Participants;

	UPROPERTY()
	TArray<UADSDialogue*> currentlyActiveWorldDialogues;

	/** Global TTS voice cache (accessible from both runtime and editor) */
	FADSVoiceCache TTSVoiceCache;

	void RegisterDialogueEvents(UADSDialogue* dialogueToStart);
	void UnregisterDialogueEvents(UADSDialogue* dialogue);

	UFUNCTION()
	void HandleDialogueStarted(UADSDialogue* dialogue);

	UFUNCTION()
	void HandleDialogueEnded(UADSDialogue* dialogue);

	UFUNCTION()
	void HandleNodeActivated(const FGuid& nodeId);

};
