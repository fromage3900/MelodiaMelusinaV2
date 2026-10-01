// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "SACFAttributeWidget.h"

#include "ACFAttributeStrUtils.h"
#include "ACFAttributePalette.h"
#include "ACFAttributeUtils.h"
#include "SACFAttributePicker.h"

#include "ContentBrowserModule.h"
#include "IContentBrowserSingleton.h"
#include "HAL/PlatformApplicationMisc.h"

static FGameplayAttribute AttributeFromClipboard()
{
	FString Str;
	FPlatformApplicationMisc::ClipboardPaste(Str);
	return ACFAttributeUtils::ImportFromString(Str);
}

void SACFAttributeWidget::Construct(const FArguments& InArgs)
{
	FilterMetaData = InArgs._FilterMetaData;
	OnAttributeChanged = InArgs._OnAttributeChanged;
	SelectedAttribute = InArgs._DefaultAttribute;
	WhiteList = InArgs._WhiteList;

	auto GetColor = [this]()
	{
		return SelectedAttribute.IsValidSafe()
			       ? ACFAttributePalette::GetColor(SelectedAttribute.GetClassName())
			       : FLinearColor{FColor::White};
	};

	TSharedPtr<SHorizontalBox> HorizontalBox;

	auto AttributeLabelBox = SNew(SHorizontalBox)
		.Clipping(EWidgetClipping::ClipToBounds);
	if (!InArgs._CompactMode)
	{
		// class name 
		AttributeLabelBox->AddSlot().AutoWidth()
		[
			SNew(STextBlock)
			.Text_Lambda([this] { return SelectedAttribute.IsValidSafe() ? FText::FromString(ACFAttributeStrUtils::GetDisplayClassName(SelectedAttribute)) : FText{}; })
			.ColorAndOpacity_Lambda(GetColor)
		];
		// separator
		AttributeLabelBox->AddSlot().AutoWidth().Padding(3, 0)
		[
			SNew(STextBlock)
			.Text_Lambda([this]()
			{
				return SelectedAttribute.IsValidSafe() ? FText::FromString(TEXT(".")) : FText{};
			})
			.Justification(ETextJustify::Type::Center)
			.ColorAndOpacity(FSlateColor{FColor::White})
		];
	}
	
	// attribute name
	AttributeLabelBox->AddSlot().AutoWidth()
	[
		SNew(STextBlock)
		.Text_Lambda([this]
		{
			return FText::FromString(SelectedAttribute.GetAttributeName());
		})
		.ColorAndOpacity_Lambda(GetColor)
	];
	
	ChildSlot
	[
		SNew(SBorder)
		.OnMouseButtonDown_Lambda([this](const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
		{
			if (MouseEvent.IsMouseButtonDown(EKeys::RightMouseButton))
			{
				OnMenu(MouseEvent);
				return FReply::Handled();
			}
			return FReply::Unhandled();
		})
		.Padding(0.0f)
		.BorderImage(FStyleDefaults::GetNoBrush())
		[
			SAssignNew(HorizontalBox, SHorizontalBox)
			+ SHorizontalBox::Slot()
			[
				SAssignNew(ComboButton, SComboButton)
				.OnGetMenuContent(this, &SACFAttributeWidget::GenerateAttributePicker)
				.ToolTipText(this, &SACFAttributeWidget::GetSelectedValueAsString)
				.ButtonContent()
				[AttributeLabelBox]
			]
		]
	];

	if (!InArgs._CompactMode)
	{
		HorizontalBox->AddSlot().AutoWidth()
		[
			SNew(SButton)
			.OnClicked_Lambda([this]()
			{
				UClass* Class = SelectedAttribute.GetClassPath().ResolveClass();
				if (Class && Class->IsAsset())
				{
					const FContentBrowserModule& ContentBrowserModule = FModuleManager::Get().LoadModuleChecked<
						FContentBrowserModule>("ContentBrowser");
					ContentBrowserModule.Get().SyncBrowserToAssets(TArray<UObject*>{Class});
				}
				return FReply::Handled();
			})
			.ToolTipText_Lambda([this]()
			{
				return FText::FromString(FString::Printf(TEXT("Show %s in Content Browser"),
				                                         *SelectedAttribute.GetClassPath().GetAssetName()));
			})
			.IsEnabled_Lambda([this]()
			{
				const UClass* Class = SelectedAttribute.GetClassPath().ResolveClass();
				return Class && Class->IsAsset();
			})
			[
				SNew(SImage)
				.Image(
					FSlateIcon(FAppStyle::GetAppStyleSetName(),
					           "SystemWideCommands.FindInContentBrowser").GetIcon())
			]
		];
		HorizontalBox->AddSlot().AutoWidth()
		[
			SNew(SButton)
			.OnClicked_Lambda([this]()
			{
				UClass* Class = SelectedAttribute.GetClassPath().ResolveClass();
				UAssetEditorSubsystem* AssetEditorSubsystem = GEditor
					                                              ? GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()
					                                              : nullptr;
				if (Class && Class->IsAsset() && AssetEditorSubsystem)
				{
					if (UBlueprintGeneratedClass* BPClass = Cast<UBlueprintGeneratedClass>(Class))
						AssetEditorSubsystem->OpenEditorForAsset(BPClass->ClassGeneratedBy);
				}
				return FReply::Handled();
			})
			.ToolTipText_Lambda([this]()
			{
				return FText::FromString(FString::Printf(TEXT("Edit %s"),
				                                         *SelectedAttribute.GetClassPath().GetAssetName()));
			})
			.IsEnabled_Lambda([this]()
			{
				const UClass* Class = SelectedAttribute.GetClassPath().ResolveClass();
				return Class && Class->IsAsset();
			})
			[
				SNew(SImage)
				.Image(FAppStyle::GetBrush("Icons.Edit"))
			]
		];
	}
}

void SACFAttributeWidget::OnCopyAttribute(const FACFAttributeWrapper& copiedAttribute)
{
	if (copiedAttribute.IsValidSafe())
	{
		FPlatformApplicationMisc::ClipboardCopy(*ACFAttributeUtils::ExportToString(copiedAttribute));
	}
}

bool SACFAttributeWidget::CanPaste() const
{
	return AttributeFromClipboard().IsValid();
}

void SACFAttributeWidget::OnPasteAttribute()
{
	if (const FGameplayAttribute Attribute = AttributeFromClipboard(); Attribute.IsValid())
	{
		FScopedTransaction Transaction(FText::FromString("Paste Gameplay Attribute"));

		SelectedAttribute = FACFAttributeWrapper{Attribute.GetUProperty()};
		OnAttributeChanged.ExecuteIfBound(SelectedAttribute);
	}
}

void SACFAttributeWidget::OnMenu(const FPointerEvent& MouseEvent)
{
	FMenuBuilder MenuBuilder(/*bShouldCloseWindowAfterMenuSelection=*/true, /*CommandList=*/nullptr);

	MenuBuilder.AddMenuEntry(
		FText::FromString("Search For References"),
		FText::FromString("Find references"),
		FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Search"),
		FUIAction(FExecuteAction::CreateLambda([&]()
		{
			const FText AttributeName = GetSelectedValueAsString();
			if (FEditorDelegates::OnOpenReferenceViewer.IsBound() && !AttributeName.IsEmpty())
			{
				TArray<FAssetIdentifier> AssetIdentifiers;
				AssetIdentifiers.Emplace(FGameplayAttribute::StaticStruct(), *AttributeName.ToString());
				FEditorDelegates::OnOpenReferenceViewer.Broadcast(AssetIdentifiers, FReferenceViewerParams());
			}
		}))
	);

	MenuBuilder.AddSeparator();

	auto IsValid = FCanExecuteAction::CreateLambda([](const FACFAttributeWrapper& Attribute)
	{
		return Attribute.IsValidSafe();
	}, SelectedAttribute);
	MenuBuilder.AddMenuEntry(FText::FromString("Copy"),
		FText::FromString("Copy attribute"),
		FSlateIcon(FAppStyle::GetAppStyleSetName(), "GenericCommands.Copy"),
		FUIAction(
			FExecuteAction::CreateLambda([this](const FACFAttributeWrapper& Attribute) { OnCopyAttribute(Attribute); },
			                             SelectedAttribute),
			IsValid));

	MenuBuilder.AddMenuEntry(
		FText::FromString("Copy Path"),
		FText::FromString("Copy attribute"),
		FSlateIcon(FAppStyle::GetAppStyleSetName(), "GenericCommands.Copy"),
		FUIAction(
			FExecuteAction::CreateLambda([this](const FACFAttributeWrapper& Attribute)
			{
				FPlatformApplicationMisc::ClipboardCopy(*Attribute.ToPathString());
			}, SelectedAttribute),
			IsValid));


	MenuBuilder.AddMenuEntry(
		FText::FromString("Paste"),
		FText::FromString("Paste attribute from clipboard"),
		FSlateIcon(FAppStyle::GetAppStyleSetName(), "GenericCommands.Paste"),
		FUIAction(FExecuteAction::CreateSP(this, &SACFAttributeWidget::OnPasteAttribute),
		          FCanExecuteAction::CreateSP(this, &SACFAttributeWidget::CanPaste)));

	FWidgetPath WidgetPath = MouseEvent.GetEventPath() != nullptr ? *MouseEvent.GetEventPath() : FWidgetPath();
	FSlateApplication::Get().PushMenu(AsShared(), WidgetPath, MenuBuilder.MakeWidget(),
	                                  MouseEvent.GetScreenSpacePosition(),
	                                  FPopupTransitionEffect(FPopupTransitionEffect::ContextMenu));
}

void SACFAttributeWidget::OnAttributePicked(const FACFAttributeWrapper& InAttribute)
{
	SelectedAttribute = InAttribute;
	OnAttributeChanged.ExecuteIfBound(SelectedAttribute);
	ComboButton->SetIsOpen(false);
}

TSharedRef<SWidget> SACFAttributeWidget::GenerateAttributePicker()
{
	FOnACFAttributePicked OnPicked(
		FOnACFAttributePicked::CreateRaw(this, &SACFAttributeWidget::OnAttributePicked));

	return SNew(SBox)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot()
			.AutoHeight()
			.MaxHeight(500)
			[
				SNew(SACFAttributePicker)
				.OnAttributePickedDelegate(OnPicked)
				.FilterMetaData(FilterMetaData)
				.WhiteList(WhiteList)
			]
		];
}

FText SACFAttributeWidget::GetSelectedValueAsString() const
{
	return FText::FromString(ACFAttributeStrUtils::ToString(SelectedAttribute));
}
