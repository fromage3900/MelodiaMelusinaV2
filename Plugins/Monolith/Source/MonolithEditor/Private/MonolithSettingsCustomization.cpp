#include "MonolithSettingsCustomization.h"
#include "MonolithSettings.h"
#include "MonolithIndexSubsystem.h"
#include "MonolithSourceSubsystem.h"
#include "DetailLayoutBuilder.h"
#include "DetailCategoryBuilder.h"
#include "DetailWidgetRow.h"
#include "Editor.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "MonolithSettingsCustomization"

TSharedRef<IDetailCustomization> FMonolithSettingsCustomization::MakeInstance()
{
	return MakeShareable(new FMonolithSettingsCustomization);
}

void FMonolithSettingsCustomization::CustomizeDetails(IDetailLayoutBuilder& DetailBuilder)
{
	IDetailCategoryBuilder& IndexCat = DetailBuilder.EditCategory("Indexing");

	// Re-Index Project button
	IndexCat.AddCustomRow(LOCTEXT("ReindexProjectRow", "Re-Index Project"))
		.NameContent()
		[
			SNew(STextBlock)
			.Text(LOCTEXT("ProjectIndexLabel", "Project Index"))
			.Font(IDetailLayoutBuilder::GetDetailFont())
		]
		.ValueContent()
		[
			SNew(SButton)
			.Text(LOCTEXT("ReindexProjectBtn", "Re-Index Now"))
			.IsEnabled_Lambda([]()
			{
				if (GEditor)
				{
					if (auto* Sub = GEditor->GetEditorSubsystem<UMonolithIndexSubsystem>())
					{
						return !Sub->IsIndexing();
					}
				}
				return false;
			})
			.OnClicked_Lambda([]()
			{
				if (GEditor)
				{
					if (auto* Sub = GEditor->GetEditorSubsystem<UMonolithIndexSubsystem>())
					{
						Sub->StartFullIndex();
					}
				}
				return FReply::Handled();
			})
		];

	// Re-Index Engine Source button
	IndexCat.AddCustomRow(LOCTEXT("ReindexEngineRow", "Re-Index Engine Source"))
		.NameContent()
		[
			SNew(STextBlock)
			.Text(LOCTEXT("EngineSourceLabel", "Engine Source"))
			.Font(IDetailLayoutBuilder::GetDetailFont())
		]
		.ValueContent()
		[
			SNew(SButton)
			.Text(LOCTEXT("ReindexEngineBtn", "Re-Index Now"))
			.IsEnabled_Lambda([]()
			{
				if (GEditor)
				{
					if (auto* Sub = GEditor->GetEditorSubsystem<UMonolithSourceSubsystem>())
					{
						return !Sub->IsIndexing();
					}
				}
				return false;
			})
			.OnClicked_Lambda([]()
			{
				if (GEditor)
				{
					if (auto* Sub = GEditor->GetEditorSubsystem<UMonolithSourceSubsystem>())
					{
						Sub->TriggerReindex();
					}
				}
				return FReply::Handled();
			})
		];
}

#undef LOCTEXT_NAMESPACE
