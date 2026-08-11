// Copyright Epic Games, Inc. All Rights Reserved.

#include "RhythmInputComponent.h"
#include "Engine/World.h"

URhythmInputComponent::URhythmInputComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void URhythmInputComponent::BeginPlay()
{
    Super::BeginPlay();
    
    CurrentBeatTime = 0.0f;
    LastInputTime = 0.0f;
}

void URhythmInputComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    
    // Update current time if needed
    // Note: CurrentBeatTime is typically set externally by RhythmBeatTracker
}

void URhythmInputComponent::RegisterRhythmInput()
{
    if (UWorld* World = GetWorld())
    {
        float CurrentTime = World->GetTimeSeconds();
        float TimingOffset = FMath::Abs(CurrentTime - CurrentBeatTime);
        
        ERhythmAccuracy Accuracy = CalculateAccuracy(TimingOffset);
        
        LastInputTime = CurrentTime;
        
        // Broadcast the input event
        OnRhythmInput.Broadcast(Accuracy, TimingOffset);
        
        UE_LOG(LogTemp, Log, TEXT("Rhythm Input: Accuracy=%d, Offset=%.3f"), 
            static_cast<int32>(Accuracy), TimingOffset);
    }
}

void URhythmInputComponent::SetCurrentBeatTime(float BeatTime)
{
    CurrentBeatTime = BeatTime;
}

ERhythmAccuracy URhythmInputComponent::CalculateAccuracy(float TimingOffset) const
{
    if (TimingOffset <= PerfectWindow)
    {
        return ERhythmAccuracy::Perfect;
    }
    else if (TimingOffset <= GoodWindow)
    {
        return ERhythmAccuracy::Good;
    }
    else
    {
        return ERhythmAccuracy::Miss;
    }
}