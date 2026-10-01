// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSTypes.h"
#include "ADSDialogueSubsystem.h"
#include <Engine/Engine.h>

TArray<FString> FADSVoiceSettings::GetAvailableVoiceNames() const
{
    return GEngine->GetEngineSubsystem<UADSDialogueSubsystem>()->GetAvailableVoiceNames();
}