// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "ACFAssetCreatorClassPicker.h"
#include "ClassViewerModule.h"
#include "EditorStyleSet.h"
#include "Runtime/Launch/Resources/Version.h"
#include "IDocumentation.h"
#include "SlateOptMacros.h"
#include "Factories/BlueprintFactory.h"
#include "Widgets/Layout/SUniformGridPanel.h"

BEGIN_SLATE_FUNCTION_BUILD_OPTIMIZATION

#define LOCTEXT_NAMESPACE "SAdventureClassPicker"

void SACFAssetCreatorClassPicker::Construct(const FArguments& InArgs)
{
	
}

bool SACFAssetCreatorClassPicker::ConfigureProperties(TWeakObjectPtr<UBlueprintFactory> InBlueprintFactory)
{
	bOkClicked = false;
	BlueprintFactory = InBlueprintFactory;
	
	ChildSlot
	[
		SNew(SBorder)
		.Visibility(EVisibility::Visible)
		.BorderImage(GetBrush("Menu.Background"))
		[
			SNew(SBox)
			.Visibility(EVisibility::Visible)
			.WidthOverride(1500.0f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.FillHeight(1)
				[
					SNew(SBorder)
					.BorderImage(GetBrush("ToolPanel.GroupBorder"))
					.Content()
					[
						SAssignNew(ParentClassContainer, SVerticalBox)
					]
				]
				// Ok/Cancel buttons
				+ SVerticalBox::Slot()
				  .AutoHeight()
				  .HAlign(HAlign_Center)
				  .VAlign(VAlign_Bottom)
				  .Padding(8)
				[
					SNew(SUniformGridPanel)
						.SlotPadding(GetMargin("StandardDialog.SlotPadding"))
						.MinDesiredSlotWidth(GetFloat("StandardDialog.MinDesiredSlotWidth"))
						.MinDesiredSlotHeight(GetFloat("StandardDialog.MinDesiredSlotHeight"))
					+ SUniformGridPanel::Slot(0, 0)
					[
						SNew(SButton)
						.HAlign(HAlign_Center)
						.ContentPadding(GetMargin("StandardDialog.ContentPadding"))
						.OnClicked(this, &SACFAssetCreatorClassPicker::OkClicked)
						.Text(LOCTEXT("ACFAssetCreatorClassPickerOk", "OK"))
					]
					+ SUniformGridPanel::Slot(1, 0)
					[
						SNew(SButton)
						.HAlign(HAlign_Center)
						.ContentPadding(GetMargin("StandardDialog.ContentPadding"))
						.OnClicked(this, &SACFAssetCreatorClassPicker::CancelClicked)
						.Text(LOCTEXT("ACFAssetCreatorClassPickerCancel", "Cancel"))
					]
				]
			]
		]
	];
	
	MakeParentClassPicker();
	
	TSharedRef<SWindow> Window = SNew(SWindow)
	.Title(FText::Format(LOCTEXT("CreateBlueprintOptions", "Create New {0}"), BlueprintFactory->GetDisplayName()))
	.ClientSize(FVector2D(400, 700))
	.SupportsMinimize(false).SupportsMaximize(false)
	[
		AsShared()
	];

	PickerWindow = Window;

	GEditor->EditorAddModalWindow(Window);
	BlueprintFactory.Reset();
	return bOkClicked;
}

FReply SACFAssetCreatorClassPicker::OkClicked()
{
	if (BlueprintFactory.IsValid())
	{
		BlueprintFactory->ParentClass = ParentClass.Get();
	}

	CloseDialog(true);

	return FReply::Handled();
}

void SACFAssetCreatorClassPicker::CloseDialog(bool bWasPicked)
{
	bOkClicked = bWasPicked;
	if (PickerWindow.IsValid())
	{
		PickerWindow.Pin()->RequestDestroyWindow();
	}
}

FReply SACFAssetCreatorClassPicker::CancelClicked()
{
	CloseDialog();
	return FReply::Handled();
}

FReply SACFAssetCreatorClassPicker::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape)
	{
		CloseDialog();
		return FReply::Handled();
	}
	
	return SWidget::OnKeyDown(MyGeometry, InKeyEvent);
}

const FSlateBrush* SACFAssetCreatorClassPicker::GetBrush(FName PropertyName)
{
	return FAppStyle::GetBrush(PropertyName);
}

const FMargin& SACFAssetCreatorClassPicker::GetMargin(FName PropertyName)
{
    return FAppStyle::GetMargin(PropertyName);

}

float SACFAssetCreatorClassPicker::GetFloat(FName PropertyName)
{
	return FAppStyle::GetFloat(PropertyName);
}

bool AdventureClassPickerFilter::IsClassAllowed(const FClassViewerInitializationOptions& InInitOptions, const UClass* InClass, TSharedRef<FClassViewerFilterFuncs> InFilterFuncs)
{
	return InFilterFuncs->IfInChildOfClassesSet(AllowedChildrenOfClasses, InClass) != EFilterReturn::Failed;
}

bool AdventureClassPickerFilter::IsUnloadedClassAllowed(const FClassViewerInitializationOptions& InInitOptions, const TSharedRef<const IUnloadedBlueprintData> InUnloadedClassData, TSharedRef<FClassViewerFilterFuncs> InFilterFuncs)
{
	return InFilterFuncs->IfInChildOfClassesSet(AllowedChildrenOfClasses, InUnloadedClassData) != EFilterReturn::Failed;
}

void SACFAssetCreatorClassPicker::MakeParentClassPicker()
{
	FClassViewerModule& ClassViewerModule = FModuleManager::LoadModuleChecked<FClassViewerModule>("ClassViewer");
	
	FClassViewerInitializationOptions Options;
	Options.Mode = EClassViewerMode::ClassPicker;
//	Options.bIsBlueprintBaseOnly = true;

	TSharedPtr<AdventureClassPickerFilter> Filter = MakeShareable(new AdventureClassPickerFilter);
	Filter->AllowedChildrenOfClasses.Add(BlueprintFactory->ParentClass);

	#if ENGINE_MAJOR_VERSION == 5
	Options.ClassFilters.Add(Filter.ToSharedRef());
	#else
	Options.ClassFilter = Filter;
	#endif
	
	Options.NameTypeToDisplay = EClassViewerNameTypeToDisplay::DisplayName;

	ParentClassContainer->ClearChildren();
	ParentClassContainer->AddSlot()
	.AutoHeight()
	[
		SNew(STextBlock)
		.Text(LOCTEXT("ParentClass", "Search for Class:"))
		.ShadowOffset(FVector2D(1.0f, 1.0f))
	];

	ParentClassContainer->AddSlot()
	[
		ClassViewerModule.CreateClassViewer(Options, FOnClassPicked::CreateSP(this, &SACFAssetCreatorClassPicker::OnClassPicked))
	];
}

void SACFAssetCreatorClassPicker::OnClassPicked(UClass* ChosenClass)
{
	ParentClass = ChosenClass;
}

#undef LOCTEXT_NAMESPACE

END_SLATE_FUNCTION_BUILD_OPTIMIZATION
