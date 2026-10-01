// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ScrollBox.h"
#include "ANSScrollBox.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnScrollIndexChanged, int32, CurrentIndex);

/**
 * A ScrollBox whose children are navigated by the ANS focus system automatically.
 * Drop ANSNavWidget subclasses as direct children in the designer; ANS handles focus movement.
 * This widget tracks which child is focused (SelectedIndex) and scrolls it into view.
 *
 * Usage:
 *   1. Place ANSScrollBox inside a NavPage widget tree.
 *   2. Add UANSNavWidget children directly inside it in the designer.
 *   3. In the NavPage Blueprint, override GetDesiredFocusTarget → return ScrollBox → GetFocusedSubWidget.
 */
UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSScrollBox : public UScrollBox
{
    GENERATED_BODY()

public:
    UANSScrollBox();

    /** Moves selection to NewIndex and scrolls it into view. */
    UFUNCTION(BlueprintCallable, Category = "ANS Navigation")
    void SetSelectedIndex(int32 NewIndex);

    UFUNCTION(BlueprintPure, Category = "ANS Navigation")
    int32 GetSelectedIndex() const { return SelectedIndex; }

    /**
     * Returns the child at SelectedIndex.
     * Use this in GetDesiredFocusTarget() on the NavPage Blueprint so that when focus
     * resets it lands on the last selected item instead of always the first.
     */
    UFUNCTION(BlueprintPure, Category = "ANS Navigation")
    UWidget* GetFocusedSubWidget() const;

    UPROPERTY(BlueprintAssignable, Category = "ANS Navigation")
    FOnScrollIndexChanged OnIndexChanged;

    virtual void ReleaseSlateResources(bool bReleaseChildren) override;

protected:
    virtual void OnSlotAdded(UPanelSlot* InSlot) override;
    virtual void OnSlotRemoved(UPanelSlot* InSlot) override;
    virtual TSharedRef<SWidget> RebuildWidget() override;

private:
    void UpdateChildrenVisuals();

    void HandleGlobalFocusChanging(
        const FFocusEvent& FocusEvent,
        const FWeakWidgetPath& OldWidgetPath,
        const TSharedPtr<SWidget>& OldWidget,
        const FWidgetPath& NewWidgetPath,
        const TSharedPtr<SWidget>& NewWidget);

    FDelegateHandle FocusChangingHandle;

    int32 SelectedIndex = 0;
};
