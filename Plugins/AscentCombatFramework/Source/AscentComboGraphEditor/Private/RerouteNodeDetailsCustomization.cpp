#include "RerouteNodeDetailsCustomization.h"
#include "DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#include "Widgets/Input/SComboBox.h"
#include "Graph/ACFRerouteNode.h"
#include "Graph/ACFComboGraph.h"
#include "PropertyEditorModule.h"  // For Property customization
#include "Modules/ModuleManager.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SComboBox.h"
#include "IDetailCustomization.h"
#include "AGSGraphNode.h"


#define LOCTEXT_NAMESPACE "RerouteNodeDetailsCustomization"

TSharedRef<IDetailCustomization> FRerouteNodeDetailsCustomization::MakeInstance()
{
    return MakeShareable(new FRerouteNodeDetailsCustomization());
}

void FRerouteNodeDetailsCustomization::CustomizeDetails(IDetailLayoutBuilder& DetailBuilder)
{
    // Get the object being customized
    TArray<TWeakObjectPtr<UObject>> ObjectsBeingCustomized;
    DetailBuilder.GetObjectsBeingCustomized(ObjectsBeingCustomized);

    if (ObjectsBeingCustomized.Num() > 0)
    {
        EditedRerouteNode = Cast<UACFRerouteNode>(ObjectsBeingCustomized[0].Get());
    }

    if (!EditedRerouteNode.IsValid())
    {
        return;
    }

    // Hide the default TargetRerouteNode property
    DetailBuilder.HideProperty(GET_MEMBER_NAME_CHECKED(UACFRerouteNode, TargetRerouteNode));

    // Customize the RerouteNode category
    IDetailCategoryBuilder& RerouteNodeCategory = DetailBuilder.EditCategory("RerouteNode");

    // Add IsProxyNode checkbox
    RerouteNodeCategory.AddProperty(GET_MEMBER_NAME_CHECKED(UACFRerouteNode, bIsProxyNode));

    // Add custom TargetRerouteNode dropdown, conditionally visible
    RerouteNodeCategory.AddCustomRow(LOCTEXT("RerouteNodeDropdown", "Reroute Node"))
        .Visibility(TAttribute<EVisibility>::Create([this]()
        {
            return EditedRerouteNode->bIsProxyNode ? EVisibility::Visible : EVisibility::Collapsed;
        }))
        .NameContent()
        [
            SNew(STextBlock)
            .Text(LOCTEXT("TargetRerouteNodeLabel", "Target Reroute Node"))
            .Font(IDetailLayoutBuilder::GetDetailFont())
        ]
        .ValueContent()
        [
            SNew(SComboBox<TSharedPtr<FName>>)
            .OptionsSource(&RerouteNodeOptions)
            .OnSelectionChanged(this, &FRerouteNodeDetailsCustomization::OnRerouteNodeSelected)
            .OnGenerateWidget_Lambda([](TSharedPtr<FName> Item)
            {
                return SNew(STextBlock).Text(FText::FromName(*Item));
            })
            .InitiallySelectedItem(CurrentSelection)
            [
                SNew(STextBlock)
                .Text_Lambda([this]()
                {
                    return CurrentSelection.IsValid() ? FText::FromName(*CurrentSelection) : LOCTEXT("SelectRerouteNode", "Select a Reroute Node");
                })
            ]
        ];

    // Generate dropdown options
    GenerateRerouteNodeOptions();
}


void FRerouteNodeDetailsCustomization::GenerateRerouteNodeOptions()
{
    RerouteNodeOptions.Empty();

    // Add default option for new reroute nodes
    RerouteNodeOptions.Add(MakeShared<FName>(TEXT("New Reroute Node")));

    if (!EditedRerouteNode.IsValid())
    {
        return;
    }

    // Get the graph containing the reroute nodes
    UACFComboGraph* ComboGraph = Cast<UACFComboGraph>(EditedRerouteNode->GetGraph());
    if (!ComboGraph)
    {
        return;
    }

    // Populate dropdown with existing reroute nodes in the graph
    for (UAGSGraphNode* Node : ComboGraph->GetAllNodes())
    {
        if (UACFRerouteNode* RerouteNode = Cast<UACFRerouteNode>(Node))
        {
            // Only add nodes where bIsProxyNode is false
            if (!RerouteNode->bIsProxyNode)
            {
                RerouteNodeOptions.Add(MakeShared<FName>(*RerouteNode->NodeName));
            }
        }
    }

    // Set the current selection to match the edited node's target
    for (TSharedPtr<FName> Option : RerouteNodeOptions)
    {
        if (Option.IsValid() && EditedRerouteNode->TargetRerouteNode && EditedRerouteNode->TargetRerouteNode->NodeName == Option->ToString())
        {
            CurrentSelection = Option;
            break;
        }
    }
}

void FRerouteNodeDetailsCustomization::OnRerouteNodeSelected(TSharedPtr<FName> NewSelection, ESelectInfo::Type SelectInfo)
{
    if (NewSelection.IsValid() && EditedRerouteNode.IsValid())
    {
        UACFComboGraph* ComboGraph = Cast<UACFComboGraph>(EditedRerouteNode->GetGraph());
        if (!ComboGraph)
        {
            return;
        }

        UE_LOG(LogTemp, Warning, TEXT("Proxy Reroute Node: %s"), *NewSelection->ToString());
        for (UAGSGraphNode* Node : ComboGraph->GetAllNodes())
        {
            if (UACFRerouteNode* RerouteNode = Cast<UACFRerouteNode>(Node))
            {
                if (RerouteNode->NodeName == NewSelection->ToString())
                {
                    EditedRerouteNode->TargetRerouteNode = RerouteNode;
                    break;
                }
            }
        }
    }
}


#undef LOCTEXT_NAMESPACE
