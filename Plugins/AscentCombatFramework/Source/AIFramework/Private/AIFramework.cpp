// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "AIFramework.h"
#include "Logging.h"

#include "Modules/ModuleManager.h"
#include <GameplayTagsManager.h>
#include "ACFAITypes.h"
#include "ACFSmartObjectsTags.h"

#define LOCTEXT_NAMESPACE "FAIFramework"

void FAIFramework::StartupModule()
{
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::AIWait);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::AIPatrol);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::AICombat);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::AIReturnHome);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::AIFollowLead);
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::AIRoutine);
}

void FAIFramework::ShutdownModule()
{
	
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FAIFramework, AIFramework);