#include "ProceduralModelingToolkitEditorModule.h"

#include "ProceduralModelingToolkitDynamicMeshPipeline.h"

#include "Framework/Docking/TabManager.h"
#include "Modules/ModuleManager.h"
#include "Styling/AppStyle.h"
#include "ToolMenus.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

DEFINE_LOG_CATEGORY(LogProceduralModelingToolkit);

#define LOCTEXT_NAMESPACE "FProceduralModelingToolkitEditorModule"

namespace ProceduralModelingToolkit
{
	static const FName TabName("ProceduralModelingToolkit");
	static const FName MenuOwner("ProceduralModelingToolkit");
}

void FProceduralModelingToolkitEditorModule::StartupModule()
{
	UE_LOG(LogProceduralModelingToolkit, Log, TEXT("Procedural Modeling Toolkit editor module starting."));

	RegisterTabSpawner();

	UToolMenus::RegisterStartupCallback(
		FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FProceduralModelingToolkitEditorModule::RegisterMenus)
	);
}

void FProceduralModelingToolkitEditorModule::ShutdownModule()
{
	UE_LOG(LogProceduralModelingToolkit, Log, TEXT("Procedural Modeling Toolkit editor module shutting down."));

	if (UToolMenus::IsToolMenuUIEnabled())
	{
		UToolMenus::UnRegisterStartupCallback(this);
		UnregisterMenus();
	}

	UnregisterTabSpawner();
}

void FProceduralModelingToolkitEditorModule::RegisterTabSpawner()
{
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(
		ProceduralModelingToolkit::TabName,
		FOnSpawnTab::CreateRaw(this, &FProceduralModelingToolkitEditorModule::SpawnToolkitTab)
	)
	.SetDisplayName(LOCTEXT("ToolkitTabTitle", "Procedural Modeling Toolkit"))
	.SetTooltipText(LOCTEXT("ToolkitTabTooltip", "Open the Procedural Modeling Toolkit framework panel."))
	.SetIcon(FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.Tabs.Details"));
}

void FProceduralModelingToolkitEditorModule::UnregisterTabSpawner()
{
	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(ProceduralModelingToolkit::TabName);
}

void FProceduralModelingToolkitEditorModule::RegisterMenus()
{
	FToolMenuOwnerScoped OwnerScoped(ProceduralModelingToolkit::MenuOwner);

	if (UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.PlayToolBar"))
	{
		FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("PluginTools");
		FToolMenuEntry Entry = FToolMenuEntry::InitToolBarButton(
			"OpenProceduralModelingToolkit",
			FUIAction(FExecuteAction::CreateRaw(this, &FProceduralModelingToolkitEditorModule::OpenToolkitTab)),
			LOCTEXT("OpenToolkitLabel", "Procedural Toolkit"),
			LOCTEXT("OpenToolkitTooltip", "Open the Procedural Modeling Toolkit panel."),
			FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.Tabs.Details")
		);
		Section.AddEntry(Entry);
	}

	if (UToolMenu* MainMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window"))
	{
		FToolMenuSection& Section = MainMenu->FindOrAddSection("WindowLayout");
		Section.AddMenuEntry(
			"OpenProceduralModelingToolkitWindow",
			LOCTEXT("OpenToolkitWindowLabel", "Procedural Modeling Toolkit"),
			LOCTEXT("OpenToolkitWindowTooltip", "Open the Procedural Modeling Toolkit panel."),
			FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.Tabs.Details"),
			FUIAction(FExecuteAction::CreateRaw(this, &FProceduralModelingToolkitEditorModule::OpenToolkitTab))
		);
	}

	UE_LOG(LogProceduralModelingToolkit, Log, TEXT("Procedural Modeling Toolkit menus registered."));
}

void FProceduralModelingToolkitEditorModule::UnregisterMenus()
{
	UToolMenus::UnregisterOwner(ProceduralModelingToolkit::MenuOwner);
}

void FProceduralModelingToolkitEditorModule::OpenToolkitTab()
{
	UE_LOG(LogProceduralModelingToolkit, Log, TEXT("Opening Procedural Modeling Toolkit tab."));
	FGlobalTabmanager::Get()->TryInvokeTab(ProceduralModelingToolkit::TabName);
}

void FProceduralModelingToolkitEditorModule::ProcessSelectedStaticMeshes()
{
	const TArray<FProceduralModelingToolkitMeshPipelineResult> Results =
		FProceduralModelingToolkitDynamicMeshPipeline::ProcessSelectedStaticMeshes();

	int32 SuccessCount = 0;
	for (const FProceduralModelingToolkitMeshPipelineResult& Result : Results)
	{
		SuccessCount += Result.bSuccess ? 1 : 0;
	}

	UE_LOG(
		LogProceduralModelingToolkit,
		Log,
		TEXT("Dynamic Mesh pipeline processed %d selected mesh(es), success=%d."),
		Results.Num(),
		SuccessCount
	);
}

TSharedRef<SDockTab> FProceduralModelingToolkitEditorModule::SpawnToolkitTab(const FSpawnTabArgs& Args)
{
	return SNew(SDockTab)
		.TabRole(ETabRole::NomadTab)
		[
			SNew(SBorder)
			.Padding(16.0f)
			[
				SNew(SScrollBox)
				+ SScrollBox::Slot()
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SNew(STextBlock)
						.Text(LOCTEXT("ToolkitHeader", "Procedural Modeling Toolkit"))
						.Font(FAppStyle::GetFontStyle("DetailsView.CategoryFontStyle"))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(0.0f, 8.0f)
					[
						SNew(SSeparator)
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(0.0f, 8.0f, 0.0f, 0.0f)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("ToolkitStatus", "Dynamic Mesh pipeline: selected Static Mesh assets are duplicated, round-tripped through Dynamic Mesh, and saved as new assets."))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(0.0f, 8.0f, 0.0f, 0.0f)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("ToolkitScope", "Output path: /Game/EnvSandbox/Procedural/Meshes/Processed. Source meshes are never overwritten."))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(0.0f, 12.0f, 0.0f, 0.0f)
					[
						SNew(SButton)
						.Text(LOCTEXT("ProcessSelectedMeshesButton", "Process Selected Static Meshes"))
						.ToolTipText(LOCTEXT("ProcessSelectedMeshesTooltip", "Duplicate selected Static Mesh assets, convert through Dynamic Mesh, save as new Static Mesh assets, and validate the round trip."))
						.OnClicked_Lambda([this]()
						{
							ProcessSelectedStaticMeshes();
							return FReply::Handled();
						})
					]
				]
			]
		];
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FProceduralModelingToolkitEditorModule, ProceduralModelingToolkitEditor)
