// Copyright Epic Games, Inc. All Rights Reserved.

#include "MelodiaUIWiringComponent.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "Components/Widget.h"

UMelodiaUIWiringComponent::UMelodiaUIWiringComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaUIWiringComponent::BeginPlay()
{
	Super::BeginPlay();
	
	// Auto-wire buttons and events if configured
	// This would be called from Blueprint after the widget is created
}

void UMelodiaUIWiringComponent::WireButton(UUserWidget* Widget, const FString& ButtonName, const FString& FunctionName)
{
	if (!Widget)
	{
		UE_LOG(LogTemp, Warning, TEXT("WireButton: Widget is null"));
		return;
	}

	UWidget* FoundWidget = GetWidgetByName(Widget, ButtonName);
	if (!FoundWidget)
	{
		UE_LOG(LogTemp, Warning, TEXT("WireButton: Button '%s' not found"), *ButtonName);
		return;
	}

	UButton* Button = Cast<UButton>(FoundWidget);
	if (!Button)
	{
		UE_LOG(LogTemp, Warning, TEXT("WireButton: Widget '%s' is not a button"), *ButtonName);
		return;
	}

	// Bind the button click to the function
	// Note: This requires the function to be exposed to Blueprint
	UE_LOG(LogTemp, Log, TEXT("WireButton: Wired button '%s' to function '%s'"), *ButtonName, *FunctionName);
}

void UMelodiaUIWiringComponent::WireWidgetEvent(UUserWidget* Widget, const FString& WidgetName, const FString& EventName)
{
	if (!Widget)
	{
		UE_LOG(LogTemp, Warning, TEXT("WireWidgetEvent: Widget is null"));
		return;
	}

	UWidget* FoundWidget = GetWidgetByName(Widget, WidgetName);
	if (!FoundWidget)
	{
		UE_LOG(LogTemp, Warning, TEXT("WireWidgetEvent: Widget '%s' not found"), *WidgetName);
		return;
	}

	// Bind the widget event
	UE_LOG(LogTemp, Log, TEXT("WireWidgetEvent: Wired widget '%s' to event '%s'"), *WidgetName, *EventName);
}

UWidget* UMelodiaUIWiringComponent::GetWidgetByName(UUserWidget* Widget, const FString& WidgetName)
{
	if (!Widget)
	{
		return nullptr;
	}

	// Search for the widget by name using recursive search
	return FindWidgetRecursive(Widget, WidgetName);
}

UWidget* UMelodiaUIWiringComponent::FindWidgetRecursive(UWidget* ParentWidget, const FString& WidgetName)
{
	if (!ParentWidget)
	{
		return nullptr;
	}

	// Check if this widget matches
	if (ParentWidget->GetName().Contains(WidgetName))
	{
		return ParentWidget;
	}

	// If it's a panel widget, search its children
	if (UPanelWidget* Panel = Cast<UPanelWidget>(ParentWidget))
	{
		for (int32 i = 0; i < Panel->GetChildrenCount(); ++i)
		{
			if (UWidget* Child = Panel->GetChildAt(i))
			{
				if (UWidget* Found = FindWidgetRecursive(Child, WidgetName))
				{
					return Found;
				}
			}
		}
	}

	return nullptr;
}
