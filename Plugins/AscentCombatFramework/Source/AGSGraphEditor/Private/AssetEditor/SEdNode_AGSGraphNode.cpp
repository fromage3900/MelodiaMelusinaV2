// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "SEdNode_AGSGraphNode.h"
#include "AGSGraphEditorPCH.h"
#include "AGSGraphEditorSettings.h"
#include "AGSGraphStyle.h"
#include "Colors_AGSGraph.h"
#include "EdNode_AGSGraphNode.h"
#include "GraphEditorSettings.h"
#include "SCommentBubble.h"
#include "SGraphPin.h"
#include "SLevelOfDetailBranchNode.h"
#include "ScopedTransaction.h"
#include "SlateOptMacros.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/SInlineEditableTextBlock.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "EdNode_AGSGraph"

namespace
{
	float GetColorLuminance(const FLinearColor& Color)
	{
		return Color.R * 0.299f + Color.G * 0.587f + Color.B * 0.114f;
	}
}

//////////////////////////////////////////////////////////////////////////
class SAGSGraphPin : public SGraphPin {
public:
    SLATE_BEGIN_ARGS(SAGSGraphPin) { }
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs, UEdGraphPin* InPin)
    {
        this->SetCursor(EMouseCursor::Default);

        bShowLabel = true;

        GraphPinObj = InPin;
        check(GraphPinObj != nullptr);

        const UEdGraphSchema* Schema = GraphPinObj->GetSchema();
        check(Schema);

        SBorder::Construct(SBorder::FArguments()
                .BorderImage(this, &SAGSGraphPin::GetPinBorder)
                .BorderBackgroundColor(this, &SAGSGraphPin::GetPinColor)
                .OnMouseButtonDown(this, &SAGSGraphPin::OnPinMouseDown)
                .Cursor(this, &SAGSGraphPin::GetPinCursor)
                .Padding(FMargin(6.0f, 4.0f)));
    }

protected:
    virtual FSlateColor GetPinColor() const override
    {
        return IsHovered() ? AGSGraphColors::Pin::Hover : AGSGraphColors::Pin::Default;
    }

    virtual TSharedRef<SWidget> GetDefaultValueWidget() override
    {
        return SNew(STextBlock);
    }

    const FSlateBrush* GetPinBorder() const
    {
        return FAGSGraphStyle::Get().GetBrush("AGSGraph.Node.Pin");
    }
};

//////////////////////////////////////////////////////////////////////////
void SEdNode_AGSGraphNode::Construct(const FArguments& InArgs, UEdNode_AGSGraphNode* InNode)
{
    GraphNode = InNode;
    UpdateGraphNode();
    InNode->SEdNode = this;
}

BEGIN_SLATE_FUNCTION_BUILD_OPTIMIZATION
void SEdNode_AGSGraphNode::UpdateGraphNode()
{
    const FMargin NodePadding = FMargin(2.0f);
    const UAGSGraphEditorSettings* AGSSettings = GetDefault<UAGSGraphEditorSettings>();

    InputPins.Empty();
    OutputPins.Empty();

    RightNodeBox.Reset();
    LeftNodeBox.Reset();
    OutputPinBox.Reset();

    TSharedPtr<SErrorText> ErrorText;
    TSharedPtr<SNodeTitle> NodeTitle = SNew(SNodeTitle, GraphNode);

    this->GetOrAddSlot(ENodeZone::Center)
        .HAlign(HAlign_Fill)
        .VAlign(VAlign_Center)
            [SNew(SVerticalBox)

                // INPUT PIN AREA
                + SVerticalBox::Slot()
                    .AutoHeight()
                        [SNew(SBox)
                                .MinDesiredHeight(NodePadding.Top)
                                    [SAssignNew(LeftNodeBox, SVerticalBox)]]

                // NODE CONTENT (style-dependent)
                + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(FMargin(NodePadding.Left, 0.0f, NodePadding.Right, 0.0f))
                        [SNew(SBox)
                                .MinDesiredWidth(AGSSettings->NodeMinWidth)
                                    [CreateContentArea(NodeTitle, ErrorText)]]

                // OUTPUT PIN AREA
                + SVerticalBox::Slot()
                    .AutoHeight()
                        [SNew(SBox)
                                .MinDesiredHeight(NodePadding.Bottom)
                                    [SAssignNew(RightNodeBox, SVerticalBox)
                                        + SVerticalBox::Slot()
                                            .HAlign(HAlign_Fill)
                                            .VAlign(VAlign_Fill)
                                            .Padding(20.0f, 0.0f)
                                            .FillHeight(1.0f)
                                                [SAssignNew(OutputPinBox, SHorizontalBox)]]]];

    // Create comment bubble
    TSharedPtr<SCommentBubble> CommentBubble;
    const FSlateColor CommentColor = GetDefault<UGraphEditorSettings>()->DefaultCommentNodeTitleColor;

    SAssignNew(CommentBubble, SCommentBubble)
        .GraphNode(GraphNode)
        .Text(this, &SGraphNode::GetNodeComment)
        .OnTextCommitted(this, &SGraphNode::OnCommentTextCommitted)
        .ColorAndOpacity(CommentColor)
        .AllowPinning(true)
        .EnableTitleBarBubble(true)
        .EnableBubbleCtrls(true)
        .GraphLOD(this, &SGraphNode::GetCurrentLOD)
        .IsGraphNodeHovered(this, &SGraphNode::IsHovered);

    GetOrAddSlot(ENodeZone::TopCenter)
        .SlotOffset2f(TAttribute<FVector2f>(CommentBubble.Get(), &SCommentBubble::GetOffset2f))
        .SlotSize2f(TAttribute<FVector2f>(CommentBubble.Get(), &SCommentBubble::GetSize2f))
        .AllowScaling(TAttribute<bool>(CommentBubble.Get(), &SCommentBubble::IsScalingAllowed))
        .VAlign(VAlign_Top)
            [CommentBubble.ToSharedRef()];

    ErrorReporting = ErrorText;
    ErrorReporting->SetError(ErrorMsg);
    CreatePinWidgets();
}

TSharedRef<SWidget> SEdNode_AGSGraphNode::CreateContentArea(TSharedPtr<SNodeTitle> NodeTitle, TSharedPtr<SErrorText>& ErrorText)
{
    const EAGSGraphNodeStyle Style = GetDefault<UAGSGraphEditorSettings>()->NodeStyle;

    switch (Style)
    {
    case EAGSGraphNodeStyle::Filled:
        return SAssignNew(NodeBody, SBorder)
            .BorderImage(FAGSGraphStyle::Get().GetBrush("AGSGraph.Node.FullBody"))
            .BorderBackgroundColor(this, &SEdNode_AGSGraphNode::GetBorderBackgroundColor)
            .Padding(FMargin(10.0f, 8.0f))
            .Visibility(EVisibility::SelfHitTestInvisible)
                [SNew(SVerticalBox)
                    + SVerticalBox::Slot()
                        .AutoHeight()
                            [CreateTitleBlock(NodeTitle, ErrorText, 11)]
                    + SVerticalBox::Slot()
                        .AutoHeight()
                        .Padding(0.0f, 4.0f, 0.0f, 0.0f)
                            [CreateParagraphBlock(NodeTitle, 9)]];

    case EAGSGraphNodeStyle::Minimal:
        return SNew(SHorizontalBox)
            + SHorizontalBox::Slot()
                .AutoWidth()
                    [SNew(SBox)
                            .WidthOverride(5.0f)
                                [SNew(SBorder)
                                        .BorderImage(FAGSGraphStyle::Get().GetBrush("AGSGraph.Node.AccentLeft"))
                                        .BorderBackgroundColor(this, &SEdNode_AGSGraphNode::GetBorderBackgroundColor)]]
            + SHorizontalBox::Slot()
                .FillWidth(1.0f)
                    [SAssignNew(NodeBody, SBorder)
                            .BorderImage(FAGSGraphStyle::Get().GetBrush("AGSGraph.Node.BodyRight"))
                            .BorderBackgroundColor(this, &SEdNode_AGSGraphNode::GetBackgroundColor)
                            .Padding(FMargin(10.0f, 8.0f))
                            .Visibility(EVisibility::SelfHitTestInvisible)
                                [SNew(SVerticalBox)
                                    + SVerticalBox::Slot()
                                        .AutoHeight()
                                            [CreateTitleBlock(NodeTitle, ErrorText, 11)]
                                    + SVerticalBox::Slot()
                                        .AutoHeight()
                                        .Padding(0.0f, 4.0f, 0.0f, 0.0f)
                                            [CreateParagraphBlock(NodeTitle, 9)]]];

    case EAGSGraphNodeStyle::Classic:
        return SNew(SBorder)
            .BorderImage(FAppStyle::GetBrush("Graph.StateNode.Body"))
            .Padding(3.0f)
            .BorderBackgroundColor(this, &SEdNode_AGSGraphNode::GetBorderBackgroundColor)
                [SAssignNew(NodeBody, SBorder)
                        .BorderImage(FAppStyle::GetBrush("BTEditor.Graph.BTNode.Body"))
                        .BorderBackgroundColor(this, &SEdNode_AGSGraphNode::GetBackgroundColor)
                        .Padding(FMargin(8.0f, 6.0f))
                        .Visibility(EVisibility::SelfHitTestInvisible)
                            [SNew(SVerticalBox)
                                + SVerticalBox::Slot()
                                    .AutoHeight()
                                        [CreateTitleBlock(NodeTitle, ErrorText, 14)]
                                + SVerticalBox::Slot()
                                    .AutoHeight()
                                    .Padding(0.0f, 2.0f, 0.0f, 0.0f)
                                        [CreateParagraphBlock(NodeTitle, 12)]]];

    case EAGSGraphNodeStyle::ModernHeader:
    default:
        return SNew(SVerticalBox)
            + SVerticalBox::Slot()
                .AutoHeight()
                    [SNew(SBorder)
                            .BorderImage(FAGSGraphStyle::Get().GetBrush("AGSGraph.Node.Header"))
                            .BorderBackgroundColor(this, &SEdNode_AGSGraphNode::GetBorderBackgroundColor)
                            .Padding(FMargin(8.0f, 6.0f))
                                [CreateTitleBlock(NodeTitle, ErrorText, 11)]]
            + SVerticalBox::Slot()
                .AutoHeight()
                    [SAssignNew(NodeBody, SBorder)
                            .BorderImage(FAGSGraphStyle::Get().GetBrush("AGSGraph.Node.Body"))
                            .BorderBackgroundColor(this, &SEdNode_AGSGraphNode::GetBackgroundColor)
                            .Padding(FMargin(10.0f, 8.0f))
                            .HAlign(HAlign_Fill)
                            .VAlign(VAlign_Center)
                            .Visibility(EVisibility::SelfHitTestInvisible)
                                [CreateParagraphBlock(NodeTitle, 9)]];
    }
}

TSharedRef<SWidget> SEdNode_AGSGraphNode::CreateTitleBlock(TSharedPtr<SNodeTitle> NodeTitle, TSharedPtr<SErrorText>& ErrorText, int32 FontSize)
{
    return SNew(SHorizontalBox)
        + SHorizontalBox::Slot()
            .AutoWidth()
                [SAssignNew(ErrorText, SErrorText)
                        .BackgroundColor(this, &SEdNode_AGSGraphNode::GetErrorColor)
                        .ToolTipText(this, &SEdNode_AGSGraphNode::GetErrorMsgToolTip)]
        + SHorizontalBox::Slot()
            .FillWidth(1.0f)
            .HAlign(HAlign_Center)
            .VAlign(VAlign_Center)
                [SAssignNew(InlineEditableText, SInlineEditableTextBlock)
                        .Font(FCoreStyle::GetDefaultFontStyle("Bold", FontSize))
                        .ColorAndOpacity(this, &SEdNode_AGSGraphNode::GetTitleTextColor)
                        .Text(NodeTitle.Get(), &SNodeTitle::GetHeadTitle)
                        .OnVerifyTextChanged(this, &SEdNode_AGSGraphNode::OnVerifyNameTextChanged)
                        .OnTextCommitted(this, &SEdNode_AGSGraphNode::OnNameTextCommited)
                        .IsReadOnly(this, &SEdNode_AGSGraphNode::IsNameReadOnly)
                        .IsSelected(this, &SEdNode_AGSGraphNode::IsSelectedExclusively)
                        .Justification(ETextJustify::Center)];
}

TSharedRef<SWidget> SEdNode_AGSGraphNode::CreateParagraphBlock(TSharedPtr<SNodeTitle> NodeTitle, int32 FontSize)
{
    return SNew(SVerticalBox)
        + SVerticalBox::Slot()
            .AutoHeight()
                [SNew(STextBlock)
                        .Font(FCoreStyle::GetDefaultFontStyle("Regular", FontSize))
                        .ColorAndOpacity(this, &SEdNode_AGSGraphNode::GetParagraphTextColor)
                        .Text(this, &SEdNode_AGSGraphNode::GetParagraphTitle)
                        .Justification(ETextJustify::Center)
                        .AutoWrapText(true)]
        + SVerticalBox::Slot()
            .AutoHeight()
                [NodeTitle.ToSharedRef()];
}

void SEdNode_AGSGraphNode::CreatePinWidgets()
{
    UEdNode_AGSGraphNode* StateNode = CastChecked<UEdNode_AGSGraphNode>(GraphNode);

    for (int32 PinIdx = 0; PinIdx < StateNode->Pins.Num(); PinIdx++) {
        UEdGraphPin* MyPin = StateNode->Pins[PinIdx];
        if (!MyPin->bHidden) {
            TSharedPtr<SGraphPin> NewPin = SNew(SAGSGraphPin, MyPin);

            AddPin(NewPin.ToSharedRef());
        }
    }
}

void SEdNode_AGSGraphNode::AddPin(const TSharedRef<SGraphPin>& PinToAdd)
{
    PinToAdd->SetOwner(SharedThis(this));

    const UEdGraphPin* PinObj = PinToAdd->GetPinObj();
    const bool bAdvancedParameter = PinObj && PinObj->bAdvancedView;
    if (bAdvancedParameter) {
        PinToAdd->SetVisibility(TAttribute<EVisibility>(PinToAdd, &SGraphPin::IsPinVisibleAsAdvanced));
    }

    if (PinToAdd->GetDirection() == EEdGraphPinDirection::EGPD_Input) {
        LeftNodeBox->AddSlot()
            .HAlign(HAlign_Fill)
            .VAlign(VAlign_Fill)
            .FillHeight(1.0f)
            .Padding(20.0f, 0.0f)
                [PinToAdd];
        InputPins.Add(PinToAdd);
    } else // Direction == EEdGraphPinDirection::EGPD_Output
    {
        OutputPinBox->AddSlot()
            .HAlign(HAlign_Fill)
            .VAlign(VAlign_Fill)
            .FillWidth(1.0f)
                [PinToAdd];
        OutputPins.Add(PinToAdd);
    }
}

bool SEdNode_AGSGraphNode::IsNameReadOnly() const
{
    UEdNode_AGSGraphNode* EdNode_Node = Cast<UEdNode_AGSGraphNode>(GraphNode);
    check(EdNode_Node != nullptr);

    UAGSGraph* AGSGraph = EdNode_Node->AGSGraphNode->Graph;
    check(AGSGraph != nullptr);

    return !AGSGraph->bCanRenameNode || SGraphNode::IsNameReadOnly();
}

END_SLATE_FUNCTION_BUILD_OPTIMIZATION

void SEdNode_AGSGraphNode::OnNameTextCommited(const FText& InText, ETextCommit::Type CommitInfo)
{
    SGraphNode::OnNameTextCommited(InText, CommitInfo);

    UEdNode_AGSGraphNode* MyNode = CastChecked<UEdNode_AGSGraphNode>(GraphNode);

    if (MyNode != nullptr && MyNode->AGSGraphNode != nullptr) {
        const FScopedTransaction Transaction(LOCTEXT("AGSGraphEditorRenameNode", "Generic Graph Editor: Rename Node"));
        MyNode->Modify();
        MyNode->AGSGraphNode->Modify();
        UpdateGraphNode();
    }
}

FText SEdNode_AGSGraphNode::GetParagraphTitle() const
{
    UEdNode_AGSGraphNode* MyNode = CastChecked<UEdNode_AGSGraphNode>(GraphNode);

    return MyNode ? MyNode->GetParagraphTitle() : FText::FromString("Implement me!");
}

FSlateColor SEdNode_AGSGraphNode::GetBorderBackgroundColor() const
{
    UEdNode_AGSGraphNode* MyNode = CastChecked<UEdNode_AGSGraphNode>(GraphNode);
    return MyNode ? MyNode->GetBackgroundColor() : AGSGraphColors::NodeBorder::HighlightAbortRange0;
}

FSlateColor SEdNode_AGSGraphNode::GetBackgroundColor() const
{
    return AGSGraphColors::NodeBody::Default;
}

FSlateColor SEdNode_AGSGraphNode::GetTitleTextColor() const
{
    const EAGSGraphNodeStyle Style = GetDefault<UAGSGraphEditorSettings>()->NodeStyle;

    // Title sits on a node-colored background: pick a contrasting color.
    if (Style == EAGSGraphNodeStyle::ModernHeader || Style == EAGSGraphNodeStyle::Filled)
    {
        const float Luminance = GetColorLuminance(GetBorderBackgroundColor().GetSpecifiedColor());
        return Luminance > 0.55f ? FLinearColor(0.08f, 0.08f, 0.1f, 1.0f) : FLinearColor(0.95f, 0.96f, 0.98f, 1.0f);
    }

    return FLinearColor(0.95f, 0.96f, 0.98f, 1.0f);
}

FSlateColor SEdNode_AGSGraphNode::GetParagraphTextColor() const
{
    if (GetDefault<UAGSGraphEditorSettings>()->NodeStyle == EAGSGraphNodeStyle::Filled)
    {
        const float Luminance = GetColorLuminance(GetBorderBackgroundColor().GetSpecifiedColor());
        return Luminance > 0.55f ? FLinearColor(0.15f, 0.15f, 0.18f, 1.0f) : FLinearColor(0.85f, 0.87f, 0.9f, 1.0f);
    }

    return FLinearColor(0.82f, 0.84f, 0.88f, 1.0f);
}

EVisibility SEdNode_AGSGraphNode::GetDragOverMarkerVisibility() const
{
    return EVisibility::Visible;
}

const FSlateBrush* SEdNode_AGSGraphNode::GetNameIcon() const
{
    return FAppStyle::GetBrush(TEXT("BTEditor.Graph.BTNode.Icon"));
}

#undef LOCTEXT_NAMESPACE
