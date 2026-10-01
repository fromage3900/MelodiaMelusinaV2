// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Data/ACFCharacterFragment.h"
#include "GameplayTagContainer.h"
#include "ACFDialogueFragment.generated.h"

class UADSDialogue;
class UADSWorldDialogue;
class UADSCameraConfigDataAsset;

/**
 * Fragment that configures dialogues and world dialogues on a character's ADSDialoguePartecipantComponent.
 * Dialogues are added via AddDialogue() on the server; FADSDialogueArray replicates to all clients.
 */
UCLASS(Blueprintable, EditInlineNew, DefaultToInstanced)
class UNITSSYSTEM_API UACFDialogueFragment : public UACFCharacterFragment
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	TArray<TObjectPtr<UADSDialogue>> Dialogues;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	TArray<TObjectPtr<UADSWorldDialogue>> WorldDialogues;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "Character"), Category = "ACF")
	FGameplayTag PartecipantTag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	TObjectPtr<UADSCameraConfigDataAsset> DefaultCameraConfig;

	virtual void ApplyFragment_Implementation(APawn* pawnOwner) override;
};
