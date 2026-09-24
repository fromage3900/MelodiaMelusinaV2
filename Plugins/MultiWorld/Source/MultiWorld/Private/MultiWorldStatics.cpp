// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#include "MultiWorldStatics.h"

#include "Components/PrimitiveComponent.h"
#include "UObject/UObjectIterator.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Engine.h"

#include "Kismet/GameplayStatics.h"

namespace {

void MovePhysicsActor(
	AActor * Actor,
	const FTransform & DeltaTransform,
	ETeleportType Teleport,
	bool bMoveActor,
	bool bMoveSimulatedComponents,
	bool bMoveAttachedActors
)
{
	if (bMoveActor)
	{
		Actor->SetActorTransform(Actor->GetActorTransform() * DeltaTransform, /*bSweep=*/false, /*OutSweepHitResult=*/nullptr, Teleport);
	}

	if (bMoveSimulatedComponents)
	{
		TArray<UPrimitiveComponent*> PrimitiveComponents;
		Actor->GetComponents(PrimitiveComponents);
		for (UPrimitiveComponent* PriComp: PrimitiveComponents)
		{
			// Root component should have been already moved by SetActorTransform().
			if (PriComp != Actor->GetRootComponent() && PriComp->IsSimulatingPhysics())
			{
				PriComp->SetWorldTransform(PriComp->GetComponentToWorld() * DeltaTransform, /*bSweep=*/false, /*OutSweepHitResult=*/nullptr, Teleport);
			}
		}
	}

	if (bMoveAttachedActors)
	{
		TArray<AActor*> AttachedActors;
		Actor->GetAttachedActors(AttachedActors);
		for(AActor * A: AttachedActors)
		{
			const bool bMoveAttachedActor = false;	/// @todo true only if A is simulated?
			MovePhysicsActor(A, DeltaTransform, Teleport, bMoveAttachedActor, bMoveSimulatedComponents, bMoveAttachedActors);
		}
	}
}

} // namespace *unnamed*



AActor* UMultiWorldStatics::GetActorOfClass(const FMultiWorldHandle& InWorldHandle, TSubclassOf<AActor> ActorClass)
{
    return UGameplayStatics::GetActorOfClass(InWorldHandle.GetWorldContextObject(), ActorClass);
}

void UMultiWorldStatics::GetAllActorsOfClass(const FMultiWorldHandle& InWorldHandle, TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors)
{
    return UGameplayStatics::GetAllActorsOfClass(InWorldHandle.GetWorldContextObject(), ActorClass, OutActors);
}

void UMultiWorldStatics::GetAllActorsWithInterface(const FMultiWorldHandle& InWorldHandle, TSubclassOf<UInterface> Interface, TArray<AActor*>& OutActors)
{
    return UGameplayStatics::GetAllActorsWithInterface(InWorldHandle.GetWorldContextObject(), Interface, OutActors);
}

void UMultiWorldStatics::GetAllActorsWithTag(const FMultiWorldHandle& InWorldHandle, FName Tag, TArray<AActor*>& OutActors)
{
    return UGameplayStatics::GetAllActorsWithTag(InWorldHandle.GetWorldContextObject(), Tag, OutActors);
}

void UMultiWorldStatics::GetAllActorsOfClassWithTag(const FMultiWorldHandle& InWorldHandle, TSubclassOf<AActor> ActorClass, FName Tag, TArray<AActor*>& OutActors)
{
    return UGameplayStatics::GetAllActorsOfClassWithTag(InWorldHandle.GetWorldContextObject(), ActorClass, Tag, OutActors);
}

void UMultiWorldStatics::GetAllObjectsWithInterface(const FMultiWorldHandle& InWorldHandle, TSubclassOf<UInterface> Interface, TArray<UObject*>& OutObjects)
{
    OutObjects.Empty();

    UObject* WorldContext = InWorldHandle.GetWorldContextObject();
    if (WorldContext == nullptr)
        return;

    UWorld* World = WorldContext->GetWorld();

    for (TObjectIterator<UObject> It; It; ++It)
    {
        if (It->GetClass()->ImplementsInterface(Interface) && IsValid(*It))
        {
            if(It->GetWorld() == World)
                OutObjects.Add(*It);
        }
    }
}

void UMultiWorldStatics::SetPhysicsActorTransform(
	AActor * Actor,
	const FTransform & NewTransform,
	ETeleportType Teleport
)
{
	MovePhysicsActor(
		Actor,
		Actor->GetActorTransform().GetRelativeTransformReverse(NewTransform),
		Teleport,
		true,	// bMoveActor
		true,	// bMoveSimulatedComponents
		true	// bMoveAttachedActors
	);
}

void UMultiWorldStatics::LoadWorldWithDelegate(const UObject* WorldContextObject, TSoftObjectPtr<UWorld> MapAsset, FMultiWorldLoadParameters InParams, FOnLoadWorldCompletedDelegateSimple OnComplete)
{
    UMultiWorldManager::GetInstance(WorldContextObject).LoadWorld(MapAsset, InParams, 
		[OnComplete](bool Success, FMultiWorldHandle WorldHandle, FMultiWorldLoadParameters Params) {
			OnComplete.ExecuteIfBound(Success, WorldHandle, Params);
		});
}

void UMultiWorldStatics::LoadWorldAsyncWithDelegate(const UObject* WorldContextObject, TSoftObjectPtr<UWorld> MapAsset, FMultiWorldLoadParameters InParams, FOnLoadWorldCompletedDelegateSimple OnComplete)
{
    UMultiWorldManager::GetInstance(WorldContextObject).LoadWorldAsync(MapAsset, InParams,
		[OnComplete](bool Success, FMultiWorldHandle WorldHandle, FMultiWorldLoadParameters Params) {
			OnComplete.ExecuteIfBound(Success, WorldHandle, Params);
		});
}

void UMultiWorldStatics::InitializeWorld(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle)
{
    UMultiWorldManager::GetInstance(WorldContextObject).InitializeWorld(InWorldHandle);
}

void UMultiWorldStatics::EndWorld(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle)
{
	FOnEndWorldCompletedDelegateSimple Delegate;
	UMultiWorldStatics::EndWorldWithDelegate(WorldContextObject, InWorldHandle, Delegate);
}

void UMultiWorldStatics::EndWorldWithDelegate(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle, FOnEndWorldCompletedDelegateSimple OnComplete)
{
	UMultiWorldManager::GetInstance(WorldContextObject).EndWorld(InWorldHandle, [OnComplete]() {
		OnComplete.ExecuteIfBound();
	});
}

void UMultiWorldStatics::EndAllWorldsWithDelegate(const UObject* WorldContextObject, FOnEndWorldCompletedDelegateSimple OnComplete)
{
	UMultiWorldManager::GetInstance(WorldContextObject).EndAllWorlds([OnComplete]() {
		OnComplete.ExecuteIfBound();
	});
}

void UMultiWorldStatics::SetShouldTickWhenInBackground(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle, bool bShouldTick)
{
    UMultiWorldManager::GetInstance(WorldContextObject).SetShouldTickWhenInBackground(InWorldHandle, bShouldTick);
}

void UMultiWorldStatics::SetAutoHandleWidgetsForMainWorld(const UObject* WorldContextObject, bool bAutoHandleWidgets)
{
    UMultiWorldManager::GetInstance(WorldContextObject).SetAutoHandleWidgetsForMainWorld(bAutoHandleWidgets);
}

void UMultiWorldStatics::SetAutoHandleInputModeForMainWorld(const UObject* WorldContextObject, bool bAutoHandleInputMode)
{
	UMultiWorldManager::GetInstance(WorldContextObject).SetAutoHandleInputModeForMainWorld(bAutoHandleInputMode);
}

bool UMultiWorldStatics::SwitchWorld(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle)
{
    return UMultiWorldManager::GetInstance(WorldContextObject).SwitchWorld(InWorldHandle);
}

void UMultiWorldStatics::RequestSwitchWorld(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle)
{
	UMultiWorldManager::GetInstance(WorldContextObject).RequestSwitchWorld(InWorldHandle, [](bool) {});
}

bool UMultiWorldStatics::ReturnToMainWorld(const UObject* WorldContextObject)
{
    return UMultiWorldManager::GetInstance(WorldContextObject).ReturnToMainWorld();
}

FMultiWorldHandle UMultiWorldStatics::GetMainWorldHandle(const UObject* WorldContextObject)
{
    return UMultiWorldManager::GetInstance(WorldContextObject).GetMainWorldHandle();
}

FMultiWorldHandle UMultiWorldStatics::GetThisWorldHandle(const UObject* WorldContextObject)
{
    return UMultiWorldManager::GetInstance(WorldContextObject).GetThisWorldHandle(WorldContextObject);
}

FMultiWorldHandle UMultiWorldStatics::GetActiveWorldHandle(const UObject* WorldContextObject)
{
    return UMultiWorldManager::GetInstance(WorldContextObject).GetActiveWorldHandle();
}

FMultiWorldHandle UMultiWorldStatics::GetWorldHandleByName(const UObject* WorldContextObject, FName WorldName)
{
    return UMultiWorldManager::GetInstance(WorldContextObject).GetWorldHandleByName(WorldName);
}

bool UMultiWorldStatics::AreWorldsEquals(const FMultiWorldHandle& InWorldHandleA, const FMultiWorldHandle& InWorldHandleB)
{
    return InWorldHandleA == InWorldHandleB;
}

bool UMultiWorldStatics::IsValidHandle(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle)
{
    return UMultiWorldManager::GetInstance(WorldContextObject).IsValidHandle(InWorldHandle);
}

UWorld* UMultiWorldStatics::GetWorldPtr(const FMultiWorldHandle& InWorldHandle)
{
	return InWorldHandle.GetWorld();
}

void UMultiWorldStatics::TransferActorToWorld(const UObject* WorldContextObject, AActor* InActor, const FMultiWorldHandle& InWorldHandle, const FMultiWorldTransferActorParameters & Options)
{
    return UMultiWorldManager::GetInstance(WorldContextObject).TransferActorToWorld(InActor, InWorldHandle, Options);
}

AActor* UMultiWorldStatics::SpawnActorInWorld(const UObject* WorldContextObject,
    TSubclassOf<class AActor> ActorClass,
    const FMultiWorldHandle& InWorldHandle,
    const FTransform& SpawnTransform,
    ESpawnActorCollisionHandlingMethod CollisionHandlingOverride,
    AActor* Owner)
{
    return UMultiWorldManager::GetInstance(WorldContextObject)
        .SpawnActorInWorld(ActorClass, InWorldHandle, SpawnTransform, CollisionHandlingOverride, Owner);
}

void UMultiWorldStatics::ExecuteConsoleCommandInWorld(const FMultiWorldHandle& InWorldHandle, const FString& Command)
{
    UObject* WorldContext = InWorldHandle.GetWorldContextObject();
    if (WorldContext == nullptr)
        return;

    UWorld* World = WorldContext->GetWorld();

    FString TruncatedCommand = Command.Left(1000);
    World->GetGameInstance()->GetGameViewportClient()->Exec(World, *TruncatedCommand, *GLog);
}

APlayerController* UMultiWorldStatics::GetPlayerController(const UObject* WorldContextObject, int32 PlayerIndex)
{
	if (UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull))
	{
		uint32 Index = 0;
		for (FConstPlayerControllerIterator Iterator = World->GetPlayerControllerIterator(); Iterator; ++Iterator)
		{
			APlayerController* PlayerController = Iterator->Get();
			if (Index == PlayerIndex)
			{
				return PlayerController;
			}
			Index++;
		}
	}
	return nullptr;
}
