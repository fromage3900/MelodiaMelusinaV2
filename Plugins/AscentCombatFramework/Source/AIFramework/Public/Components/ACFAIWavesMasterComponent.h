// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAITypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Engine/EngineTypes.h"

#include "ACFAIWavesMasterComponent.generated.h"


DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWaveStarted, const int32, waveIndex);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWaveEnded, const int32, waveIndex);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAllWavesEnded);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWaveProgressed, const int32, newIndex);


UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class AIFRAMEWORK_API UACFAIWavesMasterComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFAIWavesMasterComponent();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

	void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, SaveGame, Category = ACF)
    TArray<FWaveConfig> Waves;

public:
    /*Starts the waves from the first index*/
    /*NEEDS TO BE CALLED SERVER SIDE!*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    void StartWave();

    /*Adds an agent of the provided type to the provided wave index*/
    /*NEEDS TO BE CALLED SERVER SIDE!*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void AddAgentToWave(int32 waveIndex, TSubclassOf<AACFCharacter> agentClass, int32 count = 1);

    /*Removes an agent of the provided type to the provided wave index*/
    /*NEEDS TO BE CALLED SERVER SIDE!*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void RemoveAgentFromWave(int32 waveIndex, TSubclassOf<AACFCharacter> agentClass, int32 count = 1);

    /*Procedes to the wave at the next index. Is automatically called when a waves end*/
    /*NEEDS TO BE CALLED SERVER SIDE!*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void ProceedToNextWave();

    /*Procedes to the wave at the next index. Is automatically called when a waves end*/

    UFUNCTION(BlueprintPure, Category = ACF)
    int32 GetCurrentWaveIndex() const
    {
        return currentWaveIndex;
    }

    UFUNCTION(BlueprintCallable, Category = ACF)
    bool TryGetWaveConfigAtIndex(int32 waveIndex, FWaveConfig& outWaveConfig);

    UFUNCTION(BlueprintPure, Category = ACF)
    bool AreWavesStarted() const
    {
        return bAreWavesStarted;
    }

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnWaveStarted OnWaveStarted;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnWaveEnded OnWaveEnded;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnAllWavesEnded OnAllWavesEnded;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnWaveProgressed OnWaveProgressed;

private:
    UPROPERTY(Replicated)
    int32 currentWaveIndex;

    UPROPERTY(Replicated)

    bool bAreWavesStarted = false;

    bool Internal_StartWave(int32 waveIndex);

    UFUNCTION()
    void HandleWaveFinished();

    void TerminateCurrentWave();

    FTimerHandle nextWaveHandle;
};
