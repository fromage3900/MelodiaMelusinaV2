
#pragma once

#include "CoreMinimal.h"
#include "Templates/SharedPointer.h"
#include "Framework/MultiBox/MultiBoxExtender.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"

class FAssetEditor_AGSGraph;
class FExtender;
class FToolBarBuilder;

class AGSGRAPHEDITOR_API FAssetEditorToolbar_AGSGraph : public TSharedFromThis<FAssetEditorToolbar_AGSGraph> {
public:
    FAssetEditorToolbar_AGSGraph(TSharedPtr<FAssetEditor_AGSGraph> InGraphEditor)
		: AGSGraphEditor(InGraphEditor) {}

	void AddGraphToolbar(TSharedPtr<FExtender> Extender);


private:
	void FillGraphToolbar(FToolBarBuilder& ToolbarBuilder);

protected:
	/** Pointer back to the blueprint editor tool that owns us */
    TWeakPtr<FAssetEditor_AGSGraph> AGSGraphEditor;

};
