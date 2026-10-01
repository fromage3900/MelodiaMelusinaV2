// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ANSUITypes.h"
#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include <CommonUserWidget.h>

#include "ANSNavWidget.generated.h"

struct FFocusedWidget;
class UANSNavPageWidget;

/**
 * Single focusable element in the ANS navigation system. Override GetFocusableSubWidget in Blueprint
 * to specify which child receives focus. HandleFocusReceived / HandleFocusLost and UpdateStyle for visuals.
 */
UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSNavWidget : public UCommonUserWidget {
    GENERATED_BODY()

public:
    UANSNavWidget(const FObjectInitializer& ObjectInitializer);

    /**
     * Called when the widget receives focus.
     *
     * This function is meant to be implemented in Blueprint to define what happens when focus is gained.
     */
    UFUNCTION(BlueprintImplementableEvent, Category = ANS)
    void HandleFocusReceived();

    /**
     * Called when the widget loses focus.
     *
     * This function is meant to be implemented in Blueprint to define what happens when focus is lost.
     */
    UFUNCTION(BlueprintImplementableEvent, Category = ANS)
    void HandleFocusLost();

    /**
     * Updates the widget's visual style based on hover state.
     *
     * @param bHovered True if the widget is hovered, false otherwise.
     */
    UFUNCTION(BlueprintCallable, BlueprintImplementableEvent, Category = ANS)
    void UpdateStyle(bool bHovered);

    /**
     * Sets the style index for the widget.
     *
     * @param styleIndex The index of the style to apply.
     */
    UFUNCTION(BlueprintCallable, BlueprintImplementableEvent, Category = ANS)
    void SetStyleIndex(int32 styleIndex);

    /**
     * Requests focus for this widget.
     *
     * This function ensures the widget gains focus when called.
     */
    UFUNCTION(BlueprintCallable, Category = ANS)
    void RequestFocus();

    /**
     * Requests focus for a specific widget.
     *
     * @param widgetToFocus The widget that should receive focus.
     */
    UFUNCTION(BlueprintCallable, Category = ANS)
    void RequestFocusForWidget(/*class UANSNavPageWidget* owningPage,*/ UANSNavWidget* widgetToFocus);

    /**
     * Checks whether the widget is currently hovered.
     *
     * @return True if the widget is hovered, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ANS)
    bool GetIsHovered() const
    {
        return bIsHovered;
    }

    /**
     * Retrieves the navigation page that owns this widget.
     *
     * @return A pointer to the owning UANSNavPageWidget.
     */
    UFUNCTION(BlueprintPure, Category = ANS)
    UANSNavPageWidget* GetOwningPage() const
    {
        return navPage;
    }

    /**
     * Retrieves the focusable sub-widget inside this widget.
     *
     * This function is meant to be implemented in Blueprint to return the UI element that should receive focus.
     *
     * @return A pointer to the focusable UWidget.
     */
    UFUNCTION(BlueprintImplementableEvent, BlueprintPure, Category = ANS)
    UWidget* GetFocusableSubWidget() const;

    /**
     * Generic function for widget that requires a specific component to be initialized
     */
    UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category = ANS)
    void SetupWithComponent(const UActorComponent* component);

    UFUNCTION(BlueprintPure, Category = ANS)
    bool GetIsSelected() const { return bIsSelected; }

    /**
    * Set this nav Widget selected no matter what. 
    * It will stay selected even if its focus changes or the mouse is not pointing at it.
    */
    UFUNCTION(BlueprintCallable, Category = ANS)
    void SetIsSelected(bool val);

    /**
     * Called when a navigation event (gamepad stick / D-pad) is received on this widget.
     * Override in Blueprint to react to the direction without blocking navigation.
     * The C++ base implementation does nothing; navigation is always passed through.
     *
     * @param Direction The UI navigation direction that was triggered.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ANS)
    void OnNavigationEventReceived(EUINavigation Direction);
    virtual void OnNavigationEventReceived_Implementation(EUINavigation Direction) {}

    bool GetFocusedSubWidget(FFocusedWidget& outwidget, class UANSNavPageWidget* pageOwner);

    void OnFocusReceived();

    void OnFocusLost();

    void SetPageOwner(class UANSNavPageWidget* pageOwner);

protected:
    void NativePreConstruct() override;
    void NativeConstruct() override;
    void NativeOnMouseEnter(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
    void NativeOnMouseLeave(const FPointerEvent& InMouseEvent) override;
    FReply NativeOnFocusReceived(const FGeometry& InGeometry, const FFocusEvent& InFocusEvent) override;
    void NativeOnFocusLost(const FFocusEvent& InFocusEvent) override;
    FNavigationReply NativeOnNavigation(const FGeometry& InGeometry, const FNavigationEvent& InNavigationEvent, const FNavigationReply& InDefaultReply) override;
    void TryGetPageOwner();

private:
    TObjectPtr<class UANSNavPageWidget> navPage;

    bool bIsHovered;

    bool bIsSelected;
};
