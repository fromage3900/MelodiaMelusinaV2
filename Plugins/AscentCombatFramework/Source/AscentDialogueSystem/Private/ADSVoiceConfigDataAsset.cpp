// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSVoiceConfigDataAsset.h"

bool UADSVoiceConfigDataAsset::TryGetVoiceConfigForParticipant(FADSVoiceSettings& outConfig, const FGameplayTag& participantTag) const
{
    if (const FADSVoiceSettings* FoundConfig = VoiceConfigs.Find(participantTag)) {
        outConfig = *FoundConfig;
        return true;
    }
    return false;
}

#if WITH_EDITOR
void UADSVoiceConfigDataAsset::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
    Super::PostEditChangeProperty(PropertyChangedEvent);

    const FName PropertyName = PropertyChangedEvent.GetPropertyName();
    const FName MemberName = PropertyChangedEvent.GetMemberPropertyName();

    if (MemberName == GET_MEMBER_NAME_CHECKED(UADSVoiceConfigDataAsset, VoiceConfigs)) {
        UpdateVoiceIDsInConfigs();
    } else if (PropertyName == GET_MEMBER_NAME_CHECKED(UADSVoiceConfigDataAsset, SelectedVoiceName)) {
        UpdateVoiceIDFromName();
    }
}
#endif

void UADSVoiceConfigDataAsset::UpdateVoiceIDsInConfigs()
{
    if (const UADSDialogueSubsystem* DialogueSubsystem = GEngine->GetEngineSubsystem<UADSDialogueSubsystem>()) {
        for (auto& ConfigPair : VoiceConfigs) {
            FADSVoiceSettings& Config = ConfigPair.Value;
            FString OutID;
            if (DialogueSubsystem->GetVoiceIDByName(Config.SelectedVoiceName, OutID)) {
                Config.VoiceID = OutID;
            } else {
                Config.VoiceID = TEXT(""); // Clear if not found
            }
        }
    }
}

void UADSVoiceConfigDataAsset::UpdateVoiceIDFromName()
{
    if (const UADSDialogueSubsystem* DialogueSubsystem = GEngine->GetEngineSubsystem<UADSDialogueSubsystem>()) {
        FString OutID;
        if (DialogueSubsystem->GetVoiceIDByName(SelectedVoiceName, OutID)) {
            VoiceID = OutID;
        } else {
            VoiceID = TEXT(""); // Clear if not found
        }
    }
}