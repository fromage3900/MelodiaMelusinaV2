// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ADSDialogueSubsystem.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include <Engine/Engine.h>

#include "ADSVoiceConfigDataAsset.generated.h"

class UADSDialogueSubsystem;

/**
 *
 */
UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSVoiceConfigDataAsset : public UPrimaryDataAsset {
    GENERATED_BODY()

public:
    /**
     * Returns the list of available voice names retrieved from the Dialogue Subsystem.
     * @return Array of available voice names.
     */
    UFUNCTION(BlueprintPure, Category = "ADS")
    TArray<FString> GetAvailableVoiceNames() const
    {
        return GEngine->GetEngineSubsystem<UADSDialogueSubsystem>()->GetAvailableVoiceNames();
    }

    /**
     * Attempts to find the voice configuration for a given participant tag.
     * @param ParticipantTag  The gameplay tag identifying the participant.
     * @param outConfig       The voice configuration found, if any.
     * @return True if a configuration exists for the provided tag, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = "ADS")
    bool TryGetVoiceConfigForParticipant(FADSVoiceSettings& outConfig, const FGameplayTag& participantTag) const;

    /** Voice display name selected from the available ElevenLabs voices */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Voice Generation", meta = (GetOptions = "GetAvailableVoiceNames"))
    FString SelectedVoiceName = "James - Professional British Male";

    /** Voice ID automatically retrieved from the ElevenLabs service for the selected voice */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Voice Generation")
    FString VoiceID = "lUTamkMw7gOzZbFIwmq4";

    UPROPERTY(EditAnywhere, meta = (Categories = "Character"), BlueprintReadWrite, Category = "Voice Config")
    TMap<FGameplayTag, FADSVoiceSettings> VoiceConfigs;

protected:
#if WITH_EDITOR

    virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;

#endif

    void UpdateVoiceIDFromName();
     void UpdateVoiceIDsInConfigs(); 
};
