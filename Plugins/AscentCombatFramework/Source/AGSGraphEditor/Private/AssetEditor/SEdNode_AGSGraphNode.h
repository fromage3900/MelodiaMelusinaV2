// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "SGraphNode.h"
#include "Widgets/SBoxPanel.h"

class UEdNode_AGSGraphNode;
class SErrorText;
class SNodeTitle;

class AGSGRAPHEDITOR_API SEdNode_AGSGraphNode : public SGraphNode {
public:
	SLATE_BEGIN_ARGS(SEdNode_AGSGraphNode) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs, UEdNode_AGSGraphNode* InNode);

	virtual void UpdateGraphNode() override;
	virtual void CreatePinWidgets() override;
	virtual void AddPin(const TSharedRef<SGraphPin>& PinToAdd) override;
	virtual bool IsNameReadOnly() const override;

	void OnNameTextCommited(const FText& InText, ETextCommit::Type CommitInfo);

	virtual FText GetParagraphTitle() const;

	virtual FSlateColor GetBorderBackgroundColor() const;
	virtual FSlateColor GetBackgroundColor() const;
	virtual FSlateColor GetTitleTextColor() const;
	virtual FSlateColor GetParagraphTextColor() const;

	virtual EVisibility GetDragOverMarkerVisibility() const;

	virtual const FSlateBrush* GetNameIcon() const;

protected:
	TSharedRef<SWidget> CreateContentArea(TSharedPtr<SNodeTitle> NodeTitle, TSharedPtr<SErrorText>& ErrorText);
	TSharedRef<SWidget> CreateTitleBlock(TSharedPtr<SNodeTitle> NodeTitle, TSharedPtr<SErrorText>& ErrorText, int32 FontSize);
	TSharedRef<SWidget> CreateParagraphBlock(TSharedPtr<SNodeTitle> NodeTitle, int32 FontSize);

	TSharedPtr<SBorder> NodeBody;
	TSharedPtr<SHorizontalBox> OutputPinBox;
};
