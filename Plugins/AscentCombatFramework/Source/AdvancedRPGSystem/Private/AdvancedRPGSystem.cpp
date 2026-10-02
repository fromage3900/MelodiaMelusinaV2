// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AdvancedRPGSystem.h"
#include <GameplayTagsManager.h>
#include "ARSTypes.h"

#define LOCTEXT_NAMESPACE "FAdvancedRPGSystemModule"



void FAdvancedRPGSystemModule::StartupModule()
{
    // This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
    UGameplayTagsManager::Get().AddNativeGameplayTag(ARS::PrimaryAtt);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ARS::Attribute);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ARS::Stat);

    UGameplayTagsManager::Get().AddNativeGameplayTag(ARS::DifficultyRoot, TEXT("Root tag for game difficulty levels"));
    UGameplayTagsManager::Get().AddNativeGameplayTag(ARS::DifficultyVeryEasy, TEXT("Very Easy difficulty"));
    UGameplayTagsManager::Get().AddNativeGameplayTag(ARS::DifficultyEasy, TEXT("Easy difficulty"));
    UGameplayTagsManager::Get().AddNativeGameplayTag(ARS::DifficultyNormal, TEXT("Normal difficulty"));
    UGameplayTagsManager::Get().AddNativeGameplayTag(ARS::DifficultyHard, TEXT("Hard difficulty"));
    UGameplayTagsManager::Get().AddNativeGameplayTag(ARS::DifficultyVeryHard, TEXT("Very Hard difficulty"));
}

void FAdvancedRPGSystemModule::ShutdownModule()
{
    // This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
    // we call this function before unloading the module.
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAdvancedRPGSystemModule, AdvancedRPGSystem)