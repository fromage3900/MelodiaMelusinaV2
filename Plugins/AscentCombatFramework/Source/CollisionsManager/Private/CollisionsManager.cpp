// Copyright 1998-2018 Epic Games, Inc. All Rights Reserved.

#include "CollisionsManager.h"
#include "ACMTypes.h"
#include <GameplayTagsManager.h>

#define LOCTEXT_NAMESPACE "FCollisionsManagerModule"

void FCollisionsManagerModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::HitCue);
	UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::ImpactCue);
	UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::ActionCue);
	UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::ReactionCue);
}

void FCollisionsManagerModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FCollisionsManagerModule, CollisionsManager)