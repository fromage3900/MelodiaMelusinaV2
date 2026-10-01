// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ALSSaveGame.h"
#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"

#include "ALSSaveGameSettings.generated.h"

/**
 *
 */
UCLASS(config = Plugins, DefaultConfig, meta = (DisplayName = "Ascent Load & Save"))
class ASCENTSAVESYSTEM_API UALSSaveGameSettings : public UDeveloperSettings {
    GENERATED_BODY()

protected:
    UALSSaveGameSettings() 
        : SaveGameClass(UALSSaveGame::StaticClass())
    { }

    /* Stored as a soft class reference so that Blueprint subclasses survive
       engine startup (DeveloperSettings config is parsed before Blueprints
       can be loaded, which would otherwise reset the value to the default). */
    UPROPERTY(EditAnywhere, config, Category = "ALS | Defaults", meta = (MetaClass = "/Script/AscentSaveSystem.ALSSaveGame", AllowAbstract = "false"))
    TSoftClassPtr<class UALSSaveGame> SaveGameClass;

    UPROPERTY(EditAnywhere, config, Category = "ALS | Defaults")
    FName OnComponentSavedFunctionName = "OnComponentSaved";

    UPROPERTY(EditAnywhere, config, Category = "ALS | Defaults")
    FName OnComponentLoadedFunctionName = "OnComponentLoaded";

    UPROPERTY(EditAnywhere, config, Category = "ALS | Defaults")
    FString DefaultSaveName = "ACFSave";

    UPROPERTY(EditAnywhere, config, Category = "ALS | Defaults")
    FString SavesMetadata = "SaveMetadata";

    /*Slot Usable to travel player between maps*/
    UPROPERTY(EditAnywhere, config, Category = "ALS | Defaults")
    FString TravelSlotName = "TempSave";

    /**
     * Default load-time policy applied to savable actors that DO NOT have a
     * UALSLoadAndSaveComponent: when the actor is present in the level but missing
     * from the loaded save game, decides whether to destroy it.
     *
     * Default is false (forward-compatible): actors added to a level after release
     * survive old saves. Set to true to opt back into the legacy behavior where
     * any savable actor missing from the save is destroyed on load.
     */
    UPROPERTY(EditAnywhere, config, Category = "ALS | Defaults")
    bool bDestroyActorsMissingInSaveByDefault = false;

    UPROPERTY(EditAnywhere, config, Category = "ALS | Screenshot")
    int32 SaveScreenWidth = 1280;

    UPROPERTY(EditAnywhere, config, Category = "ALS | Screenshot")
    int32 SaveScreenHeight = 720;

    UPROPERTY(EditAnywhere, config, Category = "ALS | Screenshot")
    int32 MaxSlotsNum = 8;

public:
    TSubclassOf<class UALSSaveGame> GetSaveGameClass() const
    {
        if (SaveGameClass.IsNull()) {
            return UALSSaveGame::StaticClass();
        }
        UClass* LoadedClass = SaveGameClass.LoadSynchronous();
        return LoadedClass ? LoadedClass : UALSSaveGame::StaticClass();
    }

    FString GetSaveMetadataName() const
    {
        return SavesMetadata;
    }

    FString GetDefaultSaveName() const
    {
        return DefaultSaveName;
    }

    FString GetTravelSaveName() const
    {
        return TravelSlotName;
    }

    int32 GetDefaultScreenshotHeight() const
    {
        return SaveScreenHeight;
    }

    int32 GetDefaultScreenshotWidth() const
    {
        return SaveScreenWidth;
    }

    int32 GetMaxSlotsNum() const
    {
        return MaxSlotsNum;
    }

    FName GetOnComponentSavedFunctionName() const
    {
        return OnComponentSavedFunctionName;
    }

    FName GetOnComponentLoadedFunctionName() const
    {
        return OnComponentLoadedFunctionName;
    }

    bool GetDestroyActorsMissingInSaveByDefault() const
    {
        return bDestroyActorsMissingInSaveByDefault;
    }
};
