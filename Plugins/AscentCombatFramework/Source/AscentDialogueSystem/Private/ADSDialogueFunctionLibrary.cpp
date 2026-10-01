// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSDialogueFunctionLibrary.h"
#include "ADSDialogueMasterComponent.h"
#include <GameFramework/PlayerController.h>
#include <Kismet/GameplayStatics.h>
#include "ADSDialogueSubsystem.h"

class UADSDialogueMasterComponent* UADSDialogueFunctionLibrary::GetLocalDialogueMaster(const UObject* WorldContextObject)
{
    const APlayerController* pc = UGameplayStatics::GetPlayerController(WorldContextObject, 0);
    if (pc) {
        return pc->FindComponentByClass<UADSDialogueMasterComponent>();
    }
    return nullptr;
}

FText UADSDialogueFunctionLibrary::ReplaceDialogueVariablesInText(const UObject* WorldContextObject, const FText& inText)
{
    UADSDialogueMasterComponent* dmcomp = UADSDialogueFunctionLibrary::GetLocalDialogueMaster(WorldContextObject);
    if (dmcomp) {
        return dmcomp->ReplaceVariablesInText(inText);
    }
    return inText;
}

FString UADSDialogueFunctionLibrary::ExtractLastStringFromGameplayTag(const FGameplayTag& inTag)
{
    FString TagAsString = inTag.ToString();

    // Divide la stringa usando il separatore '.'
    TArray<FString> TagParts;
    TagAsString.ParseIntoArray(TagParts, TEXT("."), true);

    // Ottieni l'ultimo elemento
    if (TagParts.Num() > 0) {
        return TagParts.Last();
    }

    return TagAsString;
}

FString UADSDialogueFunctionLibrary::ExtractActorNameFromSoftRef(const TSoftObjectPtr<AActor>& actorSoftRef)
{
    FString left, right;
    // needs to be done twixe since the path has the name duplicate
    actorSoftRef.ToString().Split(".", &left, &right);
    right.Split(".", &left, &right);
    if (right.Contains("_C_")) {
        right.Split("_C_", &left, &right);
        return left;
    } else {
        return right;
    }
}

TArray<FString> UADSDialogueFunctionLibrary::GetAvailableVoiceNames()
{
    return GEngine->GetEngineSubsystem<UADSDialogueSubsystem>()->GetAvailableVoiceNames();
}

