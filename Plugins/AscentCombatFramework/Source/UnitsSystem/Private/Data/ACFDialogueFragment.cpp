// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Data/ACFDialogueFragment.h"
#include "Data/ACFCharacterDataAsset.h"
#include "ADSDialoguePartecipantComponent.h"
#include "ADSBaseDialoguePartecipantComponent.h"
#include "Graph/ADSDialogue.h"
#include "Graph/ADSWorldDialogue.h"
#include "GameFramework/Pawn.h"

void UACFDialogueFragment::ApplyFragment_Implementation(APawn* pawnOwner)
{
	if (!pawnOwner) {
		return;
	}

	UADSDialoguePartecipantComponent* DialogueComp = pawnOwner->FindComponentByClass<UADSDialoguePartecipantComponent>();
	if (!DialogueComp) {
		return;
	}

	if (PartecipantTag.IsValid())
	{
		DialogueComp->SetParticipantTag(PartecipantTag);
	}

	// Portrait from the owning DataAsset when present
	if (const UACFCharacterDataAsset* OwnerDA = Cast<UACFCharacterDataAsset>(GetOuter()))
	{
		if (OwnerDA->CharacterPortrait)
		{
			DialogueComp->ChangeParticipantIcon(OwnerDA->CharacterPortrait);
		}
		DialogueComp->SetParticipantName(OwnerDA->ChatacterName);
	}

	if (DefaultCameraConfig)
	{
		DialogueComp->SetDefaultCameraConfig(DefaultCameraConfig);
	}

//	if (!pawnOwner->HasAuthority()) return;

	DialogueComp->ClearAllDialogues();

	for (UADSDialogue* Dialogue : Dialogues)
	{
		if (Dialogue)
		{
			DialogueComp->AddDialogue(Dialogue);
		}
	}
	for (UADSWorldDialogue* WDialogue : WorldDialogues)
	{
		if (WDialogue)
		{
			DialogueComp->AddDialogue(WDialogue);
		}
	}
}
