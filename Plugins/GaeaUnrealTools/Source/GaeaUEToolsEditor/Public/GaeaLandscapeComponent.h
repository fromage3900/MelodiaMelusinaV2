// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GaeaLandscapeComponent.generated.h"

class ULandscapeLayerInfoObject;

UCLASS(ClassGroup=(Custom), meta=(NotBlueprintable, NotBlueprintType))
class GAEAUETOOLSEDITOR_API UGaeaLandscapeComponent final : public UActorComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UGaeaLandscapeComponent();

	UPROPERTY(EditAnywhere, Category="Gaea Landscape")
	bool LockProperties = true;

	UPROPERTY(EditAnywhere, Category = "Gaea Landscape", meta = (FilePathFilter = "png", EditCondition = "!LockProperties"))
	FFilePath HeightmapFilepath;

	UPROPERTY(EditAnywhere, Category = "Gaea Landscape", meta = (FilePathFilter = "json", EditCondition = "!LockProperties"))
	FFilePath DefinitionFilepath;
	
	UPROPERTY(EditAnywhere, Category = "Gaea Landscape", meta = (FilePathFilter = "png", EditCondition = "!LockProperties"))
	TArray<FFilePath> WeightmapFilepaths;


protected:
	// Called when the game starts
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	virtual void DestroyComponent(bool bPromoteChildren = false) override;

		
};
