// Copyright (c) 2026 Melodia Team. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaIOSInputSubsystem.generated.h"

/**
 * Haptic feedback pattern presets for iOS CoreHaptics engine integration.
 */
UENUM(BlueprintType)
enum class EMelodiaHapticFeedbackPattern : uint8
{
	LightTap            UMETA(DisplayName = "Light Tap"),
	MediumImpact        UMETA(DisplayName = "Medium Impact"),
	RhythmBeatHit       UMETA(DisplayName = "Rhythm Beat Hit"),
	PerfectSkillBurst   UMETA(DisplayName = "Perfect Skill Burst"),
	FailureWarning      UMETA(DisplayName = "Failure Warning")
};

/**
 * Subsystem handling iOS-specific touch input contexts, virtual joysticks, and CoreHaptics tactile feedback.
 */
UCLASS(BlueprintType, Blueprintable)
class BS_GODFILE_API UMelodiaIOSInputSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Trigger a predefined CoreHaptics feedback pattern on iOS devices */
	UFUNCTION(BlueprintCallable, Category = "Melodia|iOS|Haptics")
	void TriggerCoreHapticFeedback(EMelodiaHapticFeedbackPattern Pattern);

	/** Toggle mobile virtual joystick visibility and touch zones */
	UFUNCTION(BlueprintCallable, Category = "Melodia|iOS|Touch")
	void SetMobileVirtualJoystickVisible(bool bVisible);

	/** Push a named touch input context onto the mobile touch stack */
	UFUNCTION(BlueprintCallable, Category = "Melodia|iOS|Touch")
	void PushMobileTouchContext(FName ContextName);

	/** Pop the top touch input context from the mobile touch stack */
	UFUNCTION(BlueprintCallable, Category = "Melodia|iOS|Touch")
	void PopMobileTouchContext();

	/** Check if virtual joystick is currently active */
	UFUNCTION(BlueprintPure, Category = "Melodia|iOS|Touch")
	bool IsVirtualJoystickVisible() const { return bVirtualJoystickVisible; }

private:
	bool bVirtualJoystickVisible = false;
	TArray<FName> TouchContextStack;
};
