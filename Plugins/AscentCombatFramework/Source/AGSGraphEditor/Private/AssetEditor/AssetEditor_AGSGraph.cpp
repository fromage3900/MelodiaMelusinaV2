// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AssetEditor_AGSGraph.h"
#include "AGSGraph.h"
#include "AGSGraphEditorPCH.h"
#include "AssetEditorToolbar_AGSGraph.h"
#include "AssetGraphSchema_AGSGraph.h"
#include "AssetToolsModule.h"
#include "EdGraphUtilities.h"
#include "EdGraph_AGSGraph.h"
#include "EdNode_AGSGraphEdge.h"
#include "EdNode_AGSGraphNode.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "EditorCommands_AGSGraph.h"
#include "EditorStyleSet.h"
#include "Framework/Commands/GenericCommands.h"
#include "Framework/MultiBox/MultiBoxExtender.h"
#include "GraphEditorActions.h"
#include "HAL/PlatformApplicationMisc.h"
#include "IDetailsView.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "PropertyEditorModule.h"
#include "UObject/ObjectSaveContext.h"
#include "Widgets/SBoxPanel.h"
#include "ScopedTransaction.h"

#define LOCTEXT_NAMESPACE "AssetEditor_AGSGraph"

const FName AGSGraphEditorAppName = FName(TEXT("AGSGraphEditorApp"));

struct FAssetEditorTabs {
    // Tab identifiers
    static const FName AGSGraphPropertyID;
    static const FName ViewportID;
   // static const FName AGSGraphEditorSettingsID;
};

//////////////////////////////////////////////////////////////////////////

const FName FAssetEditorTabs::AGSGraphPropertyID(TEXT("AGSGraphProperty"));
const FName FAssetEditorTabs::ViewportID(TEXT("Viewport"));
// const FName FAssetEditorTabs::AGSGraphEditorSettingsID(TEXT("AGSGraphEditorSettings"));

//////////////////////////////////////////////////////////////////////////

FAssetEditor_AGSGraph::FAssetEditor_AGSGraph()
{
    EditingGraph = nullptr;

    OnPackageSavedDelegateHandle = UPackage::PackageSavedWithContextEvent.AddRaw(this, &FAssetEditor_AGSGraph::OnPackageSavedWithContext);
}

FAssetEditor_AGSGraph::~FAssetEditor_AGSGraph()
{
    UPackage::PackageSavedWithContextEvent.Remove(OnPackageSavedDelegateHandle);
}

void FAssetEditor_AGSGraph::InitGraphEditor(const EToolkitMode::Type Mode, const TSharedPtr<IToolkitHost>& InitToolkitHost, UAGSGraph* Graph)
{

    EditingGraph = Graph;
    CreateEdGraph();

    FGenericCommands::Register();
    FGraphEditorCommands::Register();
    FEditorCommands_AGSGraph::Register();

    if (!ToolbarBuilder.IsValid()) {
        ToolbarBuilder = MakeShareable(new FAssetEditorToolbar_AGSGraph(SharedThis(this)));
    }

    BindCommands();

    CreateInternalWidgets();

    TSharedPtr<FExtender> ToolbarExtender = MakeShareable(new FExtender);

    ToolbarBuilder->AddGraphToolbar(ToolbarExtender);

    // Layout
    const TSharedRef<FTabManager::FLayout> StandaloneDefaultLayout = FTabManager::NewLayout("Standalone_GraphEditor_Layout_v1")
                                                                         ->AddArea(
                                                                             FTabManager::NewPrimaryArea()->SetOrientation(Orient_Vertical)

                                                                                 ->Split(FTabManager::NewSplitter()->SetOrientation(Orient_Horizontal)->SetSizeCoefficient(0.9f)

                                                                                             ->Split(FTabManager::NewStack()->SetSizeCoefficient(0.65f)->AddTab(FAssetEditorTabs::ViewportID, ETabState::OpenedTab)->SetHideTabWell(true))

                                                                                             ->Split(FTabManager::NewSplitter()->SetOrientation(Orient_Vertical)

                                                                                                         ->Split(FTabManager::NewStack()->SetSizeCoefficient(0.7f)->AddTab(FAssetEditorTabs::AGSGraphPropertyID, ETabState::OpenedTab)->SetHideTabWell(true))

                                                                                                         /*->Split(FTabManager::NewStack()->SetSizeCoefficient(0.3f)->AddTab(FAssetEditorTabs::AGSGraphEditorSettingsID, ETabState::OpenedTab))*/)));

    const bool bCreateDefaultStandaloneMenu = true;
    const bool bCreateDefaultToolbar = true;
    FAssetEditorToolkit::InitAssetEditor(Mode, InitToolkitHost, AGSGraphEditorAppName, StandaloneDefaultLayout, bCreateDefaultStandaloneMenu, bCreateDefaultToolbar, EditingGraph, false);

    RegenerateMenusAndToolbars();
}

void FAssetEditor_AGSGraph::BindCommands()
{
    //     ToolkitCommands->MapAction(FEditorCommands_AGSGraph::Get().GraphSettings,
    //         FExecuteAction::CreateSP(this, &FAssetEditor_AGSGraph::GraphSettings),
    //         FCanExecuteAction::CreateSP(this, &FAssetEditor_AGSGraph::CanGraphSettings));
}

void FAssetEditor_AGSGraph::RegisterTabSpawners(const TSharedRef<FTabManager>& InTabManager)
{
    WorkspaceMenuCategory = InTabManager->AddLocalWorkspaceMenuCategory(LOCTEXT("WorkspaceMenu_AGSGraphEditor", "Graph Editor"));
    auto WorkspaceMenuCategoryRef = WorkspaceMenuCategory.ToSharedRef();

    FAssetEditorToolkit::RegisterTabSpawners(InTabManager);

    InTabManager->RegisterTabSpawner(FAssetEditorTabs::ViewportID, FOnSpawnTab::CreateSP(this, &FAssetEditor_AGSGraph::SpawnTab_Viewport))
        .SetDisplayName(LOCTEXT("GraphCanvasTab", "Viewport"))
        .SetGroup(WorkspaceMenuCategoryRef)
        .SetIcon(FSlateIcon(FAppStyle::GetAppStyleSetName(), "GraphEditor.EventGraph_16x"));

    InTabManager->RegisterTabSpawner(FAssetEditorTabs::AGSGraphPropertyID, FOnSpawnTab::CreateSP(this, &FAssetEditor_AGSGraph::SpawnTab_Details))
        .SetDisplayName(LOCTEXT("DetailsTab", "Property"))
        .SetGroup(WorkspaceMenuCategoryRef)
        .SetIcon(FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.Tabs.Details"));
}

void FAssetEditor_AGSGraph::UnregisterTabSpawners(const TSharedRef<FTabManager>& InTabManager)
{
    FAssetEditorToolkit::UnregisterTabSpawners(InTabManager);

    InTabManager->UnregisterTabSpawner(FAssetEditorTabs::ViewportID);
    InTabManager->UnregisterTabSpawner(FAssetEditorTabs::AGSGraphPropertyID);
}

FName FAssetEditor_AGSGraph::GetToolkitFName() const
{
    return FName("FAGSGraphEditor");
}

FText FAssetEditor_AGSGraph::GetBaseToolkitName() const
{
    return LOCTEXT("AGSGraphEditorAppLabel", "AGS Graph Editor");
}

FText FAssetEditor_AGSGraph::GetToolkitName() const
{
    const bool bDirtyState = EditingGraph->GetOutermost()->IsDirty();

    FFormatNamedArguments Args;
    Args.Add(TEXT("AGSGraphName"), FText::FromString(EditingGraph->GetName()));
    Args.Add(TEXT("DirtyState"), bDirtyState ? FText::FromString(TEXT("*")) : FText::GetEmpty());
    return FText::Format(LOCTEXT("AGSGraphEditorToolkitName", "{AGSGraphName}{DirtyState}"), Args);
}

FText FAssetEditor_AGSGraph::GetToolkitToolTipText() const
{
    return FAssetEditorToolkit::GetToolTipTextForObject(EditingGraph);
}

FLinearColor FAssetEditor_AGSGraph::GetWorldCentricTabColorScale() const
{
    return FLinearColor::White;
}

FString FAssetEditor_AGSGraph::GetWorldCentricTabPrefix() const
{
    return TEXT("AGSGraphEditor");
}

FString FAssetEditor_AGSGraph::GetDocumentationLink() const
{
    return TEXT("");
}

void FAssetEditor_AGSGraph::SaveAsset_Execute()
{
    if (EditingGraph != nullptr) {
        RebuildAGSGraph();
    }

    FAssetEditorToolkit::SaveAsset_Execute();
}

FString FAssetEditor_AGSGraph::GetReferencerName() const
{
    return "ATSGraph";
}

void FAssetEditor_AGSGraph::AddReferencedObjects(FReferenceCollector& Collector)
{
    Collector.AddReferencedObject(EditingGraph);
    Collector.AddReferencedObject(EditingGraph->EdGraph);
}

TSharedRef<SDockTab> FAssetEditor_AGSGraph::SpawnTab_Viewport(const FSpawnTabArgs& Args)
{
    check(Args.GetTabId() == FAssetEditorTabs::ViewportID);

    TSharedRef<SDockTab> SpawnedTab = SNew(SDockTab)
                                          .Label(LOCTEXT("ViewportTab_Title", "Viewport"));

    if (ViewportWidget.IsValid()) {
        SpawnedTab->SetContent(ViewportWidget.ToSharedRef());
    }

    return SpawnedTab;
}

TSharedRef<SDockTab> FAssetEditor_AGSGraph::SpawnTab_Details(const FSpawnTabArgs& Args)
{
    check(Args.GetTabId() == FAssetEditorTabs::AGSGraphPropertyID);

    return SNew(SDockTab)
     //   .Icon(FAppStyle::GetBrush("LevelEditor.Tabs.Details"))
        .Label(LOCTEXT("Details_Title", "Property"))
            [PropertyWidget.ToSharedRef()];
}

void FAssetEditor_AGSGraph::CreateInternalWidgets()
{
    ViewportWidget = CreateViewportWidget();

    FDetailsViewArgs Args;
    Args.bHideSelectionTip = true;
    Args.NotifyHook = this;

    FPropertyEditorModule& PropertyModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");
    PropertyWidget = PropertyModule.CreateDetailView(Args);
    PropertyWidget->SetObject(EditingGraph);
    PropertyWidget->OnFinishedChangingProperties().AddSP(this, &FAssetEditor_AGSGraph::OnFinishedChangingProperties);
}

TSharedRef<SGraphEditor> FAssetEditor_AGSGraph::CreateViewportWidget()
{
    FGraphAppearanceInfo AppearanceInfo;
    AppearanceInfo.CornerText = LOCTEXT("AppearanceCornerText_AGSGraph", "Ascent Toolset");

    CreateCommandList();

    SGraphEditor::FGraphEditorEvents InEvents;
    InEvents.OnSelectionChanged = SGraphEditor::FOnSelectionChanged::CreateSP(this, &FAssetEditor_AGSGraph::OnSelectedNodesChanged);
    InEvents.OnNodeDoubleClicked = FSingleNodeEvent::CreateSP(this, &FAssetEditor_AGSGraph::OnNodeDoubleClicked);

    return SNew(SGraphEditor)
        .AdditionalCommands(GraphEditorCommands)
        .IsEditable(true)
        .Appearance(AppearanceInfo)
        .GraphToEdit(EditingGraph->EdGraph)
        .GraphEvents(InEvents)
        .AutoExpandActionMenu(true)
        .ShowGraphStateOverlay(false);
}

void FAssetEditor_AGSGraph::CreateEdGraph()
{
    if (EditingGraph->EdGraph == nullptr) {
        EditingGraph->EdGraph = CastChecked<UEdGraph_AGSGraph>(FBlueprintEditorUtils::CreateNewGraph(EditingGraph, NAME_None, UEdGraph_AGSGraph::StaticClass(), UAssetGraphSchema_AGSGraph::StaticClass()));
        EditingGraph->EdGraph->bAllowDeletion = false;

        // Give the schema a chance to fill out any required nodes (like the results node)
        const UEdGraphSchema* Schema = EditingGraph->EdGraph->GetSchema();
        Schema->CreateDefaultNodesForGraph(*EditingGraph->EdGraph);
    }
}

void FAssetEditor_AGSGraph::CreateCommandList()
{
    if (GraphEditorCommands.IsValid()) {
        return;
    }

    GraphEditorCommands = MakeShareable(new FUICommandList);

    // Can't use CreateSP here because derived editor are already implementing TSharedFromThis<FAssetEditorToolkit>
    // however it should be safe, since commands are being used only within this editor
    // if it ever crashes, this function will have to go away and be reimplemented in each derived class
    //     GraphEditorCommands->MapAction(FEditorCommands_AGSGraph::Get().GraphSettings,
    //         FExecuteAction::CreateRaw(this, &FEditorCommands_AGSGraph::GraphSettings),
    //         FCanExecuteAction::CreateRaw(this, &FEditorCommands_AGSGraph::CanGraphSettings));

    GraphEditorCommands->MapAction(FGenericCommands::Get().SelectAll,
        FExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::SelectAllNodes),
        FCanExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::CanSelectAllNodes));

    GraphEditorCommands->MapAction(FGenericCommands::Get().Delete,
        FExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::DeleteSelectedNodes),
        FCanExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::CanDeleteNodes));

    GraphEditorCommands->MapAction(FGenericCommands::Get().Copy,
        FExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::CopySelectedNodes),
        FCanExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::CanCopyNodes));

    GraphEditorCommands->MapAction(FGenericCommands::Get().Cut,
        FExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::CutSelectedNodes),
        FCanExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::CanCutNodes));

    GraphEditorCommands->MapAction(FGenericCommands::Get().Paste,
        FExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::PasteNodes),
        FCanExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::CanPasteNodes));

    GraphEditorCommands->MapAction(FGenericCommands::Get().Duplicate,
        FExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::DuplicateNodes),
        FCanExecuteAction::CreateRaw(this, &FAssetEditor_AGSGraph::CanDuplicateNodes));

    GraphEditorCommands->MapAction(FGenericCommands::Get().Rename,
        FExecuteAction::CreateSP(this, &FAssetEditor_AGSGraph::OnRenameNode),
        FCanExecuteAction::CreateSP(this, &FAssetEditor_AGSGraph::CanRenameNodes));
}

TSharedPtr<SGraphEditor> FAssetEditor_AGSGraph::GetCurrGraphEditor() const
{
    return ViewportWidget;
}

FGraphPanelSelectionSet FAssetEditor_AGSGraph::GetSelectedNodes() const
{
    FGraphPanelSelectionSet CurrentSelection;
    TSharedPtr<SGraphEditor> FocusedGraphEd = GetCurrGraphEditor();
    if (FocusedGraphEd.IsValid()) {
        CurrentSelection = FocusedGraphEd->GetSelectedNodes();
    }

    return CurrentSelection;
}

void FAssetEditor_AGSGraph::RebuildAGSGraph()
{
    if (EditingGraph == nullptr) {
        LOG_WARNING(TEXT("FAssetEditor::RebuildAGSGraph EditingGraph is nullptr"));
        return;
    }

    UEdGraph_AGSGraph* EdGraph = Cast<UEdGraph_AGSGraph>(EditingGraph->EdGraph);
    check(EdGraph != nullptr);

    EdGraph->RebuildAGSGraph();
}

void FAssetEditor_AGSGraph::SelectAllNodes()
{
    TSharedPtr<SGraphEditor> CurrentGraphEditor = GetCurrGraphEditor();
    if (CurrentGraphEditor.IsValid()) {
        CurrentGraphEditor->SelectAllNodes();
    }
}

bool FAssetEditor_AGSGraph::CanSelectAllNodes()
{
    return true;
}

void FAssetEditor_AGSGraph::DeleteSelectedNodes()
{
    TSharedPtr<SGraphEditor> CurrentGraphEditor = GetCurrGraphEditor();
    if (!CurrentGraphEditor.IsValid()) {
        return;
    }

    const FScopedTransaction Transaction(FGenericCommands::Get().Delete->GetDescription());

    CurrentGraphEditor->GetCurrentGraph()->Modify();

    const FGraphPanelSelectionSet SelectedNodes = CurrentGraphEditor->GetSelectedNodes();
    CurrentGraphEditor->ClearSelectionSet();

    for (FGraphPanelSelectionSet::TConstIterator NodeIt(SelectedNodes); NodeIt; ++NodeIt) {
        UEdGraphNode* EdNode = Cast<UEdGraphNode>(*NodeIt);
        if (EdNode == nullptr || !EdNode->CanUserDeleteNode())
            continue;
        ;

        if (UEdNode_AGSGraphNode* EdNode_Node = Cast<UEdNode_AGSGraphNode>(EdNode)) {
            EdNode_Node->Modify();

            const UEdGraphSchema* Schema = EdNode_Node->GetSchema();
            if (Schema != nullptr) {
                Schema->BreakNodeLinks(*EdNode_Node);
            }

            EdNode_Node->DestroyNode();
        } else {
            EdNode->Modify();
            EdNode->DestroyNode();
        }
    }
}

bool FAssetEditor_AGSGraph::CanDeleteNodes()
{
    // If any of the nodes can be deleted then we should allow deleting
    const FGraphPanelSelectionSet SelectedNodes = GetSelectedNodes();
    for (FGraphPanelSelectionSet::TConstIterator SelectedIter(SelectedNodes); SelectedIter; ++SelectedIter) {
        UEdGraphNode* Node = Cast<UEdGraphNode>(*SelectedIter);
        if (Node != nullptr && Node->CanUserDeleteNode()) {
            return true;
        }
    }

    return false;
}

void FAssetEditor_AGSGraph::DeleteSelectedDuplicatableNodes()
{
    TSharedPtr<SGraphEditor> CurrentGraphEditor = GetCurrGraphEditor();
    if (!CurrentGraphEditor.IsValid()) {
        return;
    }

    const FGraphPanelSelectionSet OldSelectedNodes = CurrentGraphEditor->GetSelectedNodes();
    CurrentGraphEditor->ClearSelectionSet();

    for (FGraphPanelSelectionSet::TConstIterator SelectedIter(OldSelectedNodes); SelectedIter; ++SelectedIter) {
        UEdGraphNode* Node = Cast<UEdGraphNode>(*SelectedIter);
        if (Node && Node->CanDuplicateNode()) {
            CurrentGraphEditor->SetNodeSelection(Node, true);
        }
    }

    // Delete the duplicatable nodes
    DeleteSelectedNodes();

    CurrentGraphEditor->ClearSelectionSet();

    for (FGraphPanelSelectionSet::TConstIterator SelectedIter(OldSelectedNodes); SelectedIter; ++SelectedIter) {
        if (UEdGraphNode* Node = Cast<UEdGraphNode>(*SelectedIter)) {
            CurrentGraphEditor->SetNodeSelection(Node, true);
        }
    }
}

void FAssetEditor_AGSGraph::CutSelectedNodes()
{
    CopySelectedNodes();
    DeleteSelectedDuplicatableNodes();
}

bool FAssetEditor_AGSGraph::CanCutNodes()
{
    return CanCopyNodes() && CanDeleteNodes();
}

void FAssetEditor_AGSGraph::CopySelectedNodes()
{
    // Export the selected nodes and place the text on the clipboard
    FGraphPanelSelectionSet SelectedNodes = GetSelectedNodes();

    FString ExportedText;

    for (FGraphPanelSelectionSet::TIterator SelectedIter(SelectedNodes); SelectedIter; ++SelectedIter) {
        UEdGraphNode* Node = Cast<UEdGraphNode>(*SelectedIter);
        if (Node == nullptr) {
            SelectedIter.RemoveCurrent();
            continue;
        }

        if (UEdNode_AGSGraphEdge* EdNode_Edge = Cast<UEdNode_AGSGraphEdge>(*SelectedIter)) {
            UEdNode_AGSGraphNode* StartNode = EdNode_Edge->GetStartNode();
            UEdNode_AGSGraphNode* EndNode = EdNode_Edge->GetEndNode();

            if (!SelectedNodes.Contains(StartNode) || !SelectedNodes.Contains(EndNode)) {
                SelectedIter.RemoveCurrent();
                continue;
            }
        }

        Node->PrepareForCopying();
    }

    FEdGraphUtilities::ExportNodesToText(SelectedNodes, ExportedText);
    FPlatformApplicationMisc::ClipboardCopy(*ExportedText);
}

bool FAssetEditor_AGSGraph::CanCopyNodes()
{
    // If any of the nodes can be duplicated then we should allow copying
    const FGraphPanelSelectionSet SelectedNodes = GetSelectedNodes();
    for (FGraphPanelSelectionSet::TConstIterator SelectedIter(SelectedNodes); SelectedIter; ++SelectedIter) {
        UEdGraphNode* Node = Cast<UEdGraphNode>(*SelectedIter);
        if (Node && Node->CanDuplicateNode()) {
            return true;
        }
    }

    return false;
}

void FAssetEditor_AGSGraph::PasteNodes()
{
    TSharedPtr<SGraphEditor> CurrentGraphEditor = GetCurrGraphEditor();
    if (CurrentGraphEditor.IsValid()) {
        PasteNodesHere(CurrentGraphEditor->GetPasteLocation2f());
    }
}

void FAssetEditor_AGSGraph::PasteNodesHere(const FVector2f& Location)
{
    // Find the graph editor with focus
    TSharedPtr<SGraphEditor> CurrentGraphEditor = GetCurrGraphEditor();
    if (!CurrentGraphEditor.IsValid()) {
        return;
    }
    // Select the newly pasted stuff
    UEdGraph* EdGraph = CurrentGraphEditor->GetCurrentGraph();

    {
        const FScopedTransaction Transaction(FGenericCommands::Get().Paste->GetDescription());
        EdGraph->Modify();

        // Clear the selection set (newly pasted stuff will be selected)
        CurrentGraphEditor->ClearSelectionSet();

        // Grab the text to paste from the clipboard.
        FString TextToImport;
        FPlatformApplicationMisc::ClipboardPaste(TextToImport);

        // Import the nodes
        TSet<UEdGraphNode*> PastedNodes;
        FEdGraphUtilities::ImportNodesFromText(EdGraph, TextToImport, PastedNodes);

        // Average position of nodes so we can move them while still maintaining relative distances to each other
        FVector2D AvgNodePosition(0.0f, 0.0f);

        for (TSet<UEdGraphNode*>::TIterator It(PastedNodes); It; ++It) {
            UEdGraphNode* Node = *It;
            AvgNodePosition.X += Node->NodePosX;
            AvgNodePosition.Y += Node->NodePosY;
        }

        float InvNumNodes = 1.0f / float(PastedNodes.Num());
        AvgNodePosition.X *= InvNumNodes;
        AvgNodePosition.Y *= InvNumNodes;

        for (TSet<UEdGraphNode*>::TIterator It(PastedNodes); It; ++It) {
            UEdGraphNode* Node = *It;
            CurrentGraphEditor->SetNodeSelection(Node, true);

            Node->NodePosX = (Node->NodePosX - AvgNodePosition.X) + Location.X;
            Node->NodePosY = (Node->NodePosY - AvgNodePosition.Y) + Location.Y;

            Node->SnapToGrid(16);

            // Give new node a different Guid from the old one
            Node->CreateNewGuid();
        }
    }

    // Update UI
    CurrentGraphEditor->NotifyGraphChanged();

    UObject* GraphOwner = EdGraph->GetOuter();
    if (GraphOwner) {
        GraphOwner->PostEditChange();
        GraphOwner->MarkPackageDirty();
    }
}

bool FAssetEditor_AGSGraph::CanPasteNodes()
{
    TSharedPtr<SGraphEditor> CurrentGraphEditor = GetCurrGraphEditor();
    if (!CurrentGraphEditor.IsValid()) {
        return false;
    }

    FString ClipboardContent;
    FPlatformApplicationMisc::ClipboardPaste(ClipboardContent);

    return FEdGraphUtilities::CanImportNodesFromText(CurrentGraphEditor->GetCurrentGraph(), ClipboardContent);
}

void FAssetEditor_AGSGraph::DuplicateNodes()
{
    CopySelectedNodes();
    PasteNodes();
}

bool FAssetEditor_AGSGraph::CanDuplicateNodes()
{
    return CanCopyNodes();
}

void FAssetEditor_AGSGraph::GraphSettings()
{
    PropertyWidget->SetObject(EditingGraph);
}

bool FAssetEditor_AGSGraph::CanGraphSettings() const
{
    return true;
}

void FAssetEditor_AGSGraph::OnRenameNode()
{
    TSharedPtr<SGraphEditor> CurrentGraphEditor = GetCurrGraphEditor();
    if (CurrentGraphEditor.IsValid()) {
        const FGraphPanelSelectionSet SelectedNodes = GetSelectedNodes();
        for (FGraphPanelSelectionSet::TConstIterator NodeIt(SelectedNodes); NodeIt; ++NodeIt) {
            UEdGraphNode* SelectedNode = Cast<UEdGraphNode>(*NodeIt);
            if (SelectedNode != NULL && SelectedNode->bCanRenameNode) {
                CurrentGraphEditor->IsNodeTitleVisible(SelectedNode, true);
                break;
            }
        }
    }
}

bool FAssetEditor_AGSGraph::CanRenameNodes() const
{
    UEdGraph_AGSGraph* EdGraph = Cast<UEdGraph_AGSGraph>(EditingGraph->EdGraph);
    check(EdGraph != nullptr);

    UAGSGraph* Graph = EdGraph->GetAGSGraph();
    check(Graph != nullptr)

            return Graph->bCanRenameNode
        && GetSelectedNodes().Num() == 1;
}

void FAssetEditor_AGSGraph::OnSelectedNodesChanged(const TSet<class UObject*>& NewSelection)
{
    TArray<UObject*> Selection;

    for (UObject* SelectionEntry : NewSelection) {
        Selection.Add(SelectionEntry);
    }

    if (Selection.Num() == 0) {
        PropertyWidget->SetObject(EditingGraph);

    } else {
        PropertyWidget->SetObjects(Selection);
    }
}

void FAssetEditor_AGSGraph::OnNodeDoubleClicked(UEdGraphNode* Node)
{
}

void FAssetEditor_AGSGraph::OnFinishedChangingProperties(const FPropertyChangedEvent& PropertyChangedEvent)
{
    if (EditingGraph == nullptr)
        return;

    EditingGraph->EdGraph->GetSchema()->ForceVisualizationCacheClear();
}

void FAssetEditor_AGSGraph::OnPackageSavedWithContext(const FString& PackageFileName, UPackage* Package, FObjectPostSaveContext ObjectSaveContext)
{
    RebuildAGSGraph();
}

#undef LOCTEXT_NAMESPACE
