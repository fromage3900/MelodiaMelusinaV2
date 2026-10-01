// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ANSWidgetSwitcher.h"
#include "ANSNavWidget.h"
#include "ANSUIPlayerSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "UITag.h"
#include <Components/HorizontalBox.h>
#include <Engine/GameInstance.h>

void UANSWidgetSwitcher::ProcessOnKeyDown(const FKeyEvent& InKeyEvent)
{
    UANSUIPlayerSubsystem* UISub = GetUISubsystem();
    TArray<FUIActionTag> UIactions;
    if (UISub->TryGetActionsFromKey(InKeyEvent.GetKey(), UIactions)) {
        if (UIactions.Contains(NextAction)) {
            NavigateToNext();
        } else if (UIactions.Contains(PreviousAction)) {
            NavigateToPrevious();
        }
    }
    //     TObjectPtr<UUserWidget> currentWidget = Cast<UUserWidget>(GetCurrentActiveWidget());
    //     if (currentWidget) {
    //         currentWidget->SetKeyboardFocus();
    //     }
}

void UANSWidgetSwitcher::NavigateToNext()
{
    const int32 nextIndex = GetActiveWidgetIndex() + 1;
    if (nextIndex < GetNumWidgets()) {
        SetActiveWidgetIndex(nextIndex);
    } else if (bAllowCircularNavigation) {
        SetActiveWidgetIndex(0);
    }
}

void UANSWidgetSwitcher::NavigateToPrevious()
{
    const int32 nextIndex = GetActiveWidgetIndex() - 1;
    if (nextIndex >= 0) {
        SetActiveWidgetIndex(nextIndex);
    } else if (bAllowCircularNavigation) {
        SetActiveWidgetIndex(GetNumWidgets() - 1);
    }
}

UWidget* UANSWidgetSwitcher::GetCurrentActiveWidget() const
{
    return GetWidgetAtIndex(GetActiveWidgetIndex());
}

void UANSWidgetSwitcher::SetTopBar(UHorizontalBox* topbar)
{
    Topbar = topbar;
    UANSNavWidget* widgetRef = Cast<UANSNavWidget>(Topbar->GetChildAt(0));
    if (widgetRef) {
        widgetRef->SetIsSelected(true);
    }
}

void UANSWidgetSwitcher::SetActiveWidgetIndex(int32 Index)
{
    if (Topbar && Index != GetActiveWidgetIndex()) {
        UANSNavWidget* widgetRef = Cast<UANSNavWidget>(Topbar->GetChildAt(GetActiveWidgetIndex()));
        if (widgetRef) {
            widgetRef->SetIsSelected(false);
        }
    }
    Super::SetActiveWidgetIndex(Index);
}

void UANSWidgetSwitcher::HandleSlateActiveIndexChanged(int32 ActiveIndex)
{
    Super::HandleSlateActiveIndexChanged(ActiveIndex);

    if (Topbar) {
        for (int32 index = 0; index < Topbar->GetChildrenCount(); index++) {
            UANSNavWidget* widgetRef = Cast<UANSNavWidget>(Topbar->GetChildAt(index));
            if (widgetRef ) {
                // widgetRef->SetFocus();
                widgetRef->SetIsSelected(ActiveIndex == index);
            }
        }
    }
    GetWidgetAtIndex(GetActiveWidgetIndex())->SetKeyboardFocus();
    OnIndexChanged.Broadcast(ActiveIndex);
}

UANSUIPlayerSubsystem* UANSWidgetSwitcher::GetUISubsystem() const
{
    const UGameInstance* gameInst = UGameplayStatics::GetGameInstance(this);
    return gameInst->GetSubsystem<UANSUIPlayerSubsystem>();
}
