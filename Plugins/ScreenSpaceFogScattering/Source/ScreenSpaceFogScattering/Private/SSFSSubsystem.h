// Copyright 2025 Dmitry Karpukhin. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/EngineSubsystem.h"
#include "SSFSSubsystem.generated.h"

UCLASS()
class UScreenSpaceFogScatteringSubsystem : public UEngineSubsystem
{
	GENERATED_BODY()
public:

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

private:
	TSharedPtr<class FScreenSpaceFogScatteringViewExtension, ESPMode::ThreadSafe> ScreenSpaceFogScatteringViewExtension;
};