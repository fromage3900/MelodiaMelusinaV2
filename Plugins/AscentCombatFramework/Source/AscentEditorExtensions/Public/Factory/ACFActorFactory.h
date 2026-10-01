// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "ActorFactories/ActorFactory.h"
#include "ACFActorFactory.generated.h"

UCLASS()
class UACFActorFactory : public UActorFactory
{
	GENERATED_BODY()

	//UActorFactory interface implementation
	virtual bool CanCreateActorFrom(const FAssetData& AssetData, FText& OutErrorMsg) override;
	virtual void PostSpawnActor(UObject* Asset, AActor* NewActor) override;
	//End of implementation

	public:

	UPROPERTY()
	class UACFAssetAction* AssetAction;
};
