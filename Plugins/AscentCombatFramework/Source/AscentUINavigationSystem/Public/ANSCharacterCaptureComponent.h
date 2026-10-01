// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/SceneCaptureComponent2D.h"
#include "CoreMinimal.h"

#include "ANSCharacterCaptureComponent.generated.h"


/**
 *
 */
UCLASS(Blueprintable, ClassGroup = (ANS), meta = (BlueprintSpawnableComponent))
class ASCENTUINAVIGATIONSYSTEM_API UANSCharacterCaptureComponent : public USceneCaptureComponent2D {
    GENERATED_BODY()

public:

    UFUNCTION(BlueprintCallable, Category = ANS)
    void SetCaptureEnabled(bool bEnabled);
};
