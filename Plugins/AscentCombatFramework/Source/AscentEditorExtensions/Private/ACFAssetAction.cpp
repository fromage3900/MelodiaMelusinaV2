// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACFAssetAction.h"

void UACFAssetAction::PostSpawnActor(UObject* Asset, AActor* NewActor)
{
	K2_PostSpawnActor(Asset, NewActor);
}



TSubclassOf<UObject> UACFAssetAction::GetClassFromAsset(UObject* Asset)
{
	if (IsValid(Asset))
	{
		if (UBlueprint* Blueprint = Cast<UBlueprint>(Asset))
		{
			return Blueprint->GeneratedClass;
		}
	}

	return {};
}
