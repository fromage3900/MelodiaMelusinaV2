// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "ACFSkillTreeConnectionsWidget.h"

void UACFSkillTreeConnectionsWidget::AddConnection(UWidget* From, UWidget* To, FLinearColor Color, float Thickness)
{
    if (From && To) {
        FSkillConnection Connection;
        Connection.From = From;
        Connection.To = To;
        Connection.LineColor = Color;
        Connection.Thickness = Thickness;   
        Connections.Add(Connection);
    }
}

int32 UACFSkillTreeConnectionsWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry,
    const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements,
    int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
    const FGeometry& MyGeo = GetCachedGeometry();

    for (const FSkillConnection& Connection : Connections) {
        if (!Connection.From.IsValid() || !Connection.To.IsValid()) {
            continue;
        }

        const FGeometry& FromGeo = Connection.From->GetCachedGeometry();
        const FGeometry& ToGeo = Connection.To->GetCachedGeometry();

        const FVector2D FromCenter = FromGeo.GetAccumulatedLayoutTransform().TransformPoint(FromGeo.GetLocalSize() * 0.5f);
        const FVector2D ToCenter = ToGeo.GetAccumulatedLayoutTransform().TransformPoint(ToGeo.GetLocalSize() * 0.5f);

        const FVector2D LocalFrom = MyGeo.AbsoluteToLocal(FromCenter);
        const FVector2D LocalTo = MyGeo.AbsoluteToLocal(ToCenter);

        const TArray<FVector2D> LinePoints = { LocalFrom, LocalTo };

        FSlateDrawElement::MakeLines(
            OutDrawElements,
            LayerId - 1, // Draw behind
            AllottedGeometry.ToPaintGeometry(),
            LinePoints,
            ESlateDrawEffect::None,
            Connection.LineColor,
            true,
            Connection.Thickness);
    }

    return LayerId;
}
