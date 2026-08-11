// Copyright Bruno Caxito. All Rights Reserved.

#include "QuillscriptEditor.h"

#include "DirectoryWatcherModule.h"
#include "IDirectoryWatcher.h"
#include "LevelEditor.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Core/QuillscriptAsset.h"
#include "Core/QuillscriptAssetActions.h"
#include "Core/QuillscriptInterpreterActions.h"
#include "Core/QuillscriptSettings.h"
#include "Core/QuillscriptSettingsActions.h"
#include "EditorFramework/AssetImportData.h"
#include "Interfaces/IPluginManager.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Styling/SlateStyle.h"
#include "Styling/SlateStyleRegistry.h"
#include "Utils/QuillscriptEditorToolbarCommands.h"
#include "Widgets/BackgroundBox.h"
#include "Widgets/BackgroundBoxActions.h"
#include "Widgets/DialogBox.h"
#include "Widgets/DialogBoxActions.h"
#include "Widgets/SelectionBox.h"
#include "Widgets/SelectionBoxActions.h"
#include "Widgets/SpriteBoxActions.h"


void FQuillscriptEditorModule::StartupModule()
{
	// Register Quillscript content browser menu category.
	IAssetTools& AssetTools{ FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get() };
	const EAssetTypeCategories::Type QuillscriptAssetCategory{ AssetTools.RegisterAdvancedAssetCategory(FName("QuillscriptAssetCategory"), FText::FromString("Quillscript")) };

	AssetTools.RegisterAssetTypeActions(MakeShareable(new FQuillscriptAssetActions(QuillscriptAssetCategory)));
	AssetTools.RegisterAssetTypeActions(MakeShareable(new FQuillscriptInterpreterActions(QuillscriptAssetCategory)));
	AssetTools.RegisterAssetTypeActions(MakeShareable(new FDialogBoxActions(QuillscriptAssetCategory)));
	AssetTools.RegisterAssetTypeActions(MakeShareable(new FSelectionBoxActions(QuillscriptAssetCategory)));
	AssetTools.RegisterAssetTypeActions(MakeShareable(new FBackgroundBoxActions(QuillscriptAssetCategory)));
	AssetTools.RegisterAssetTypeActions(MakeShareable(new FSpriteBoxActions(QuillscriptAssetCategory)));
	AssetTools.RegisterAssetTypeActions(MakeShareable(new FQuillscriptSettingsActions(QuillscriptAssetCategory)));

	/// ----------

	// Create the plugin style set.
	{
		// Get the path to the resources' folder.
		this->StyleSet = MakeShareable(new FSlateStyleSet("QuillscriptStyle"));
		this->StyleSet->SetContentRoot(IPluginManager::Get().FindPlugin("Quillscript")->GetBaseDir() / "Resources");

		// Creates thumbnail icons.
		this->StyleSet->Set("ClassThumbnail.QuillscriptAsset", new FSlateImageBrush(this->StyleSet->RootToContentDir("Script.png"), FVector2D(256, 256)));
		this->StyleSet->Set("ClassThumbnail.QuillscriptInterpreter", new FSlateImageBrush(this->StyleSet->RootToContentDir("Interpreter.png"), FVector2D(256, 256)));
		this->StyleSet->Set("ClassThumbnail.QuillscriptSaveGame", new FSlateImageBrush(this->StyleSet->RootToContentDir("Save.png"), FVector2D(256, 256)));

		this->StyleSet->Set("ClassThumbnail.DialogBox", new FSlateImageBrush(this->StyleSet->RootToContentDir("Dialog.png"), FVector2D(256, 256)));
		this->StyleSet->Set("ClassThumbnail.SelectionBox", new FSlateImageBrush(this->StyleSet->RootToContentDir("Selection.png"), FVector2D(256, 256)));
		this->StyleSet->Set("ClassThumbnail.BackgroundBox", new FSlateImageBrush(this->StyleSet->RootToContentDir("Background.png"), FVector2D(256, 256)));
		this->StyleSet->Set("ClassThumbnail.SpriteBox", new FSlateImageBrush(this->StyleSet->RootToContentDir("Sprite.png"), FVector2D(256, 256)));

		this->StyleSet->Set("ClassThumbnail.QuillscriptSettings", new FSlateImageBrush(this->StyleSet->RootToContentDir("Settings.png"), FVector2D(256, 256)));

		// Create UI icons.
		this->StyleSet->Set("Tabs", new FSlateImageBrush(StyleSet->RootToContentDir("Tabs.png"), FVector2D(24, 24)));

		// Register the created style.
		FSlateStyleRegistry::RegisterSlateStyle(*this->StyleSet);
	}

	/// ----------

	// Watch the 'Content' folder for changes.
	if (IDirectoryWatcher* DirectoryWatcher{ FModuleManager::Get().LoadModuleChecked<FDirectoryWatcherModule>(TEXT("DirectoryWatcher")).Get() })
	{
		FDelegateHandle DelegateHandle;

		DirectoryWatcher->RegisterDirectoryChangedCallback_Handle(
			FPaths::ProjectDir(),
			IDirectoryWatcher::FDirectoryChanged::CreateStatic(&FQuillscriptEditorModule::OnDirectoryContentsChanged),
			DelegateHandle
		);
	}

	/// ----------

	// Register the main toolbar extension.
	{
		FQuillscriptEditorToolbarCommands::Register();

		this->Commands = MakeShareable(new FUICommandList);
		// this->Commands->MapAction(
		// 	FQuillscriptEditorToolbarCommands::Get().OpenAlbum,
		// 	FExecuteAction::CreateLambda([this]()
		// 	{
		// 		UEditorTools::SpawnTab(
		// 			FText::FromString("Cards Album"),
		// 			"/Game/Editor/Widgets/CardsAlbumBP.CardsAlbumBP",
		// 			FSlateIcon(this->StyleSet->GetStyleSetName(), "Tabs")
		// 		);
		// 	})
		// );
		// this->Commands->MapAction(
		// 	FQuillscriptEditorToolbarCommands::Get().OpenHomeSite,
		// 	FExecuteAction::CreateLambda([]{ FString Error; FPlatformProcess::LaunchURL(TEXT("https://quillscript.ink/"), TEXT(""), &Error); })
		// );
		// this->Commands->MapAction(
		// 	FQuillscriptEditorToolbarCommands::Get().OpenIllustrationsFolder,
		// 	FExecuteAction::CreateLambda([]
		// 	{
		// 		const FString Path{ "file://" + FPaths::ConvertRelativePathToFull(FPaths::ProjectContentDir()) + "Apt/Cards/Illustrations" };
		// 		FString Error;
		// 		FPlatformProcess::LaunchURL(*Path, TEXT(""), &Error);
		// 	})
		// );

		const TSharedPtr<FExtender> ToolbarExtender{ MakeShareable(new FExtender) };
		ToolbarExtender->AddToolBarExtension(
			"Play",
			EExtensionHook::After,
			this->Commands,
			FToolBarExtensionDelegate::CreateRaw(this, &FQuillscriptEditorModule::AddToolbarButtons)
		);

		FLevelEditorModule& LevelEditorModule{ FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor") };
		LevelEditorModule.GetToolBarExtensibilityManager()->AddExtender(ToolbarExtender);
	}

	/// ----------

	// Register menu extension.
	{
		const TSharedRef<FExtender> MenuExtender(new FExtender());
		MenuExtender->AddMenuExtension(
			"LevelEditor",
			EExtensionHook::After,
			nullptr,
			FMenuExtensionDelegate::CreateRaw(this, &FQuillscriptEditorModule::AddMenuEntry)
		);

		FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor").GetMenuExtensibilityManager()->AddExtender(MenuExtender);
	}

	/// ----------

	// Register Default Events for Custom Assets.
	{
		// Dialog Box
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, UDialogBox::StaticClass(), "PreConstruct");
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, UDialogBox::StaticClass(), "Construct");
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, UDialogBox::StaticClass(), "Tick");
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, UDialogBox::StaticClass(), "Play");

		// Selection Box
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, USelectionBox::StaticClass(), "PreConstruct");
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, USelectionBox::StaticClass(), "Construct");
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, USelectionBox::StaticClass(), "Tick");
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, USelectionBox::StaticClass(), "Play");

		// Background Box
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, UBackgroundBox::StaticClass(), "PreConstruct");
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, UBackgroundBox::StaticClass(), "Construct");
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, UBackgroundBox::StaticClass(), "Tick");
		FKismetEditorUtilities::RegisterAutoGeneratedDefaultEvent(nullptr, UBackgroundBox::StaticClass(), "Play");
	}
}

void FQuillscriptEditorModule::ShutdownModule()
{
	// Unregister the style.
	FSlateStyleRegistry::UnRegisterSlateStyle(this->StyleSet->GetStyleSetName());

	// Unregister directory watcher.
	if (FDirectoryWatcherModule* DirectoryWatcherModule = FModuleManager::GetModulePtr<FDirectoryWatcherModule>(TEXT("DirectoryWatcher")))
	{
		if (IDirectoryWatcher* DirectoryWatcher = DirectoryWatcherModule->Get())
		{
			const FDelegateHandle DelegateHandle;
			DirectoryWatcher->UnregisterDirectoryChangedCallback_Handle(FPaths::ProjectContentDir(), DelegateHandle);
		}
	}
}

void FQuillscriptEditorModule::OnDirectoryContentsChanged(const TArray<FFileChangeData>& FileChanges)
{
	// Update existent Script asset.
	if (UQuillscriptSettings::Get()->GetAutoReimportScripts())
	{
		bool bSetup{ true };

		for (FFileChangeData FileChange : FileChanges)
		{
			// Check if it is a modified Quillscript script file.
			if (FileChange.Action == FFileChangeData::EFileChangeAction::FCA_Modified && FileChange.Filename.EndsWith(".qsc"))
			{
				TArray<FAssetData> OutAssetData;

				// Get all Script assets.
				if (bSetup)
				{
					FAssetRegistryModule& AssetRegistryModule{ FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry") };
					FTopLevelAssetPath AssetPath{ UQuillscriptAsset::StaticClass()->GetPathName() };

					AssetRegistryModule.Get().GetAssetsByClass(AssetPath, OutAssetData);
					bSetup = false;
				}

				// Reimport.
				for (FAssetData AssetData : OutAssetData)
					if (UQuillscriptAsset* ScriptAsset = Cast<UQuillscriptAsset>(AssetData.GetAsset()))
						if (ScriptAsset->AssetImportData->GetFirstFilename().Replace(TEXT("\\"), TEXT("/")) == FileChange.Filename.Replace(TEXT("\\"), TEXT("/")))
							ScriptAsset->ReimportScript();
			}
		}
	}
}

void FQuillscriptEditorModule::AddToolbarButtons(FToolBarBuilder& ToolbarBuilder)
{
	// // Add toolbar button.
	// ToolbarBuilder.AddSeparator();
	//
	// ToolbarBuilder.AddToolBarButton(
	// 	FQuillscriptEditorToolbarCommands::Get().OpenAlbum,
	// 	NAME_None,
	// 	FText::FromString("Cards Album"),
	// 	FText::FromString("Open Cards Album"),
	// 	FSlateIcon(QuillscriptStyleName, "Tabs")
	// );
	// ToolbarBuilder.AddToolBarButton(
	// 	FQuillscriptEditorToolbarCommands::Get().ToggleLocalTestMode,
	// 	NAME_None,
	// 	FText::FromString("Local Test Mode"),
	// 	FText::FromString("Toggle Local Test Mode"),
	// 	FSlateIcon(QuillscriptStyleName, "Tabs")
	// );
	//
	// // Add toolbar more options sub-menu.
	// const FUIAction CompileOptionsCommand;
	//
	// ToolbarBuilder.AddComboButton(
	// 	CompileOptionsCommand,
	// 	FOnGetContent::CreateStatic(&FQuillscriptEditorModule::FillComboButton, this->Commands),
	// 	FText::FromString("Apotheosis"),
	// 	FText::FromString("More options"),
	// 	TAttribute<FSlateIcon>(),
	// 	true
	// );
}

TSharedRef<SWidget> FQuillscriptEditorModule::FillComboButton(const TSharedPtr<FUICommandList> CommandsList)
{
	FMenuBuilder MenuBuilder(true, CommandsList);

	// // Add entries to the combo button.
	// MenuBuilder.BeginSection("CustomMenu", TAttribute(FText::FromString("URLs")));
	// MenuBuilder.AddMenuEntry(FQuillscriptEditorToolbarCommands::Get().OpenHomeSite);
	// MenuBuilder.AddMenuEntry(FQuillscriptEditorToolbarCommands::Get().OpenPlanningSite);
	// MenuBuilder.AddMenuEntry(FQuillscriptEditorToolbarCommands::Get().OpenRepositorySite);
	// MenuBuilder.AddMenuEntry(FQuillscriptEditorToolbarCommands::Get().OpenStorageSite);
	// MenuBuilder.EndSection();
	//
	// MenuBuilder.BeginSection("CustomMenu", TAttribute(FText::FromString("Folders")));
	// MenuBuilder.AddMenuEntry(FQuillscriptEditorToolbarCommands::Get().OpenCloudFolder);
	// MenuBuilder.AddMenuEntry(FQuillscriptEditorToolbarCommands::Get().OpenIllustrationsFolder);
	// MenuBuilder.EndSection();

	return MenuBuilder.MakeWidget();
}

void FQuillscriptEditorModule::AddMenuEntry(FMenuBuilder& MenuBuilder) const
{
	// Create a section.
	MenuBuilder.BeginSection("CustomMenu", TAttribute(FText::FromString("Quillscript")));
	{
		// MenuBuilder.AddMenuEntry(
		// 	FText::FromString("Graph Viewer"),
		// 	FText::FromString("Spawn Graph Viewer tab."),
		// 	FSlateIcon(FAppStyle::GetAppStyleSetName(), "Kismet.HarvestBlueprintFromActors"),
		// 	FUIAction(FExecuteAction::CreateLambda([]{ FString Error; FPlatformProcess::LaunchURL(TEXT("https://quillscript.ink/"), TEXT(""), &Error); }))
		// );

		// Create a submenu inside the section.
		// MenuBuilder.AddSubMenu(FText::FromString("Tabs"),
		// 	FText::FromString("Open Editor tabs."),
		// 	FNewMenuDelegate::CreateRaw(this, &FQuillscriptEditorModule::FillSubmenu),
		// 	false,
		// 	FSlateIcon(this->StyleSet->GetStyleSetName(), "Tabs")
		// );
	}

	MenuBuilder.EndSection();
}

void FQuillscriptEditorModule::FillSubmenu(FMenuBuilder& MenuBuilder) const
{
	// Create the submenu entries.
	// MenuBuilder.AddMenuEntry(
	// 	FText::FromString("Script Viewer"),
	// 	FText::FromString("Spawn Script Viewer tab."),
	// 	FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.Tabs.Details"),
	// 	FUIAction(FExecuteAction::CreateRaw(this, &FQuillscriptEditorModule::SpawnScriptViewer))
	// );
	//
	// MenuBuilder.AddMenuEntry(
	// 	FText::FromString("Graph Viewer"),
	// 	FText::FromString("Spawn Graph Viewer tab."),
	// 	FSlateIcon(FAppStyle::GetAppStyleSetName(), "Kismet.HarvestBlueprintFromActors"),
	// 	FUIAction(FExecuteAction::CreateRaw(this, &FQuillscriptEditorModule::SpawnGraphViewer))
	// );

	// MenuBuilder.AddMenuEntry(
	// 	FText::FromString("Graph Viewer"),
	// 	FText::FromString("Spawn Graph Viewer tab."),
	// 	FSlateIcon(FAppStyle::GetAppStyleSetName(), "Kismet.HarvestBlueprintFromActors"),
	// 	FUIAction(FExecuteAction::CreateLambda([]{ FString Error; FPlatformProcess::LaunchURL(TEXT("https://quillscript.ink/"), TEXT(""), &Error); }))
	// );
}

void FQuillscriptEditorModule::SpawnScriptViewer() const
{
	// UEditorTools::SpawnTab(
	// 	FText::FromString("Script Viewer"),
	//	"/Quillscript/Editor/ScriptEditor/QuillscriptEditorBP.QuillscriptEditorBP",
	// 	FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.Tabs.Details")
	// );
}

void FQuillscriptEditorModule::OnGatherExtensions(const TSharedPtr<FExtender> Extender, UBlueprint* Blueprint)
{
	// // Stop, if the blueprint is not child of the target classes.
	// if (
	// 	!Blueprint ||
	// 	!Blueprint->ParentClass ||
	// 	!Blueprint->ParentClass->IsChildOf(UCard::StaticClass())
	// )
	// 	return;
	//
	// // This specific editor needs its own Command List with delegates that include the blueprint pointer.
	// if (const TSharedPtr<FUICommandList> CommandList = MakeShareable(new FUICommandList))
	// {
	// 	CommandList->MapAction(
	// 		FQuillscriptEditorToolbarCommands::Get().OpenAlbum,
	// 		FExecuteAction::CreateStatic(
	// 			&FQuillscriptEditorModule::OnOpenAlbum,
	// 			Blueprint
	// 		)
	// 	);
	// 	CommandList->MapAction(
	// 		FQuillscriptEditorToolbarCommands::Get().ViewCard,
	// 		FExecuteAction::CreateStatic(
	// 			&UAptEditor::OpenCardViewerTab,
	// 			Blueprint
	// 		)
	// 	);
	//
	// 	Extender->AddToolBarExtension(
	// 		"Asset",
	// 		EExtensionHook::After,
	// 		CommandList,
	// 		FToolBarExtensionDelegate::CreateStatic(&FQuillscriptEditorModule::AddBlueprintsToolbarButton)
	// 	);
	// }
}

void FQuillscriptEditorModule::AddBlueprintsToolbarButton(class FToolBarBuilder& Builder)
{
	// // Cards Blueprint - Cards Viewer.
	// Builder.AddToolBarButton(
	// 	FQuillscriptEditorToolbarCommands::Get().OpenAlbum,
	// 	NAME_None,
	// 	TAttribute<FText>(),
	// 	TAttribute<FText>(),
	// 	FSlateIcon(QuillscriptStyleName, "Cards"),
	// 	NAME_None
	// );
	//
	// // Cards Blueprint - Card Viewer.
	// Builder.AddToolBarButton(
	// 	FQuillscriptEditorToolbarCommands::Get().ViewCard,
	// 	NAME_None,
	// 	TAttribute<FText>(),
	// 	TAttribute<FText>(),
	// 	FSlateIcon(QuillscriptStyleName, "Card"),
	// 	NAME_None
	// );
}

void FQuillscriptEditorModule::OnOpenAlbum(UBlueprint* Blueprint)
{
	// if (Blueprint == nullptr)
	// 	return;
	//
	// const TObjectPtr<UClass> CardClass{ Blueprint->GeneratedClass };
	//
	// if (!CardClass || !CardClass->IsChildOf(UCard::StaticClass()))
	// 	return;
	//
	// // Get blueprint utility widget reference.
	// const FSoftObjectPath BlueprintPath{ FSoftObjectPath("EditorUtilityWidgetBlueprint'/Game/AptEditor/Widgets/CardsAlbumBP.CardsAlbumBP'") };
	// const TObjectPtr<UWidgetBlueprint> WidgetBlueprint{ Cast<UWidgetBlueprint>(BlueprintPath.TryLoad()) };
	//
	// if (!WidgetBlueprint || !IsValidChecked(WidgetBlueprint))
	// 	return;
	//
	// if (!WidgetBlueprint->GeneratedClass->IsChildOf(UEditorUtilityWidget::StaticClass()))
	// 	return;
	//
	// if (const TObjectPtr<UEditorUtilityWidgetBlueprint> EditorWidget{ Cast<UEditorUtilityWidgetBlueprint>(WidgetBlueprint) })
	// {
	// 	// Open tab.
	// 	const TObjectPtr<UEditorUtilitySubsystem> EditorUtilitySubsystem{ GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>() };
	//
	// 	if (UCardViewerEditorUtilityWidget* CardViewerEditorUtilityWidget{ Cast<UCardViewerEditorUtilityWidget>(EditorUtilitySubsystem->SpawnAndRegisterTab(EditorWidget)) })
	// 		CardViewerEditorUtilityWidget->UpdateCard(CardClass->GetDefaultObject<UCard>()->GetClass());
	// }
}


IMPLEMENT_MODULE( FQuillscriptEditorModule, QuillscriptEditor )