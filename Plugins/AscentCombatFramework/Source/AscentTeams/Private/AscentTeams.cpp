// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AscentTeams.h"
#include "Logging.h"
#include <GameplayTagsManager.h>


#include "Modules/ModuleManager.h"

#define LOCTEXT_NAMESPACE "FAscentTeams"

namespace ACF {
const FName Teams = TEXT("Teams");
}

void FAscentTeams::StartupModule()
{
    UGameplayTagsManager::Get().AddNativeGameplayTag(ACF::Teams);
}

void FAscentTeams::ShutdownModule()
{
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAscentTeams, AscentTeams);