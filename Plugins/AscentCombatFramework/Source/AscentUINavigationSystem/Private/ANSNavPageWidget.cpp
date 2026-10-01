// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ANSNavPageWidget.h"
#include "ANSNavWidget.h"
#include "ANSNavbarWidget.h"
#include "ANSUIPlayerSubsystem.h"
#include "ANSUITypes.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/PanelWidget.h"
#include "Components/Widget.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "Input/Events.h"
#include "Layout/WidgetPath.h"
#include "Widgets/SPanel.h"
#include "Widgets/SWidget.h"
#include <CommonInputSubsystem.h>
#include <Components/Button.h>
#include <Engine/GameInstance.h>
#include <Framework/Application/SlateApplication.h>
#include <Kismet/GameplayStatics.h>
#include <Sound/SoundBase.h>
#include <Styling/SlateTypes.h>

UANSNavPageWidget::UANSNavPageWidget()
{
	SetIsFocusable(true);
}

TOptional<FUIInputConfig> UANSNavPageWidget::GetDesiredInputConfig() const
{
	return FUIInputConfig(ECommonInputMode::Menu, EMouseCaptureMode::NoCapture);
}


void UANSNavPageWidget::SetStartFocus(UANSNavWidget* parentNavWidget /*= nullptr*/)
{
	SetIsFocusable(true);
	SetKeyboardFocus();
	if (parentNavWidget) {
		UWidget* SubWidget = parentNavWidget->GetFocusableSubWidget();
		if (SubWidget) {
			startFocusedWidget = FFocusedWidget(SubWidget, parentNavWidget);
			bPendingFocusRequest = true;
		}
	}
}

void UANSNavPageWidget::ResetDefaultFocus()
{
	UANSNavWidget* navTarget = Cast<UANSNavWidget>(GetDesiredFocusTarget());
	if (navTarget) {
		SetStartFocus(navTarget);
	}
	else if (GetDesiredFocusTarget()) {
		GetDesiredFocusTarget()->SetKeyboardFocus();
	}
}

void UANSNavPageWidget::SetFocusToWidget(UANSNavWidget* parentNavWidget)
{
	if (parentNavWidget) {
		UWidget* SubWidget = parentNavWidget->GetFocusableSubWidget();
		if (SubWidget) {
			Internal_SetFocusToWidget(FFocusedWidget(SubWidget, parentNavWidget), FGeometry());
		}
	}
}

void UANSNavPageWidget::SetNavigationEnabled(bool bNavEnabled)
{
	bIsNavEnabled = bNavEnabled;

	if (bIsNavEnabled)
	{
		if (FSlateApplication::IsInitialized() && !FocusChangingHandle.IsValid())
		{
			FocusChangingHandle = FSlateApplication::Get().OnFocusChanging().AddUObject(
				this, &UANSNavPageWidget::HandleGlobalFocusChanging);
		}
	}
	else
	{
		bPendingFocusRequest = false;

		if (FSlateApplication::IsInitialized() && FocusChangingHandle.IsValid())
		{
			FSlateApplication::Get().OnFocusChanging().Remove(FocusChangingHandle);
			FocusChangingHandle = FDelegateHandle();
		}
	}
}

void UANSNavPageWidget::DisableNavigation()
{
	SetNavigationEnabled(false);
}

UANSNavbarWidget* UANSNavPageWidget::GetCurrentNavbar()
{
	return navBar;
}

void UANSNavPageWidget::GoToWidget(TSubclassOf<UUserWidget> nextPage)
{
	if (UISubsystem && nextPage) {
		const bool bPaused = UGameplayStatics::IsGamePaused(this);
		UISubsystem->SpawnInGameWidget(nextPage, bPaused);
	}
}

void UANSNavPageWidget::GoToPreviousWidget()
{
	if (UISubsystem) {
		UISubsystem->GoToPreviousWidget();
	}
}

void UANSNavPageWidget::RemoveSelf(bool bUnlockUIInput, bool bRemovePause)
{
	if (UISubsystem) {
		UISubsystem->RemoveInGameWidget(this, bUnlockUIInput, bRemovePause);
	}
}

void UANSNavPageWidget::OnFocusedWidgetChanged_Implementation(const FFocusedWidget& newFocusedWidget)
{
}

void UANSNavPageWidget::NativeOnActivated()
{
	Super::NativeOnActivated();
	SetNavigationEnabled(true);
	SetNeedsReset();
}

void UANSNavPageWidget::NativeOnDeactivated()
{
	OnWidgetRemoved.Broadcast();
	Super::NativeOnDeactivated();
}

void UANSNavPageWidget::NativeConstruct()
{

	const UGameInstance* gameInst = UGameplayStatics::GetGameInstance(this);
	UISubsystem = gameInst->GetSubsystem<UANSUIPlayerSubsystem>();
	SetNavigationEnabled(true);
	Super::NativeConstruct();
	UCommonInputSubsystem* commonInputSub = GetInputSubsystem();
	commonInputSub->OnInputMethodChangedNative.AddUObject(this, &ThisClass::HandleInputChanged);
	HandleInputChanged(commonInputSub->GetCurrentInputType());
	GatherNavbar();
	bNeedsReset = true;
}

void UANSNavPageWidget::NativeDestruct()
{
	if (FSlateApplication::IsInitialized() && FocusChangingHandle.IsValid())
	{
		FSlateApplication::Get().OnFocusChanging().Remove(FocusChangingHandle);
		FocusChangingHandle = FDelegateHandle();
	}

	UCommonInputSubsystem* commonInputSub = GetInputSubsystem();
	if (commonInputSub) {
		commonInputSub->OnInputMethodChangedNative.RemoveAll(this);
	}
	APlayerController* controller = GetOwningPlayer();
	if (controller && GetAutoSwitchFromMouseAndGamepad()) {
		controller->bShowMouseCursor = false;
	}

	Super::NativeDestruct();
}

UCommonInputSubsystem* UANSNavPageWidget::GetInputSubsystem() const
{
	// In the new system, we may be representing an action for any player, not necessarily the one that technically owns this action icon widget
	// We want to be sure to use the LocalPlayer that the binding is actually for so we can display the icon that corresponds to their current input method
	const ULocalPlayer* BindingOwner = GetOwningLocalPlayer();
	return UCommonInputSubsystem::Get(BindingOwner);
}

void UANSNavPageWidget::GatherNavbar()
{
	TArray<UWidget*> navWidgets;
	WidgetTree->GetAllWidgets(navWidgets);

	for (auto widget : navWidgets) {
		if (widget->IsA<UANSNavbarWidget>()) {
			navBar = Cast<UANSNavbarWidget>(widget);
		}
		else if (widget->IsA<UANSNavWidget>()) {
			UANSNavWidget* navWidget = Cast<UANSNavWidget>(widget);
			navWidget->SetPageOwner(this);
		}
	}
}

void UANSNavPageWidget::NativePreConstruct()
{
	Super::NativePreConstruct();
}

void UANSNavPageWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (!bIsNavEnabled)
	{
		return;
	}

	if (bPendingFocusRequest)
	{
		Internal_SetStartFocus();
		bPendingFocusRequest = false;
		return;
	}

	if (bNeedsReset)
	{
		if (CheckFocusedWidget(MyGeometry))
		{
			bNeedsReset = false;
		}
	}
}

bool UANSNavPageWidget::CheckFocusedWidget(const FGeometry& MyGeometry)
{
	if (!UISubsystem || !bIsNavEnabled)
	{
		return false;
	}

	bool bFound = false;
	TArray<UWidget*> navWidgets;
	WidgetTree->GetAllWidgets(navWidgets);

	for (UWidget* widget : navWidgets) {
		if (widget == focusedWidget.focusedWidget) {
			if (!widget->HasAnyUserFocus())
			{
				// Slate focus may have moved to the page root (e.g. after a widget transition).
				// Make a copy: Internal_SetFocusToWidget clears focusedWidget internally via
				// RemoveFocusToCurrentWidget before reassigning, so we must not pass by reference.
				const FFocusedWidget ToRestore = focusedWidget;
				Internal_SetFocusToWidget(ToRestore, MyGeometry);
			}
			bFound = true;
			break;
		}
		else if (widget->IsA<UANSNavWidget>()) {
			UANSNavWidget* navWidget = Cast<UANSNavWidget>(widget);
			if (Internal_SetFocusToNavWidget(navWidget, MyGeometry)) {
				bFound = true;
				break;
			}
		}
		else if (widget && widget->GetIsEnabled() && widget->HasAnyUserFocus()) {
			Internal_SetFocusToWidget(FFocusedWidget(widget, nullptr), MyGeometry);
			bFound = true;
			break;
		}
	}

	if (!bFound
		&& FSlateApplication::IsInitialized()
		&& !FSlateApplication::Get().GetKeyboardFocusedWidget().IsValid())
	{
		ResetDefaultFocus();
		return false;
	}

	return bFound;
}

void UANSNavPageWidget::NativeOnAddedToFocusPath(const FFocusEvent& InFocusEvent)
{
	Super::NativeOnAddedToFocusPath(InFocusEvent);
}

FReply UANSNavPageWidget::NativeOnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (IsValid(GetCurrentNavbar())) {
		GetCurrentNavbar()->ProcessOnKeyDown(InKeyEvent);
	}
	return Super::NativeOnKeyDown(MyGeometry, InKeyEvent);
}

FNavigationReply UANSNavPageWidget::NativeOnNavigation(const FGeometry& MyGeometry, const FNavigationEvent& InNavigationEvent, const FNavigationReply& InDefaultReply)
{
	return Super::NativeOnNavigation(MyGeometry, InNavigationEvent, InDefaultReply);
}

void UANSNavPageWidget::Internal_SetFocusToWidget(const FFocusedWidget& widget, const FGeometry& MyGeometry)
{
	RemoveFocusToCurrentWidget();
	if (widget.focusedWidget) {
		focusedWidget = widget;

		UButton* focusedButton = Cast<UButton>(widget.focusedWidget);
		if (focusedButton) {
			FButtonStyle copyStyle = focusedButton->GetStyle();
			focusedWidget.initStyle = copyStyle;
			copyStyle.Normal = copyStyle.Hovered;
			focusedButton->SetStyle(copyStyle);
			/*
			USoundBase* soundBase = Cast<USoundBase>(copyStyle.HoveredSlateSound.GetResourceObject());
			if (soundBase) {
				PlaySound(soundBase);
			}*/

			focusedButton->OnHovered.Broadcast();
		}
		widget.focusedWidget->SetFocus();
		widget.focusedWidget->SetKeyboardFocus();
		if (widget.parentNavWidget) {
			widget.parentNavWidget->OnFocusReceived();
		}
		if (UISubsystem) {
			UISubsystem->OnFocusChanged.Broadcast(focusedWidget.parentNavWidget);
		}
		OnFocusedWidgetChanged(focusedWidget);
	}
}

bool UANSNavPageWidget::Internal_SetFocusToNavWidget(UANSNavWidget* widget, const FGeometry& MyGeometry)
{
	FFocusedWidget outWidgets;
	if (widget->GetFocusedSubWidget(outWidgets, this)) {
		if (outWidgets.focusedWidget == focusedWidget.focusedWidget) {
			return true;
		}
		else {
			Internal_SetFocusToWidget(outWidgets, MyGeometry);

			return true;
		}
	}
	return false;
}

void UANSNavPageWidget::Internal_SetStartFocus()
{
	if (startFocusedWidget.focusedWidget) {
		TSharedPtr<const SWidget> widgetHanlde = startFocusedWidget.focusedWidget->GetCachedWidget();
		if (widgetHanlde) {
			const FGeometry widgetGeom = widgetHanlde->GetTickSpaceGeometry();
			const FVector2D widgetPos = widgetGeom.GetAbsolutePosition();
			FWidgetPath WidgetsUnderCursor = FSlateApplication::Get().LocateWindowUnderMouse(widgetPos,
				FSlateApplication::Get().GetInteractiveTopLevelWindows());
			Internal_SetFocusToWidget(startFocusedWidget, widgetGeom);
		}
	}
}

void UANSNavPageWidget::RemoveFocusToCurrentWidget()
{
	if (IsValid(focusedWidget.focusedWidget)) {
		UButton* focusedButton = Cast<UButton>(focusedWidget.focusedWidget);
		if (focusedButton) {
			focusedButton->SetStyle(focusedWidget.initStyle);
			focusedButton->OnUnhovered.Broadcast();
		}
		if (IsValid(focusedWidget.parentNavWidget)) {
			focusedWidget.parentNavWidget->OnFocusLost();
		}
		focusedWidget = FFocusedWidget();
	}
}

void UANSNavPageWidget::HandleGlobalFocusChanging(
	const FFocusEvent& FocusEvent,
	const FWeakWidgetPath& /*OldWidgetPath*/,
	const TSharedPtr<SWidget>& /*OldWidget*/,
	const FWidgetPath& /*NewWidgetPath*/,
	const TSharedPtr<SWidget>& /*NewWidget*/)
{
	if (FocusEvent.GetCause() != EFocusCause::Mouse)
	{
		bNeedsReset = true;
	}
}

void UANSNavPageWidget::HandleInputChanged(ECommonInputType bNewInputType)
{
	if (bIsNavEnabled) {
		switch (bNewInputType) {
		case ECommonInputType::Gamepad:
			UGameplayStatics::GetPlayerController(this, 0)->SetShowMouseCursor(false);
			ResetDefaultFocus();
			break;
		case ECommonInputType::MouseAndKeyboard:
			RemoveFocusToCurrentWidget();
			UGameplayStatics::GetPlayerController(this, 0)->SetShowMouseCursor(true);

			break;
		default:
			break;
		}
	}
}
