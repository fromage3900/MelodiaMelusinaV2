// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "ACFEditorTypes.h"

#include "ACFAssetAction.generated.h"



// Responsible for adding different functionalities to an asset in the editor.
UCLASS(Blueprintable, NotBlueprintType, /*Abstract,*/ DisplayName = "Asset Action")
class ASCENTEDITOREXTENSIONS_API UACFAssetAction : public UObject {
    GENERATED_BODY()

public:
    // Checks if the Asset Act
    virtual bool IsAssetActionValid()
    {
        return AssetActionSettings.IsValid();
    };

    // Fires when a actor has spawned from drag dropping an asset into the viewport.
    // This will ONLY fire if this Asset Action has Drag Drop support or is in the Place Actors menu.
    virtual void PostSpawnActor(UObject* Asset, AActor* NewActor);

  
protected:
    // Fires when a actor has spawned from drag dropping an asset into the viewport.
    // This will ONLY fire if this Asset Action has Drag Drop support or is in the Place Actors menu.
    UFUNCTION(BlueprintImplementableEvent, Category = "Asset Action", DisplayName = "Post Spawn Actor")
    void K2_PostSpawnActor(UObject* Asset, AActor* NewActor);

    // Gets the class from the UBlueprint asset class.
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Asset Action")
    TSubclassOf<UObject> GetClassFromAsset(UObject* Asset);

public:
    UPROPERTY(EditAnywhere, meta = (ShowOnlyInnerProperties), Category = "Asset Action")
    FAssetActionSettings AssetActionSettings;

};
