#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaMotionGrammar.generated.h"

/**
 * The one UI motion vocabulary (Figma Storybook Kit "Motion Grammar", owner-decided 2026-09-26):
 * GLINT -> UNSEAL -> BLOOM -> ORBIT -> BREATHE, snapped to the beat. At 128 BPM the stage ends fall at
 * 117 / 352 / 586 / 879 ms -- within a few ms of the Figma 160 / 340 / 560 / 860.
 */
UENUM(BlueprintType)
enum class EMelodiaMotionStage : uint8
{
	Glint,   // a single crystal wakes
	Unseal,  // tabs, plaques, latches soften open
	Bloom,   // hero emblem reaches full form, restrained overshoot
	Orbit,   // rings and beads establish hierarchy
	Breathe  // only the core or one accent keeps living
};

UCLASS()
class MELODIACORE_API UMelodiaMotionGrammarLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Stage start/end in beats: Glint 0-1/4, Unseal 1/4-3/4, Bloom 3/4-5/4, Orbit 5/4-15/8, Breathe 15/8+. */
	static void GetStageBeats(EMelodiaMotionStage Stage, float& OutStartBeat, float& OutEndBeat);

	/** 0..1 eased progress of a stage, ElapsedSeconds since the sequence started. Bloom overshoots
	 * (peaks ~1.08 then settles to 1). Breathe returns a slow 0..1 sine at one cycle per bar. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Motion")
	static float GetStageProgress(EMelodiaMotionStage Stage, float ElapsedSeconds, float BPM = 128.0f);

	/** Seconds until the sequence has fully settled into Breathe. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Motion")
	static float GetSettleSeconds(float BPM = 128.0f);
};
