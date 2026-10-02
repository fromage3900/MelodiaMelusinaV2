// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CommonAnimatedSwitcher.h"
#include "Components/WidgetSwitcher.h"
#include "CoreMinimal.h"
#include "UITag.h"

#include "ANSWidgetSwitcher.generated.h"

struct FUIActionTag;
class UANSUIPlayerSubsystem;
class UHorizontalBox;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FANSOnIndexChanged, int32, newIndex);

/**
 * Custom widget switcher derived from UCommonAnimatedSwitcher.
 * Handles manual navigation between child widgets and updates an optional top bar indicator.
 */
UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSWidgetSwitcher : public UCommonAnimatedSwitcher
{
	GENERATED_BODY()

public:

	/**
	 * Processes a key input and triggers navigation if applicable.
	 *
	 * @param InKeyEvent The key event to process.
	 */
	UFUNCTION(BlueprintCallable, Category = "ANS")
	void ProcessOnKeyDown(const FKeyEvent& InKeyEvent);

	/**
	 * Switches to the next available widget.
	 * Broadcasts OnIndexChanged if successful.
	 */
	UFUNCTION(BlueprintCallable, Category = "ANS")
	void NavigateToNext();

	/**
	 * Switches to the previous available widget.
	 * Broadcasts OnIndexChanged if successful.
	 */
	UFUNCTION(BlueprintCallable, Category = "ANS")
	void NavigateToPrevious();

	/**
	 * Assigns a top bar widget, typically used for visual navigation indicators.
	 *
	 * @param topbar The horizontal box used as the top bar.
	 */
	UFUNCTION(BlueprintCallable, Category = "ANS")
	void SetTopBar(UHorizontalBox* topbar);

	/** Delegate called whenever the active index changes. */
	UPROPERTY(BlueprintAssignable, Category = "ANS")
	FANSOnIndexChanged OnIndexChanged;

	/**
	 * Returns the currently active widget in the switcher.
	 *
	 * @return The currently visible widget, or nullptr if none is active.
	 */
	UFUNCTION(BlueprintPure, BlueprintCallable, Category = "ANS")
	UWidget* GetCurrentActiveWidget() const;

	virtual void SetActiveWidgetIndex(int32 Index) override;

protected:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ANS)
	bool bAllowCircularNavigation = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ANS)
	FUIActionTag PreviousAction;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ANS)
	FUIActionTag NextAction;

	virtual void HandleSlateActiveIndexChanged(int32 ActiveIndex) override;

	UPROPERTY(BlueprintReadOnly, Category = ANS)
	UHorizontalBox* Topbar;

private:
	UANSUIPlayerSubsystem* GetUISubsystem() const;
};
