// Copyright Epic Games, Inc. All Rights Reserved.

#include "RhythmBeatTracker.h"

#include "Engine/World.h"
#include "MelodiaMusicClockSubsystem.h"

URhythmBeatTracker::URhythmBeatTracker()
{
    // No tick: beats arrive from the music-clock authority, not from DeltaTime.
    PrimaryComponentTick.bCanEverTick = false;
}

void URhythmBeatTracker::BeginPlay()
{
    Super::BeginPlay();
    BindMusicClock();
}

void URhythmBeatTracker::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    UnbindMusicClock();
    Super::EndPlay(EndPlayReason);
}

UMelodiaMusicClockSubsystem* URhythmBeatTracker::GetMusicClock() const
{
    const UWorld* World = GetWorld();
    return World ? World->GetSubsystem<UMelodiaMusicClockSubsystem>() : nullptr;
}

void URhythmBeatTracker::BindMusicClock()
{
    if (bBound)
    {
        return;
    }

    UMelodiaMusicClockSubsystem* MusicClock = GetMusicClock();
    if (!MusicClock)
    {
        return;
    }

    MusicClock->OnMelodiaBeat.AddUniqueDynamic(this, &ThisClass::HandleMusicClockBeat);
    MusicClock->OnMelodiaBar.AddUniqueDynamic(this, &ThisClass::HandleMusicClockBar);
    bBound = true;
}

void URhythmBeatTracker::UnbindMusicClock()
{
    if (!bBound)
    {
        return;
    }

    if (UMelodiaMusicClockSubsystem* MusicClock = GetMusicClock())
    {
        MusicClock->OnMelodiaBeat.RemoveDynamic(this, &ThisClass::HandleMusicClockBeat);
        MusicClock->OnMelodiaBar.RemoveDynamic(this, &ThisClass::HandleMusicClockBar);
    }
    bBound = false;
}

void URhythmBeatTracker::StartTracking()
{
    bIsTracking = true;
    CurrentBeat = 0;
    CurrentBar = 0;
    BindMusicClock();

    const UMelodiaMusicClockSubsystem* MusicClock = GetMusicClock();
    if (!MusicClock || !MusicClock->HasMusicalTime())
    {
        UE_LOG(LogTemp, Log, TEXT("RhythmBeatTracker started, but no music clock is running. "
            "Start a Harmonix music source or the Quartz battle clock to produce beats."));
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("RhythmBeatTracker started at %.1f BPM"), MusicClock->GetTempoBPM());
}

void URhythmBeatTracker::StopTracking()
{
    bIsTracking = false;
    UE_LOG(LogTemp, Log, TEXT("RhythmBeatTracker stopped"));
}

void URhythmBeatTracker::SetBPM(float NewBPM)
{
    UE_LOG(LogTemp, Warning, TEXT("RhythmBeatTracker::SetBPM(%.1f) ignored. Tempo is owned by the "
        "Harmonix tempo map or the Quartz battle clock, not by this component."), NewBPM);
}

float URhythmBeatTracker::GetBPM() const
{
    const UMelodiaMusicClockSubsystem* MusicClock = GetMusicClock();
    return MusicClock ? MusicClock->GetTempoBPM() : 0.0f;
}

float URhythmBeatTracker::GetBeatPhase() const
{
    const UMelodiaMusicClockSubsystem* MusicClock = GetMusicClock();
    return MusicClock ? MusicClock->GetBeatPhase() : 0.0f;
}

bool URhythmBeatTracker::HasMusicalTime() const
{
    const UMelodiaMusicClockSubsystem* MusicClock = GetMusicClock();
    return MusicClock && MusicClock->HasMusicalTime();
}

void URhythmBeatTracker::HandleMusicClockBeat(int32 BeatNumber, int32 BeatInBar)
{
    if (!bIsTracking)
    {
        return;
    }

    CurrentBeat = BeatInBar;
    OnBeat.Broadcast(BeatInBar);
}

void URhythmBeatTracker::HandleMusicClockBar(int32 BarNumber)
{
    if (!bIsTracking)
    {
        return;
    }

    CurrentBar = BarNumber;
    OnBar.Broadcast(BarNumber);
}
