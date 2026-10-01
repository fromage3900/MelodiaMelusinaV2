// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AMSMapMarkerComponent.h"
#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"

#include "AMSTypes.generated.h"

class UAMSMarkerWidget;
class UAMSMapMarkerComponent;
/**
 *
 */
UENUM(BlueprintType)
enum class EMarkerRotation : uint8 {
    ENoRotation = 0 UMETA(DisplayName = "Don't Rotate"),
    ERotateWithActor = 1 UMETA(DisplayName = "Rotate With Actor"),
    ERotateWithController = 1 UMETA(DisplayName = "Rotate With Controller"),
};

UENUM(BlueprintType)
enum class EAMSBackgroundType : uint8 {
    ERenderTarget = 0 UMETA(DisplayName = "Automatically Generated"),
    ECustomTexture = 1 UMETA(DisplayName = "Custom Image"),
};

UENUM()
enum class EZoomState : uint8 {
    ENone = 0,
    EZoomIn = 1,
    EZoomOut = 2
};

USTRUCT(BlueprintType)
struct FAMSMarker {

    GENERATED_BODY()

public:
    FAMSMarker()
    {
        markerComp = nullptr;
        markerWidget = nullptr;
        bHighlighted = false;
    };

    FAMSMarker(class UAMSMapMarkerComponent* inComp, class UAMSMarkerWidget* inWidget)
    {
        markerComp = inComp;
        markerWidget = inWidget;
        bHighlighted = false;
    }

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    class UAMSMapMarkerComponent* markerComp;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    class UAMSMarkerWidget* markerWidget;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    bool bHighlighted;

    void Reset()
    {
        markerComp = nullptr;
        markerWidget = nullptr;
    }

    bool ValidCheck() const;
 

    FORCEINLINE bool operator!=(const FAMSMarker& Other) const
    {
        return markerWidget != Other.markerWidget;
    }

    FORCEINLINE bool operator==(const FAMSMarker& Other) const
    {
        return markerWidget == Other.markerWidget;
    }

    FORCEINLINE bool operator!=(const UAMSMarkerWidget* Other) const
    {
        return markerWidget != Other;
    }

    FORCEINLINE bool operator==(const UAMSMarkerWidget* Other) const
    {
        return markerWidget == Other;
    }

    FORCEINLINE bool operator!=(const UAMSMapMarkerComponent* Other) const
    {
        return markerComp != Other;
    }

    FORCEINLINE bool operator==(const UAMSMapMarkerComponent* Other) const
    {
        return markerComp == Other;
    }
};

UCLASS()
class ASCENTMAPSSYSTEM_API UAMSTypes : public UObject {
    GENERATED_BODY()
};
