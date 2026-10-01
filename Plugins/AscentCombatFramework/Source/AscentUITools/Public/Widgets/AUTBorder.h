// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/Border.h"
#include "CoreMinimal.h"

#include "AUTBorder.generated.h"

/**
 *
 */
UCLASS()
class ASCENTUITOOLS_API UAUTBorder : public UBorder {
    GENERATED_BODY()

protected:
    UPROPERTY(EditAnywhere, Category = AUT)
    int32 StyleIndex = 0;

    UPROPERTY(EditAnywhere, Category = AUT)
    bool bUseStyle = true;

    virtual void SynchronizeProperties() override;

public:
    UFUNCTION(BlueprintCallable, Category = AUT)
    void SetStyle(int32 inStyle);

    UFUNCTION(BlueprintPure, Category = AUT)
    int32 GetStyleIndex() const
    {
        return StyleIndex;
    }
};
