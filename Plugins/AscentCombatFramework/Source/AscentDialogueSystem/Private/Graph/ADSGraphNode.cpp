// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Graph/ADSGraphNode.h"
#include "ADSDialogueDeveloperSettings.h"
#include "ADSDialogueFunctionLibrary.h"
#include "ADSDialoguePartecipantComponent.h"
#include "AGSAction.h"
#include "AGSCondition.h"
#include "AGSGraphNode.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "Graph/ADSDialogue.h"
#include "Graph/ADSDialogueResponseNode.h"
#include "Graph/ADSGraphEdge.h"
#include "Sound/SoundNodeWavePlayer.h"
#include "Sound/SoundWave.h"
#include <Animation/AnimInstance.h>
#include <Animation/AnimMontage.h>
#include <Animation/AnimSequence.h>
#include <Components/AudioComponent.h>
#include <Components/SkeletalMeshComponent.h>
#include <GameFramework/Actor.h>
#include <GameFramework/PlayerController.h>
#include <Kismet/GameplayStatics.h>
#include <Sound/SoundCue.h>
#include "ADSDialogueSubsystem.h"
#include <Engine/Engine.h>

void UADSGraphNode::ActivateNode()
{
	Super::ActivateNode();

 	participant = Cast<UADSDialoguePartecipantComponent>(GatherPartecipant());

	for (UAGSAction* action : ActivationActions) {
		if (action) {
			action->Execute(UGameplayStatics::GetPlayerController(this, 0), this);
		}
	}

	if (!participant) {
		UE_LOG(LogTemp, Error, TEXT("Invalid Partecipant!"));
		return;
	}

	USkeletalMeshComponent* skeletal = participant->GetOwnerMesh();

	if (skeletal) {
		participant->PlayAnimationOnCharacterOwner(Animation);
		participant->PlayFacialAnimationOnCharacterOwner(FacialAnimation);

		if (SoundToPlay) {
			audioPlayer = UGameplayStatics::SpawnSoundAttached(SoundToPlay, skeletal, participant->GetVoiceSpawningSocketName());
			if (!audioPlayer) {
				UE_LOG(LogTemp, Error, TEXT("Failed to spawn audio for node"));
			}
		}
		else {
			// No sound assigned is a valid case: the node simply plays no audio.
			UE_LOG(LogTemp, Verbose, TEXT("No SoundToPlay assigned for node: %s (skipping audio playback)"), *GetName());
		}
	}
}

void UADSGraphNode::DeactivateNode()
{
	if (IsValid(audioPlayer) && audioPlayer->IsPlaying()) {
		audioPlayer->Stop();
	}
	Super::DeactivateNode();
}

UADSDialoguePartecipantComponent* UADSGraphNode::GatherPartecipant() const
{
	const UADSDialogue* dialogue = Cast<UADSDialogue>(GetGraph());

	if (!dialogue) {
		return nullptr;
	}
	return Cast<UADSDialoguePartecipantComponent>(dialogue->FindPartecipant(PartecipantTag));
}

UADSDialoguePartecipantComponent* UADSGraphNode::GetDialogueParticipant() const
{
	return participant.Get() ? participant.Get() : GatherPartecipant();
}

bool UADSGraphNode::TryGetParticipantVoiceConfig(FADSVoiceSettings& outVoiceConfig) const
{
	return GEngine->GetEngineSubsystem<UADSDialogueSubsystem>()->TryGetParticipantVoiceConfig(outVoiceConfig, PartecipantTag);
}



bool UADSGraphNode::IsLocalPlayerPartecipant() const
{
	if (controller && GetDialogueParticipant()) {
		return GetDialogueParticipant()->GetOwner() == controller->GetPawn();
	}
	return false;
}

bool UADSGraphNode::CanBeActivated(APlayerController* inController)
{
	controller = inController;

	return true;
}

#if WITH_EDITOR

FText UADSGraphNode::GetNodeTitle() const
{
	if (PartecipantTag != FGameplayTag()) {

		return FText::FromString(UADSDialogueFunctionLibrary::ExtractLastStringFromGameplayTag(PartecipantTag));
	}
	return FText::FromString("Set Participant Tag!");
}

FText UADSGraphNode::GetParagraphTitle() const
{
	const FString final = Text.ToString().Left(30);
	return FText::FromString(final);
}

void UADSGraphNode::InitializeNode()
{
	Super::InitializeNode();
	const UADSDialogue* dialogue = Cast<UADSDialogue>(GetGraph());
	PartecipantTag = dialogue->GetDefaultParticipantTag();
}

#endif
