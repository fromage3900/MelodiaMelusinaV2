
#pragma once

#include "Blueprint/UserWidget.h"

#include "MultiWorldSeamTransitionFXLayer.generated.h"

UCLASS(BlueprintType)
class UMultiWorldSeamTransitionFXLayer : public UUserWidget
{
    GENERATED_BODY()

public:

    UFUNCTION(BlueprintImplementableEvent)
    void SetEffect(UMaterialInstance* InMaterial);
};
