// Copyright 2025 Dmitry Karpukhin. All Rights Reserved.

#include "SSFSSubsystem.h"
#include "SSFSViewExtension.h"
#include "SceneViewExtension.h"

void UScreenSpaceFogScatteringSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	ScreenSpaceFogScatteringViewExtension = FSceneViewExtensions::NewExtension<FScreenSpaceFogScatteringViewExtension>();
	UE_LOG(LogTemp, Log, TEXT("ScreenSpaceFogScatteringSubsystem: Subsystem initialized & SceneViewExtension created"));
}

void UScreenSpaceFogScatteringSubsystem::Deinitialize()
{
	{
		ScreenSpaceFogScatteringViewExtension->IsActiveThisFrameFunctions.Empty();

		FSceneViewExtensionIsActiveFunctor IsActiveFunctor;

		IsActiveFunctor.IsActiveFunction = [](const ISceneViewExtension* SceneViewExtension, const FSceneViewExtensionContext& Context)
		{
			return TOptional<bool>(false);
		};

		ScreenSpaceFogScatteringViewExtension->IsActiveThisFrameFunctions.Add(IsActiveFunctor);
	}

	ScreenSpaceFogScatteringViewExtension.Reset();
	ScreenSpaceFogScatteringViewExtension = nullptr;
}
