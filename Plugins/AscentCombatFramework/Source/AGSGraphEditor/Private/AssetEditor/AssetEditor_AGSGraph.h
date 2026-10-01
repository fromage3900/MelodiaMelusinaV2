// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AGSGraph.h"
#include "CoreMinimal.h"
#include <GraphEditor.h>
#include "Toolkits/AssetEditorToolkit.h"
#include "Misc/NotifyHook.h"
#include "Widgets/Docking/SDockTab.h"

class FAssetEditorToolbar_AGSGraph;

class AGSGRAPHEDITOR_API FAssetEditor_AGSGraph : public FAssetEditorToolkit, public FNotifyHook, public FGCObject {
public:
    FAssetEditor_AGSGraph();
    virtual ~FAssetEditor_AGSGraph();

    void InitGraphEditor(const EToolkitMode::Type Mode, const TSharedPtr<IToolkitHost>& InitToolkitHost, UAGSGraph* Graph);

    // IToolkit interface
    virtual void RegisterTabSpawners(const TSharedRef<FTabManager>& TabManager) override;
    virtual void UnregisterTabSpawners(const TSharedRef<FTabManager>& TabManager) override;
    // End of IToolkit interface

    // FAssetEditorToolkit
    virtual FName GetToolkitFName() const override;
    virtual FText GetBaseToolkitName() const override;
    virtual FText GetToolkitName() const override;
    virtual FText GetToolkitToolTipText() const override;
    virtual FLinearColor GetWorldCentricTabColorScale() const override;
    virtual FString GetWorldCentricTabPrefix() const override;
    virtual FString GetDocumentationLink() const override;
    virtual void SaveAsset_Execute() override;
    // End of FAssetEditorToolkit

    // Toolbar

    virtual FString GetReferencerName() const override;

    // FSerializableObject interface
    virtual void AddReferencedObjects(FReferenceCollector& Collector) override;
    // End of FSerializableObject interface

private:
    TSharedRef<SDockTab> SpawnTab_Viewport(const FSpawnTabArgs& Args);
    TSharedRef<SDockTab> SpawnTab_Details(const FSpawnTabArgs& Args);

    void CreateInternalWidgets();
    TSharedRef<SGraphEditor> CreateViewportWidget();

    void CreateEdGraph();

    void CreateCommandList();

    TSharedPtr<SGraphEditor> GetCurrGraphEditor() const;

    FGraphPanelSelectionSet GetSelectedNodes() const;

    void RebuildAGSGraph();

    // Delegates for graph editor commands
    void SelectAllNodes();
    bool CanSelectAllNodes();
    void DeleteSelectedNodes();
    bool CanDeleteNodes();
    void DeleteSelectedDuplicatableNodes();
    void CutSelectedNodes();
    bool CanCutNodes();
    void CopySelectedNodes();
    bool CanCopyNodes();
    void PasteNodes();
    void PasteNodesHere(const FVector2f& Location);
    bool CanPasteNodes();
    void DuplicateNodes();
    bool CanDuplicateNodes();

    void BindCommands();
    void GraphSettings();
    bool CanGraphSettings() const;

    void OnRenameNode();
    bool CanRenameNodes() const;

    //////////////////////////////////////////////////////////////////////////
    // graph editor event
    void OnSelectedNodesChanged(const TSet<class UObject*>& NewSelection);

    void OnNodeDoubleClicked(UEdGraphNode* Node);

    void OnFinishedChangingProperties(const FPropertyChangedEvent& PropertyChangedEvent);


    void OnPackageSavedWithContext(const FString& PackageFileName, UPackage* Package, FObjectPostSaveContext ObjectSaveContext);
private:
    TObjectPtr<UAGSGraph> EditingGraph;

    // Toolbar
    TSharedPtr<class FAssetEditorToolbar_AGSGraph> ToolbarBuilder;

    /** Handle to the registered OnPackageSave delegate */
    FDelegateHandle OnPackageSavedDelegateHandle;

    TSharedPtr<SGraphEditor> ViewportWidget;
    TSharedPtr<class IDetailsView> PropertyWidget;

    /** The command list for this editor */
    TSharedPtr<FUICommandList> GraphEditorCommands;
};
