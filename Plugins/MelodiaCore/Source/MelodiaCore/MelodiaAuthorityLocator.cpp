#include "MelodiaAuthorityLocator.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

UMelodiaAuthorityLocator* UMelodiaAuthorityLocator::Get(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaAuthorityLocator>() : nullptr;
}

void UMelodiaAuthorityLocator::RegisterTravelProvider(TScriptInterface<IMelodiaTravelProvider> Provider)
{
	TravelProvider = TWeakInterfacePtr<IMelodiaTravelProvider>(Provider.GetObject());
}

void UMelodiaAuthorityLocator::RegisterInputContextProvider(TScriptInterface<IMelodiaInputContextProvider> Provider)
{
	InputContextProvider = TWeakInterfacePtr<IMelodiaInputContextProvider>(Provider.GetObject());
}

TScriptInterface<IMelodiaTravelProvider> UMelodiaAuthorityLocator::GetTravelProvider() const
{
	TScriptInterface<IMelodiaTravelProvider> Result;
	if (UObject* Obj = TravelProvider.GetObject())
	{
		Result.SetObject(Obj);
		Result.SetInterface(TravelProvider.Get());
	}
	return Result;
}

TScriptInterface<IMelodiaInputContextProvider> UMelodiaAuthorityLocator::GetInputContextProvider() const
{
	TScriptInterface<IMelodiaInputContextProvider> Result;
	if (UObject* Obj = InputContextProvider.GetObject())
	{
		Result.SetObject(Obj);
		Result.SetInterface(InputContextProvider.Get());
	}
	return Result;
}
