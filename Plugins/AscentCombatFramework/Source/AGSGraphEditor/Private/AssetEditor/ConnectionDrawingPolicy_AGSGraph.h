// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ConnectionDrawingPolicy.h"
#include "CoreMinimal.h"

class AGSGRAPHEDITOR_API FConnectionDrawingPolicy_AGSGraph : public FConnectionDrawingPolicy {
protected:
    UEdGraph* GraphObj;
    TMap<UEdGraphNode*, int32> NodeWidgetMap;

public:
    FConnectionDrawingPolicy_AGSGraph(int32 InBackLayerID, int32 InFrontLayerID, float ZoomFactor, const FSlateRect& InClippingRect, FSlateWindowElementList& InDrawElements, UEdGraph* InGraphObj);

    // FConnectionDrawingPolicy interface
    virtual void DetermineWiringStyle(UEdGraphPin* OutputPin, UEdGraphPin* InputPin, /*inout*/ FConnectionParams& Params) override;
    virtual void Draw(TMap<TSharedRef<SWidget>, FArrangedWidget>& PinGeometries, FArrangedChildren& ArrangedNodes) override;
    virtual void DrawSplineWithArrow(const FGeometry& StartGeom, const FGeometry& EndGeom, const FConnectionParams& Params) override;
    virtual void DrawSplineWithArrow(const FVector2f& StartPoint, const FVector2f& EndPoint, const FConnectionParams& Params) override;
    virtual void DrawPreviewConnector(const FGeometry& PinGeometry, const FVector2f& StartPoint, const FVector2f& EndPoint, UEdGraphPin* Pin) override;
    virtual FVector2f ComputeSplineTangent(const FVector2f& Start, const FVector2f& End) const override;
    virtual void DetermineLinkGeometry(FArrangedChildren& ArrangedNodes, TSharedRef<SWidget>& OutputPinWidget, UEdGraphPin* OutputPin, UEdGraphPin* InputPin, FArrangedWidget*& StartWidgetGeometry, FArrangedWidget*& EndWidgetGeometry) override;
    // End of FConnectionDrawingPolicy interface

protected:
    void Internal_DrawLineWithArrow(const FVector2f& StartAnchorPoint, const FVector2f& EndAnchorPoint, const FConnectionParams& Params);
};
