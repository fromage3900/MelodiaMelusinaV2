// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ANSScrollBox.h"
#include "ANSNavWidget.h"
#include "Widgets/Layout/SScrollBox.h"
#include <Framework/Application/SlateApplication.h>

UANSScrollBox::UANSScrollBox()
{
    SelectedIndex = 0;
    SetAnimateWheelScrolling(true);
}

TSharedRef<SWidget> UANSScrollBox::RebuildWidget()
{
    TSharedRef<SWidget> Widget = Super::RebuildWidget();

    if (MyScrollBox.IsValid())
    {
        MyScrollBox->SetScrollWhenFocusChanges(EScrollWhenFocusChanges::AnimatedScroll);
    }

    if (FSlateApplication::IsInitialized())
    {
        if (FocusChangingHandle.IsValid())
        {
            FSlateApplication::Get().OnFocusChanging().Remove(FocusChangingHandle);
        }
        FocusChangingHandle = FSlateApplication::Get().OnFocusChanging().AddUObject(
            this, &UANSScrollBox::HandleGlobalFocusChanging);
    }

    return Widget;
}

void UANSScrollBox::ReleaseSlateResources(bool bReleaseChildren)
{
    if (FSlateApplication::IsInitialized() && FocusChangingHandle.IsValid())
    {
        FSlateApplication::Get().OnFocusChanging().Remove(FocusChangingHandle);
        FocusChangingHandle = FDelegateHandle();
    }
    Super::ReleaseSlateResources(bReleaseChildren);
}

void UANSScrollBox::HandleGlobalFocusChanging(
    const FFocusEvent& /*FocusEvent*/,
    const FWeakWidgetPath& /*OldWidgetPath*/,
    const TSharedPtr<SWidget>& /*OldWidget*/,
    const FWidgetPath& NewWidgetPath,
    const TSharedPtr<SWidget>& /*NewWidget*/)
{
    // OnFocusChanging fires BEFORE focus is committed, so HasAnyUserFocus() still reports
    // the old state. We must use NewWidgetPath, which contains the incoming focus path.
    const int32 Count = GetChildrenCount();
    for (int32 i = 0; i < Count; i++)
    {
        UWidget* Child = GetChildAt(i);
        if (!Child) continue;

        TSharedPtr<SWidget> ChildSlate = Child->GetCachedWidget();
        if (ChildSlate.IsValid() && NewWidgetPath.ContainsWidget(ChildSlate.Get()))
        {
            if (SelectedIndex != i)
            {
                SelectedIndex = i;
                UpdateChildrenVisuals();
                OnIndexChanged.Broadcast(SelectedIndex);
            }
            return;
        }
    }
}

void UANSScrollBox::SetSelectedIndex(int32 NewIndex)
{
    const int32 Count = GetChildrenCount();
    if (Count == 0) return;

    NewIndex = FMath::Clamp(NewIndex, 0, Count - 1);
    if (SelectedIndex == NewIndex) return;

    SelectedIndex = NewIndex;
    UpdateChildrenVisuals();
    OnIndexChanged.Broadcast(SelectedIndex);

    if (UWidget* Selected = GetChildAt(SelectedIndex))
    {
        ScrollWidgetIntoView(Selected, true, EDescendantScrollDestination::IntoView, 0.f);
    }
}

UWidget* UANSScrollBox::GetFocusedSubWidget() const
{
    const int32 Count = GetChildrenCount();
    if (Count > 0 && SelectedIndex >= 0 && SelectedIndex < Count)
    {
        return GetChildAt(SelectedIndex);
    }
    return nullptr;
}

void UANSScrollBox::OnSlotAdded(UPanelSlot* InSlot)
{
    Super::OnSlotAdded(InSlot);
    UpdateChildrenVisuals();
}

void UANSScrollBox::OnSlotRemoved(UPanelSlot* InSlot)
{
    Super::OnSlotRemoved(InSlot);

    const int32 Count = GetChildrenCount();
    SelectedIndex = Count > 0 ? FMath::Clamp(SelectedIndex, 0, Count - 1) : 0;
}

void UANSScrollBox::UpdateChildrenVisuals()
{
    for (int32 i = 0; i < GetChildrenCount(); i++)
    {
        if (UANSNavWidget* NavWidget = Cast<UANSNavWidget>(GetChildAt(i)))
        {
            NavWidget->SetIsSelected(i == SelectedIndex);
        }
    }
}
