#include "MelodiaUIBridgeLibrary.h"

#include "MelodiaUIBridgeSubsystem.h"
#include "Blueprint/UserWidget.h"

void UMelodiaUIBridgeLibrary::ShowMelodiaBattleUI(const UObject* WorldContextObject)
{
	if (UMelodiaUIBridgeSubsystem* Bridge = UMelodiaUIBridgeSubsystem::Get(WorldContextObject))
	{
		Bridge->ShowMelodiaBattleUI();
	}
}

void UMelodiaUIBridgeLibrary::HideMelodiaBattleUI(const UObject* WorldContextObject)
{
	if (UMelodiaUIBridgeSubsystem* Bridge = UMelodiaUIBridgeSubsystem::Get(WorldContextObject))
	{
		Bridge->HideMelodiaBattleUI();
	}
}

void UMelodiaUIBridgeLibrary::ToggleMelodiaBattleUI(const UObject* WorldContextObject)
{
	if (UMelodiaUIBridgeSubsystem* Bridge = UMelodiaUIBridgeSubsystem::Get(WorldContextObject))
	{
		if (Bridge->IsMelodiaUIVisible())
		{
			Bridge->HideMelodiaBattleUI();
		}
		else
		{
			Bridge->ShowMelodiaBattleUI();
		}
	}
}

bool UMelodiaUIBridgeLibrary::CreateMelodiaBattleUI(const UObject* WorldContextObject, TSubclassOf<UUserWidget> WidgetClass)
{
	if (UMelodiaUIBridgeSubsystem* Bridge = UMelodiaUIBridgeSubsystem::Get(WorldContextObject))
	{
		return Bridge->CreateMelodiaBattleUI(WidgetClass) != nullptr;
	}
	return false;
}

void UMelodiaUIBridgeLibrary::DestroyMelodiaBattleUI(const UObject* WorldContextObject)
{
	if (UMelodiaUIBridgeSubsystem* Bridge = UMelodiaUIBridgeSubsystem::Get(WorldContextObject))
	{
		Bridge->DestroyMelodiaBattleUI();
	}
}

bool UMelodiaUIBridgeLibrary::IsMelodiaUIActive(const UObject* WorldContextObject)
{
	if (UMelodiaUIBridgeSubsystem* Bridge = UMelodiaUIBridgeSubsystem::Get(WorldContextObject))
	{
		return Bridge->IsMelodiaUIActive();
	}
	return false;
}
