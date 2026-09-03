// Fill out your copyright notice in the Description page of Project Settings.


#include "ImporterPanelSettings.h"
#include "GaeaSubsystem.h"

UImporterPanelSettings::UImporterPanelSettings()
{
}

UImporterPanelSettings::~UImporterPanelSettings()
{
}

void UImporterPanelSettings::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	FName PropertyName = (PropertyChangedEvent.Property != nullptr) ? PropertyChangedEvent.Property->GetFName() : NAME_None;

	if (PropertyName == GET_MEMBER_NAME_CHECKED(UImporterPanelSettings, WeightmapFileNames))
	{
		WeightmapFilePaths.Empty();
		for(int i = 0; i < WeightmapFileNames.Num(); i++) 
		{
			FString FullPath = FPaths::Combine(*StoredPath, *WeightmapFileNames[i]);
			WeightmapFilePaths.Add(FullPath); // When WeightmapFileNames is reordered or changed, we mutate WeightmapFilePaths to generate the full paths. This is for UX benefits, and the paths will be used later with the actual layer system.
			
		}
	}
	else if (PropertyName == GET_MEMBER_NAME_CHECKED(UImporterPanelSettings, LandscapeMaterial))
	{
		UGaeaSubsystem* Manager = UGaeaSubsystem::GetGaeaSubsystem();
		TArray<UMaterialExpressionLandscapeLayerBlend*> BlendNodes = Manager->GetLandscapeLayerBlendNodes(LandscapeMaterial);
		Manager->GetLandscapeLayerBlendNames(BlendNodes, LandscapeMaterialLayerNames);
	}
	

	Super::PostEditChangeProperty(PropertyChangedEvent);
}

