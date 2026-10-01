// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "ANSNavWidget.h"
#include "CommonUserWidget.h"

#include "ACFSkillTreeConnectionsWidget.generated.h"


/** Struct representing a link between two widgets */
USTRUCT(BlueprintType)
struct FSkillConnection {
    GENERATED_BODY()

    UPROPERTY(Category = ACF, EditAnywhere, BlueprintReadWrite)
    TWeakObjectPtr<UWidget> From;

    UPROPERTY(Category = ACF, EditAnywhere, BlueprintReadWrite)
    TWeakObjectPtr<UWidget> To;

    UPROPERTY(Category = ACF, EditAnywhere, BlueprintReadWrite)
    FLinearColor LineColor = FLinearColor::White;

    UPROPERTY(Category = ACF, EditAnywhere, BlueprintReadWrite)
    float Thickness = 2.f;

};

/**
 * Widget responsible for drawing visual connections between skill nodes in the skill tree.
 * Each connection is a line rendered between two widgets, with customizable color and thickness.
 */
UCLASS()
class ASCENTSKILLTREE_API UACFSkillTreeConnectionsWidget : public UUserWidget {
    GENERATED_BODY()

public:
    /**
     * Adds a visual connection (line) between two widget nodes
     * @param From The start widget
     * @param To The end widget
     * @param Color The color of the line
     * @param Thickness The line thickness
     * @param offset Optional vertical offset
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void AddConnection(UWidget* From, UWidget* To, FLinearColor Color = FLinearColor::White, float Thickness = 2.f);

    /**
     * Removes all existing visual connections from the widget.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void EmptyConnections()
    {
        Connections.Empty();
    };

protected:
    /** List of connections to draw */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TArray<FSkillConnection> Connections;

    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry,
        const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle,
        bool bParentEnabled) const override;
};
