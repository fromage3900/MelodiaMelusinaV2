#include "AssetEditorToolbar_AGSGraph.h"

#include "AssetEditor_AGSGraph.h"
#include "EditorCommands_AGSGraph.h"

#define LOCTEXT_NAMESPACE "AssetEditorToolbar_AGSGraph"

void FAssetEditorToolbar_AGSGraph::AddGraphToolbar(TSharedPtr<FExtender> Extender)
{
    check(AGSGraphEditor.IsValid());
    TSharedPtr<FAssetEditor_AGSGraph> GenericGraphEditorPtr = AGSGraphEditor.Pin();

	TSharedPtr<FExtender> ToolbarExtender = MakeShareable(new FExtender);
	ToolbarExtender->AddToolBarExtension("Asset", EExtensionHook::After, GenericGraphEditorPtr->GetToolkitCommands(), FToolBarExtensionDelegate::CreateSP( this,
		&FAssetEditorToolbar_AGSGraph::FillGraphToolbar ));
	GenericGraphEditorPtr->AddToolbarExtender(ToolbarExtender);
}

void FAssetEditorToolbar_AGSGraph::FillGraphToolbar(FToolBarBuilder& ToolbarBuilder)
{
    check(AGSGraphEditor.IsValid());
    TSharedPtr<FAssetEditor_AGSGraph> GenericGraphEditorPtr = AGSGraphEditor.Pin();

	ToolbarBuilder.BeginSection("Generic Graph");
	{
// 		ToolbarBuilder.AddToolBarButton(FEditorCommands_AGSGraph::Get().GraphSettings,
// 			NAME_None,
// 			LOCTEXT("GraphSettings_Label", "Graph Settings"),
// 			LOCTEXT("GraphSettings_ToolTip", "Show the Graph Settings"),
// 			FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.GameSettings"));
	}
	ToolbarBuilder.EndSection();

}


#undef LOCTEXT_NAMESPACE
