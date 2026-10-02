// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/TriggerSphere.h"

#include "ACFMusicVolume.generated.h"

class USoundCue;

UCLASS(Blueprintable, BlueprintType, ClassGroup = (ACF))
class MUSICMANAGER_API AACFMusicVolume : public ATriggerSphere
{
    GENERATED_BODY()

public:
    AACFMusicVolume();

protected:
    /** Music cue played while a player is inside this volume. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    TObjectPtr<USoundCue> MusicOverride;

    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void HandleBeginOverlap(AActor* OverlappedActor, AActor* OtherActor);

    UFUNCTION()
    void HandleEndOverlap(AActor* OverlappedActor, AActor* OtherActor);
};
