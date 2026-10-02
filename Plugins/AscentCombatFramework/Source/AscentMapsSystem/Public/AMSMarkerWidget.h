// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Blueprint/UserWidget.h"
#include "Components/Image.h"
#include "CoreMinimal.h"

#include "AMSMarkerWidget.generated.h"

/** Delegate broadcast when this marker is hovered. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnHovered, const UAMSMarkerWidget*, marker);
/** Delegate broadcast when this marker is unhovered. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnUnhovered, const UAMSMarkerWidget*, marker);

/**
 * Single marker widget on the map (icon + optional label). Used by UAMSMapWidget for each UAMSMapMarkerComponent.
 * Implement SetupMarkerIcon and HandleHovered/HandleUnhovered in Blueprint for visuals.
 */
UCLASS()
class ASCENTMAPSSYSTEM_API UAMSMarkerWidget : public UUserWidget {
    GENERATED_BODY()

public:
    /** Sets the marker icon texture. */
    UFUNCTION(BlueprintCallable, Category = AMS)
    void SetMarkerIcon(UTexture2D* icon);

    /** Called to set up the widget from a marker component; implement in Blueprint. */
    UFUNCTION(BlueprintImplementableEvent, Category = AMS)
    void SetupMarkerIcon(UAMSMapMarkerComponent* markerComp);

    UPROPERTY(BlueprintAssignable, Category = AMS)
    FOnHovered OnHovered;

    UPROPERTY(BlueprintAssignable, Category = AMS)
    FOnUnhovered OnUnhovered;

    UFUNCTION(BlueprintPure, Category = AMS)
	bool IsTracked() const { return bTracked; }

    /** Sets whether this marker is the currently tracked one. */
    UFUNCTION(BlueprintCallable, Category = AMS)
    void TrackMarker(bool bIsTracked);

    /** Called to rotate the marker (e.g. for direction); implement in Blueprint. */
    UFUNCTION(BlueprintImplementableEvent, Category = ANS)
    void Rotate(float Yaw);

protected:
    /** Icon image to display for the marker; bind in Blueprint. */
    UPROPERTY(BlueprintReadWrite, meta = (BindWidget), Category = AMS)
    UImage* Icon;

  

    UFUNCTION(BlueprintImplementableEvent, Category = ANS)
    void HandleHovered();

    UFUNCTION(BlueprintImplementableEvent, Category = ANS)
    void HandleUnhovered();
    
    UFUNCTION(BlueprintImplementableEvent, Category = AMS)
    void HandleTrackStatusChanged(bool isTracked);

    virtual void NativeOnMouseEnter(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;

    virtual void NativeOnMouseLeave(const FPointerEvent& MouseEvent) override;

    bool bTracked;
};
