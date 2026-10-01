// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ALSLoadTask.h"
#include "ALSFunctionLibrary.h"
#include "ALSLoadAndSaveSubsystem.h"
#include "ALSSavableInterface.h"
#include "ALSSaveGame.h"
#include "ALSSaveGameSettings.h"
#include "ALSSaveTypes.h"
#include "Async/TaskGraphInterfaces.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Kismet/GameplayStatics.h"
#include "ALSLoadAndSaveComponent.h"
#include <UObject/UObjectIterator.h>

void FLoadWorldTask::DoWork()
{

    loadedGame = UGameplayStatics::GetGameInstance(this->world)->GetSubsystem<UALSLoadAndSaveSubsystem>()->GetCurrentSaveGame();

    if (!loadedGame || !world) {
        FinishLoad(false);
        return;
    }

    ToBeDestroyed.Empty();

    FALSLevelData toBeDeserialized;
    const bool bHasLevelData = loadedGame->TryGetLevelData(levelName, toBeDeserialized);

    if (bHasLevelData) {
        TArray<FALSActorData> actorsData = toBeDeserialized.GetActorsCopy();

        ToBeSpawned = actorsData;
        for (auto& actor : LoadableActors) {
            FALSActorData* actorData = actorsData.FindByKey(actor);
            if (actorData) {
                DeserializeActor(actor, *actorData);
                ToBeSpawned.Remove(*actorData);
            } else if (!UALSFunctionLibrary::IsSpecialActor(world, actor)
                && !IALSSavableInterface::Execute_ShouldBeIgnored(actor)
                && UALSFunctionLibrary::ShouldDestroyActorIfMissingInSave(actor)) {
                ToBeDestroyed.Add(actor);
            }
        }

        for (TObjectIterator<UALSLoadAndSaveComponent> It; It; ++It) {
            UALSLoadAndSaveComponent* Component = *It;
            if (IsValid(Component) && IsValid(Component->GetOwner())) {
                AActor* wpOwner = Component->GetOwner();

                // If this actor was already restored from the level's Actors list above,
                // that record comes from the last full world save and is the freshest
                // complete snapshot: don't let an older per-actor WP record overwrite it.
                if (SuccessfullyLoadedActors.Contains(wpOwner)) {
                    wpActors.Add(Component);
                    continue;
                }

                FALSActorData outData;
                if (loadedGame->TryGetStoredWPActor(levelName, wpOwner, outData)) {
                    // Use the task's DeserializeActor so the record's Transform is queued in
                    // SuccessfullyLoadedActors and applied on the game thread by GFinishLoad
                    // (together with the OnLoaded/OnComponentLoaded interface calls), exactly
                    // like actors restored from the level record. Previously this path
                    // deserialized the data blob only, silently dropping the saved transform.
                    DeserializeActor(wpOwner, outData);
                    wpActors.Add(Component);
                }
            }
        }
    }

    if (bLoadAll) {
        ReloadPlayer();
    }

    // The GameState is treated as a special, global actor: it must be restored on every
    // load regardless of whether the current level has a per-level record in the save.
    ReloadGameState();

    // Same treatment for the local PlayerState: restored on every load so cross-level
    // persistent data (reputation, achievements, etc) survives map travel.
    ReloadPlayerState();

    if (bHasLevelData) {
        loadedGame->OnLoaded();
    }

    FinishLoad(bHasLevelData || bLoadAll);
}

bool FLoadWorldTask::DeserializeActor(AActor* Actor, const FALSActorData& Record)
{
    if (!IsValid(Actor) || !Record.IsValid() || Actor->GetClass() != Record.Class) {
        return false;
    }

    UALSFunctionLibrary::DeserializeActor(Actor, Record);

    SuccessfullyLoadedActors.Add(Actor, FALSActorLoaded(Record.Transform));

    return true;
}

void FLoadWorldTask::FinishLoad(const bool bSuccess)
{
    if (IsInGameThread()) {
        UGameplayStatics::GetGameInstance(this->world)->GetSubsystem<UALSLoadAndSaveSubsystem>()->FinishLoadWork(bSuccess);
    } else {
        FSimpleDelegateGraphTask::CreateAndDispatchWhenReady(
            FSimpleDelegateGraphTask::FDelegate::CreateStatic(
                &GFinishLoad, world, ToBeSpawned, SuccessfullyLoadedActors, ToBeDestroyed, wpActors,
                bSuccess),
            GetStatId(),
            nullptr, ENamedThreads::GameThread);
    }
}

void FLoadWorldTask::ReloadPlayer()
{
    FALSPlayerData outData;
    loadedGame->GetLocalPlayer(outData);
    APlayerController* playerCont = UGameplayStatics::GetPlayerController(world, 0);

    DeserializeActor(playerCont, outData.PlayerController);

    APawn* pawn = UGameplayStatics::GetPlayerPawn(world, 0);
    FALSActorData playerData;
    DeserializeActor(pawn, outData.Pawn);
}

void FLoadWorldTask::ReloadGameState()
{
    if (!loadedGame || !loadedGame->HasGameState()) {
        return;
    }
    FALSActorData gameStateData;
    loadedGame->GetGameState(gameStateData);
    AGameStateBase* gameState = UGameplayStatics::GetGameState(world);
    DeserializeActor(gameState, gameStateData);
}

void FLoadWorldTask::ReloadPlayerState()
{
    if (!loadedGame || !loadedGame->HasPlayerState()) {
        return;
    }
    APlayerController* playerCont = UGameplayStatics::GetPlayerController(world, 0);
    if (!playerCont) {
        return;
    }
    APlayerState* playerState = playerCont->PlayerState;
    if (!playerState) {
        return;
    }
    FALSActorData playerStateData;
    loadedGame->GetPlayerState(playerStateData);
    DeserializeActor(playerState, playerStateData);
}
