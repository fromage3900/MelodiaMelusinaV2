// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFConquestFunctionLibrary.h"
#include "ACFConqueringComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

UACFConqueringComponent* UACFConquestFunctionLibrary::GetLocalConqueringComponent(const UObject* WorldContextObject)
{
    const APlayerController* pc = UGameplayStatics::GetPlayerController(WorldContextObject, 0);
    if (pc) {
        return pc->FindComponentByClass<UACFConqueringComponent>();
    }

    UE_LOG(LogTemp, Warning, TEXT("Missing Assault Point! - UACFConquestFunctionLibrary::GetLocalConqueringComponent "));

    return nullptr;
}

AACFAssaultPoint* UACFConquestFunctionLibrary::GetAssaultPoint(const UObject* WorldContextObject, const FGameplayTag& pointTag)
{
    const UACFConqueringComponent* conquerComp = UACFConquestFunctionLibrary::GetLocalConqueringComponent(WorldContextObject);
    if (conquerComp) {
        return conquerComp->GetAssaultPoint(pointTag);
    }
    UE_LOG(LogTemp, Warning, TEXT("Missing Conquer Component from player Controller! - UACFConquestFunctionLibrary::GetLocalConqueringComponent "));

    return nullptr;
}
