// Copyright 2025 UNAmedia.All rights reserved.

#pragma once

#include "Kismet/BlueprintAsyncActionBase.h"

#include "MultiWorldManager.h"

#include "MultiWorldAsyncActions.generated.h"

/** Class to create a proper "async" action node for the LoadWorld function. */
UCLASS()
class MULTIWORLD_API ULoadWorldAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()

public:

    /** Execute the actual load */
    virtual void Activate() override;

    /** @copydoc UMultiWorldStatics::LoadWorldWithDelegate */
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", Category = "MultiWorld", WorldContext = "WorldContextObject"))
    static ULoadWorldAction* LoadWorld(UObject* WorldContextObject, TSoftObjectPtr<UWorld> InMapAsset, FMultiWorldLoadParameters InParams);

    /// Completion delegate.
    UPROPERTY(BlueprintAssignable)
    FOnLoadWorldCompletedDelegate Completed;

private:

    UFUNCTION()
    void OnCompleted(bool Success, FMultiWorldHandle WorldHandle, FMultiWorldLoadParameters LoadParams);

private:

    TSoftObjectPtr<UWorld> MapAsset;

    FMultiWorldLoadParameters Params;
};

/** Class to create a proper async action node for the LoadWorldAsync function. */
UCLASS()
class MULTIWORLD_API ULoadWorldAsyncAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()

public:

    /** Execute the actual load */
    virtual void Activate() override;

    /** @copydoc UMultiWorldStatics::LoadWorldAsyncWithDelegate */
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", Category = "MultiWorld", WorldContext = "WorldContextObject"))
    static ULoadWorldAsyncAction* LoadWorldAsync(UObject* WorldContextObject, TSoftObjectPtr<UWorld> InMapAsset, FMultiWorldLoadParameters InParams);

    /// Completion delegate.
    UPROPERTY(BlueprintAssignable)
    FOnLoadWorldCompletedDelegate Completed;

private:

    UFUNCTION()
    void OnCompleted(bool Success, FMultiWorldHandle WorldHandle, FMultiWorldLoadParameters LoadParams);

private:

    TSoftObjectPtr<UWorld> MapAsset;

    FMultiWorldLoadParameters Params;
};

UCLASS()
class MULTIWORLD_API UEndWorldAsyncAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()

public:

    /** Execute the actual task */
    virtual void Activate() override;

    /** @copydoc UMultiWorldStatics::EndWorldAsyncWithDelegate */
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", Category = "MultiWorld", WorldContext = "WorldContextObject"))
    static UEndWorldAsyncAction* EndWorldAsync(UObject* WorldContextObject, FMultiWorldHandle WorldHandle);

    /// Completion delegate.
    UPROPERTY(BlueprintAssignable)
    FOnEndWorldCompletedDelegate Completed;

private:

    UFUNCTION()
    void OnCompleted();

private:

    FMultiWorldHandle WorldHandle;
};

UCLASS()
class MULTIWORLD_API UEndAllWorldsAsyncAction : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()

public:

    /** Execute the actual task */
    virtual void Activate() override;

    /** @copydoc UMultiWorldStatics::EndWorldAsyncWithDelegate */
    UFUNCTION(BlueprintCallable, meta = (BlueprintInternalUseOnly = "true", Category = "MultiWorld", WorldContext = "WorldContextObject"))
    static UEndAllWorldsAsyncAction* EndAllWorldsAsync(UObject* WorldContextObject);

    /// Completion delegate.
    UPROPERTY(BlueprintAssignable)
    FOnEndWorldCompletedDelegate Completed;

private:

    UFUNCTION()
    void OnCompleted();
};
