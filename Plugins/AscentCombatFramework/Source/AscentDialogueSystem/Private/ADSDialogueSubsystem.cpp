// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSDialogueSubsystem.h"
#include "ADSDialogueDeveloperSettings.h"
#include "ADSDialoguePartecipantComponent.h"
#include "ADSVoiceConfigDataAsset.h"
#include <Kismet/GameplayStatics.h>
#include "Graph/ADSWorldDialogue.h"
#include "Graph/ADSDialogue.h"




/**
 * Global voice cache populated by async TTS API calls.
 * Stores voice names, mappings, and last request state to avoid redundant API requests.
 */

void UADSDialogueSubsystem::RegisterParticipant(UADSDialoguePartecipantComponent* participant)
{
	if (participant) {
		Participants.Add(participant->GetParticipantTag(), participant);
	}
}

void UADSDialogueSubsystem::UnregisterParticipant(const FGameplayTag& participant)
{
	if (Participants.Contains(participant)) {
		Participants.Remove(participant);
	}
}

UADSDialoguePartecipantComponent* UADSDialogueSubsystem::FindParticipant(const FGameplayTag& participant) const
{
	if (Participants.Contains(participant)) {
		return *(Participants.Find(participant));
	}
	return nullptr;
}

FGameplayTag UADSDialogueSubsystem::GetDefaultPlayerResponseTag() const
{

	UADSDialogueDeveloperSettings* settings = GetMutableDefault<UADSDialogueDeveloperSettings>();

	if (settings) {
		return settings->GetDefaultPlayerResponseTag();
	}

	return FGameplayTag();
}

bool UADSDialogueSubsystem::StartWorldDialogue(const TArray<UADSBaseDialoguePartecipantComponent*>& participants, UADSWorldDialogue* dialogue)
{
	if (!IsValid(dialogue)) {
		UE_LOG(LogTemp, Error, TEXT("No ADS Dialogue Set!- UADSDialoguePartecipantComponent::TryStartDialogue"));
		return false;
	}
	if (participants.Num() == 0) {
		UE_LOG(LogTemp, Error, TEXT("No participants provided to TryStartDialogue!"));
		return false;
	}
	for (int32 i = 0; i < participants.Num(); ++i) {
		if (!IsValid(participants[i])) {
			UE_LOG(LogTemp, Error, TEXT("Participant at index %d is invalid!"), i);
		}
		else {
			FText name = participants[i]->GetParticipantName();
			if (name.IsEmpty() || name.ToString().Equals(TEXT("Unknown"))) {
				UE_LOG(LogTemp, Warning, TEXT("Participant at index %d has unknown name!"), i);
			}
			else {
				UE_LOG(LogTemp, Log, TEXT("Participant at index %d: %s"), i, *name.ToString());
			}
		}
	}
	RegisterDialogueEvents(dialogue);

	const bool result = IsValid(dialogue->StartDialogue(UGameplayStatics::GetPlayerController(this, 0), participants));
	if (!result) {
		UE_LOG(LogTemp, Warning, TEXT("StartDialogue failed in TryStartDialogue!"));
	}
	else {
		currentlyActiveWorldDialogues.Add(dialogue);
	}

	return result;
}


void UADSDialogueSubsystem::StopAllWorldDialogues()
{
	const TArray<UADSDialogue*> copy = currentlyActiveWorldDialogues;
	for (UADSDialogue* dialogue : copy) {
		if (IsValid(dialogue)) {
			dialogue->EndDialogue();
		}
	}
}

bool UADSDialogueSubsystem::IsPlayingWorldDialogue() const
{
	return !currentlyActiveWorldDialogues.IsEmpty();
}

bool UADSDialogueSubsystem::StartWorldDialogueFromActors(const TArray<AActor*>& participants, UADSWorldDialogue* dialogue)
{
	TArray<UADSBaseDialoguePartecipantComponent*> participantComps;
	for (const auto& actor : participants) {
		UADSBaseDialoguePartecipantComponent* dialogueComp = actor->FindComponentByClass<UADSBaseDialoguePartecipantComponent>();
		if (dialogueComp) {
			participantComps.Add(dialogueComp);
		}
		else {
			UE_LOG(LogTemp, Error, TEXT("No ADS Dialogue Component in the participant actor %s!"), *actor->GetName());
			return false;
		}
	}
	return StartWorldDialogue(participantComps, dialogue);
}

void UADSDialogueSubsystem::RegisterDialogueEvents(UADSDialogue* dialogueToStart)
{
	// Fixes a randomic bug in which the widget does not get removed
	if (!dialogueToStart->OnDialogueStarted.IsAlreadyBound(this, &UADSDialogueSubsystem::HandleDialogueStarted)) {
		dialogueToStart->OnDialogueStarted.AddDynamic(this, &UADSDialogueSubsystem::HandleDialogueStarted);
	}
	if (!dialogueToStart->OnDialogueEnded.IsAlreadyBound(this, &UADSDialogueSubsystem::HandleDialogueEnded)) {
		dialogueToStart->OnDialogueEnded.AddDynamic(this, &UADSDialogueSubsystem::HandleDialogueEnded);
	}
	if (!dialogueToStart->OnDialogueNodeActivated.IsAlreadyBound(this, &UADSDialogueSubsystem::HandleNodeActivated)) {
		dialogueToStart->OnDialogueNodeActivated.AddDynamic(this, &UADSDialogueSubsystem::HandleNodeActivated);
	}
}

void UADSDialogueSubsystem::UnregisterDialogueEvents(UADSDialogue* dialogue)
{
	if (dialogue) {
		dialogue->OnDialogueStarted.RemoveDynamic(this, &UADSDialogueSubsystem::HandleDialogueStarted);
		dialogue->OnDialogueEnded.RemoveDynamic(this, &UADSDialogueSubsystem::HandleDialogueEnded);
		dialogue->OnDialogueNodeActivated.RemoveDynamic(this, &UADSDialogueSubsystem::HandleNodeActivated);
	}
}

void UADSDialogueSubsystem::HandleDialogueStarted(UADSDialogue* dialogue)
{
	OnDialogueStarted.Broadcast(dialogue);
}

void UADSDialogueSubsystem::HandleDialogueEnded(UADSDialogue* dialogue)
{
	UnregisterDialogueEvents(dialogue);
	if (currentlyActiveWorldDialogues.Contains(dialogue)) {
		currentlyActiveWorldDialogues.Remove(dialogue);
	}
	OnDialogueEnded.Broadcast(dialogue);
}

void UADSDialogueSubsystem::HandleNodeActivated(const FGuid& nodeId)
{

}

TArray<FString> UADSDialogueSubsystem::GetAvailableVoiceNames() const
{
	const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
	const FString CurrentAPIKey = Settings->GetTTSVoiceGenAPIKey();

	if (CurrentAPIKey.IsEmpty()) {
		return { TEXT("Set API key in Project Settings") };
	}

	if (!IsCacheValid(CurrentAPIKey)) {
		return { TEXT("Click 'Refresh Voices' to load from API") };
	}

	// Ritorna una copia della lista di voci dalla cache
	return TTSVoiceCache.VoiceNames;
}

bool UADSDialogueSubsystem::TryGetParticipantVoiceConfig(FADSVoiceSettings& outVoiceConfig, const FGameplayTag& participantTag) const
{
	const UADSDialogueDeveloperSettings* Settings = GetDefault<UADSDialogueDeveloperSettings>();
	const UADSVoiceConfigDataAsset* voiceData = Settings->GetVoiceConfigDataAsset();
	if (voiceData) {
		return voiceData->TryGetVoiceConfigForParticipant(outVoiceConfig, participantTag);
	}
	return false;
}
