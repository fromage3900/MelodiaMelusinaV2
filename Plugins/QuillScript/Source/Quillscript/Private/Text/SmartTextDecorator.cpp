// Copyright Bruno Caxito. All Rights Reserved.

#include "Text/SmartTextDecorator.h"

#include "Blueprint/UserWidget.h"
#include "Utils/Tools.h"
#include "Text/SmartTextBlockDecorator.h"
#include "Widgets/SToolTip.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Text/STextBlock.h"


FSmartTextDecorator::FSmartTextDecorator(URichTextBlock* InOwner, USmartTextBlockDecorator* InSmartTextBlockDecorator)
	: FRichTextDecorator(InOwner)
	, SmartTextBlockDecorator(InSmartTextBlockDecorator)
{
	CustomTooltipBrush = MakeShareable(new FSlateBrush());
	CustomTooltipBrush->TintColor = FLinearColor(0, 0, 0, 0);
	CustomTooltipBrush->DrawAs = ESlateBrushDrawType::Box;
}

bool FSmartTextDecorator::Supports(const FTextRunParseResults& RunParseResult, const FString& Text) const
{
	return SmartTextBlockDecorator->TooltipTags.Contains(RunParseResult.Name) || RunParseResult.Name == USmartTextBlockDecorator::DelayTagName;
}

TSharedPtr<SWidget> FSmartTextDecorator::CreateDecoratorWidget(const FTextRunInfo& InRunInfo, const FTextBlockStyle& InTextStyle) const
{
	// Check if the given tag has a valid data associated to it.
	if (const auto* TooltipTextStyle{ SmartTextBlockDecorator->TooltipTags.Find(InRunInfo.Name) }; TooltipTextStyle)
	{
		TSharedPtr<SWidget> TextElement;
		TSharedPtr<SToolTip> TooltipElement;

		// Create the text widget.
		if (TooltipTextStyle->TextWidgetClass && this->SmartTextBlockDecorator->GetWorld())
		{
			if (const TObjectPtr<UUserWidget> TextWidget{ CreateWidget<UUserWidget>(this->SmartTextBlockDecorator->GetWorld(), TooltipTextStyle->TextWidgetClass) })
			{
				// Pass data.
				UTools::InsertPropertyByName(TextWidget, "Name", &InRunInfo.Name);
				UTools::InsertPropertyByName(TextWidget, "Content", &InRunInfo.Content);
				UTools::InsertPropertyByName(TextWidget, "Metadata", &InRunInfo.MetaData);

				// Create the text element.
				TextElement = SNew(SBorder)
					.Padding(this->SmartTextBlockDecorator->TooltipTags[InRunInfo.Name].TextPadding)
					.BorderImage(&this->SmartTextBlockDecorator->TooltipTags[InRunInfo.Name].TextBorderBrush)
					[
						TextWidget->TakeWidget()
					];
			}
		}

		// Use a simple text block as the text element.
		else
		{
			TextElement = SNew(SBorder)
				.Padding(this->SmartTextBlockDecorator->TooltipTags[InRunInfo.Name].TextPadding)
				.BorderImage(&this->SmartTextBlockDecorator->TooltipTags[InRunInfo.Name].TextBorderBrush)
				[
					SNew(STextBlock)
						.Text(InRunInfo.Content)
						.TextStyle(&TooltipTextStyle->TextStyle)
				];
		}

		// Create the tooltip widget.
		if (TooltipTextStyle->TooltipWidgetClass && this->SmartTextBlockDecorator->GetWorld())
		{
			if (const TObjectPtr<UUserWidget> TooltipWidget{ CreateWidget<UUserWidget>(this->SmartTextBlockDecorator->GetWorld(), TooltipTextStyle->TooltipWidgetClass) })
			{
				// Pass data.
				UTools::InsertPropertyByName(TooltipWidget, "Name", &InRunInfo.Name);
				UTools::InsertPropertyByName(TooltipWidget, "Content", &InRunInfo.Content);
				UTools::InsertPropertyByName(TooltipWidget, "Metadata", &InRunInfo.MetaData);

				// Create the tooltip element.
				TooltipElement = SNew(SToolTip)
					.BorderImage(CustomTooltipBrush.Get())
					[
						SNew(SBorder)
							.Padding(this->SmartTextBlockDecorator->TooltipTags[InRunInfo.Name].TooltipPadding)
							.BorderImage(&this->SmartTextBlockDecorator->TooltipTags[InRunInfo.Name].TooltipBorderBrush)
							[
								TooltipWidget->TakeWidget()
							]
					];
					// .IsInteractive(true)
					// .OnSetInteractiveWindowLocation_Lambda([](FVector2D& InOutDesiredLocation)
					// {
					// 	UTools::Print(InOutDesiredLocation.ToString());
					// 	InOutDesiredLocation = FVector2D(0, 0);
					// });
			}
		}

		// Use a simple text block as the tooltip.
		else
		{
			if (InRunInfo.MetaData.Contains("tooltip"))
			{
				TooltipElement = SNew(SToolTip)
					.BorderImage(CustomTooltipBrush.Get())
					[
						SNew(SBorder)
							.Padding(this->SmartTextBlockDecorator->TooltipTags[InRunInfo.Name].TooltipPadding)
							.BorderImage(&this->SmartTextBlockDecorator->TooltipTags[InRunInfo.Name].TooltipBorderBrush)
							[
								SNew(STextBlock)
									.Text(FText::FromString(InRunInfo.MetaData["tooltip"]))
									.TextStyle(&TooltipTextStyle->TooltipStyle)
							]
					];
			}
		}

		// Return the created widget.
		if (TextElement.IsValid() && TooltipElement.IsValid())
			TextElement->SetToolTip(TooltipElement);

		if (TextElement.IsValid())
			return TextElement;
	}

	// It's a <delay value="100"></> tag (milliseconds)
	return nullptr;
}