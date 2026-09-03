// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RhythmInputComponent.generated.h"

UENUM(BlueprintType)
enum class ERhythmAccuracy : uint8
{
    Miss UMETA(DisplayName = "Miss"),
    Good UMETA(DisplayName = "Good"),
    Perfect UMETA(DisplayName = "Perfect")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnRhythmInput, ERhythmAccuracy, Accuracy, float, TimingOffset);

UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API URhythmInputComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    URhythmInputComponent();

    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // Register a rhythm input at the current time
    UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm")
    void RegisterRhythmInput();

    // Set the current beat time (called by beat tracker)
    UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm")
    void SetCurrentBeatTime(float BeatTime);

    // Get the timing window for Perfect accuracy (in seconds)
    UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
    float GetPerfectWindow() const { return PerfectWindow; }

    // Get the timing window for Good accuracy (in seconds)
    UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
    float GetGoodWindow() const { return GoodWindow; }

    // Event fired when rhythm input is registered
    UPROPERTY(BlueprintAssignable, Category="Melodia|Rhythm")
    FOnRhythmInput OnRhythmInput;

protected:
    virtual void BeginPlay() override;

private:
    // Timing windows (in seconds)
    UPROPERTY(EditAnywhere, Category="Melodia|Rhythm", meta=(ClampMin="0.01", ClampMax="0.5"))
    float PerfectWindow = 0.05f;

    UPROPERTY(EditAnywhere, Category="Melodia|Rhythm", meta=(ClampMin="0.05", ClampMax="1.0"))
    float GoodWindow = 0.15f;

    // Current beat time (updated by beat tracker)
    float CurrentBeatTime = 0.0f;

    // Last input time
    float LastInputTime = 0.0f;

    // Calculate accuracy based on timing offset
    ERhythmAccuracy CalculateAccuracy(float TimingOffset) const;
};