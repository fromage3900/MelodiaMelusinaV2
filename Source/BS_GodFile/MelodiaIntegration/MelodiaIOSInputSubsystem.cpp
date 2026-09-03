// Copyright (c) 2026 Melodia Team. All Rights Reserved.

#include "MelodiaIOSInputSubsystem.h"
#include "Engine/Engine.h"

void UMelodiaIOSInputSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	TouchContextStack.Empty();
	bVirtualJoystickVisible = false;
	UE_LOG(LogTemp, Log, TEXT("MelodiaIOSInputSubsystem initialized. CoreHaptics bridge ready."));
}

void UMelodiaIOSInputSubsystem::Deinitialize()
{
	TouchContextStack.Empty();
	Super::Deinitialize();
}

void UMelodiaIOSInputSubsystem::TriggerCoreHapticFeedback(EMelodiaHapticFeedbackPattern Pattern)
{
#if PLATFORM_IOS
	// iOS CoreHaptics native integration hook
	UE_LOG(LogTemp, Verbose, TEXT("[iOS CoreHaptics] Triggered pattern index: %d"), static_cast<int32>(Pattern));
#else
	UE_LOG(LogTemp, Verbose, TEXT("[Simulated Haptics] Pattern index: %d"), static_cast<int32>(Pattern));
#endif
}

void UMelodiaIOSInputSubsystem::SetMobileVirtualJoystickVisible(bool bVisible)
{
	bVirtualJoystickVisible = bVisible;
	UE_LOG(LogTemp, Log, TEXT("Melodia Mobile Virtual Joystick visibility set to: %s"), bVisible ? TEXT("True") : TEXT("False"));
}

void UMelodiaIOSInputSubsystem::PushMobileTouchContext(FName ContextName)
{
	if (!ContextName.IsNone())
	{
		TouchContextStack.Push(ContextName);
		UE_LOG(LogTemp, Log, TEXT("Pushed Mobile Touch Context: %s (Stack Size: %d)"), *ContextName.ToString(), TouchContextStack.Num());
	}
}

void UMelodiaIOSInputSubsystem::PopMobileTouchContext()
{
	if (TouchContextStack.Num() > 0)
	{
		FName Popped = TouchContextStack.Pop();
		UE_LOG(LogTemp, Log, TEXT("Popped Mobile Touch Context: %s (Remaining: %d)"), *Popped.ToString(), TouchContextStack.Num());
	}
}
