// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ALSSavableInterface.h"
#include "ALSSaveTypes.h"
#include "CoreMinimal.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/NoExportTypes.h"
#include <Async/AsyncWork.h>

#include "ALSLoadTask.generated.h"

class UALSLoadAndSaveComponent;
class UALSSaveGame;
/**
 *
 */
DECLARE_DYNAMIC_DELEGATE_OneParam(FOnLoadFinished, const bool, Success);

class FLoadWorldTask : public FNonAbandonableTask {

    FString saveName;
    UWorld* world;
    FString levelName;
    bool bLoadAll;

public:
    FLoadWorldTask(const FString& slotName, UWorld* inWorld, const FString& inLevel, const bool loadLocalPlayer)
    {
        saveName = slotName;
        world = inWorld;
        levelName = inLevel;
        bLoadAll = loadLocalPlayer;
        if (world) {
            UGameplayStatics::GetAllActorsWithInterface(world, UALSSavableInterface::StaticClass(), LoadableActors);
        }
        SuccessfullyLoadedActors.Empty();
        ToBeDestroyed.Empty();
        ToBeSpawned.Empty();
    }

    void DoWork();

private:

    TObjectPtr<UALSSaveGame> loadedGame;

    bool bLoading = false;

    FName currentlyLoadingMap;

    bool DeserializeActor(AActor* Actor, const FALSActorData& Record);

    void FinishLoad(const bool bSuccess);
    void ReloadPlayer();
    void ReloadGameState();
    void ReloadPlayerState();

    TArray<AActor*> LoadableActors;
    TMap<AActor*, FALSActorLoaded> SuccessfullyLoadedActors;
    TArray<AActor*> ToBeDestroyed;
    TArray<FALSActorData> ToBeSpawned;
    TArray<UALSLoadAndSaveComponent*> wpActors;

public:
    FORCEINLINE TStatId GetStatId() const
    {
        RETURN_QUICK_DECLARE_CYCLE_STAT(FLoadWorldTask, STATGROUP_ThreadPoolAsyncTasks);
    }
};

UCLASS()
class ASCENTSAVESYSTEM_API UALSLoadTask : public UObject {
    GENERATED_BODY()
};
