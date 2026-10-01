// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ANSUITypes.h"
#include "Blueprint/UserWidget.h"
#include "CommonActivatableWidget.h"
#include "CoreMinimal.h"
#include "Delegates/Delegate.h"
#include "Input/Events.h"
#include "Layout/Geometry.h"
#include "Layout/WidgetPath.h"
#include "Widgets/SWidget.h"

#include "ANSNavPageWidget.generated.h"

class UANSNavWidget;
class UANSNavbarWidget;

/** Delegate broadcast when this page widget is deactivated by the CommonUI stack
 *  (popped from the layer or hidden by another page activated on top).
 *  This is the safe hook for gameplay/network cleanup (e.g. server RPCs to end
 *  an interaction); NativeDestruct is NOT used because it is not deterministic
 *  in all teardown paths.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnWidgetRemoved);

/**
 * Full-screen navigation page that manages gamepad focus, focusable widgets, and transitions
 * to other pages (GoToWidget / GoToPreviousWidget). Works with ANSNavbarWidget for actions.
 */

UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSNavPageWidget : public UCommonActivatableWidget {
	GENERATED_BODY()

public:
	/* Constructor for the navigation page widget */
	UANSNavPageWidget();

	/* Sets the initial focus for gamepad navigation to the provided widget.
	 * If no widget is specified, it will use the default one.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void SetStartFocus(UANSNavWidget* navWidget = nullptr);

	/* Resets the focus to the default focusable widget,
	 * which is obtained from GetDesiredFocusTarget.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void ResetDefaultFocus();

	/* Sets the focus to a specific widget.
	 * If no widget is provided, the focus remains unchanged.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void SetFocusToWidget(UANSNavWidget* navWidget = nullptr);

	/* Returns the currently focused navigation widget */
	UFUNCTION(BlueprintPure, Category = ANS)
	UANSNavWidget* GetFocusedWidget() const
	{
		return focusedWidget.parentNavWidget;
	}

	/**
	 * Enables or disables ANS navigation for this page.
	 * When false: clears pending focus / dirty flags and unbinds Slate OnFocusChanging.
	 * When true: binds OnFocusChanging (if not already bound).
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void SetNavigationEnabled(bool bNavEnabled);

	/* Disables gamepad navigation */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void DisableNavigation();

	/* Checks whether gamepad navigation is enabled */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = ANS)
	bool GetNavigationEnabled() const
	{
		return bIsNavEnabled;
	}

	/* Returns the currently active navigation bar widget */
	UFUNCTION(BlueprintPure, Category = ANS)
	UANSNavbarWidget* GetCurrentNavbar();

	/* Pushes the next page onto the same CommonUI layer stack.
	 * The current page stays underneath; use GoToPreviousWidget to pop back.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void GoToWidget(TSubclassOf<UUserWidget> nextPage);

	/* Pops the top widget from the stack, revealing the previous page. */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void GoToPreviousWidget();

	/**
	 * Removes this page from the subsystem (deactivates the widget via the ANS subsystem).
	 * Equivalent to calling UANSUIPlayerSubsystem::RemoveInGameWidget on this widget.
	 * @param bUnlockUIInput  If true, restores game-only input mode after removal.
	 * @param bRemovePause    If true, un-pauses the game if it was paused by the subsystem.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void RemoveSelf(bool bUnlockUIInput = true, bool bRemovePause = true);

	/* Checks whether the system automatically switches input focus
	 * between mouse and gamepad navigation.
	 */
	UFUNCTION(BlueprintPure, Category = ANS)
	bool GetAutoSwitchFromMouseAndGamepad() const { return bAutoSwitchFromMouseAndGamepad; }

	/* Enables or disables the automatic switching between
	 * mouse and gamepad navigation input.
	 */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void SetAutoSwitchFromMouseAndGamepad(bool val) { bAutoSwitchFromMouseAndGamepad = val; }

	/** Marks this page to keep retrying ResetDefaultFocus every tick until keyboard focus is valid. */
	void SetNeedsReset() { bNeedsReset = true; }

	/**
	 * Generic init for widgets that need a specific component reference.
	 */
	UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category = ANS)
	void SetupWithComponent(const UActorComponent* component);

	/**
	 * Generic init for widgets that need a specific actor reference.
	 */
	UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category = ANS)
	void SetupWithActor(AActor* actor);

	/**
	 * Delegate that is triggered when the page is deactivated by the CommonUI
	 * stack (popped or hidden by another page on top). Bind here for cleanup
	 * such as ending a server-side interaction; do NOT use NativeDestruct.
	 */
	UPROPERTY(BlueprintAssignable, Category = ANS)
	FOnWidgetRemoved OnWidgetRemoved;

	virtual TOptional<FUIInputConfig> GetDesiredInputConfig() const override;
protected:
	UFUNCTION(BlueprintNativeEvent, Category = ANS)
	void OnFocusedWidgetChanged(const FFocusedWidget& newFocusedWidget);

	virtual void NativeOnActivated() override;
	virtual void NativeOnDeactivated() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UCommonInputSubsystem* GetInputSubsystem() const;
	void GatherNavbar();

	virtual void NativePreConstruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FNavigationReply NativeOnNavigation(const FGeometry& MyGeometry, const FNavigationEvent& InNavigationEvent, const FNavigationReply& InDefaultReply) override;

	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	bool CheckFocusedWidget(const FGeometry& MyGeometry);

	virtual void NativeOnAddedToFocusPath(const FFocusEvent& InFocusEvent) override;

	UPROPERTY(BlueprintReadOnly, Category = ANS)
	UANSNavbarWidget* navBar;

	UPROPERTY(EditAnywhere, Category = ANS)
	bool bAutoSwitchFromMouseAndGamepad = true;

private:
	void Internal_SetFocusToWidget(const FFocusedWidget& widget, const FGeometry& MyGeometry);
	bool Internal_SetFocusToNavWidget(UANSNavWidget* widget, const FGeometry& MyGeometry);

	void Internal_SetStartFocus();
	void RemoveFocusToCurrentWidget();

	TObjectPtr<class UANSUIPlayerSubsystem> UISubsystem;

	// class UWidget* currentlyFocusedWidget;
	UPROPERTY()
	FFocusedWidget startFocusedWidget;
	bool bPendingFocusRequest = false;
	bool bIsNavEnabled;

	UPROPERTY()
	FFocusedWidget focusedWidget;

	bool bNeedsReset;

	UFUNCTION()
	void HandleInputChanged(ECommonInputType bNewInputType);

	FDelegateHandle FocusChangingHandle;

	void HandleGlobalFocusChanging(
		const FFocusEvent& FocusEvent,
		const FWeakWidgetPath& OldWidgetPath,
		const TSharedPtr<SWidget>& OldWidget,
		const FWidgetPath& NewWidgetPath,
		const TSharedPtr<SWidget>& NewWidget);
};
