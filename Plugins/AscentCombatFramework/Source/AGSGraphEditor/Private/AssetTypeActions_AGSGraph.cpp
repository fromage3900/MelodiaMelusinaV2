// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "AssetTypeActions_AGSGraph.h"
#include "AGSGraphEditorPCH.h"
#include "AssetEditor/AssetEditor_AGSGraph.h"

#define LOCTEXT_NAMESPACE "AssetTypeActions_AGSGraph"

FAssetTypeActions_AGSGraph::FAssetTypeActions_AGSGraph(EAssetTypeCategories::Type InAssetCategory)
	: MyAssetCategory(InAssetCategory)
{
}

FText FAssetTypeActions_AGSGraph::GetName() const
{
	return LOCTEXT("FAGSGraphAssetTypeActionsName", "Ascent Graph");
}

FColor FAssetTypeActions_AGSGraph::GetTypeColor() const
{
	return FColor(80,80,220,255);
}

UClass* FAssetTypeActions_AGSGraph::GetSupportedClass() const
{
	return UAGSGraph::StaticClass();
}

void FAssetTypeActions_AGSGraph::OpenAssetEditor(const TArray<UObject*>& InObjects, TSharedPtr<class IToolkitHost> EditWithinLevelEditor)
{
	const EToolkitMode::Type Mode = EditWithinLevelEditor.IsValid() ? EToolkitMode::WorldCentric : EToolkitMode::Standalone;

	for (auto ObjIt = InObjects.CreateConstIterator(); ObjIt; ++ObjIt)
	{
		if (UAGSGraph* Graph = Cast<UAGSGraph>(*ObjIt))
		{
			TSharedRef<FAssetEditor_AGSGraph> NewGraphEditor(new FAssetEditor_AGSGraph());
			NewGraphEditor->InitGraphEditor(Mode, EditWithinLevelEditor, Graph);
		}
	}
}

uint32 FAssetTypeActions_AGSGraph::GetCategories()
{
	return MyAssetCategory;
}

//////////////////////////////////////////////////////////////////////////

#undef LOCTEXT_NAMESPACE