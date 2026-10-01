// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "UANSHorizontalNavBox.h" 
#include "ANSUIPlayerSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "ANSNavWidget.h" 
#include <Engine/GameInstance.h>

UANSHorizontalNavBox::UANSHorizontalNavBox()
{
	// Default constructor
	SelectedIndex = 0;
}

void UANSHorizontalNavBox::ProcessOnKeyDown(const FKeyEvent& InKeyEvent)
{
	UANSUIPlayerSubsystem* UISub = GetUISubsystem();
	if (!UISub) return;

	TArray<FUIActionTag> UIactions;
	if (UISub->TryGetActionsFromKey(InKeyEvent.GetKey(), UIactions))
	{
		if (UIactions.Contains(NextAction))
		{
			NavigateToNext();
		}
		else if (UIactions.Contains(PreviousAction))
		{
			NavigateToPrevious();
		}
	}
}

void UANSHorizontalNavBox::NavigateToNext()
{
	const int32 NumWidgets = GetChildrenCount();
	if (NumWidgets == 0) return;

	int32 NextIndex = SelectedIndex + 1;

	if (NextIndex < NumWidgets)
	{
		SetSelectedIndex(NextIndex);
	}
	else if (bAllowCircularNavigation)
	{
		SetSelectedIndex(0);
	}
}

void UANSHorizontalNavBox::NavigateToPrevious()
{
	const int32 NumWidgets = GetChildrenCount();
	if (NumWidgets == 0) return;

	int32 PrevIndex = SelectedIndex - 1;

	if (PrevIndex >= 0)
	{
		SetSelectedIndex(PrevIndex);
	}
	else if (bAllowCircularNavigation)
	{
		SetSelectedIndex(NumWidgets - 1);
	}
}

void UANSHorizontalNavBox::SetSelectedIndex(int32 NewIndex)
{
	const int32 NumWidgets = GetChildrenCount();

	if (NumWidgets == 0)
	{
		SelectedIndex = -1;
		return;
	}

	if (NewIndex >= 0 && NewIndex < NumWidgets)
	{
		if (SelectedIndex != NewIndex)
		{
			SelectedIndex = NewIndex;
			UpdateChildrenVisuals();
			OnIndexChanged.Broadcast(SelectedIndex);
		}
	}
}

UWidget* UANSHorizontalNavBox::GetSelectedWidget() const
{
	if (GetChildrenCount() > 0 && SelectedIndex >= 0 && SelectedIndex < GetChildrenCount())
	{
		return GetChildAt(SelectedIndex);
	}
	return nullptr;
}

void UANSHorizontalNavBox::OnSlotAdded(UPanelSlot* InSlot)
{
	Super::OnSlotAdded(InSlot);
	UpdateChildrenVisuals();
}

void UANSHorizontalNavBox::OnSlotRemoved(UPanelSlot* InSlot)
{
	Super::OnSlotRemoved(InSlot);

	const int32 NumWidgets = GetChildrenCount();
	if (SelectedIndex >= NumWidgets && NumWidgets > 0)
	{
		SetSelectedIndex(NumWidgets - 1);
	}
	else if (NumWidgets == 0)
	{
		SelectedIndex = -1;
	}
}

void UANSHorizontalNavBox::UpdateChildrenVisuals()
{
	for (int32 i = 0; i < GetChildrenCount(); i++)
	{
		UWidget* Child = GetChildAt(i);
		if (UANSNavWidget* NavWidget = Cast<UANSNavWidget>(Child))
		{
			NavWidget->SetIsSelected(i == SelectedIndex);
		}
	}
}

UANSUIPlayerSubsystem* UANSHorizontalNavBox::GetUISubsystem() const
{
	if (const UGameInstance* GameInst = UGameplayStatics::GetGameInstance(this))
	{
		return GameInst->GetSubsystem<UANSUIPlayerSubsystem>();
	}
	return nullptr;
}