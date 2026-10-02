// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ActionsSystem.h"

#include "ACFActionTypes.h"
#include "Modules/ModuleManager.h"
#include <GameplayTagsManager.h>
#include <Interfaces/IPluginManager.h>

#define LOCTEXT_NAMESPACE "FActionsSystem"

void FActionsSystem::StartupModule()
{
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::ExitTag);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::EnterSubTag);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::ExitSubTag);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::NotableTag);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::FXTag);
     UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::DamageTag);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::AbilityRoot);
   // UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::CooldownTag);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::AimTag);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::BlockTag);
}

void FActionsSystem::ShutdownModule()
{
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FActionsSystem, ActionsSystem);