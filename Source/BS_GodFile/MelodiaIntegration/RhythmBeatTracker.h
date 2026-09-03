// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RhythmBeatTracker.generated.h"

class UMelodiaMusicClockSubsystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBeat, int32, BeatNumber);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBar, int32, BarNumber);

/**
 * Thin Blueprint-facing forwarder over UMelodiaMusicClockSubsystem.
 *
 * This component used to own a DeltaTime accumulator and its own BPM.  That
 * drifted against real audio within a minute and was a third competing notion
 * of "the beat".  It now subscribes to the single music-clock authority
 * (Harmonix, else Quartz) and re-broadcasts on the same pins, so existing
 * Blueprint graphs keep working while the timing becomes correct.
 *
 * Presentation only: it must never gate damage, turns, or results.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API URhythmBeatTracker : public UActorComponent
{
    GENERATED_BODY()

public:
    URhythmBeatTracker();

    /** Begin re-broadcasting beats from the music-clock authority. */
    UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm")
    void StartTracking();

    /** Stop re-broadcasting.  Does not stop the underlying music clock. */
    UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm")
    void StopTracking();

    UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
    bool IsTracking() const { return bIsTracking; }

    /**
     * Tempo now comes from the authored Harmonix tempo map or the Quartz battle
     * clock, so this is no longer settable here.  Retained as a warning-only
     * no-op because Blueprint graphs may still call it.
     */
    UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm", meta=(DeprecatedFunction, DeprecationMessage="Tempo is owned by the music clock. Set it on the Harmonix music source or via StartBattleClock."))
    void SetBPM(float NewBPM);

    /** Current tempo reported by the music-clock authority.  0 when no clock is running. */
    UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
    float GetBPM() const;

    /** Zero-based beat within the current bar, as last broadcast. */
    UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
    int32 GetCurrentBeat() const { return CurrentBeat; }

    UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
    int32 GetCurrentBar() const { return CurrentBar; }

    /** 0..1 within the current beat, sampled on the visual timebase. */
    UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
    float GetBeatPhase() const;

    /** True when Harmonix or Quartz is actually running. */
    UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
    bool HasMusicalTime() const;

    UPROPERTY(BlueprintAssignable, Category="Melodia|Rhythm")
    FOnBeat OnBeat;

    UPROPERTY(BlueprintAssignable, Category="Melodia|Rhythm")
    FOnBar OnBar;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    UFUNCTION()
    void HandleMusicClockBeat(int32 BeatNumber, int32 BeatInBar);

    UFUNCTION()
    void HandleMusicClockBar(int32 BarNumber);

    UMelodiaMusicClockSubsystem* GetMusicClock() const;

    void BindMusicClock();
    void UnbindMusicClock();

    bool bIsTracking = false;
    int32 CurrentBeat = 0;
    int32 CurrentBar = 0;
    bool bBound = false;
};
