// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Factory/ACFActorFactory.h"
#include "ACFAssetAction.h"

bool UACFActorFactory::CanCreateActorFrom(const FAssetData& AssetData, FText& OutErrorMsg)
{
    if (!AssetAction) {
        return true;
    }
    UObject* Asset = AssetData.FastGetAsset(false);
    if (UBlueprint* Blueprint = Cast<UBlueprint>(Asset)) {
        return Blueprint->GeneratedClass->IsChildOf(AssetAction->AssetActionSettings.AssetClass);
    }
    return Super::CanCreateActorFrom(AssetData, OutErrorMsg);
}

void UACFActorFactory::PostSpawnActor(UObject* Asset, AActor* NewActor)
{
    if (AssetAction) {
        AssetAction->PostSpawnActor(Asset, NewActor);
    }
}
