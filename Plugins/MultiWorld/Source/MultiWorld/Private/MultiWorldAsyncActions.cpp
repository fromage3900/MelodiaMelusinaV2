// Copyright 2025 UNAmedia.All rights reserved.

#include "MultiWorldAsyncActions.h"

#include "MultiWorldStatics.h"

#include "MultiWorldManager.h"

void ULoadWorldAction::Activate()
{
    FOnLoadWorldCompletedDelegateSimple Delegate;
    Delegate.BindDynamic(this, &ThisClass::OnCompleted);

    UMultiWorldStatics::LoadWorldWithDelegate(RegisteredWithGameInstance.Get(), MapAsset, Params, Delegate);
}

ULoadWorldAction* ULoadWorldAction::LoadWorld(UObject* WorldContextObject, TSoftObjectPtr<UWorld> InMapAsset, FMultiWorldLoadParameters InParams)
{
    // Create Action Instance for Blueprint System
    ULoadWorldAction* Action = NewObject<ULoadWorldAction>();
    Action->MapAsset = InMapAsset;
    Action->Params = InParams;
    Action->RegisterWithGameInstance(WorldContextObject);

    return Action;
}

void ULoadWorldAction::OnCompleted(bool Success, FMultiWorldHandle WorldHandle, FMultiWorldLoadParameters LoadParams)
{
    Completed.Broadcast(Success, WorldHandle, LoadParams);

    SetReadyToDestroy();
}

void ULoadWorldAsyncAction::Activate()
{
    FOnLoadWorldCompletedDelegateSimple Delegate;
    Delegate.BindDynamic(this, &ThisClass::OnCompleted);

    UMultiWorldStatics::LoadWorldAsyncWithDelegate(RegisteredWithGameInstance.Get(), MapAsset, Params, Delegate);
}

ULoadWorldAsyncAction* ULoadWorldAsyncAction::LoadWorldAsync(UObject* WorldContextObject, TSoftObjectPtr<UWorld> InMapAsset, FMultiWorldLoadParameters InParams)
{
    // Create Action Instance for Blueprint System
    ULoadWorldAsyncAction* Action = NewObject<ULoadWorldAsyncAction>();
    Action->MapAsset = InMapAsset;
    Action->Params = InParams;
    Action->RegisterWithGameInstance(WorldContextObject);

    return Action;
}

void ULoadWorldAsyncAction::OnCompleted(bool Success, FMultiWorldHandle WorldHandle, FMultiWorldLoadParameters LoadParams)
{
    Completed.Broadcast(Success, WorldHandle, LoadParams);

    SetReadyToDestroy();
}

void UEndWorldAsyncAction::Activate()
{
    FOnEndWorldCompletedDelegateSimple Delegate;
    Delegate.BindDynamic(this, &ThisClass::OnCompleted);

    UMultiWorldStatics::EndWorldWithDelegate(RegisteredWithGameInstance.Get(), WorldHandle, Delegate);
}

UEndWorldAsyncAction* UEndWorldAsyncAction::EndWorldAsync(UObject* WorldContextObject, FMultiWorldHandle InWorldHandle)
{
    // Create Action Instance for Blueprint System
    UEndWorldAsyncAction* Action = NewObject<UEndWorldAsyncAction>();
    Action->WorldHandle = InWorldHandle;
    Action->RegisterWithGameInstance(WorldContextObject);

    return Action;
}

void UEndWorldAsyncAction::OnCompleted()
{
    Completed.Broadcast();

    SetReadyToDestroy();
}

void UEndAllWorldsAsyncAction::Activate()
{
    FOnEndWorldCompletedDelegateSimple Delegate;
    Delegate.BindDynamic(this, &ThisClass::OnCompleted);

    UMultiWorldStatics::EndAllWorldsWithDelegate(RegisteredWithGameInstance.Get(), Delegate);
}

UEndAllWorldsAsyncAction* UEndAllWorldsAsyncAction::EndAllWorldsAsync(UObject* WorldContextObject)
{
    // Create Action Instance for Blueprint System
    UEndAllWorldsAsyncAction* Action = NewObject<UEndAllWorldsAsyncAction>();
    Action->RegisterWithGameInstance(WorldContextObject);

    return Action;
}

void UEndAllWorldsAsyncAction::OnCompleted()
{
    Completed.Broadcast();

    SetReadyToDestroy();
}
