// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AMSMarkerWidget.h"
#include <Components/CanvasPanelSlot.h>

void UAMSMarkerWidget::SetMarkerIcon(UTexture2D* icon)
{
    if (Icon) {
        Icon->SetBrushFromTexture(icon);
    }
}

void UAMSMarkerWidget::TrackMarker(bool bIsTracked)
{
    bTracked = bIsTracked;
    HandleTrackStatusChanged(bTracked);
}

void UAMSMarkerWidget::NativeOnMouseEnter(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
    Super::NativeOnMouseEnter(MyGeometry, MouseEvent);
    OnHovered.Broadcast(this);
    HandleHovered();
}

void UAMSMarkerWidget::NativeOnMouseLeave(const FPointerEvent& MouseEvent)
{
    Super::NativeOnMouseLeave(MouseEvent);
    OnUnhovered.Broadcast(this);
    HandleUnhovered();
}

